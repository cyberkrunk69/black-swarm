/**
 * Dashboard Keyboard Shortcuts
 *
 * Shortcuts:
 *   g – Switch to Grid view
 *   l – Switch to Log view
 *   t – Switch to Tree view
 *   Space – Pause/Resume auto‑refresh
 *   r – Force a refresh
 *   ? – Toggle help overlay
 *
 * The current mode is displayed in the header element with id="dashboard-header".
 * A help overlay is created on‑the‑fly if it does not already exist.
 */

(() => {
    // Configuration – IDs of elements used by the dashboard
    const HEADER_ID = "dashboard-header";
    const HELP_OVERLAY_ID = "dashboard-help-overlay";

    // State tracking
    let currentMode = "grid";      // default mode
    let autoRefreshPaused = false;

    // Utility: update the header with the current mode
    function updateHeader() {
        const header = document.getElementById(HEADER_ID);
        if (header) {
            header.textContent = `Dashboard – ${currentMode.toUpperCase()} view`;
        }
    }

    // Utility: toggle auto‑refresh pause state
    function toggleAutoRefresh() {
        autoRefreshPaused = !autoRefreshPaused;
        // Assuming there is a global function `setAutoRefreshPaused(boolean)`
        if (typeof setAutoRefreshPaused === "function") {
            setAutoRefreshPaused(autoRefreshPaused);
        }
        const status = autoRefreshPaused ? "PAUSED" : "RESUMED";
        console.info(`[Dashboard] Auto‑refresh ${status}`);
    }

    // Utility: force a refresh
    function forceRefresh() {
        // Assuming there is a global function `refreshDashboard()`
        if (typeof refreshDashboard === "function") {
            refreshDashboard();
            console.info("[Dashboard] Forced refresh");
        }
    }

    // Utility: switch view mode
    function switchMode(mode) {
        if (!["grid", "log", "tree"].includes(mode)) return;
        currentMode = mode;
        // Assuming there is a global function `setDashboardMode(mode)`
        if (typeof setDashboardMode === "function") {
            setDashboardMode(mode);
        }
        updateHeader();
        console.info(`[Dashboard] Switched to ${mode} view`);
    }

    // Utility: create or toggle the help overlay
    function toggleHelpOverlay() {
        let overlay = document.getElementById(HELP_OVERLAY_ID);
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.id = HELP_OVERLAY_ID;
            overlay.style.position = "fixed";
            overlay.style.top = "0";
            overlay.style.left = "0";
            overlay.style.width = "100%";
            overlay.style.height = "100%";
            overlay.style.backgroundColor = "rgba(0,0,0,0.8)";
            overlay.style.color = "#fff";
            overlay.style.zIndex = "10000";
            overlay.style.display = "flex";
            overlay.style.flexDirection = "column";
            overlay.style.alignItems = "center";
            overlay.style.justifyContent = "center";
            overlay.style.fontFamily = "sans-serif";
            overlay.style.fontSize = "1.2rem";
            overlay.style.padding = "2rem";
            overlay.style.boxSizing = "border-box";

            overlay.innerHTML = `
                <h2>Dashboard Keyboard Shortcuts</h2>
                <ul style="list-style:none; padding:0; line-height:1.8;">
                    <li><strong>g</strong> – Grid view</li>
                    <li><strong>l</strong> – Log view</li>
                    <li><strong>t</strong> – Tree view</li>
                    <li><strong>Space</strong> – Pause/Resume auto‑refresh</li>
                    <li><strong>r</strong> – Force refresh</li>
                    <li><strong>?</strong> – Toggle this help overlay</li>
                </ul>
                <p style="margin-top:1rem; font-size:0.9rem;">Press <strong>?</strong> again to close.</p>
            `;
            document.body.appendChild(overlay);
        } else {
            overlay.style.display = overlay.style.display === "none" ? "flex" : "none";
        }
    }

    // Keydown handler
    function handleKeydown(event) {
        // Ignore if focus is on an input/textarea/select to avoid interfering with typing
        const activeTag = document.activeElement?.tagName?.toLowerCase();
        if (["input", "textarea", "select"].includes(activeTag)) return;

        const key = event.key.toLowerCase();

        switch (key) {
            case "g":
                switchMode("grid");
                break;
            case "l":
                switchMode("log");
                break;
            case "t":
                switchMode("tree");
                break;
            case " ":
                event.preventDefault(); // prevent page scrolling
                toggleAutoRefresh();
                break;
            case "r":
                forceRefresh();
                break;
            case "?":
                toggleHelpOverlay();
                break;
            default:
                return; // not a handled key
        }

        // Prevent default browser actions for handled shortcuts
        event.preventDefault();
    }

    // Initialize
    function init() {
        updateHeader();
        document.addEventListener("keydown", handleKeydown);
    }

    // Run init when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();