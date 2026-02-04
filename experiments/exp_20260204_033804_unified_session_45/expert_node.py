"""
expert_node.py
----------------
Implementation of an Expert Node used in the unified swarm architecture.

The node receives “hydration” data from the Gut‑Check Planner, accumulates
queries from downstream components and forwards them in batches to an
expensive LLM (e.g., DeepSeek‑R1).  Batching is triggered when either:

* 5 queries have been collected, or
* 10 seconds have elapsed since the first query in the current batch.

The node runs an asyncio background task that handles flushing the batch.
The expensive model call is abstracted behind ``_call_expensive_model`` so
that it can be swapped out for a real API client later.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any, Awaitable, Callable, Deque, List, Optional

# --------------------------------------------------------------------------- #
# Helper: placeholder for the expensive LLM call.
# --------------------------------------------------------------------------- #
async def _call_expensive_model(prompts: List[str]) -> List[str]:
    """
    Simulate a call to an expensive LLM (e.g., DeepSeek‑R1).

    In production this would hit the real API.  For now we just echo the
    prompts with a short async sleep to mimic latency.
    """
    await asyncio.sleep(0.5)  # simulate network / compute latency
    # Echo back the prompts as "answers"
    return [f"Response to: {p}" for p in prompts]


# --------------------------------------------------------------------------- #
# ExpertNode definition
# --------------------------------------------------------------------------- #
class ExpertNode:
    """
    Core class for the Expert Node.

    Usage:
        node = ExpertNode()
        await node.hydrate(initial_context)
        result = await node.query("What is the capital of France?")
    """

    # Batch configuration constants
    MAX_BATCH_SIZE: int = 5          # number of queries to trigger a batch
    MAX_BATCH_AGE: float = 10.0      # seconds before a batch is flushed

    def __init__(self,
                 model_caller: Callable[[List[str]], Awaitable[List[str]]] = _call_expensive_model):
        """
        Initialise the node.

        Args:
            model_caller: Async callable that receives a list of prompts and
                          returns a list of responses.  Defaults to the stub.
        """
        self._model_caller = model_caller
        self._hydration: Optional[dict[str, Any]] = None

        # Queue of pending queries (prompt, future) pairs
        self._pending: Deque[tuple[str, asyncio.Future[str]]] = deque()

        # Timestamp of the first query in the current batch
        self._batch_start: Optional[float] = None

        # Background task that watches the batch timeout
        self._batch_task: Optional[asyncio.Task[None]] = None
        self._shutdown = False

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    async def hydrate(self, data: dict[str, Any]) -> None:
        """
        Receive hydration data from the Gut‑Check Planner.

        The data can be any JSON‑serialisable dict that the expert node
        might need (e.g., system prompts, domain knowledge, etc.).
        """
        self._hydration = data
        # Ensure the background task is running
        if self._batch_task is None:
            self._batch_task = asyncio.create_task(self._batch_watcher())

    async def query(self, prompt: str) -> str:
        """
        Submit a single prompt to the expert node and await the response.

        The prompt is queued; the response will be delivered once the batch
        is flushed (either by size or timeout).
        """
        if self._shutdown:
            raise RuntimeError("ExpertNode has been shut down.")

        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()
        self._pending.append((prompt, future))

        # Initialise batch timer if this is the first entry
        if self._batch_start is None:
            self._batch_start = time.time()

        # If we hit the size threshold, flush immediately
        if len(self._pending) >= self.MAX_BATCH_SIZE:
            await self._flush_batch()

        return await future

    async def close(self) -> None:
        """
        Gracefully shut down the node, flushing any remaining queries.
        """
        self._shutdown = True
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        # Flush any leftovers
        if self._pending:
            await self._flush_batch()

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    async def _batch_watcher(self) -> None:
        """
        Background coroutine that watches the age of the current batch.
        It wakes up periodically (once per second) and flushes the batch
        if the age exceeds ``MAX_BATCH_AGE``.
        """
        try:
            while not self._shutdown:
                await asyncio.sleep(1.0)
                if self._pending and self._batch_start is not None:
                    age = time.time() - self._batch_start
                    if age >= self.MAX_BATCH_AGE:
                        await self._flush_batch()
        except asyncio.CancelledError:
            # Normal shutdown path – ensure pending work is processed.
            pass

    async def _flush_batch(self) -> None:
        """
        Send the accumulated prompts to the expensive model and resolve
        the associated futures with the returned answers.
        """
        if not self._pending:
            self._batch_start = None
            return

        # Extract prompts and futures
        batch = list(self._pending)
        self._pending.clear()
        self._batch_start = None

        prompts, futures = zip(*batch)  # type: ignore[misc]

        # Optionally prepend system‑level hydration if provided.
        if self._hydration and "system_prompt" in self._hydration:
            system_prompt = self._hydration["system_prompt"]
            # Prepend the system prompt to each user prompt.
            prompts = tuple(f"{system_prompt}\n\n{p}" for p in prompts)

        # Call the expensive model
        try:
            responses = await self._model_caller(list(prompts))
        except Exception as exc:
            # Propagate the exception to all waiting futures.
            for fut in futures:
                if not fut.done():
                    fut.set_exception(exc)
            return

        # Resolve each future with its corresponding response.
        for fut, resp in zip(futures, responses):
            if not fut.done():
                fut.set_result(resp)

# --------------------------------------------------------------------------- #
# Simple sanity test (executed only when run as a script)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    async def demo():
        node = ExpertNode()
        await node.hydrate({"system_prompt": "You are a helpful expert."})

        # Fire off several queries quickly to trigger size‑based batching.
        tasks = [
            asyncio.create_task(node.query(f"Question {i}?"))
            for i in range(7)
        ]

        # Wait for all answers.
        answers = await asyncio.gather(*tasks)
        for a in answers:
            print(a)

        await node.close()

    asyncio.run(demo())