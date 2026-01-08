#!/usr/bin/env python3
"""
CORTEX - Advanced Prompt Pipeline

Optimized prompt engineering system for RAG applications with:
- Template management with variable substitution
- Few-shot example integration
- Context optimization and ranking
- Token budget management
"""

import re
from dataclasses import dataclass
from typing import Any

# Try to import tiktoken for accurate token counting
try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DEFAULT_MAX_CONTEXT_TOKENS = 2048
DEFAULT_MAX_HISTORY_TURNS = 5
DEFAULT_ENCODING = "cl100k_base"  # GPT-4 tokenizer


# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are CORTEX AI, an expert assistant with access to a curated knowledge base.

Core Principles:
- Provide accurate, well-sourced answers
- Cite sources explicitly using [Source N] notation
- Admit uncertainty when context is insufficient
- Be concise yet comprehensive
- Maintain conversation coherence

Citation Guidelines:
- ONLY use information from the provided context
- Every factual claim must reference a source
- Present conflicting information from multiple sources when relevant
- Do NOT extrapolate beyond the given context

Response Format:
- Direct answer first
- Supporting details with citations
- Source references at the end if needed
"""

RAG_PROMPT_TEMPLATE = """Conversation History:
{history}

Retrieved Context (ranked by relevance):
{context}

Current Question: {question}

Instructions:
- Answer based on the context above
- Cite sources using [Source N]
- If context doesn't contain the answer, explain what's missing
- Maintain conversation flow

