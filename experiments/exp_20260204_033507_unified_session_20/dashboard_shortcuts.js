/**
 * Dashboard Keyboard Shortcuts
 *
 * This module registers global keyboard shortcuts for the dashboard UI:
 *   - g : Switch to Grid view
 *   - l : Switch to Log view
 *   - t : Switch to Tree view
 *   - Space : Pause / Resume auto‑refresh
 *   - r : Force a manual refresh
 *   - ? : Show a help overlay describing the shortcuts
 *
 * It also updates the header to display the current view mode.
 *
 * The implementation assumes the existence of a global `dashboard` object with the
 * following API:
 *   - dashboard.setView(mode: 'grid' | 'log' | 'tree')
 *   - dashboard.togglePause()
 *   - dashboard.refresh()
 *   - dashboard.showHelp()
 *
 * The current mode is displayed in an element with id `header-mode`.
 *
 * To integrate, simply import this script in the dashboard page:
 *   <script src="/experiments/exp_20260204_033507_unified_session_20/dashboard_shortcuts.js"></script>
 */

(function () {
  // Mapping from key to view mode
  const viewKeyMap = {
    g: 'grid',
    l: 'log',
    t: 'tree'
  };

  // Helper to update the header with the current mode
  function updateHeader(mode) {
    const headerEl = document.getElementById('header-mode');
    if (headerEl) {
      headerEl.textContent = mode.charAt(0).toUpperCase() + mode.slice(1) + ' View';
    }
  }

  // Main keydown handler
  function onKeyDown(event) {
    // Ignore events when focus is on input/textarea/select to avoid interfering with typing
    const target = event.target;
    const tag = target.tagName.toLowerCase();
    if (['input', 'textarea', 'select'].includes(tag) || target.isContentEditable) {
      return;
    }

    const key = event.key.toLowerCase();

    // Help overlay
    if (key === '?') {
      if (typeof dashboard.showHelp === 'function') {
        dashboard.showHelp();
      }
      event.preventDefault();
      return;
    }

    // Space – pause/resume auto‑refresh
    if (key === ' ') {
      if (typeof dashboard.togglePause === 'function') {
        dashboard.togglePause();
      }
      event.preventDefault();
      return;
    }

    // Force refresh
    if (key === 'r') {
      if (typeof dashboard.refresh === 'function') {
        dashboard.refresh();
      }
      event.preventDefault();
      return;
    }

    // View switching
    if (viewKeyMap[key]) {
      const mode = viewKeyMap[key];
      if (typeof dashboard.setView === 'function') {
        dashboard.setView(mode);
        updateHeader(mode);
      }
      event.preventDefault();
    }
  }

  // Attach the listener once the DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      document.addEventListener('keydown', onKeyDown);
    });
  } else {
    document.addEventListener('keydown', onKeyDown);
  }

  // Expose a minimal API for testing / external use
  window.dashboardShortcuts = {
    setView: (mode) => {
      if (typeof dashboard.setView === 'function') {
        dashboard.setView(mode);
        updateHeader(mode);
      }
    },
    togglePause: () => {
      if (typeof dashboard.togglePause === 'function') {
        dashboard.togglePause();
      }
    },
    refresh: () => {
      if (typeof dashboard.refresh === 'function') {
        dashboard.refresh();
      }
    },
    showHelp: () => {
      if (typeof dashboard.showHelp === 'function') {
        dashboard.showHelp();
      }
    }
  };
})();