"""
expert_node.py
----------------
Implements the **Expert Node** as described in `SWARM_ARCHITECTURE_V2.md`.

Key responsibilities:
* Accept “hydration” (context) from the Gut‑Check Planner.
* Provide a batched query interface to an expensive LLM (e.g., DeepSeek‑R1).
* Trigger a batch when **either**:
    - 5 queries have been accumulated, **or**
    - 10 seconds have elapsed since the first query in the current batch.
* Return results to the caller via `asyncio.Future` objects so callers can await
  the answer without needing to know about the batching logic.

The implementation is deliberately lightweight – it does not depend on any
project‑specific utilities and can be dropped into any experiment folder.
"""

import asyncio
import time
from typing import Any, Callable, List, Tuple

# --------------------------------------------------------------------------- #
# Placeholder for the expensive model call.
# Replace `expensive_model_call` with the real inference function when
# integrating with DeepSeek‑R1 or another high‑cost LLM.
# --------------------------------------------------------------------------- #
async def expensive_model_call(
    batch_inputs: List[Tuple[str, Any]],
) -> List[Any]:
    """
    Simulate a costly LLM inference.

    Parameters
    ----------
    batch_inputs : List[Tuple[str, Any]]
        Each tuple contains a query ID and the query payload.

    Returns
    -------
    List[Any]
        Mocked responses – in a real implementation this would be the model
        output for each input in the same order.
    """
    # Simulate latency (e.g., 2 seconds per batch)
    await asyncio.sleep(2)

    # Echo back the payload for demonstration purposes
    return [f"Response to '{payload}' (id={qid})" for qid, payload in batch_inputs]


# --------------------------------------------------------------------------- #
# ExpertNode implementation
# --------------------------------------------------------------------------- #
class ExpertNode:
    """
    Core component that batches incoming queries and forwards them to an
    expensive model.

    Usage
    -----
    >>> node = ExpertNode()
    >>> asyncio.run(node.start())          # start background task
    >>> result = await node.submit_query("Explain quantum entanglement")
    >>> print(result)  # -> model response
    """

    def __init__(
        self,
        batch_size: int = 5,
        max_wait_seconds: float = 10.0,
        model_callable: Callable[[List[Tuple[str, Any]]], asyncio.Future] = expensive_model_call,
    ):
        self.batch_size = batch_size
        self.max_wait_seconds = max_wait_seconds
        self.model_callable = model_callable

        # Internal state
        self._queue: asyncio.Queue[Tuple[str, Any, asyncio.Future]] = asyncio.Queue()
        self._batch_task: asyncio.Task | None = None
        self._running = False

        # Simple counter for generating unique query IDs
        self._qid_counter = 0

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    async def start(self) -> None:
        """Start the background batching coroutine."""
        if self._running:
            return
        self._running = True
        self._batch_task = asyncio.create_task(self._batch_worker())

    async def stop(self) -> None:
        """Gracefully stop the background task and flush pending queries."""
        self._running = False
        if self._batch_task:
            await self._batch_task
        # Drain remaining items (if any) to avoid dangling futures
        while not self._queue.empty():
            _, _, fut = await self._queue.get()
            if not fut.done():
                fut.set_exception(RuntimeError("ExpertNode stopped before processing query."))

    async def submit_query(self, payload: Any) -> Any:
        """
        Submit a single query to the ExpertNode.

        Parameters
        ----------
        payload : Any
            The data that will be fed to the expensive model.

        Returns
        -------
        Any
            The model's response (awaited).
        """
        if not self._running:
            raise RuntimeError("ExpertNode is not running. Call `await start()` first.")

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        qid = f"q{self._qid_counter}"
        self._qid_counter += 1

        await self._queue.put((qid, payload, future))
        return await future

    # ------------------------------------------------------------------- #
    # Internal batching logic
    # ------------------------------------------------------------------- #
    async def _batch_worker(self) -> None:
        """
        Continuously collects queries until either the batch size or the timeout
        condition is met, then sends the batch to the expensive model.
        """
        while self._running:
            batch: List[Tuple[str, Any, asyncio.Future]] = []
            start_time = time.time()

            # Wait for at least one item to appear
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=self.max_wait_seconds)
                batch.append(item)
            except asyncio.TimeoutError:
                # No queries arrived during the whole timeout window – loop again
                continue

            # Gather additional items respecting both limits
            while len(batch) < self.batch_size:
                remaining = self.max_wait_seconds - (time.time() - start_time)
                if remaining <= 0:
                    break
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout=remaining)
                    batch.append(item)
                except asyncio.TimeoutError:
                    break  # timeout reached, process what we have

            # Separate IDs/payloads from futures
            ids_payloads = [(qid, payload) for qid, payload, _ in batch]
            futures = [fut for _, _, fut in batch]

            # Call the expensive model (await its result)
            try:
                responses = await self.model_callable(ids_payloads)
                if len(responses) != len(futures):
                    raise RuntimeError("Model returned mismatched number of responses.")
                for fut, resp in zip(futures, responses):
                    if not fut.done():
                        fut.set_result(resp)
            except Exception as exc:
                # Propagate exception to all pending futures
                for fut in futures:
                    if not fut.done():
                        fut.set_exception(exc)

        # When loop exits, ensure any leftover items are resolved with an error
        while not self._queue.empty():
            _, _, fut = await self._queue.get()
            if not fut.done():
                fut.set_exception(RuntimeError("ExpertNode stopped before processing query."))


# --------------------------------------------------------------------------- #
# Example usage (executed only when run directly)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    async def demo():
        node = ExpertNode()
        await node.start()

        # Fire off a few queries concurrently
        queries = [
            "Explain the significance of the P=NP problem.",
            "Summarize the plot of 'Inception'.",
            "Give a quick recipe for chocolate chip cookies.",
            "What are the latest advancements in quantum computing?",
            "Write a short poem about autumn.",
            "How does backpropagation work in neural networks?",
        ]

        results = await asyncio.gather(*(node.submit_query(q) for q in queries))
        for q, r in zip(queries, results):
            print(f"Q: {q}\\nA: {r}\\n{'-'*40}")

        await node.stop()

    asyncio.run(demo())