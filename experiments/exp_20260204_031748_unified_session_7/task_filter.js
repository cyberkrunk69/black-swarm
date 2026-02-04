/**
 * Task Filtering & Search Module
 *
 * Adds a search box that filters visible tasks by:
 *   - id
 *   - description text
 *   - status
 *   - phase
 *
 * Features:
 *   - Regex support (case‑insensitive)
 *   - Highlighting of matched substrings
 *   - Persisted filter in URL hash for easy sharing
 *
 * Expected HTML structure:
 *
 * <input type="text" id="task-search" placeholder="Search tasks (regex supported)" />
 *
 * <div class="task-list">
 *   <div class="task-item"
 *        data-id="123"
 *        data-description="Fix login bug"
 *        data-status="open"
 *        data-phase="development">
 *       <!-- task content -->
 *   </div>
 *   ...
 * </div>
 *
 * The module works without any external dependencies.
 */

(() => {
    const SEARCH_INPUT_ID = 'task-search';
    const TASK_ITEM_CLASS = 'task-item';
    const HIGHLIGHT_CLASS = 'task-match-highlight';
    const HASH_KEY = 'filter';

    /**
     * Reads the current filter string from the URL hash.
     * Expected format: #filter=encodedRegex
     */
    function readFilterFromHash() {
        const hash = window.location.hash.substring(1); // strip '#'
        const params = new URLSearchParams(hash);
        const encoded = params.get(HASH_KEY);
        return encoded ? decodeURIComponent(encoded) : '';
    }

    /**
     * Writes the given filter string to the URL hash.
     */
    function writeFilterToHash(filter) {
        const params = new URLSearchParams();
        if (filter) {
            params.set(HASH_KEY, encodeURIComponent(filter));
        }
        const newHash = params.toString();
        // Replace only the hash part to avoid navigation
        history.replaceState(null, '', newHash ? `#${newHash}` : window.location.pathname + window.location.search);
    }

    /**
     * Escapes HTML special characters to avoid XSS when injecting highlighted markup.
     */
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.innerText = str;
        return div.innerHTML;
    }

    /**
     * Highlights all matches of the regex within the given text.
     * Returns HTML string with <span class="task-match-highlight"> wrappers.
     */
    function highlightMatches(text, regex) {
        if (!regex) return escapeHtml(text);
        // Use replace with a function to preserve original case
        return escapeHtml(text).replace(regex, (match) => {
            return `<span class="${HIGHLIGHT_CLASS}">${match}</span>`;
        });
    }

    /**
     * Applies the filter to all task items.
     */
    function applyFilter(filterText) {
        const tasks = document.querySelectorAll(`.${TASK_ITEM_CLASS}`);
        let regex = null;

        if (filterText) {
            try {
                regex = new RegExp(filterText, 'gi');
            } catch (e) {
                // Invalid regex – treat as plain text search (escaped)
                const escaped = filterText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                regex = new RegExp(escaped, 'gi');
            }
        }

        tasks.forEach(task => {
            const fields = {
                id: task.dataset.id || '',
                description: task.dataset.description || '',
                status: task.dataset.status || '',
                phase: task.dataset.phase || ''
            };

            // Determine if any field matches
            const matches = Object.values(fields).some(value => {
                return regex ? regex.test(value) : true; // if no regex, always true (show all)
            });

            if (matches) {
                task.style.display = '';
                // Highlight matches in each field that is rendered inside the task element.
                // This implementation assumes that the task's innerHTML contains the raw
                // field values (e.g., via <span class="field-id">...</span> etc.).
                // For a generic approach, we replace the whole innerHTML safely.
                let html = task.innerHTML;
                if (regex) {
                    // Escape before re‑highlighting to avoid double‑escaping
                    html = html.replace(/<span class="[^"]*">.*?<\/span>/gi, (m) => {
                        // Strip existing highlight spans to avoid nesting
                        const tmp = document.createElement('div');
                        tmp.innerHTML = m;
                        return tmp.textContent;
                    });
                    // Apply highlighting to each field text
                    Object.values(fields).forEach(value => {
                        if (value) {
                            const safeValue = escapeHtml(value);
                            const highlighted = highlightMatches(safeValue, regex);
                            // Replace raw text occurrences (case‑insensitive)
                            const pattern = new RegExp(safeValue, 'gi');
                            html = html.replace(pattern, highlighted);
                        }
                    });
                } else {
                    // No regex – remove any existing highlights
                    html = html.replace(/<span class="[^"]*">([^<]*)<\/span>/gi, '$1');
                }
                task.innerHTML = html;
            } else {
                task.style.display = 'none';
            }
        });
    }

    /**
     * Initializes the search UI and binds events.
     */
    function init() {
        const input = document.getElementById(SEARCH_INPUT_ID);
        if (!input) {
            console.warn(`[TaskFilter] No input element found with id="${SEARCH_INPUT_ID}".`);
            return;
        }

        // Load filter from URL hash on page load
        const initialFilter = readFilterFromHash();
        input.value = initialFilter;
        applyFilter(initialFilter);

        // Debounce helper
        let debounceTimer = null;
        const DEBOUNCE_MS = 300;

        input.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const filter = input.value.trim();
                writeFilterToHash(filter);
                applyFilter(filter);
            }, DEBOUNCE_MS);
        });

        // Listen to hash changes (e.g., back/forward navigation)
        window.addEventListener('hashchange', () => {
            const newFilter = readFilterFromHash();
            input.value = newFilter;
            applyFilter(newFilter);
        });
    }

    // Run after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();