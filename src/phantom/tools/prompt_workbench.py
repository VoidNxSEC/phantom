"""
CORTEX - Prompt Workbench

Testing and validation framework for prompts
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prompt_pipeline import PromptPipeline, PromptTemplate, TokenCounter

# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class PromptTest:
    """Test case for prompt"""
    name: str
    template: str
    variables: dict[str, Any]
    expected_keywords: list[str] = None
    max_tokens: int = 2048
    min_quality_score: float = 0.7


@dataclass
class TestResult:
    """Result of prompt test"""
    test_name: str
    passed: bool
    output: str
    tokens_used: int
    latency_ms: float
    quality_score: float
    errors: list[str] = None


# ═══════════════════════════════════════════════════════════════
# PROMPT WORKBENCH
# ═══════════════════════════════════════════════════════════════

class PromptWorkbench:
    """Interactive prompt testing environment"""

    def __init__(self, pipeline: PromptPipeline = None):
        self.pipeline = pipeline or PromptPipeline()
        self.token_counter = TokenCounter()
        self.tests: list[PromptTest] = []

    def render_template(
        self,
        template: str,
        variables: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Render template with variables and return analysis
        
        Returns:
            - rendered: Rendered prompt
            - tokens: Token count
            - variables_used: List of variables actually used
            - warnings: Any issues found
        """
        try:
            # Create temporary template
            temp = PromptTemplate(template)

            # Render
            rendered = temp.render(**variables)

            # Count tokens
            tokens = self.token_counter.count(rendered)

            # Check which variables were used
            variables_used = temp.variables

            # Warnings
            warnings = []
            if tokens > 4000:
                warnings.append(f"High token count: {tokens}")

            unused = set(variables.keys()) - set(variables_used)
            if unused:
                warnings.append(f"Unused variables: {unused}")

            return {
                "rendered": rendered,
                "tokens": tokens,
                "variables_used": variables_used,
                "warnings": warnings,
                "success": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def add_test(self, test: PromptTest):
        """Add test case"""
        self.tests.append(test)

    def run_test(
        self,
        test: PromptTest,
        llm_function = None
    ) -> TestResult:
        """
        Run single test case
        
        Args:
            test: Test to run
            llm_function: Optional LLM function to call (for integration tests)
        """
        start = time.time()
        errors = []

        try:
            # Render template
            result = self.render_template(test.template, test.variables)

            if not result["success"]:
                return TestResult(
                    test_name=test.name,
                    passed=False,
                    output="",
                    tokens_used=0,
                    latency_ms=0,
                    quality_score=0.0,
                    errors=[result.get("error", "Unknown error")]
                )

            rendered = result["rendered"]
            tokens = result["tokens"]

            # Check token limit
            if tokens > test.max_tokens:
                errors.append(f"Token limit exceeded: {tokens} > {test.max_tokens}")

            # If LLM function provided, test actual generation
            output = ""
            quality_score = 1.0

            if llm_function:
                output = llm_function(rendered)

                # Check for expected keywords
                if test.expected_keywords:
                    found = sum(1 for kw in test.expected_keywords if kw.lower() in output.lower())
                    quality_score = found / len(test.expected_keywords)

                    if quality_score < test.min_quality_score:
                        errors.append(f"Quality score too low: {quality_score:.2f}")

            latency = (time.time() - start) * 1000

            return TestResult(
                test_name=test.name,
                passed=len(errors) == 0,
                output=output or rendered,
                tokens_used=tokens,
                latency_ms=latency,
                quality_score=quality_score,
                errors=errors if errors else None
            )

        except Exception as e:
            return TestResult(
                test_name=test.name,
                passed=False,
                output="",
                tokens_used=0,
                latency_ms=(time.time() - start) * 1000,
                quality_score=0.0,
                errors=[str(e)]
            )

    def run_all_tests(self, llm_function = None) -> list[TestResult]:
        """Run all test cases"""
        results = []

        for test in self.tests:
            result = self.run_test(test, llm_function)
            results.append(result)

        return results

    def save_tests(self, filepath: Path):
        """Save tests to JSON file"""
        data = [
            {
                "name": t.name,
                "template": t.template,
                "variables": t.variables,
                "expected_keywords": t.expected_keywords,
                "max_tokens": t.max_tokens,
                "min_quality_score": t.min_quality_score
            }
            for t in self.tests
        ]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_tests(self, filepath: Path):
        """Load tests from JSON file"""
        with open(filepath) as f:
            data = json.load(f)

        self.tests = [
            PromptTest(
                name=t["name"],
                template=t["template"],
                variables=t["variables"],
                expected_keywords=t.get("expected_keywords"),
                max_tokens=t.get("max_tokens", 2048),
                min_quality_score=t.get("min_quality_score", 0.7)
            )
            for t in data
        ]


# ═══════════════════════════════════════════════════════════════
# EXAMPLE TESTS
# ═══════════════════════════════════════════════════════════════

DEFAULT_TESTS = [
    PromptTest(
        name="Basic RAG Query",
        template="""Context: {context}

Question: {question}

Answer:""",
        variables={
            "context": "Python uses try-except blocks for error handling.",
            "question": "How to handle errors in Python?"
        },
        expected_keywords=["try", "except", "error"],
        max_tokens=500
    ),
    PromptTest(
        name="Few-Shot Example",
        template="""Examples:
{examples}

Now answer: {question}""",
        variables={
            "examples": "Q: What is 2+2? A: 4",
            "question": "What is 3+3?"
        },
        expected_keywords=["6"],
        max_tokens=300
    )
]


# ═══════════════════════════════════════════════════════════════
# CLI FOR TESTING
# ═══════════════════════════════════════════════════════════════

def main():
    """Test prompt workbench"""
    workbench = PromptWorkbench()

    # Load default tests
    workbench.tests = DEFAULT_TESTS

    print("=" * 60)
    print("PROMPT WORKBENCH - Test Suite")
    print("=" * 60)

    # Run tests
    results = workbench.run_all_tests()

    # Display results
    passed = sum(1 for r in results if r.passed)

    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"\n{status} - {result.test_name}")
        print(f"   Tokens: {result.tokens_used}")
        print(f"   Latency: {result.latency_ms:.1f}ms")
        print(f"   Quality: {result.quality_score:.2f}")

        if result.errors:
            print(f"   Errors: {', '.join(result.errors)}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{len(results)} tests passed")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
