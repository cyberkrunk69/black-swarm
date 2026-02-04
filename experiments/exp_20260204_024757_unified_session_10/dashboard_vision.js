/**
 * dashboard_vision.js
 *
 * Implements interactive tree collapsing/expanding for the task dashboard.
 * The functions below are wired to the UI via event listeners attached to
 * root‑level task nodes.  When a root node is collapsed, all its descendant
 * task items are hidden and a compact summary is displayed that contains
 * the tree icon, title and a completion ratio (e.g. 3/7).
 *
 * The UI/UX specification for this behaviour lives in
 * UIUX_INTERACTION_SPEC.md §4.
 */

/* -------------------------------------------------------------------------- */
/* Helper utilities                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Returns the numeric completion ratio for a given tree root element.
 * The ratio is expressed as an object `{ completed, total }`.
 *
 * @param {HTMLElement} rootEl - The root element of a task tree.
 * @returns {{completed:number,total:number}}
 */
function _getCompletionRatio(rootEl) {
    // All task nodes (including the root) have the class `task-node`.
    // Completed nodes additionally have the class `completed`.
    const allNodes = rootEl.querySelectorAll('.task-node');
    const completedNodes = rootEl.querySelectorAll('.task-node.completed');

    // Exclude the root itself from the count – the ratio is about its children.
    const total = Math.max(allNodes.length - 1, 0);
    const completed = Math.max(completedNodes.length - (rootEl.classList.contains('completed') ? 1 : 0), 0);

    return { completed, total };
}

/**
 * Creates (or updates) the compact summary element for a collapsed tree.
 *
 * @param {HTMLElement} rootEl - The root element of a task tree.
 */
function _ensureSummaryElement(rootEl) {
    let summaryEl = rootEl.querySelector('.tree-summary');
    const { completed, total } = _getCompletionRatio(rootEl);
    const ratioText = total > 0 ? `${completed}/${total}` : '0/0';

    if (!summaryEl) {
        summaryEl = document.createElement('div');
        summaryEl.className = 'tree-summary';
        // Preserve visual alignment with the existing tree layout.
        summaryEl.style.display = 'flex';
        summaryEl.style.alignItems = 'center';
        summaryEl.style.marginLeft = '1.5rem'; // indent similar to child nodes
        rootEl.appendChild(summaryEl);
    }

    // Build the content: icon, title, ratio.
    // Re‑use the existing icon element if present.
    const icon = rootEl.querySelector('.tree-icon')?.cloneNode(true) ?? document.createElement('span');
    icon.className = 'tree-icon summary-icon';

    // Title is taken from the root node's title element.
    const titleEl = rootEl.querySelector('.node-title');
    const titleText = titleEl ? titleEl.textContent.trim() : 'Untitled';

    // Clear previous content.
    summaryEl.innerHTML = '';
    summaryEl.appendChild(icon);

    const titleSpan = document.createElement('span');
    titleSpan.className = 'summary-title';
    titleSpan.textContent = ` ${titleText} `;
    summaryEl.appendChild(titleSpan);

    const ratioSpan = document.createElement('span');
    ratioSpan.className = 'summary-ratio';
    ratioSpan.textContent = `(${ratioText})`;
    summaryEl.appendChild(ratioSpan);
}

/* -------------------------------------------------------------------------- */
/* Core API – collapse/expand/toggle                                         */
/* -------------------------------------------------------------------------- */

/**
 * Collapses a task tree into a compact mini‑summary.
 *
 * @param {HTMLElement} rootEl - The root element of the task tree to collapse.
 */
function collapseTree(rootEl) {
    if (!rootEl) return;

    // Guard against double‑collapse.
    if (rootEl.dataset.collapsed === 'true') return;

    // Hide all descendant task nodes (but keep the root visible).
    const descendantNodes = rootEl.querySelectorAll('.task-node');
    descendantNodes.forEach(node => {
        if (node !== rootEl) {
            node.style.display = 'none';
        }
    });

    // Insert (or update) the summary element.
    _ensureSummaryElement(rootEl);

    // Update button visual state.
    const toggleBtn = rootEl.querySelector('.collapse-toggle-btn');
    if (toggleBtn) {
        toggleBtn.textContent = '+';
        toggleBtn.title = 'Expand tree';
    }

    // Persist collapsed state.
    rootEl.dataset.collapsed = 'true';
}

/**
 * Expands a previously collapsed task tree, restoring the full view.
 *
 * @param {HTMLElement} rootEl - The root element of the task tree to expand.
 */
function expandTree(rootEl) {
    if (!rootEl) return;

    // Guard against double‑expand.
    if (rootEl.dataset.collapsed !== 'true') return;

    // Reveal all descendant task nodes.
    const descendantNodes = rootEl.querySelectorAll('.task-node');
    descendantNodes.forEach(node => {
        if (node !== rootEl) {
            node.style.display = '';
        }
    });

    // Remove the summary element.
    const summaryEl = rootEl.querySelector('.tree-summary');
    if (summaryEl) {
        summaryEl.remove();
    }

    // Update button visual state.
    const toggleBtn = rootEl.querySelector('.collapse-toggle-btn');
    if (toggleBtn) {
        toggleBtn.textContent = '–';
        toggleBtn.title = 'Collapse tree';
    }

    // Clear collapsed flag.
    delete rootEl.dataset.collapsed;
}

/**
 * Toggles the collapsed/expanded state of a task tree.
 *
 * This function is intended to be used as an event handler for the collapse
 * button attached to each root node.
 *
 * @param {Event} evt - The click event from the collapse button.
 */
function toggleTreeCollapse(evt) {
    const btn = evt.currentTarget;
    if (!btn) return;

    // The button lives inside the root node element.
    const rootEl = btn.closest('.task-node');
    if (!rootEl) return;

    if (rootEl.dataset.collapsed === 'true') {
        expandTree(rootEl);
    } else {
        collapseTree(rootEl);
    }
}

/* -------------------------------------------------------------------------- */
/* Initialization – attach collapse buttons to all root nodes               */
/* -------------------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // Root nodes are identified by the class `task-root` (a subset of `.task-node`).
    const rootNodes = document.querySelectorAll('.task-node.task-root');

    rootNodes.forEach(rootEl => {
        // Avoid adding duplicate buttons if the script reloads.
        if (rootEl.querySelector('.collapse-toggle-btn')) return;

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'collapse-toggle-btn';
        btn.textContent = '–'; // initially expanded
        btn.title = 'Collapse tree';
        btn.style.marginRight = '0.5rem';
        btn.addEventListener('click', toggleTreeCollapse);

        // Insert the button as the first child of the root node's header.
        // Assume the header container has class `node-header`.
        const header = rootEl.querySelector('.node-header') || rootEl;
        header.insertBefore(btn, header.firstChild);
    });
});

/* -------------------------------------------------------------------------- */
/* Export (for unit‑testing or external modules)                              */
/* -------------------------------------------------------------------------- */
export {
    collapseTree,
    expandTree,
    toggleTreeCollapse
};