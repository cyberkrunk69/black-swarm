/**
 * Task Filtering & Search Module
 *
 * Adds a search box to the task list UI that filters tasks by:
 *   - id
 *   - description text
 *   - status
 *   - phase
 *
 * Features:
 *   - Regex support (case‑insensitive)
 *   - Highlighting of matching substrings
 *   - Persisted filter string in the URL hash for easy sharing
 *
 * Integration:
 *   1. Include this script after the task list markup.
 *   2. Ensure each task row has the following data attributes:
 *        data-id, data-description, data-status, data-phase
 *      Example:
 *        <tr class="task-row"
 *            data-id="123"
 *            data-description="Fix login bug"
 *            data-status="open"
 *            data-phase="development">
 *            ...
 *        </tr>
 *   3. The script will automatically inject a search input
 *      element above the task table.
 */

(function () {
    // Configuration
    const SEARCH_INPUT_ID = 'task-search-input';
    const TASK_ROW_CLASS = 'task-row';
    const HIGHLIGHT_CLASS = 'task-search-highlight';

    // Helper: Escape HTML to avoid injection when highlighting
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // Helper: Highlight matches in a string using <mark>
    function highlightMatches(text, regex) {
        if (!regex) return escapeHtml(text);
        // Use replace with function to keep HTML safe
        return escapeHtml(text).replace(regex, (match) => `<mark class="${HIGHLIGHT_CLASS}">${match}</mark>`);
    }

    // Build the search UI
    function createSearchBox() {
        const container = document.createElement('div');
        container.style.margin = '1rem 0';
        container.innerHTML = `
            <input type="text" id="${SEARCH_INPUT_ID}" placeholder="Search tasks (regex supported)" style="width: 100%; padding: 0.5rem; font-size: 1rem;">
        `;
        // Insert before the first task table (or at body start if none)
        const firstTable = document.querySelector('table');
        if (firstTable) {
            firstTable.parentNode.insertBefore(container, firstTable);
        } else {
            document.body.insertBefore(container, document.body.firstChild);
        }
    }

    // Retrieve the current filter string from the URL hash (if any)
    function getFilterFromHash() {
        const hash = decodeURIComponent(window.location.hash.slice(1));
        return hash.startsWith('filter=') ? hash.slice(7) : '';
    }

    // Persist the filter string to the URL hash
    function setFilterToHash(filter) {
        const encoded = encodeURIComponent(`filter=${filter}`);
        if (window.location.hash !== `#${encoded}`) {
            window.location.hash = encoded;
        }
    }

    // Main filter logic
    function applyFilter(filter) {
        let regex = null;
        if (filter) {
            try {
                regex = new RegExp(filter, 'gi');
            } catch (e) {
                // Invalid regex – ignore filtering but keep UI responsive
                console.warn('Invalid regex for task filter:', e);
                regex = null;
            }
        }

        const rows = document.querySelectorAll(`.${TASK_ROW_CLASS}`);
        rows.forEach(row => {
            const id = row.dataset.id || '';
            const description = row.dataset.description || '';
            const status = row.dataset.status || '';
            const phase = row.dataset.phase || '';

            const combined = `${id} ${description} ${status} ${phase}`;

            const isMatch = regex ? regex.test(combined) : !filter; // show all if no filter
            row.style.display = isMatch ? '' : 'none';

            // Highlight matches in the visible columns
            // Assuming each column contains a span or text node with the raw value
            // We'll replace innerHTML safely for the columns we know.
            const cells = row.querySelectorAll('td');
            if (cells.length) {
                // Map column order: id, description, status, phase (adjust if needed)
                const [idCell, descCell, statusCell, phaseCell] = cells;
                if (idCell) idCell.innerHTML = highlightMatches(id, regex);
                if (descCell) descCell.innerHTML = highlightMatches(description, regex);
                if (statusCell) statusCell.innerHTML = highlightMatches(status, regex);
                if (phaseCell) phaseCell.innerHTML = highlightMatches(phase, regex);
            }
        });
    }

    // Initialize
    function init() {
        createSearchBox();
        const input = document.getElementById(SEARCH_INPUT_ID);
        if (!input) return;

        // Load persisted filter from URL hash
        const persisted = getFilterFromHash();
        if (persisted) {
            input.value = persisted;
            applyFilter(persisted);
        }

        // Debounce input handling for performance
        let timeout = null;
        input.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const val = input.value.trim();
                setFilterToHash(val);
                applyFilter(val);
            }, 200);
        });

        // React to hash changes (e.g., user pastes a new URL)
        window.addEventListener('hashchange', () => {
            const newFilter = getFilterFromHash();
            input.value = newFilter;
            applyFilter(newFilter);
        });
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();