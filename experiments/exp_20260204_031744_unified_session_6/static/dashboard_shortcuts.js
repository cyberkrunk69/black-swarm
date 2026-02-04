/**
 * Dashboard Keyboard Shortcuts
 *
 * Shortcuts:
 *   g - Grid view
 *   l - Log view
 *   t - Tree view
 *   Space - Pause/Resume auto‑refresh
 *   r - Force refresh
 *   ? - Toggle help overlay
 *
 * The current view mode is displayed in the header element with id="view-mode-indicator".
 * The auto‑refresh status is displayed in the header element with id="auto-refresh-indicator".
 *
 * To use:
 *   1. Include this script in the dashboard HTML after the main dashboard script.
 *      <script src="/static/dashboard_shortcuts.js"></script>
 *   2. Ensure the header contains the two indicator elements:
 *      <span id="view-mode-indicator"></span>
 *      <span id="auto-refresh-indicator"></span>
 *   3. Ensure the dashboard exposes the following functions (or adapt the calls below):
 *        - setViewMode(mode)          // Switches view mode ('grid','log','tree')
 *        - pauseAutoRefresh()         // Pauses auto‑refresh
 *        - resumeAutoRefresh()        // Resumes auto‑refresh
 *        - forceRefresh()             // Forces an immediate refresh
 *
 * If the dashboard uses a different API, adjust the function calls accordingly.
 */

(() => {
  // Current state
  let currentMode = 'grid'; // default mode
  let autoRefreshPaused = false;
  let helpOverlayVisible = false;

  // Helper: update header indicators
  const updateHeader = () => {
    const modeEl = document.getElementById('view-mode-indicator');
    const refreshEl = document.getElementById('auto-refresh-indicator');
    if (modeEl) modeEl.textContent = `Mode: ${currentMode}`;
    if (refreshEl) refreshEl.textContent = `Auto‑Refresh: ${autoRefreshPaused ? 'Paused' : 'Running'}`;
  };

  // Helper: toggle help overlay
  const toggleHelpOverlay = () => {
    if (!document.getElementById('dashboard-help-overlay')) {
      const overlay = document.createElement('div');
      overlay.id = 'dashboard-help-overlay';
      overlay.style.position = 'fixed';
      overlay.style.top = '0';
      overlay.style.left = '0';
      overlay.style.width = '100%';
      overlay.style.height = '100%';
      overlay.style.backgroundColor = 'rgba(0,0,0,0.8)';
      overlay.style.color = '#fff';
      overlay.style.zIndex = '10000';
      overlay.style.display = 'flex';
      overlay.style.flexDirection = 'column';
      overlay.style.alignItems = 'center';
      overlay.style.justifyContent = 'center';
      overlay.style.fontFamily = 'sans-serif';
      overlay.style.fontSize = '1.2rem';
      overlay.innerHTML = `
        <h2>Dashboard Keyboard Shortcuts</h2>
        <ul style="list-style:none; padding:0;">
          <li><strong>g</strong> – Grid view</li>
          <li><strong>l</strong> – Log view</li>
          <li><strong>t</strong> – Tree view</li>
          <li><strong>Space</strong> – Pause/Resume auto‑refresh</li>
          <li><strong>r</strong> – Force refresh</li>
          <li><strong>?</strong> – Hide this help</li>
        </ul>
        <p>Press any key to dismiss.</p>
      `;
      overlay.addEventListener('click', () => {
        overlay.remove();
        helpOverlayVisible = false;
      });
      document.body.appendChild(overlay);
    } else {
      const overlay = document.getElementById('dashboard-help-overlay');
      overlay.remove();
    }
    helpOverlayVisible = !helpOverlayVisible;
  };

  // Core shortcut handler
  const handleKeyDown = (e) => {
    // Ignore if focus is on an input/textarea/select to avoid interfering with typing
    const activeTag = document.activeElement?.tagName?.toLowerCase();
    if (['input', 'textarea', 'select'].includes(activeTag)) return;

    switch (e.key) {
      case 'g':
      case 'G':
        if (typeof setViewMode === 'function') setViewMode('grid');
        currentMode = 'grid';
        updateHeader();
        break;
      case 'l':
      case 'L':
        if (typeof setViewMode === 'function') setViewMode('log');
        currentMode = 'log';
        updateHeader();
        break;
      case 't':
      case 'T':
        if (typeof setViewMode === 'function') setViewMode('tree');
        currentMode = 'tree';
        updateHeader();
        break;
      case ' ':
        e.preventDefault(); // prevent page scroll
        if (autoRefreshPaused) {
          if (typeof resumeAutoRefresh === 'function') resumeAutoRefresh();
        } else {
          if (typeof pauseAutoRefresh === 'function') pauseAutoRefresh();
        }
        autoRefreshPaused = !autoRefreshPaused;
        updateHeader();
        break;
      case 'r':
      case 'R':
        if (typeof forceRefresh === 'function') forceRefresh();
        break;
      case '?':
        toggleHelpOverlay();
        break;
      default:
        // If help overlay is visible and any other key is pressed, hide it
        if (helpOverlayVisible) toggleHelpOverlay();
        break;
    }
  };

  // Initialise
  document.addEventListener('keydown', handleKeyDown);
  // Initial header update
  updateHeader();
})();