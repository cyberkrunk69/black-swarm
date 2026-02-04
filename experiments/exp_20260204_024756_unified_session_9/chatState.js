/**
 * Utility for persisting and restoring the chat window's position and collapsed state.
 *
 * The state is stored in `localStorage` under the key `'chatState'` as a JSON string:
 * {
 *   position: { top: number, left: number }, // pixel coordinates
 *   collapsed: boolean
 * }
 *
 * Usage:
 *   saveChatPosition({ top: 100, left: 200 }, false);
 *   const state = loadChatPosition();
 *   if (state) {
 *     // apply state.position and state.collapsed to the UI
 *   }
 */

/**
 * Saves the chat window's position and collapsed state to localStorage.
 *
 * @param {{top:number, left:number}} position - The pixel coordinates of the chat window.
 * @param {boolean} collapsed - Whether the chat window is collapsed.
 */
export function saveChatPosition(position, collapsed) {
  try {
    const payload = {
      position,
      collapsed,
    };
    localStorage.setItem('chatState', JSON.stringify(payload));
  } catch (e) {
    // localStorage may be unavailable (e.g., private mode). Fail silently.
    console.warn('Unable to save chat position:', e);
  }
}

/**
 * Loads the chat window's position and collapsed state from localStorage.
 *
 * @returns {{position:{top:number, left:number}, collapsed:boolean}|null}
 *          Returns the stored state, or null if none is found or parsing fails.
 */
export function loadChatPosition() {
  try {
    const raw = localStorage.getItem('chatState');
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Basic validation
    if (
      typeof parsed === 'object' &&
      parsed !== null &&
      typeof parsed.position === 'object' &&
      typeof parsed.position.top === 'number' &&
      typeof parsed.position.left === 'number' &&
      typeof parsed.collapsed === 'boolean'
    ) {
      return {
        position: {
          top: parsed.position.top,
          left: parsed.position.left,
        },
        collapsed: parsed.collapsed,
      };
    }
  } catch (e) {
    console.warn('Unable to load chat position:', e);
  }
  return null;
}