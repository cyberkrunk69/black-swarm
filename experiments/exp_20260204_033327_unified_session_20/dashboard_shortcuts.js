/**
 * Dashboard Keyboard Shortcuts
 *
 * Shortcuts:
 *   g - Switch to Grid view
 *   l - Switch to Log view
 *   t - Switch to Tree view
 *   Space - Pause/Resume auto‑refresh
 *   r - Force a manual refresh
 *   ? - Toggle help overlay
 *
 * The current mode is displayed in the header element with id="dashboard-mode".
 *
 * This script assumes the existence of the following functions / elements in the
 * dashboard page:
 *   - setViewMode(mode)            // Switches view mode ('grid' | 'log' | 'tree')
 *   - toggleAutoRefresh()         // Pauses or resumes auto‑refresh
 *   - forceRefresh()              // Triggers an immediate data refresh
 *   - toggleHelpOverlay()         // Shows/hides the help overlay
 *   - document.getElementById('dashboard-mode')
 *
 * If any of these are missing, you will need to implement them in the main
 * dashboard code.
 */

(() => {
  // Mapping of keys to view modes
  const VIEW_KEYS = {
    g: 'grid',
    l: 'log',
    t: 'tree',
  };

  // Current state
  let autoRefreshPaused = false;
  let currentMode = 'grid'; // default mode; adjust if needed

  // Helper: update header display
  const updateHeader = () => {
    const headerEl = document.getElementById('dashboard-mode');
    if (headerEl) {
      headerEl.textContent = `Mode: ${currentMode.charAt(0).toUpperCase() + currentMode.slice(1)}`;
    }
  };

  // Switch view mode
  const setMode = (mode) => {
    if (!mode || mode === currentMode) return;
    if (typeof window.setViewMode === 'function') {
      window.setViewMode(mode);
    }
    currentMode = mode;
    updateHeader();
  };

  // Toggle auto‑refresh pause/resume
  const togglePause = () => {
    if (typeof window.toggleAutoRefresh === 'function') {
      window.toggleAutoRefresh();
    }
    autoRefreshPaused = !autoRefreshPaused;
    // Optional visual cue: change header style
    const headerEl = document.getElementById('dashboard-mode');
    if (headerEl) {
      headerEl.style.opacity = autoRefreshPaused ? '0.5' : '1';
    }
  };

  // Force a manual refresh
  const refreshNow = () => {
    if (typeof window.forceRefresh === 'function') {
      window.forceRefresh();
    }
  };

  // Toggle help overlay
  const toggleHelp = () => {
    if (typeof window.toggleHelpOverlay === 'function') {
      window.toggleHelpOverlay();
    }
  };

  // Keydown handler
  const onKeyDown = (e) => {
    // Ignore key events when focus is on input/textarea/select elements
    const tag = e.target.tagName.toLowerCase();
    if (['input', 'textarea', 'select'].includes(tag)) return;

    const key = e.key.toLowerCase();

    if (key === ' ') {
      e.preventDefault(); // prevent page scrolling
      togglePause();
      return;
    }

    if (key === 'r') {
      e.preventDefault();
      refreshNow();
      return;
    }

    if (key === '?') {
      e.preventDefault();
      toggleHelp();
      return;
    }

    if (VIEW_KEYS[key]) {
      e.preventDefault();
      setMode(VIEW_KEYS[key]);
    }
  };

  // Initialize
  document.addEventListener('keydown', onKeyDown);
  // Initial header update
  updateHeader();
})();