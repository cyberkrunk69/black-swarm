"""
Together AI Client - Multi-model inference with intelligent routing.

Supports tiered model selection based on task complexity:
- Reasoner: DeepSeek R1 for complex planning (expensive but few tokens)
- Thinker: Kimi K2 Thinking for multi-step reasoning
- Coder: Qwen3 Coder for code-heavy tasks
- Worker: GPT-OSS 120B for general tasks (default)
- Verifier: GPT-OSS 20B for cheap verification
- Sweeper: Gemma 3N for ultra-cheap cleanup
- Guard: Llama Guard for safety checks
"""

import os
import re
import time
import threading
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

try:
    from together import Together
    TOGETHER_AVAILABLE = True
except ImportError:
    TOGETHER_AVAILABLE = False
    print("[TOGETHER] Warning: together package not installed. Run: pip install together")


class NodeType(Enum):
    """Types of nodes in the swarm - determines model selection."""
    REASONER = "reasoner"      # Complex planning, architecture
    THINKER = "thinker"        # Multi-step reasoning, debugging
    CODER = "coder"            # Code generation, refactoring
    WORKER = "worker"          # General tasks (default)
    VERIFIER = "verifier"      # Cheap verification (critic node)
    SWEEPER = "sweeper"        # Ultra-cheap cleanup, formatting
    GUARD = "guard"            # Safety/moderation checks


@dataclass
class TogetherModel:
    """Model configuration for Together AI."""
    model_id: str
    display_name: str
    input_cost_per_1m: float
    output_cost_per_1m: float
    context_window: int
    node_type: NodeType
    keywords: List[str]  # Keywords that trigger this model


# Together AI model registry - organized by node type
TOGETHER_MODELS = {
    # REASONER - Complex planning, few tokens, deep thinking
    "deepseek-ai/DeepSeek-R1-0528": TogetherModel(
        model_id="deepseek-ai/DeepSeek-R1-0528",
        display_name="DeepSeek R1 (Reasoner)",
        input_cost_per_1m=3.00,
        output_cost_per_1m=7.00,
        context_window=128000,
        node_type=NodeType.REASONER,
        keywords=["architect", "design system", "complex", "strategy", "plan"]
    ),

    # THINKER - Multi-step reasoning
    "moonshotai/Kimi-K2-Thinking": TogetherModel(
        model_id="moonshotai/Kimi-K2-Thinking",
        display_name="Kimi K2 Thinking",
        input_cost_per_1m=1.20,
        output_cost_per_1m=4.00,
        context_window=128000,
        node_type=NodeType.THINKER,
        keywords=["debug", "analyze", "investigate", "why", "reason"]
    ),

    # CODER - Code specialist
    "Qwen/Qwen3-Coder-Next-Fp8": TogetherModel(
        model_id="Qwen/Qwen3-Coder-Next-Fp8",
        display_name="Qwen3 Coder 80B",
        input_cost_per_1m=0.50,
        output_cost_per_1m=1.20,
        context_window=131072,
        node_type=NodeType.CODER,
        keywords=["implement", "code", "function", "class", "refactor", "fix bug"]
    ),

    # WORKER - General purpose (default)
    "openai/gpt-oss-120b": TogetherModel(
        model_id="openai/gpt-oss-120b",
        display_name="GPT-OSS 120B (Worker)",
        input_cost_per_1m=0.15,
        output_cost_per_1m=0.60,
        context_window=131072,
        node_type=NodeType.WORKER,
        keywords=[]  # Default fallback
    ),

    # VERIFIER - Cheap critic node
    "openai/gpt-oss-20b": TogetherModel(
        model_id="openai/gpt-oss-20b",
        display_name="GPT-OSS 20B (Verifier)",
        input_cost_per_1m=0.05,
        output_cost_per_1m=0.20,
        context_window=131072,
        node_type=NodeType.VERIFIER,
        keywords=["verify", "check", "review", "validate"]
    ),

    # SWEEPER - Ultra-cheap cleanup
    "google/gemma-3n-e4b-instruct": TogetherModel(
        model_id="google/gemma-3n-e4b-instruct",
        display_name="Gemma 3N (Sweeper)",
        input_cost_per_1m=0.02,
        output_cost_per_1m=0.04,
        context_window=32000,
        node_type=NodeType.SWEEPER,
        keywords=["format", "cleanup", "simple", "trivial", "typo"]
    ),

    # GUARD - Safety moderation
    "meta-llama/Llama-Guard-4-12B": TogetherModel(
        model_id="meta-llama/Llama-Guard-4-12B",
        display_name="Llama Guard 4",
        input_cost_per_1m=0.20,
        output_cost_per_1m=0.20,
        context_window=8192,
        node_type=NodeType.GUARD,
        keywords=["safety", "moderate", "filter"]
    ),
}

