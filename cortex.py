#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  CORTEX v1.1 - Intelligent Markdown ETL Pipeline                ║
║  ─────────────────────────────────────────────────────────────── ║
║  • Local LLM processing via llamacpp server                     ║
║  • Semantic Chunking Integration (New!)                         ║
║  • Extract: Themes, Patterns, Learnings, Concepts, Recommendations 
║  • Batch processing with configurable concurrency               ║
║  • JSON schema validation with Pydantic                         ║
║  • VRAM monitoring and retry logic                              ║
║  • Output: JSON Lines (.jsonl)                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import logging
import argparse
import psutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

# External imports
try:
    from pydantic import BaseModel, Field, ValidationError, field_validator
    import requests
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("\n📦 Install required packages:")
    print("   nix develop")
    sys.exit(1)

# Optional Chunker Import
try:
    from cortex_chunker import MarkdownChunker, ChunkStrategy
    CHUNKER_AVAILABLE = True
except ImportError:
    CHUNKER_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

VERSION = "1.1.0"
CODENAME = "CORTEX"

# LlamaCPP Server Configuration
DEFAULT_MODEL = "unsloth_Qwen3-Coder-30B-A3B-Instruct-GGUF_Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf"
DEFAULT_LLAMACPP_URL = "http://localhost:8080"
DEFAULT_CONTEXT_SIZE = 4096
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.3  # Low temperature for consistent extraction

# Processing Configuration
DEFAULT_BATCH_SIZE = 10
DEFAULT_WORKERS = 4
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 2  # seconds

# VRAM Monitoring
VRAM_CHECK_INTERVAL = 5  # seconds
VRAM_WARNING_THRESHOLD_MB = 512  # Warn if less than 512MB available
VRAM_CRITICAL_THRESHOLD_MB = 256  # Pause if less than 256MB available

# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS - JSON Schema Validation
# ═══════════════════════════════════════════════════════════════

