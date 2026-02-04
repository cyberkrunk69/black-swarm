/**
 * Node Position Persistence Module
 *
 * Provides `saveNodePosition` and `loadNodePosition` utilities that store
 * node coordinates in `localStorage` under the key `nodePositions`.
 *
 * Expected usage:
 *   - Call `saveNodePosition(nodeId, x, y)` whenever a node is moved.
 *   - Call `loadNodePosition()` on page load to restore saved positions.
 *
 * The data format stored in `localStorage` is:
 *   {
 *     "nodeId1": { "x": 123, "y": 456 },
 *     "nodeId2": { "x": 78,  "y": 90  },
 *     ...
 *   }
 */

(function () {
  const STORAGE_KEY = 'nodePositions';

  /**
   * Retrieves the current node positions map from localStorage.
   * If none exists, returns an empty object.
   *
   * @returns {Object<string, {x:number, y:number}>}
   */
  function _getStoredPositions() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return {};
    }
    try {
      const parsed = JSON.parse(raw);
      // Ensure we have an object
      return typeof parsed === 'object' && parsed !== null ? parsed : {};
    } catch (e) {
      console.warn('Failed to parse nodePositions from localStorage:', e);
      return {};
    }
  }

  /**
   * Persists the supplied positions map back to localStorage.
   *
   * @param {Object<string, {x:number, y:number}>} positions
   */
  function _storePositions(positions) {
    try {
      const serialized = JSON.stringify(positions);
      localStorage.setItem(STORAGE_KEY, serialized);
    } catch (e) {
      console.error('Unable to store node positions:', e);
    }
  }

  /**
   * Save the position of a single node.
   *
   * @param {string} nodeId - The DOM id of the node.
   * @param {number} x - The horizontal coordinate (in pixels).
   * @param {number} y - The vertical coordinate (in pixels).
   */
  function saveNodePosition(nodeId, x, y) {
    if (!nodeId) {
      console.warn('saveNodePosition called with empty nodeId');
      return;
    }
    const positions = _getStoredPositions();
    positions[nodeId] = { x: Number(x), y: Number(y) };
    _storePositions(positions);
  }

  /**
   * Load all saved node positions from localStorage and apply them to the DOM.
   * Nodes are expected to have their id attribute set to the stored key.
   * The function sets `style.left` and `style.top` (assuming absolute/relative positioning).
   */
  function loadNodePosition() {
    const positions = _getStoredPositions();
    Object.entries(positions).forEach(([nodeId, pos]) => {
      const el = document.getElementById(nodeId);
      if (!el) {
        // Node may have been removed; ignore silently.
        return;
      }
      // Apply position – using CSS left/top. If the element uses transform,
      // you could adapt this to set `transform: translate(...)` instead.
      el.style.position = el.style.position || 'absolute';
      if (typeof pos.x === 'number') {
        el.style.left = `${pos.x}px`;
      }
      if (typeof pos.y === 'number') {
        el.style.top = `${pos.y}px`;
      }
    });
  }

  // Expose functions globally (or as module exports if using a bundler)
  window.saveNodePosition = saveNodePosition;
  window.loadNodePosition = loadNodePosition;

  // Auto‑load positions on DOM ready
  document.addEventListener('DOMContentLoaded', loadNodePosition);
})();