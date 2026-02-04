/**
 * Simple debounce implementation.
 * Calls `func` after `wait` ms have elapsed since the last invocation.
 */
export function debounce(func, wait) {
  let timeout;
  return function (...args) {
    const later = () => {
      timeout = null;
      func.apply(this, args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Wrap a callback so it runs inside requestAnimationFrame.
 * Guarantees the callback is executed at most once per frame.
 */
export function rafCallback(callback) {
  let scheduled = false;
  return function (...args) {
    if (!scheduled) {
      scheduled = true;
      requestAnimationFrame(() => {
        scheduled = false;
        callback.apply(this, args);
      });
    }
  };
}