Answer:"""


# ═══════════════════════════════════════════════════════════════
# FEW-SHOT EXAMPLES
# ═══════════════════════════════════════════════════════════════

FEW_SHOT_EXAMPLES = [
    {
        "context": "[Source 1] Python error handling uses try-except blocks. The try block contains code that might raise exceptions, while except blocks handle specific error types.",
        "question": "How do I handle errors in Python?",
        "answer": "Use try-except blocks for error handling [Source 1]. Place potentially problematic code in the try block and handle specific exceptions in except blocks.",
    },
    {
        "context": "[Source 1] FastAPI supports async endpoints using async def. [Source 2] Use await with async database calls for better performance.",
        "question": "Should I use async in FastAPI?",
        "answer": "Yes, FastAPI supports async endpoints [Source 1]. Use async def for routes that involve I/O operations, especially database calls [Source 2], to improve performance.",
    },
    {
        "context": "[Source 1] NixOS uses declarative configuration in configuration.nix.",
        "question": "How do I deploy a web app?",
        "answer": "The provided context only covers NixOS configuration [Source 1], but doesn't contain specific information about web app deployment. I would need additional context about deployment strategies, hosting options, and web server configuration.",
    },
]


# ═══════════════════════════════════════════════════════════════
# TOKEN COUNTING
# ═══════════════════════════════════════════════════════════════


class TokenCounter:
    """Accurate token counting using tiktoken"""

    def __init__(self, encoding_name: str = DEFAULT_ENCODING):
        if TIKTOKEN_AVAILABLE:
            self.encoding = tiktoken.get_encoding(encoding_name)
        else:
            self.encoding = None

    def count(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Approximate: 1 token ≈ 4 characters
            return len(text) // 4


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════


@dataclass
class Source:
    """Retrieved source document"""

    id: int
    text: str
    score: float
    metadata: dict[str, Any]

    def format(self) -> str:
        """Format source for prompt"""
        return f"[Source {self.id}] {self.text}"


@dataclass
class Message:
    """Chat message"""

    role: str  # "user" | "assistant"
    content: str

    def format(self) -> str:
        """Format message for prompt"""
        role_label = "User" if self.role == "user" else "Assistant"
        return f"{role_label}: {self.content}"


# ═══════════════════════════════════════════════════════════════
# PROMPT TEMPLATE
# ═══════════════════════════════════════════════════════════════


class PromptTemplate:
    """Template with variable substitution"""

    def __init__(self, template: str):
        self.template = template
        self.variables = self._extract_variables(template)

    def _extract_variables(self, template: str) -> list[str]:
        """Extract {variable} placeholders"""
        return re.findall(r"\{(\w+)\}", template)

    def render(self, **kwargs) -> str:
        """Render template with variables"""
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing template variables: {missing}")

        return self.template.format(**kwargs)


# ═══════════════════════════════════════════════════════════════
# CONTEXT OPTIMIZATION
# ═══════════════════════════════════════════════════════════════


class ContextOptimizer:
    """Optimize retrieved context for prompt"""

    def __init__(self, max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS):
        self.max_tokens = max_tokens
        self.token_counter = TokenCounter()

    def optimize(self, sources: list[Source]) -> list[Source]:
        """
        Optimize sources to fit token budget

        Strategy:
        1. Sort by relevance score
        2. Remove near-duplicates
        3. Truncate to fit budget
        4. Re-rank by diversity
        """
        # Sort by score
        sorted_sources = sorted(sources, key=lambda x: x.score, reverse=True)

        # Remove duplicates
        unique_sources = self._dedup_sources(sorted_sources)

        # Fit to budget
        selected = []
        token_count = 0

        for source in unique_sources:
            source_tokens = self.token_counter.count(source.text)

            if token_count + source_tokens <= self.max_tokens:
                selected.append(source)
                token_count += source_tokens
            else:
                # Try to fit truncated version
                remaining = self.max_tokens - token_count
                if remaining > 100:  # Minimum useful context
                    truncated = self._truncate_source(source, remaining)
                    selected.append(truncated)
                break

        return selected

    def _dedup_sources(
        self, sources: list[Source], threshold: float = 0.8
    ) -> list[Source]:
        """Remove near-duplicate sources"""
        unique = []

        for source in sources:
            is_duplicate = False
            for existing in unique:
                similarity = self._text_similarity(source.text, existing.text)
                if similarity > threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(source)

        return unique

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity (Jaccard)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _truncate_source(self, source: Source, max_tokens: int) -> Source:
        """Truncate source to fit token budget"""
        words = source.text.split()
        truncated = ""

        for word in words:
            test = truncated + " " + word
            if self.token_counter.count(test) > max_tokens:
                break
            truncated = test

        return Source(
            id=source.id,
            text=truncated.strip() + "...",
            score=source.score,
            metadata=source.metadata,
        )


# ═══════════════════════════════════════════════════════════════
# PROMPT PIPELINE
# ═══════════════════════════════════════════════════════════════


class PromptPipeline:
    """Main prompt engineering pipeline"""

    def __init__(
        self,
        system_prompt: str = SYSTEM_PROMPT,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        max_history_turns: int = DEFAULT_MAX_HISTORY_TURNS,
    ):
        self.system_prompt = system_prompt
        self.max_context_tokens = max_context_tokens
        self.max_history_turns = max_history_turns

        self.template = PromptTemplate(RAG_PROMPT_TEMPLATE)
        self.optimizer = ContextOptimizer(max_context_tokens)
        self.token_counter = TokenCounter()

    def build_rag_prompt(
        self, question: str, sources: list[Source], history: list[Message] = None
    ) -> str:
        """
        Build complete RAG prompt

        Args:
            question: User's current question
            sources: Retrieved context sources
            history: Conversation history

        Returns:
            Complete prompt string
        """
        # Optimize context
        optimized_sources = self.optimizer.optimize(sources)
        context = self._format_context(optimized_sources)

        # Format history
        history_text = self._format_history(history or [])

        # Render template
        user_prompt = self.template.render(
            history=history_text, context=context, question=question
        )

        # Combine system + user
        full_prompt = f"{self.system_prompt}\n\n{user_prompt}"

        return full_prompt

    def _format_context(self, sources: list[Source]) -> str:
        """Format sources for prompt"""
        if not sources:
            return "[No relevant context found]"

        formatted = [source.format() for source in sources]
        return "\n\n".join(formatted)

    def _format_history(self, messages: list[Message]) -> str:
        """Format conversation history"""
        if not messages:
            return "[Start of conversation]"

        # Keep last N turns
        recent = messages[-self.max_history_turns * 2 :]  # *2 for user+assistant pairs

        formatted = [msg.format() for msg in recent]
        return "\n".join(formatted)

    def add_few_shot_examples(self, prompt: str, examples: list[dict] = None) -> str:
        """Add few-shot examples to prompt"""
        examples = examples or FEW_SHOT_EXAMPLES

        examples_text = "\n\nExample Interactions:\n"
        for i, ex in enumerate(examples[:3], 1):  # Limit to 3 examples
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Context: {ex['context']}\n"
            examples_text += f"Question: {ex['question']}\n"
            examples_text += f"Answer: {ex['answer']}\n"

        # Insert before the actual query
        return prompt.replace(
            "Current Question:", examples_text + "\nCurrent Question:"
        )

    def estimate_tokens(self, prompt: str) -> int:
        """Estimate token count for prompt"""
        return self.token_counter.count(prompt)


# ═══════════════════════════════════════════════════════════════
# CLI FOR TESTING
# ═══════════════════════════════════════════════════════════════


def main():
    """Test prompt pipeline"""
    # Example sources
    sources = [
        Source(1, "Error handling in Python uses try-except blocks.", 0.95, {}),
        Source(2, "FastAPI supports async/await for better performance.", 0.82, {}),
        Source(3, "Use logging instead of print for production code.", 0.75, {}),
    ]

    # Example history
    history = [
        Message("user", "Tell me about Python"),
        Message("assistant", "Python is a versatile programming language."),
    ]

    # Build prompt
    pipeline = PromptPipeline()
    prompt = pipeline.build_rag_prompt(
        question="How do I handle errors?", sources=sources, history=history
    )

    print("=" * 60)
    print("GENERATED PROMPT")
    print("=" * 60)
    print(prompt)
    print("\n" + "=" * 60)
    print(f"Token count: {pipeline.estimate_tokens(prompt)}")


if __name__ == "__main__":
    main()
