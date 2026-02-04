/**
 * Dashboard Keyboard Shortcuts
 *
 * Shortcuts:
 *   g – Grid view
 *   l – Log view
 *   t – Tree view
 *   Space – Pause/Resume auto‑refresh
 *   r – Force refresh
 *   ? – Show help overlay
 *
 * The current mode is displayed in the header element with id="mode-header".
 * The help overlay is rendered in a div with id="help-overlay".
 *
 * This script is self‑contained and can be included on the dashboard page
 * via a <script src="static/dashboardShortcuts.js"></script> tag.
 */

(function () {
    // -------------------------------------------------------------------------
    // Configuration – IDs of DOM elements that must exist on the page
    // -------------------------------------------------------------------------
    const MODE_HEADER_ID = 'mode-header';      // <span> or similar in the header
    const HELP_OVERLAY_ID = 'help-overlay';    // hidden <div> for help text
    const REFRESH_TOGGLE_ID = 'refresh-toggle'; // optional element to reflect pause state

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------
    let currentMode = 'grid';   // default mode
    let autoRefreshPaused = false;

    // -------------------------------------------------------------------------
    // Utility helpers
    // -------------------------------------------------------------------------
    const $ = (selector) => document.querySelector(selector);
    const show = (el) => el && (el.style.display = 'block');
    const hide = (el) => el && (el.style.display = 'none');
    const toggle = (el) => el && (el.style.display = (el.style.display === 'none' ? 'block' : 'none'));

    // -------------------------------------------------------------------------
    // UI Updates
    // -------------------------------------------------------------------------
    function updateModeHeader() {
        const header = $(`#${MODE_HEADER_ID}`);
        if (header) {
            header.textContent = `${currentMode.charAt(0).toUpperCase() + currentMode.slice(1)} View`;
        }
    }

    function updateRefreshToggle() {
        const toggleEl = $(`#${REFRESH_TOGGLE_ID}`);
        if (toggleEl) {
            toggleEl.textContent = autoRefreshPaused ? 'Paused' : 'Running';
        }
    }

    function renderHelpOverlay() {
        let overlay = $(`#${HELP_OVERLAY_ID}`);
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = HELP_OVERLAY_ID;
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.backgroundColor = 'rgba(0,0,0,0.8)';
            overlay.style.color = '#fff';
            overlay.style.zIndex = '10000';
            overlay.style.display = 'none';
            overlay.style.padding = '2rem';
            overlay.style.overflowY = 'auto';
            overlay.style.fontFamily = 'sans-serif';
            overlay.innerHTML = `
                <h2>Dashboard Keyboard Shortcuts</h2>
                <ul style="font-size: 1.2rem; line-height: 1.6;">
                    <li><strong>g</strong> – Grid view</li>
                    <li><strong>l</strong> – Log view</li>
                    <li><strong>t</strong> – Tree view</li>
                    <li><strong>Space</strong> – Pause/Resume auto‑refresh</li>
                    <li><strong>r</strong> – Force refresh</li>
                    <li><strong>?</strong> – Show/Hide this help overlay</li>
                </ul>
                <p>Press <strong>Esc</strong> or click anywhere to close.</p>
            `;
            document.body.appendChild(overlay);

            // Close on click or Esc
            overlay.addEventListener('click', () => hide(overlay));
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') hide(overlay);
            });
        }
    }

    // -------------------------------------------------------------------------
    // Mode switching logic (placeholder – integrate with your actual view code)
    // -------------------------------------------------------------------------
    function switchMode(mode) {
        if (!['grid', 'log', 'tree'].includes(mode)) return;
        currentMode = mode;
        // Insert your view‑switching code here, e.g.:
        // window.dispatchEvent(new CustomEvent('dashboard:modeChange', {detail: mode}));
        updateModeHeader();
    }

    // -------------------------------------------------------------------------
    // Auto‑refresh control (placeholder – integrate with your refresh logic)
    // -------------------------------------------------------------------------
    function toggleAutoRefresh() {
        autoRefreshPaused = !autoRefreshPaused;
        // Insert your pause/resume logic here, e.g.:
        // window.dispatchEvent(new Event(autoRefreshPaused ? 'dashboard:pause' : 'dashboard:resume'));
        updateRefreshToggle();
    }

    function forceRefresh() {
        // Insert your manual refresh logic here, e.g.:
        // window.dispatchEvent(new Event('dashboard:refresh'));
        // For visual feedback we flash the header briefly
        const header = $(`#${MODE_HEADER_ID}`);
        if (header) {
            const original = header.style.transition;
            header.style.transition = 'background-color 0.2s';
            header.style.backgroundColor = '#ff0';
            setTimeout(() => {
                header.style.backgroundColor = '';
                header.style.transition = original;
            }, 200);
        }
    }

    // -------------------------------------------------------------------------
    // Keyboard handler
    // -------------------------------------------------------------------------
    function handleKeydown(e) {
        // Ignore if focus is on an input/textarea/select to avoid interfering typing
        const targetTag = e.target.tagName.toLowerCase();
        if (['input', 'textarea', 'select'].includes(targetTag)) return;

        switch (e.key) {
            case 'g':
            case 'G':
                switchMode('grid');
                break;
            case 'l':
            case 'L':
                switchMode('log');
                break;
            case 't':
            case 'T':
                switchMode('tree');
                break;
            case ' ':
                e.preventDefault(); // prevent page scroll
                toggleAutoRefresh();
                break;
            case 'r':
            case 'R':
                forceRefresh();
                break;
            case '?':
                renderHelpOverlay();
                const overlay = $(`#${HELP_OVERLAY_ID}`);
                toggle(overlay);
                break;
            default:
                // no action
                break;
        }
    }

    // -------------------------------------------------------------------------
    // Initialization
    // -------------------------------------------------------------------------
    function init() {
        updateModeHeader();
        updateRefreshToggle();
        document.addEventListener('keydown', handleKeydown);
    }

    // Run after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();