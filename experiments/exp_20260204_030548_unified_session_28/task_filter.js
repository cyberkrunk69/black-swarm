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
 *   - Regex support (fallback to plain text if regex invalid)
 *   - Highlight matched substrings
 *   - Persist filter string in URL hash for shareability
 *
 * Expected DOM structure:
 *   <div id="task-filter-container"></div>
 *   <ul id="task-list">
 *     <li class="task-item"
 *         data-id="123"
 *         data-description="Fix login bug"
 *         data-status="open"
 *         data-phase="development">
 *       ... task content ...
 *     </li>
 *   </ul>
 *
 * Include this script in the page (e.g., <script src="task_filter.js"></script>)
 * and optionally the accompanying CSS file.
 */

(() => {
  const FILTER_CONTAINER_ID = 'task-filter-container';
  const TASK_LIST_ID = 'task-list';
  const HASH_PREFIX = '#filter=';

  /** Debounce helper */
  function debounce(fn, delay) {
    let timer = null;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  /** Escape regex special chars */
  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /** Retrieve current filter string from URL hash */
  function getFilterFromHash() {
    if (location.hash.startsWith(HASH_PREFIX)) {
      try {
        return decodeURIComponent(location.hash.slice(HASH_PREFIX.length));
      } catch (_) {
        return '';
      }
    }
    return '';
  }

  /** Persist filter string to URL hash */
  function setFilterToHash(filter) {
    const encoded = encodeURIComponent(filter);
    if (encoded) {
      location.hash = `${HASH_PREFIX}${encoded}`;
    } else {
      // clear hash if empty
      history.replaceState('', document.title, location.pathname + location.search);
    }
  }

  /** Highlight matches inside a string */
  function highlightMatches(text, regex) {
    // Use a <mark> element for highlighting (styled via CSS)
    return text.replace(regex, (match) => `<mark>${match}</mark>`);
  }

  /** Main filter function */
  function applyFilter(filterStr) {
    const taskList = document.getElementById(TASK_LIST_ID);
    if (!taskList) return;

    const tasks = taskList.querySelectorAll('.task-item');
    let regex = null;
    let isRegex = false;

    if (filterStr) {
      try {
        regex = new RegExp(filterStr, 'gi');
        isRegex = true;
      } catch (_) {
        // Invalid regex – treat as plain text
        regex = new RegExp(escapeRegExp(filterStr), 'gi');
      }
    }

    tasks.forEach((task) => {
      const fields = [
        task.dataset.id || '',
        task.dataset.description || '',
        task.dataset.status || '',
        task.dataset.phase || '',
      ];
      const combined = fields.join(' ');

      // Determine visibility
      const match = !filterStr || regex.test(combined);
      task.style.display = match ? '' : 'none';

      // Reset previous highlights
      const originalHTML = task.dataset.originalHtml || task.innerHTML;
      task.dataset.originalHtml = originalHTML; // store once
      task.innerHTML = originalHTML;

      // Apply highlights if visible and filter present
      if (match && filterStr) {
        // Highlight each field individually to keep markup clean
        const htmlParts = task.innerHTML.split(/(<[^>]+>)/g); // keep existing tags separate
        const highlighted = htmlParts.map((part) => {
          // Only process text nodes (not tags)
          if (part.startsWith('<')) return part;
          return highlightMatches(part, regex);
        });
        task.innerHTML = highlighted.join('');
      }
    });
  }

  /** Initialize UI */
  function init() {
    // Create container if missing
    let container = document.getElementById(FILTER_CONTAINER_ID);
    if (!container) {
      container = document.createElement('div');
      container.id = FILTER_CONTAINER_ID;
      const taskList = document.getElementById(TASK_LIST_ID);
      if (taskList && taskList.parentNode) {
        taskList.parentNode.insertBefore(container, taskList);
      }
    }

    // Build search input
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Search tasks (id, description, status, phase)…';
    input.style.width = '100%';
    input.style.boxSizing = 'border-box';
    input.style.marginBottom = '0.5rem';
    input.id = 'task-search-input';
    container.appendChild(input);

    // Load filter from URL hash
    const initialFilter = getFilterFromHash();
    input.value = initialFilter;
    applyFilter(initialFilter);

    // Bind events (debounced for performance)
    const onInput = debounce(() => {
      const value = input.value.trim();
      setFilterToHash(value);
      applyFilter(value);
    }, 250);
    input.addEventListener('input', onInput);

    // React to manual hash changes (e.g., back/forward navigation)
    window.addEventListener('hashchange', () => {
      const newFilter = getFilterFromHash();
      if (newFilter !== input.value) {
        input.value = newFilter;
        applyFilter(newFilter);
      }
    });
  }

  // Run after DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();