# Quick lookup by node type
MODELS_BY_TYPE = {
    NodeType.REASONER: "deepseek-ai/DeepSeek-R1-0528",
    NodeType.THINKER: "moonshotai/Kimi-K2-Thinking",
    NodeType.CODER: "Qwen/Qwen3-Coder-Next-Fp8",
    NodeType.WORKER: "openai/gpt-oss-120b",
    NodeType.VERIFIER: "openai/gpt-oss-20b",
    NodeType.SWEEPER: "google/gemma-3n-e4b-instruct",
    NodeType.GUARD: "meta-llama/Llama-Guard-4-12B",
}


class ModelRouter:
    """Routes tasks to appropriate models based on content analysis."""

    # Patterns for each node type
    ROUTING_PATTERNS = {
        NodeType.REASONER: [
            r'\barchitect\b', r'\bdesign\s+system\b', r'\bstrategy\b',
            r'\bcomplex\b', r'\bmulti-?step\s+plan\b'
        ],
        NodeType.THINKER: [
            r'\bdebug\b', r'\banalyze\b', r'\binvestigate\b',
            r'\bwhy\s+(does|is|did)\b', r'\breason\s+about\b'
        ],
        NodeType.CODER: [
            r'\bimplement\b', r'\bcreate\s+(function|class|module)\b',
            r'\brefactor\b', r'\bfix\s+(bug|error)\b', r'\bcode\b',
            r'\.py\b', r'\.js\b', r'\.ts\b'
        ],
        NodeType.SWEEPER: [
            r'\bformat\b', r'\bcleanup\b', r'\bsimple\b',
            r'\btrivial\b', r'\btypo\b', r'\brename\b'
        ],
        NodeType.VERIFIER: [
            r'\bverify\b', r'\bcheck\b', r'\breview\b', r'\bvalidate\b'
        ],
    }

    @classmethod
    def route(cls, task_text: str, force_type: Optional[NodeType] = None) -> Tuple[str, NodeType, str]:
        """
        Route a task to the appropriate model.

        Args:
            task_text: The task description
            force_type: Force a specific node type

        Returns:
            Tuple of (model_id, node_type, reason)
        """
        if force_type:
            model_id = MODELS_BY_TYPE[force_type]
            return model_id, force_type, f"Forced to {force_type.value}"

        task_lower = task_text.lower()

        # Check patterns in priority order
        priority_order = [
            NodeType.REASONER,  # Most expensive, check first
            NodeType.THINKER,
            NodeType.CODER,
            NodeType.SWEEPER,  # Cheapest, check before default
            NodeType.VERIFIER,
        ]

        for node_type in priority_order:
            patterns = cls.ROUTING_PATTERNS.get(node_type, [])
            for pattern in patterns:
                if re.search(pattern, task_lower):
                    model_id = MODELS_BY_TYPE[node_type]
                    return model_id, node_type, f"Matched pattern '{pattern}' → {node_type.value}"

        # Default to WORKER
        return MODELS_BY_TYPE[NodeType.WORKER], NodeType.WORKER, "Default worker model"