class ExtractionLevel(str, Enum):
    """Extraction confidence level"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Theme(BaseModel):
    """Extracted theme from markdown content"""
    title: str = Field(..., description="Theme title (2-5 words)")
    description: str = Field(..., description="Brief theme description")
    confidence: ExtractionLevel = Field(default=ExtractionLevel.MEDIUM)
    keywords: List[str] = Field(default_factory=list, description="Related keywords")

    @field_validator('keywords')
    @classmethod
    def limit_keywords(cls, v):
        return v[:10]  # Max 10 keywords


class Pattern(BaseModel):
    """Identified pattern in the content"""
    pattern_type: str = Field(..., description="Type of pattern (e.g., 'code', 'workflow', 'concept')")
    description: str = Field(..., description="Pattern description")
    examples: List[str] = Field(default_factory=list, description="Examples from content")
    frequency: int = Field(default=1, ge=1, description="How often this pattern appears")

    @field_validator('examples')
    @classmethod
    def limit_examples(cls, v):
        return v[:3]  # Max 3 examples


class Learning(BaseModel):
    """Key learning or insight"""
    title: str = Field(..., description="Learning title")
    description: str = Field(..., description="Detailed description")
    category: str = Field(..., description="Category (e.g., 'technical', 'process', 'concept')")
    actionable: bool = Field(default=False, description="Is this actionable?")


class Concept(BaseModel):
    """Core concept explained in the document"""
    name: str = Field(..., description="Concept name")
    definition: str = Field(..., description="Concept definition")
    related_concepts: List[str] = Field(default_factory=list, description="Related concepts")
    complexity: ExtractionLevel = Field(default=ExtractionLevel.MEDIUM)

    @field_validator('related_concepts')
    @classmethod
    def limit_related(cls, v):
        return v[:5]  # Max 5 related concepts


class Recommendation(BaseModel):
    """Actionable recommendation"""
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    priority: ExtractionLevel = Field(..., description="Priority level")
    category: str = Field(..., description="Category (e.g., 'best_practice', 'optimization', 'security')")
    implementation_effort: str = Field(..., description="Effort level (low/medium/high)")


class MarkdownInsights(BaseModel):
    """Complete insights extracted from a markdown file"""
    file_path: str = Field(..., description="Source file path")
    file_name: str = Field(..., description="Source file name")
    processed_at: str = Field(..., description="ISO timestamp of processing")
    word_count: int = Field(..., ge=0, description="Word count of source")
    
    # Extracted data
    themes: List[Theme] = Field(default_factory=list, description="Identified themes")
    patterns: List[Pattern] = Field(default_factory=list, description="Identified patterns")
    learnings: List[Learning] = Field(default_factory=list, description="Key learnings")
    concepts: List[Concept] = Field(default_factory=list, description="Core concepts")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Actionable recommendations")
    
    # Metadata
    extraction_confidence: ExtractionLevel = Field(default=ExtractionLevel.MEDIUM)
    processing_time_seconds: float = Field(..., ge=0)
    model_used: str = Field(...)
    chunk_count: int = Field(default=1, description="Number of chunks processed")
    
    @field_validator('themes', 'patterns', 'learnings', 'concepts', 'recommendations')
    @classmethod
    def check_not_empty_lists(cls, v):
        # Allow empty lists but log warning
        if len(v) == 0:
            logging.warning(f"Empty list detected")
        return v


# ═══════════════════════════════════════════════════════════════
# SYSTEM MONITORING
# ═══════════════════════════════════════════════════════════════

class SystemMonitor:
    """Monitor system resources, especially VRAM"""
    
    def __init__(self, console: Console):
        self.console = console
        self.last_check = 0
        
    def get_vram_usage(self) -> Dict[str, Any]:
        """Get GPU VRAM usage if available"""
        try:
            # Try nvidia-smi for NVIDIA GPUs
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total,memory.free', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                used, total, free = map(int, result.stdout.strip().split(','))
                return {
                    'used_mb': used,
                    'total_mb': total,
                    'free_mb': free,
                    'usage_percent': (used / total) * 100 if total > 0 else 0
                }
        except Exception as e:
            logging.debug(f"VRAM check failed: {e}")
        
        return {'free_mb': float('inf'), 'available': False}
    
    def get_ram_usage(self) -> Dict[str, Any]:
        """Get system RAM usage"""
        mem = psutil.virtual_memory()
        return {
            'used_mb': mem.used // (1024 * 1024),
            'total_mb': mem.total // (1024 * 1024),
            'free_mb': mem.available // (1024 * 1024),
            'usage_percent': mem.percent
        }
    
    def check_resources(self, warn_only: bool = False) -> bool:
        """
        Check system resources
        Returns True if safe to proceed, False if critical
        """
        current_time = time.time()
        
        # Rate limit checks
        if current_time - self.last_check < VRAM_CHECK_INTERVAL:
            return True
        
        self.last_check = current_time
        
        vram = self.get_vram_usage()
        ram = self.get_ram_usage()
        
        # Check VRAM
        if vram.get('available', False):
            free_vram = vram['free_mb']
            
            if free_vram < VRAM_CRITICAL_THRESHOLD_MB:
                if not warn_only:
                    self.console.print(f"[red]⚠️  CRITICAL: VRAM low ({free_vram}MB free). Pausing...[/red]")
                    time.sleep(5)  # Brief pause to let VRAM free up
                return False
            elif free_vram < VRAM_WARNING_THRESHOLD_MB:
                self.console.print(f"[yellow]⚠️  WARNING: VRAM low ({free_vram}MB free)[/yellow]")
        
        # Check RAM
        if ram['free_mb'] < 512:
            self.console.print(f"[yellow]⚠️  WARNING: RAM low ({ram['free_mb']}MB free)[/yellow]")
        
        return True


# ═══════════════════════════════════════════════════════════════
# LLAMACPP CLIENT
# ═══════════════════════════════════════════════════════════════

class LlamaCppClient:
    """Client for llamacpp server API"""
    
    def __init__(self, 
                 base_url: str = DEFAULT_LLAMACPP_URL,
                 model: str = DEFAULT_MODEL,
                 context_size: int = DEFAULT_CONTEXT_SIZE,
                 max_tokens: int = DEFAULT_MAX_TOKENS,
                 temperature: float = DEFAULT_TEMPERATURE):
        
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.context_size = context_size
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # API endpoints
        self.completion_endpoint = f"{self.base_url}/completion"
        self.health_endpoint = f"{self.base_url}/health"
        
        logging.info(f"LlamaCpp client initialized: {self.base_url}")
    
    def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return False
    
    def generate(self, prompt: str, max_retries: int = DEFAULT_RETRY_ATTEMPTS) -> Optional[str]:
        """
        Generate completion from prompt
        Returns the generated text or None on failure
        """
        payload = {
            "prompt": prompt,
            "n_predict": self.max_tokens,
            "temperature": self.temperature,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "stop": ["</s>", "###", "\n\n\n"],
            "stream": False
        }
        
        for attempt in range(max_retries):
            try:
                logging.debug(f"Sending completion request (attempt {attempt + 1}/{max_retries})")
                response = requests.post(
                    self.completion_endpoint,
                    json=payload,
                    timeout=120  # 2 minutes timeout for generation
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get('content', '').strip()
                    
                    if content:
                        logging.debug(f"Generated {len(content)} characters")
                        return content
                    else:
                        logging.warning("Empty response from model")
                else:
                    logging.error(f"API error: {response.status_code} - {response.text}")
            
            except requests.Timeout:
                logging.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logging.error(f"Generation error: {e}")
            
            # Exponential backoff
            if attempt < max_retries - 1:
                delay = DEFAULT_RETRY_DELAY * (2 ** attempt)
                logging.info(f"Retrying in {delay}s...")
                time.sleep(delay)
        
        logging.error("All retry attempts exhausted")
        return None


# ═══════════════════════════════════════════════════════════════
# PROMPT ENGINEERING
# ═══════════════════════════════════════════════════════════════

class PromptBuilder:
    """Build structured prompts for extraction tasks"""
    
    SYSTEM_PROMPT = """You are an expert data analyst specializing in extracting structured insights from markdown documentation.

