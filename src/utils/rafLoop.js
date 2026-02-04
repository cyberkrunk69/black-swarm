/**
 * Runs a callback on every animation frame.
 * Returns a function to cancel the loop.
 *
 * @param {Function} callback - Receives the timestamp.
 * @returns {Function} cancel - Call to stop the loop.
 */
export function startRafLoop(callback) {
  let rafId;
  const loop = (time) => {
    callback(time);
    rafId = requestAnimationFrame(loop);
  };
  rafId = requestAnimationFrame(loop);
  return () => cancelAnimationFrame(rafId);
}