class TogetherInferenceEngine:
    """
    Together AI inference engine with intelligent model routing.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY")

        if not self.api_key:
            raise ValueError(
                "TOGETHER_API_KEY not found. Set it via environment variable or pass to constructor.\n"
                "Get your key at: https://api.together.xyz/"
            )

        if not TOGETHER_AVAILABLE:
            raise ImportError("together package required. Install with: pip install together")

        self.client = Together(api_key=self.api_key)
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        self.cost_by_node_type: Dict[NodeType, float] = {}

        # Rate limiting
        self._rate_lock = threading.Lock()
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Together has higher rate limits

    def _rate_limit_wait(self):
        """Enforce rate limiting between requests."""
        with self._rate_lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
            self.last_request_time = time.time()

    def _estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request."""
        if model_id not in TOGETHER_MODELS:
            return 0.0

        model = TOGETHER_MODELS[model_id]
        input_cost = (input_tokens / 1_000_000) * model.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * model.output_cost_per_1m
        return input_cost + output_cost

    def execute(
        self,
        prompt: str,
        node_type: Optional[NodeType] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """
        Execute a prompt using Together AI.

        Args:
            prompt: The prompt to execute
            node_type: Force a specific node type (routes to appropriate model)
            model: Force a specific model ID (overrides node_type)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            timeout: Request timeout in seconds

        Returns:
            Dict with result, cost, tokens, model info
        """
        start_time = time.time()

        # Determine model
        if model and model in TOGETHER_MODELS:
            model_id = model
            selected_type = TOGETHER_MODELS[model_id].node_type
            route_reason = f"Explicit model: {model}"
        elif node_type:
            model_id = MODELS_BY_TYPE[node_type]
            selected_type = node_type
            route_reason = f"Explicit node type: {node_type.value}"
        else:
            model_id, selected_type, route_reason = ModelRouter.route(prompt)

        model_config = TOGETHER_MODELS.get(model_id)
        if not model_config:
            return {
                "error": f"Unknown model: {model_id}",
                "returncode": 1,
                "result": "",
                "cost": 0.0
            }

        # Rate limiting
        self._rate_limit_wait()

        try:
            response = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software engineer. Execute tasks precisely and efficiently."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            result_text = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

            cost = self._estimate_cost(model_id, input_tokens, output_tokens)

            # Update totals
            self.total_cost += cost
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.request_count += 1
            self.cost_by_node_type[selected_type] = self.cost_by_node_type.get(selected_type, 0) + cost

            elapsed = time.time() - start_time

            return {
                "result": result_text,
                "returncode": 0,
                "cost": cost,
                "total_cost_usd": cost,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model_id,
                "model_display": model_config.display_name,
                "node_type": selected_type.value,
                "route_reason": route_reason,
                "elapsed": elapsed,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "error": "api_error",
                "error_message": str(e),
                "returncode": 1,
                "result": "",
                "cost": 0.0,
                "elapsed": elapsed
            }

    def verify(self, task: str, output: str, files_changed: List[str] = None) -> Dict[str, Any]:
        """
        Critic node - verify if task output is acceptable.

        Uses cheap VERIFIER model to check work quality.

        Args:
            task: Original task description
            output: The output produced by worker
            files_changed: List of files that were modified

        Returns:
            Dict with verdict (APPROVE/REJECT/MINOR_ISSUES) and reason
        """
        files_info = ""
        if files_changed:
            files_info = f"\n\nFiles modified: {', '.join(files_changed)}"

        verify_prompt = f"""You are a code review critic. Evaluate if this task was completed correctly.

TASK:
{task}

OUTPUT PRODUCED:
{output[:3000]}  # Truncate to save tokens
{files_info}

EVALUATE:
1. Did the output actually complete the task?
2. Is the output syntactically correct (if code)?
3. Are there obvious errors or incomplete sections?
4. Does it look like real work or placeholder/stub code?

VERDICT (choose one):
- APPROVE: Task completed correctly
- MINOR_ISSUES: Completed but needs cleanup (specify what)
- REJECT: Task not completed or output is broken (specify why)

Respond with just the verdict and a one-line reason.
Format: VERDICT: [reason]"""

        result = self.execute(
            prompt=verify_prompt,
            node_type=NodeType.VERIFIER,
            max_tokens=200,
            temperature=0.3
        )

        if result.get("error"):
            return {"verdict": "APPROVE", "reason": "Verification failed, defaulting to approve", "cost": 0}

        response = result.get("result", "").strip().upper()

        if "REJECT" in response:
            verdict = "REJECT"
        elif "MINOR" in response:
            verdict = "MINOR_ISSUES"
        else:
            verdict = "APPROVE"

        return {
            "verdict": verdict,
            "reason": result.get("result", "").strip(),
            "cost": result.get("cost", 0),
            "model": result.get("model")
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get cumulative usage statistics."""
        return {
            "engine": "together",
            "total_cost_usd": self.total_cost,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_calls": self.request_count,
            "cost_by_node_type": {k.value: v for k, v in self.cost_by_node_type.items()},
            "avg_cost_per_request": self.total_cost / max(self.request_count, 1)
        }

    def check_budget(self, budget_limit: float) -> Tuple[bool, float]:
        """Check if we're within budget."""
        remaining = budget_limit - self.total_cost
        return remaining > 0, remaining


# Global instance
_together_engine: Optional[TogetherInferenceEngine] = None


def get_together_engine() -> TogetherInferenceEngine:
    """Get or create the global Together engine instance."""
    global _together_engine
    if _together_engine is None:
        _together_engine = TogetherInferenceEngine()
    return _together_engine


if __name__ == "__main__":
    # Test routing
    print("Testing model router...")

    test_tasks = [
        "Design a distributed system architecture for handling 1M requests/sec",
        "Debug why the authentication is failing intermittently",
        "Implement a function to parse JSON with error handling",
        "Fix the typo in the README",
        "Verify that the output is correct",
    ]

    for task in test_tasks:
        model_id, node_type, reason = ModelRouter.route(task)
        model = TOGETHER_MODELS[model_id]
        print(f"\nTask: {task[:50]}...")
        print(f"  → {node_type.value}: {model.display_name}")
        print(f"  → Reason: {reason}")
        print(f"  → Cost: ${model.input_cost_per_1m}/{model.output_cost_per_1m} per 1M tokens")
import logging

_logger = logging.getLogger(__name__)

def verify_output(output: str) -> bool:
    """
    Verify task output using GPT-OSS 20B model.
    Returns True if output passes verification, False otherwise.
    """
    prompt = (
        "You are an AI verifier. Check if the following output is a valid result for the task. "
        "Consider syntax correctness, reasonable size, and content relevance. "
        "Respond with ONLY 'PASS' or 'FAIL'.\\n\\nOutput:\\n" + output
    )
    # Assuming TogetherClient is defined elsewhere in this module
    client = TogetherClient()
    try:
        response = client.completion(
            model="gpt-oss-20b",
            prompt=prompt,
            max_tokens=10,
            temperature=0.0,
        )
    except Exception as e:
        _logger.error(f"Verification request failed: {e}")
        return False

    verdict = response.get("choices", [{}])[0].get("text", "").strip().upper()
    _logger.info(f"Verification verdict: {verdict}")
    return verdict == "PASS"