Your task is to analyze markdown content and extract:
1. **Themes**: Main topics and subjects discussed
2. **Patterns**: Recurring structures, workflows, or code patterns
3. **Learnings**: Key insights and knowledge gained
4. **Concepts**: Core ideas and definitions explained
5. **Recommendations**: Actionable best practices and improvements

OUTPUT FORMAT: You MUST respond with ONLY a valid JSON object. Do not include markdown code blocks, explanations, or any text outside the JSON.

JSON Schema:
{
  "themes": [{"title": str, "description": str, "confidence": "high|medium|low", "keywords": [str]}],
  "patterns": [{"pattern_type": str, "description": str, "examples": [str], "frequency": int}],
  "learnings": [{"title": str, "description": str, "category": str, "actionable": bool}],
  "concepts": [{"name": str, "definition": str, "related_concepts": [str], "complexity": "high|medium|low"}],
  "recommendations": [{"title": str, "description": str, "priority": "high|medium|low", "category": str, "implementation_effort": "low|medium|high"}]
}"""
    
    @staticmethod
    def build_extraction_prompt(content: str, file_name: str, chunk_info: str = "") -> str:
        """Build extraction prompt for markdown content"""
        
        # Truncate content if too long (leave room for response)
        # Note: With chunking, this is less likely to happen
        max_content_chars = DEFAULT_CONTEXT_SIZE * 3  # Rough estimate: 1 token ≈ 3 chars
        if len(content) > max_content_chars:
            content = content[:max_content_chars] + "\n\n[... content truncated ...]"
        
        context_str = f"SOURCE FILE: {file_name}"
        if chunk_info:
            context_str += f" | {chunk_info}"
            
        prompt = f"""
{PromptBuilder.SYSTEM_PROMPT}

