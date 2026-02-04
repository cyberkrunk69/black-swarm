/**
 * Node Position Persistence Utilities
 *
 * Provides functions to save and load node positions using the browser's
 * localStorage. All positions are stored under a single key: 'nodePositions'.
 *
 * The stored structure is a JSON object where each key is a node identifier
 * and the value is an object containing the x and y coordinates, e.g.:
 *
 * {
 *   "node-1": { "x": 120, "y": 250 },
 *   "node-2": { "x": 400, "y": 80 }
 * }
 *
 * These utilities are deliberately lightweight and have no external
 * dependencies, making them suitable for import into any UI component that
 * manages draggable nodes.
 */

/**
 * Saves the position of a node to localStorage.
 *
 * @param {string} nodeId - Unique identifier for the node (e.g., DOM id).
 * @param {{x:number, y:number}} position - Object containing x and y coordinates.
 */
export function saveNodePosition(nodeId, position) {
  if (typeof nodeId !== 'string' || typeof position !== 'object' || position === null) {
    console.warn('saveNodePosition: Invalid arguments');
    return;
  }

  // Retrieve the current map from storage, or start with an empty object.
  const stored = localStorage.getItem('nodePositions');
  let positions = {};

  try {
    positions = stored ? JSON.parse(stored) : {};
  } catch (e) {
    // Corrupted data – reset.
    console.error('saveNodePosition: Failed to parse stored positions, resetting.', e);
    positions = {};
  }

  // Update the specific node's position.
  positions[nodeId] = { x: position.x, y: position.y };

  // Persist back to localStorage.
  try {
    localStorage.setItem('nodePositions', JSON.stringify(positions));
  } catch (e) {
    console.error('saveNodePosition: Unable to write to localStorage.', e);
  }
}

/**
 * Loads the saved position for a given node from localStorage.
 *
 * @param {string} nodeId - Unique identifier for the node.
 * @returns {{x:number, y:number}|null} The saved position, or null if none exists.
 */
export function loadNodePosition(nodeId) {
  if (typeof nodeId !== 'string') {
    console.warn('loadNodePosition: Invalid nodeId');
    return null;
  }

  const stored = localStorage.getItem('nodePositions');
  if (!stored) return null;

  try {
    const positions = JSON.parse(stored);
    const pos = positions[nodeId];
    return pos ? { x: pos.x, y: pos.y } : null;
  } catch (e) {
    console.error('loadNodePosition: Failed to parse stored positions.', e);
    return null;
  }
}

/**
 * Convenience helper – called on page load to restore all saved node positions.
 *
 * @param {NodeList|Array<HTMLElement>} nodeElements - Collection of node DOM elements.
 *        Each element must have a unique id attribute that matches the key used
 *        in saveNodePosition().
 */
export function applySavedNodePositions(nodeElements) {
  if (!nodeElements) return;

  nodeElements.forEach((el) => {
    const nodeId = el.id;
    if (!nodeId) return;

    const savedPos = loadNodePosition(nodeId);
    if (savedPos) {
      el.style.position = 'absolute';
      el.style.left = `${savedPos.x}px`;
      el.style.top = `${savedPos.y}px`;
    }
  });
}

/**
 * Example usage (to be placed wherever node drag handling occurs):
 *
 * // When a node is moved:
 * const nodeId = nodeElement.id;
 * const position = { x: newX, y: newY };
 * saveNodePosition(nodeId, position);
 *
 * // On page reload (e.g., inside a DOMContentLoaded handler):
 * const allNodes = document.querySelectorAll('.draggable-node');
 * applySavedNodePositions(Array.from(allNodes));
 */