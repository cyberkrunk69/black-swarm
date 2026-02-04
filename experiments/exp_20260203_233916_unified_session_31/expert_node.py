"""
expert_node.py
----------------
Implements the *Expert Node* component of the Swarm Architecture (v2).

Responsibilities
----------------
* Accept “hydration” (queries) from the Gut‑Check Planner.
* Batch queries to amortize the cost of an expensive LLM (e.g., DeepSeek‑R1).
* Trigger a batch when **either**:
    * 5 queries have been accumulated, **or**
    * 10 seconds have elapsed since the first query in the current batch.
* Dispatch the batched queries to the LLM and return the results to the caller.

Design notes
------------
* The node runs an asyncio background task that watches the pending queue.
* Calls to the expensive model are wrapped in a thin async helper so the rest
  of the system stays responsive.
* The implementation is deliberately self‑contained – no external Swarm
  infrastructure is imported, keeping the file safe to add to the experiment
  directory.
"""

import asyncio
import time
from typing import Any, Callable, List, Tuple, Awaitable

# --------------------------------------------------------------------------- #
# Mock of the expensive LLM interface.
# Replace `expensive_llm_call` with the real API client for DeepSeek‑R1 or
# another model when integrating into the full system.
# --------------------------------------------------------------------------- #
async def expensive_llm_call(prompt: str) -> str:
    """
    Simulated call to an expensive LLM. In production this should be replaced
    with the actual async client call (e.g., OpenAI, DeepSeek, etc.).
    """
    await asyncio.sleep(0.5)  # simulate network / compute latency
    return f"[DeepSeek‑R1 response] {prompt[:50]}..."


# --------------------------------------------------------------------------- #
# ExpertNode implementation
# --------------------------------------------------------------------------- #
class ExpertNode:
    """
    Core expert node that batches incoming queries and forwards them to an
    expensive LLM.  The node is instantiated per experiment and started with
    ``await node.start()``.  Queries are submitted via ``await node.submit(query,
    callback)`` where ``callback`` is an async callable that receives the LLM
    response.
    """

    BATCH_SIZE = 5          # trigger batch when this many queries are queued
    BATCH_TIMEOUT = 10.0    # seconds – trigger batch after this time elapses

    def __init__(self) -> None:
        # Queue holds tuples: (query_str, callback)
        self._queue: List[Tuple[str, Callable[[str], Awaitable[None]]]] = []
        self._queue_lock = asyncio.Lock()
        self._batch_event = asyncio.Event()
        self._background_task: asyncio.Task | None = None
        self._shutdown = False

    async def start(self) -> None:
        """Start the background batch‑processing loop."""
        if self._background_task is None:
            self._background_task = asyncio.create_task(self._batch_loop())

    async def shutdown(self) -> None:
        """Gracefully stop the background task."""
        self._shutdown = True
        if self._background_task:
            self._batch_event.set()          # wake the loop if waiting
            await self._background_task
            self._background_task = None

    async def submit(
        self,
        query: str,
        callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """
        Receive a hydration query from the planner.

        Parameters
        ----------
        query: str
            The prompt / problem statement to be solved.
        callback: async callable
            Function that will be awaited with the LLM response.
        """
        async with self._queue_lock:
            self._queue.append((query, callback))
            # If we just hit the batch size, notify the loop immediately.
            if len(self._queue) >= self.BATCH_SIZE:
                self._batch_event.set()

    async def _batch_loop(self) -> None:
        """
        Background coroutine that watches the queue and dispatches batches.
        """
        while not self._shutdown:
            # Wait for either the event (size trigger) or timeout (time trigger)
            try:
                await asyncio.wait_for(self._batch_event.wait(), timeout=self.BATCH_TIMEOUT)
            except asyncio.TimeoutError:
                pass  # timeout – we will evaluate the queue below

            async with self._queue_lock:
                # Determine if we have anything to process
                if not self._queue:
                    self._batch_event.clear()
                    continue

                # If we have reached size threshold OR timeout elapsed, process batch
                if len(self._queue) >= self.BATCH_SIZE or self._batch_event.is_set():
                    batch = self._queue[:]
                    self._queue.clear()
                    self._batch_event.clear()
                else:
                    # Not enough items and timeout not yet fired – continue waiting
                    self._batch_event.clear()
                    continue

            # Process the extracted batch outside the lock
            await self._process_batch(batch)

    async def _process_batch(
        self,
        batch: List[Tuple[str, Callable[[str], Awaitable[None]]]],
    ) -> None:
        """
        Send the batched queries to the LLM and invoke callbacks with the results.

        Parameters
        ----------
        batch: list of (query, callback) tuples.
        """
        # For demonstration we fire each query sequentially; a real implementation
        # could issue them concurrently (e.g., via asyncio.gather) if the model
        # API supports multi‑prompt calls.
        for query, callback in batch:
            try:
                response = await expensive_llm_call(query)
                await callback(response)
            except Exception as exc:
                # Ensure a failure in one query does not halt the whole batch.
                error_msg = f"[ExpertNode error] {type(exc).__name__}: {exc}"
                await callback(error_msg)


# --------------------------------------------------------------------------- #
# Convenience helper for quick testing (executed only when run as a script)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    async def demo():
        node = ExpertNode()
        await node.start()

        async def print_result(res: str):
            print(f"Result: {res}")

        # Submit 7 dummy queries to trigger two batches (5 + 2 after timeout)
        for i in range(7):
            await node.submit(f"Query #{i+1}: solve hard problem {i}", print_result)
            await asyncio.sleep(0.3)  # stagger a bit

        # Allow time for remaining batch to fire via timeout
        await asyncio.sleep(12)
        await node.shutdown()

    asyncio.run(demo())