{context_str}

CONTENT:
{content}

INSTRUCTIONS:
1. Analyze the above markdown content carefully
2. Extract ALL relevant themes, patterns, learnings, concepts, and recommendations
3. Be specific and detailed in descriptions
4. Assign appropriate confidence/priority levels
5. Provide concrete examples where applicable

OUTPUT (JSON only, no markdown):"""
        
        return prompt
    
    @staticmethod
    def parse_json_response(response: str) -> Optional[Dict]:
        """
        Parse JSON from LLM response
        Handles cases where model includes markdown code blocks
        """
        # Remove markdown code blocks if present
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        # Try to extract JSON object
        response = response.strip()
        
        # Find first { and last }
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            response = response[start_idx:end_idx + 1]
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error: {e}")
            logging.debug(f"Response: {response[:500]}...")
            return None


# ═══════════════════════════════════════════════════════════════
# MARKDOWN PROCESSOR - Main ETL Engine
# ═══════════════════════════════════════════════════════════════

@dataclass
class ProcessingStats:
    """Track processing statistics"""
    total_files: int = 0
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    total_words: int = 0
    total_processing_time: float = 0.0
    errors: List[Dict] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.processed / self.total_files) * 100


class MarkdownProcessor:
    """Main ETL processor for markdown files"""
    
    def __init__(self, 
                 input_dir: str,
                 output_file: str,
                 llamacpp_url: str = DEFAULT_LLAMACPP_URL,
                 model: str = DEFAULT_MODEL,
                 batch_size: int = DEFAULT_BATCH_SIZE,
                 workers: int = DEFAULT_WORKERS,
                 context_size: int = DEFAULT_CONTEXT_SIZE,
                 chunking_strategy: Optional[str] = None,
                 chunk_size: int = 1024,
                 verbose: bool = False):
        
        self.input_dir = Path(input_dir).resolve()
        self.output_file = Path(output_file).resolve()
        self.batch_size = batch_size
        self.workers = workers
        self.verbose = verbose
        
        # Chunking configuration
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunker = None
        
        if self.chunking_strategy and CHUNKER_AVAILABLE:
            try:
                self.chunker = MarkdownChunker(
                    strategy=ChunkStrategy(self.chunking_strategy),
                    max_tokens=self.chunk_size
                )
                logging.info(f"Chunking enabled: {self.chunking_strategy} ({self.chunk_size} tokens)")
            except Exception as e:
                logging.error(f"Failed to initialize chunker: {e}")
        elif self.chunking_strategy and not CHUNKER_AVAILABLE:
            logging.warning("Chunking requested but cortex_chunker module not found. Proceeding without chunking.")
        
        # Ensure input exists
        if not self.input_dir.exists():
            raise ValueError(f"Input directory does not exist: {self.input_dir}")
        
        # Create output directory
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.console = Console()
        self.llm_client = LlamaCppClient(
            base_url=llamacpp_url,
            model=model,
            context_size=context_size
        )
        self.monitor = SystemMonitor(self.console)
        self.stats = ProcessingStats()
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        chunk_msg = f"\n📦 Chunking: {self.chunking_strategy}" if self.chunker else "\n📦 Chunking: Disabled"
        
        self.console.print(Panel.fit(
            f"[bold cyan]CORTEX v{VERSION}[/bold cyan]\n"
            f"Intelligent Markdown ETL Pipeline\n\n"
            f"📁 Input:  {self.input_dir}\n"
            f"📄 Output: {self.output_file}\n"
            f"🤖 Model:  {model}\n"
            f"⚙️  Workers: {workers} | Batch: {batch_size}"
            f"{chunk_msg}",
            title="Configuration",
            border_style="cyan"
        ))
    
    def discover_markdown_files(self) -> List[Path]:
        """Discover all .md files in input directory"""
        files = list(self.input_dir.rglob('*.md'))
        
        # Filter out hidden files and specific patterns
        files = [f for f in files if not any(part.startswith('.') for part in f.parts)]
        
        self.stats.total_files = len(files)
        self.console.print(f"\n[green]📋 Discovered {len(files)} markdown files[/green]")
        
        return files
    
    def read_markdown_file(self, filepath: Path) -> Optional[str]:
        """Read markdown file content"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            logging.error(f"Failed to read {filepath}: {e}")
            return None
    
    def count_words(self, content: str) -> int:
        """Count words in content"""
        return len(content.split())
    
    def process_chunk(self, text: str, filename: str, chunk_info: str) -> Optional[Dict]:
        """Process a single text chunk"""
        prompt = PromptBuilder.build_extraction_prompt(text, filename, chunk_info)
        response = self.llm_client.generate(prompt)
        
        if not response:
            return None
            
        return PromptBuilder.parse_json_response(response)

    def aggregate_insights(self, chunk_results: List[Dict], filepath: Path, word_count: int, processing_time: float) -> MarkdownInsights:
        """Aggregate insights from multiple chunks into a single result"""
        aggregated = {
            'themes': [],
            'patterns': [],
            'learnings': [],
            'concepts': [],
            'recommendations': []
        }
        
        for res in chunk_results:
            if not res: continue
            for key in aggregated:
                if key in res and isinstance(res[key], list):
                    # Extend and deduplicate if needed (simple dedupe for now)
                    for item in res[key]:
                        if item not in aggregated[key]: # Basic check
                            aggregated[key].append(item)
        
        # Calculate average confidence
        confidences = []
        for res in chunk_results:
            if res and 'extraction_confidence' in res:
                # Convert 'high', 'medium', 'low' to numeric for averaging
                if res['extraction_confidence'] == 'high': confidences.append(1.0)
                elif res['extraction_confidence'] == 'medium': confidences.append(0.5)
                elif res['extraction_confidence'] == 'low': confidences.append(0.0)
        
        avg_confidence_val = sum(confidences) / len(confidences) if confidences else 0.5 # Default to medium
        # Convert back to ExtractionLevel
        if avg_confidence_val > 0.75: final_confidence = ExtractionLevel.HIGH
        elif avg_confidence_val > 0.25: final_confidence = ExtractionLevel.MEDIUM
        else: final_confidence = ExtractionLevel.LOW

        return MarkdownInsights(
            file_path=str(filepath),
            file_name=filepath.name,
            processed_at=datetime.now(timezone.utc).isoformat(),
            word_count=word_count,
            themes=[Theme(**t) for t in aggregated['themes']],
            patterns=[Pattern(**p) for p in aggregated['patterns']],
            learnings=[Learning(**l) for l in aggregated['learnings']],
            concepts=[Concept(**c) for c in aggregated['concepts']],
            recommendations=[Recommendation(**r) for r in aggregated['recommendations']],
            processing_time_seconds=processing_time,
            model_used=self.llm_client.model,
            chunk_count=len(chunk_results),
            extraction_confidence=final_confidence
        )

    def process_single_file(self, filepath: Path) -> Optional[MarkdownInsights]:
        """Process a single markdown file through the ETL pipeline"""
        start_time = time.time()
        
        try:
            # Check resources before processing
            if not self.monitor.check_resources():
                logging.warning(f"Pausing due to low resources before processing {filepath.name}")
                time.sleep(10)
            
            # Read content
            content = self.read_markdown_file(filepath)
            if not content:
                self.stats.skipped += 1
                return None
            
            word_count = self.count_words(content)
            self.stats.total_words += word_count
            
            chunk_results = []
            
            # Chunking Logic
            if self.chunker:
                logging.info(f"Chunking {filepath.name}...")
                chunks = self.chunker.chunk_text(content, str(filepath))
                logging.info(f"Generated {len(chunks)} chunks for {filepath.name}")
                
                for i, chunk in enumerate(chunks):
                    chunk_info = f"Chunk {i+1}/{len(chunks)}"
                    res = self.process_chunk(chunk.text, filepath.name, chunk_info)
                    if res:
                        chunk_results.append(res)
            else:
                # No chunking - process as single unit
                res = self.process_chunk(content, filepath.name, "")
                if res:
                    chunk_results.append(res)
            
            if not chunk_results:
                raise ValueError("No valid insights extracted from any chunk")
            
            # Aggregate and Validate
            processing_time = time.time() - start_time
            insights = self.aggregate_insights(chunk_results, filepath, word_count, processing_time)
            
            self.stats.processed += 1
            self.stats.total_processing_time += processing_time
            
            chunk_str = f"{insights.chunk_count} chunks" if insights.chunk_count > 1 else "1 doc"
            
            self.console.print(
                f"[green]✓[/green] {filepath.name} ({chunk_str}) | "
                f"{len(insights.themes)}T {len(insights.patterns)}P {len(insights.learnings)}L | "
                f"{processing_time:.1f}s"
            )
            
            return insights
        
        except ValidationError as e:
            self.stats.failed += 1
            error_msg = f"Validation error: {e}"
            logging.error(f"{filepath.name}: {error_msg}")
            self.stats.errors.append({
                'file': str(filepath),
                'error': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return None
        
        except Exception as e:
            self.stats.failed += 1
            error_msg = str(e)
            logging.error(f"{filepath.name}: {error_msg}")
            self.stats.errors.append({
                'file': str(filepath),
                'error': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return None
    
    def save_insights(self, insights: MarkdownInsights):
        """Save insights to JSONL file"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                json.dump(insights.dict(), f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logging.error(f"Failed to save insights: {e}")
    
    def process_batch(self, files: List[Path]):
        """Process a batch of files with threading"""
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.process_single_file, f): f for f in files}
            
            for future in as_completed(futures):
                filepath = futures[future]
                try:
                    insights = future.result()
                    if insights:
                        self.save_insights(insights)
                except Exception as e:
                    logging.error(f"Worker exception for {filepath}: {e}")
    
    def run(self):
        """Execute the complete ETL pipeline"""
        overall_start = time.time()
        
        # Health check
        self.console.print("\n[yellow]🔍 Checking llamacpp server...[/yellow]")
        if not self.llm_client.health_check():
            self.console.print("[red]❌ llamacpp server health check failed![/red]")
            self.console.print(f"[yellow]   Please ensure the server is running at {self.llm_client.base_url}[/yellow]")
            sys.exit(1)
        self.console.print("[green]✓ Server is healthy[/green]")
        
        # Discover files
        files = self.discover_markdown_files()
        if not files:
            self.console.print("[yellow]No markdown files found![/yellow]")
            return
        
        # Clear/create output file
        if self.output_file.exists():
            self.console.print(f"[yellow]⚠️  Output file exists, appending...[/yellow]")
        else:
            self.output_file.touch()
        
        # Process in batches
        self.console.print(f"\n[bold cyan]🚀 Starting processing...[/bold cyan]\n")
        
        for i in range(0, len(files), self.batch_size):
            batch = files[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(files) + self.batch_size - 1) // self.batch_size
            
            self.console.print(f"\n[bold]Batch {batch_num}/{total_batches}[/bold] ({len(batch)} files)")
            self.console.print("─" * 70)
            
            self.process_batch(batch)
            
            # Brief pause between batches
            if i + self.batch_size < len(files):
                time.sleep(2)
        
        # Generate final report
        overall_duration = time.time() - overall_start
        self.generate_report(overall_duration)
    
    def generate_report(self, duration: float):
        """Generate and display final processing report"""
        self.console.print("\n" + "═" * 70)
        self.console.print("[bold cyan]📊 PROCESSING REPORT[/bold cyan]")
        self.console.print("═" * 70 + "\n")
        
        # Stats table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", justify="right", style="green")
        
        table.add_row("Total Files", str(self.stats.total_files))
        table.add_row("Processed Successfully", f"{self.stats.processed} ({self.stats.success_rate:.1f}%)")
        table.add_row("Failed", str(self.stats.failed))
        table.add_row("Skipped", str(self.stats.skipped))
        table.add_row("Total Words Analyzed", f"{self.stats.total_words:,}")
        table.add_row("Total Processing Time", f"{self.stats.total_processing_time:.1f}s")
        table.add_row("Overall Duration", f"{duration:.1f}s")
        
        if self.stats.processed > 0:
            avg_time = self.stats.total_processing_time / self.stats.processed
            table.add_row("Avg Time per File", f"{avg_time:.1f}s")
        
        self.console.print(table)
        
        # Errors
        if self.stats.errors:
            self.console.print(f"\n[red]❌ {len(self.stats.errors)} Errors:[/red]")
            for err in self.stats.errors[:10]:  # Show first 10
                self.console.print(f"  • {Path(err['file']).name}: {err['error']}")
            
            if len(self.stats.errors) > 10:
                self.console.print(f"  ... and {len(self.stats.errors) - 10} more")
        
        # Output location
        self.console.print(f"\n[green]✓ Results saved to:[/green] {self.output_file}")
        
        # System resources
        ram = self.monitor.get_ram_usage()
        vram = self.monitor.get_vram_usage()
        
        self.console.print(f"\n[cyan]💾 RAM Usage:[/cyan] {ram['usage_percent']:.1f}% ({ram['used_mb']}/{ram['total_mb']} MB)")
        if vram.get('available'):
            self.console.print(f"[cyan]🎮 VRAM Usage:[/cyan] {vram['usage_percent']:.1f}% ({vram['used_mb']}/{vram['total_mb']} MB)")


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description=f"CORTEX v{VERSION} - Intelligent Markdown ETL Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Process all markdown files in input_data/
  cortex.py -i input_data -o insights.jsonl

  # Custom llamacpp server and batch size
  cortex.py -i notes/ -o insights.jsonl --url http://localhost:8080 --batch-size 5

  # Enable semantic chunking (requires cortex_chunker)
  cortex.py -i docs/ -o results.jsonl --chunk-strategy recursive --chunk-size 1024"""
    )
    
    # Required arguments
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input directory containing markdown files'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output JSONL file path'
    )
    
    # LlamaCPP configuration
    parser.add_argument(
        '--url',
        default=DEFAULT_LLAMACPP_URL,
        help=f'LlamaCPP server URL (default: {DEFAULT_LLAMACPP_URL})'
    )
    parser.add_argument(
        '--model',
        default=DEFAULT_MODEL,
        help=f'Model name (default: {DEFAULT_MODEL[:50]}...)'
    )
    parser.add_argument(
        '--context-size',
        type=int,
        default=DEFAULT_CONTEXT_SIZE,
        help=f'Context window size (default: {DEFAULT_CONTEXT_SIZE})'
    )
    
    # Processing configuration
    parser.add_argument(
        '--batch-size',
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f'Batch size for processing (default: {DEFAULT_BATCH_SIZE})'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=DEFAULT_WORKERS,
        help=f'Number of worker threads (default: {DEFAULT_WORKERS})'
    )
    
    # Chunking options
    parser.add_argument(
        '--chunk-strategy',
        choices=['recursive', 'sliding', 'simple'],
        help='Enable chunking with specific strategy'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1024,
        help='Max tokens per chunk (default: 1024)'
    )
    
    # Flags
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'CORTEX v{VERSION}'
    )
    
    args = parser.parse_args()
    
    try:
        processor = MarkdownProcessor(
            input_dir=args.input,
            output_file=args.output,
            llamacpp_url=args.url,
            model=args.model,
            batch_size=args.batch_size,
            workers=args.workers,
            context_size=args.context_size,
            chunking_strategy=args.chunk_strategy,
            chunk_size=args.chunk_size,
            verbose=args.verbose
        )
        
        processor.run()
        
    except KeyboardInterrupt:
        print("\n\n[yellow]⚠️  Processing interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        print(f"\n[red]❌ Fatal error: {e}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
