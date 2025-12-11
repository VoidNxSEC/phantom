#!/usr/bin/env python3
"""
Quick validation test for cortex.py
Tests the core components without requiring the LlamaCPP server
"""

import sys
from pathlib import Path

# Add parent directory to path to import cortex
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required imports work"""
    print("🔍 Testing imports...")
    try:
        from pydantic import BaseModel, Field, ValidationError
        from rich.console import Console
        from rich.progress import Progress
        import requests
        import psutil
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_pydantic_models():
    """Test Pydantic model validation"""
    print("\n🔍 Testing Pydantic models...")
    try:
        import cortex
        
        # Test Theme model
        theme = cortex.Theme(
            title="Test Theme",
            description="A test theme description",
            confidence=cortex.ExtractionLevel.HIGH,
            keywords=["test", "validation"]
        )
        
        # Test Pattern model
        pattern = cortex.Pattern(
            pattern_type="test",
            description="Test pattern",
            examples=["example1", "example2"],
            frequency=2
        )
        
        # Test Learning model
        learning = cortex.Learning(
            title="Test Learning",
            description="Test learning description",
            category="technical",
            actionable=True
        )
        
        # Test Concept model
        concept = cortex.Concept(
            name="Test Concept",
            definition="Test definition",
            related_concepts=["concept1"],
            complexity=cortex.ExtractionLevel.MEDIUM
        )
        
        # Test Recommendation model
        recommendation = cortex.Recommendation(
            title="Test Recommendation",
            description="Test recommendation description",
            priority=cortex.ExtractionLevel.HIGH,
            category="best_practice",
            implementation_effort="low"
        )
        
        print("✅ All Pydantic models validated!")
        return True
        
    except Exception as e:
        print(f"❌ Pydantic validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_builder():
    """Test prompt building functionality"""
    print("\n🔍 Testing PromptBuilder...")
    try:
        import cortex
        
        content = "# Test Document\n\nThis is a test markdown file."
        prompt = cortex.PromptBuilder.build_extraction_prompt(content, "test.md")
        
        assert "Test Document" in prompt
        assert "test.md" in prompt
        assert "JSON" in prompt
        
        print("✅ PromptBuilder works!")
        return True
        
    except Exception as e:
        print(f"❌ PromptBuilder test failed: {e}")
        return False


def test_json_parsing():
    """Test JSON response parsing"""
    print("\n🔍 Testing JSON parsing...")
    try:
        import cortex
        
        # Test with markdown code blocks
        response1 = """```json
{
  "themes": [],
  "patterns": [],
  "learnings": [],
  "concepts": [],
  "recommendations": []
}
```"""
        
        data1 = cortex.PromptBuilder.parse_json_response(response1)
        assert data1 is not None
        assert "themes" in data1
        
        # Test with plain JSON
        response2 = """
{
  "themes": [{"title": "Test", "description": "Test desc", "confidence": "high", "keywords": []}],
  "patterns": [],
  "learnings": [],
  "concepts": [],
  "recommendations": []
}
"""
        
        data2 = cortex.PromptBuilder.parse_json_response(response2)
        assert data2 is not None
        assert len(data2["themes"]) == 1
        
        print("✅ JSON parsing works!")
        return True
        
    except Exception as e:
        print(f"❌ JSON parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_monitor():
    """Test system monitoring"""
    print("\n🔍 Testing SystemMonitor...")
    try:
        import cortex
        from rich.console import Console
        
        console = Console()
        monitor = cortex.SystemMonitor(console)
        
        # Test RAM monitoring
        ram = monitor.get_ram_usage()
        assert 'used_mb' in ram
        assert 'free_mb' in ram
        assert ram['usage_percent'] >= 0
        assert ram['usage_percent'] <= 100
        
        print(f"   RAM: {ram['usage_percent']:.1f}% used ({ram['used_mb']}/{ram['total_mb']} MB)")
        
        # Test VRAM monitoring (may not be available)
        vram = monitor.get_vram_usage()
        if vram.get('available'):
            print(f"   VRAM: {vram['usage_percent']:.1f}% used ({vram['used_mb']}/{vram['total_mb']} MB)")
        else:
            print("   VRAM: Not available (no NVIDIA GPU detected)")
        
        print("✅ SystemMonitor works!")
        return True
        
    except Exception as e:
        print(f"❌ SystemMonitor test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("CORTEX Validation Test Suite")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_pydantic_models,
        test_prompt_builder,
        test_json_parsing,
        test_system_monitor
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if all(results):
        print("\n🎉 All tests passed! CORTEX is ready to use.")
        print("\nNext steps:")
        print("1. Start your llamacpp server")
        print("2. Run: ./cortex.py -i input_data -o output/insights.jsonl")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
