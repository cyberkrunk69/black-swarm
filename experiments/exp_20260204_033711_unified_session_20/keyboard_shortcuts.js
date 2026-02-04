/**
 * Keyboard shortcuts for the dashboard.
 *
 * Shortcuts:
 *   g - Switch to Grid view
 *   l - Switch to Log view
 *   t - Switch to Tree view
 *   Space - Pause/Resume auto‑refresh
 *   r - Force refresh
 *   ? - Show help overlay
 *
 * The current mode is displayed in the header element with id="mode-header".
 *
 * This module assumes the existence of the following functions/variables in the
 * global scope (provided by the main dashboard code):
 *
 *   switchToGrid()          – activate grid view
 *   switchToLog()           – activate log view
 *   switchToTree()          – activate tree view
 *   toggleAutoRefresh()    – pause/resume auto‑refresh
 *   forceRefresh()          – immediate refresh
 *   showHelpOverlay()       – display help overlay
 *   getCurrentMode()        – returns a string identifier of the current mode
 *
 * If any of these are missing, the shortcuts will silently fail for that action.
 */

(function () {
  // Mapping of key codes to actions
  const keyMap = {
    // 'g' key
    71: () => {
      if (typeof switchToGrid === 'function') {
        switchToGrid();
        updateHeader('Grid');
      }
    },
    // 'l' key
    76: () => {
      if (typeof switchToLog === 'function') {
        switchToLog();
        updateHeader('Log');
      }
    },
    // 't' key
    84: () => {
      if (typeof switchToTree === 'function') {
        switchToTree();
        updateHeader('Tree');
      }
    },
    // Space bar
    32: (e) => {
      // Prevent page scrolling when space is used as a shortcut
      e.preventDefault();
      if (typeof toggleAutoRefresh === 'function') {
        toggleAutoRefresh();
        // Update header to reflect pause state if needed
        const mode = typeof getCurrentMode === 'function' ? getCurrentMode() : '';
        updateHeader(mode);
      }
    },
    // 'r' key
    82: () => {
      if (typeof forceRefresh === 'function') {
        forceRefresh();
      }
    },
    // '?' key (Shift + /)
    191: (e) => {
      // Detect if Shift is held for '?'
      if (e.shiftKey) {
        if (typeof showHelpOverlay === 'function') {
          showHelpOverlay();
        }
        e.preventDefault();
      }
    },
  };

  /**
   * Updates the header element with the current mode.
   *
   * @param {string} mode - Human readable mode name (e.g., "Grid", "Log", "Tree").
   */
  function updateHeader(mode) {
    const headerEl = document.getElementById('mode-header');
    if (!headerEl) return;
    headerEl.textContent = `Mode: ${mode}`;
  }

  /**
   * Initialize the current mode display on page load.
   */
  function initHeader() {
    if (typeof getCurrentMode === 'function') {
      const mode = getCurrentMode();
      // Convert internal identifiers to friendly names
      const friendly = {
        grid: 'Grid',
        log: 'Log',
        tree: 'Tree',
      }[mode] || mode;
      updateHeader(friendly);
    }
  }

  // Attach the keydown listener to the document
  document.addEventListener('keydown', (e) => {
    // Ignore key events when focus is on an input/textarea/select to avoid interfering with typing
    const target = e.target;
    const tag = target.tagName.toLowerCase();
    if (['input', 'textarea', 'select'].includes(tag) && !target.readOnly) {
      return;
    }

    const handler = keyMap[e.keyCode];
    if (handler) {
      handler(e);
    }
  });

  // Run header initialization once the DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeader);
  } else {
    initHeader();
  }
})();