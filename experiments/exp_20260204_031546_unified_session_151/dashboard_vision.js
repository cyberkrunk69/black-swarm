/**
 * dashboard_vision.js
 *
 * This module provides UI interaction utilities for the task‑tree dashboard.
 * The functions below implement collapsing/expanding of whole task trees.
 *
 * The UI/UX spec (section 4) requires that each root node display a collapse
 * button. When collapsed the tree is replaced by a compact summary that shows:
 *   • a generic tree icon,
 *   • the tree title,
 *   • the completion ratio (completed / total * 100 %).
 *
 * The implementation works with the existing DOM structure used throughout the
 * application:
 *   • Each tree node is a `<li>` element with the class `tree-node`.
 *   • The root of a tree has the additional class `root-node`.
 *   • The node’s visual header is wrapped in an element with class `node-header`.
 *   • Child nodes are placed inside a `<ul>` directly under the node.
 *   • Individual tasks have the class `task-item`; completed tasks also have
 *     the class `completed`.
 *
 * The functions are deliberately defensive – they first verify that the
 * supplied element matches the expected structure and then perform the UI
 * transformation.  All DOM updates are performed using plain JavaScript to
 * avoid additional dependencies.
 */

/**
 * Collapse a whole task tree into a compact summary.
 *
 * @param {HTMLElement} rootNode - The root `<li>` element of the tree to collapse.
 */
function collapseTree(rootNode) {
    if (!rootNode || !rootNode.classList.contains('root-node')) {
        console.warn('collapseTree: supplied element is not a root-node', rootNode);
        return;
    }

    // Prevent double‑collapse.
    if (rootNode.dataset.collapsed === 'true') {
        return;
    }

    // -------------------------------------------------------------------------
    // 1️⃣ Compute the completion ratio.
    // -------------------------------------------------------------------------
    const taskItems   = rootNode.querySelectorAll('.task-item');
    const completed   = rootNode.querySelectorAll('.task-item.completed');
    const totalCount  = taskItems.length;
    const doneCount   = completed.length;
    const ratio       = totalCount ? Math.round((doneCount / totalCount) * 100) : 0;

    // -------------------------------------------------------------------------
    // 2️⃣ Hide the children list.
    // -------------------------------------------------------------------------
    const childrenList = rootNode.querySelector('ul');
    if (childrenList) {
        childrenList.style.display = 'none';
    }

    // -------------------------------------------------------------------------
    // 3️⃣ Build and insert the summary element.
    // -------------------------------------------------------------------------
    const summary = document.createElement('div');
    summary.className = 'tree-summary';
    // The spec calls for a generic tree icon – we use a simple Unicode glyph.
    const title   = rootNode.dataset.title ||
                    (rootNode.querySelector('.node-header')?.textContent?.trim() ?? 'Untitled');
    summary.innerHTML = `
        <span class="tree-icon" aria-hidden="true">📂</span>
        <span class="tree-title">${title}</span>
        <span class="completion-ratio">(${ratio}%)</span>
    `.trim();

    // Insert the summary after the node header (or as the first child if no header).
    const header = rootNode.querySelector('.node-header') || rootNode;
    header.appendChild(summary);

    // -------------------------------------------------------------------------
    // 4️⃣ Mark the node as collapsed.
    // -------------------------------------------------------------------------
    rootNode.dataset.collapsed = 'true';
}

/**
 * Expand a previously collapsed task tree, restoring its original view.
 *
 * @param {HTMLElement} rootNode - The root `<li>` element of the tree to expand.
 */
function expandTree(rootNode) {
    if (!rootNode || !rootNode.classList.contains('root-node')) {
        console.warn('expandTree: supplied element is not a root-node', rootNode);
        return;
    }

    // Nothing to do if the tree is already expanded.
    if (rootNode.dataset.collapsed !== 'true') {
        return;
    }

    // -------------------------------------------------------------------------
    // 1️⃣ Remove the summary element.
    // -------------------------------------------------------------------------
    const summary = rootNode.querySelector('.tree-summary');
    if (summary) {
        summary.remove();
    }

    // -------------------------------------------------------------------------
    // 2️⃣ Reveal the children list.
    // -------------------------------------------------------------------------
    const childrenList = rootNode.querySelector('ul');
    if (childrenList) {
        childrenList.style.display = '';
    }

    // -------------------------------------------------------------------------
    // 3️⃣ Clear the collapsed flag.
    // -------------------------------------------------------------------------
    delete rootNode.dataset.collapsed;
}

/**
 * Event handler attached to the collapse/expand button on each root node.
 *
 * The button toggles between the collapsed and expanded state.
 *
 * @param {Event} e - The click event from the collapse button.
 */
function toggleTreeCollapse(e) {
    // The button may be nested inside other elements; walk up to the root node.
    const btn = e.currentTarget || e.target;
    const rootNode = btn.closest('li.root-node');

    if (!rootNode) {
        console.warn('toggleTreeCollapse: could not locate root-node for button', btn);
        return;
    }

    const isCollapsed = rootNode.dataset.collapsed === 'true';
    if (isCollapsed) {
        expandTree(rootNode);
        btn.setAttribute('aria-label', 'Collapse tree');
        btn.textContent = '▾'; // down‑arrow indicates “collapse”
    } else {
        collapseTree(rootNode);
        btn.setAttribute('aria-label', 'Expand tree');
        btn.textContent = '▴'; // up‑arrow indicates “expand”
    }
}

/**
 * Initialise collapse buttons on all root nodes.
 *
 * This function should be called once after the DOM for the dashboard is ready.
 */
function initialiseTreeCollapseControls() {
    const rootNodes = document.querySelectorAll('li.root-node');
    rootNodes.forEach(root => {
        // Avoid adding duplicate buttons.
        if (root.querySelector('.collapse-btn')) {
            return;
        }

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'collapse-btn';
        btn.setAttribute('aria-label', 'Collapse tree');
        btn.textContent = '▾'; // default to “collapse” (tree is initially expanded)
        btn.addEventListener('click', toggleTreeCollapse);

        // Insert the button into the node header (or prepend to the root node).
        const header = root.querySelector('.node-header') || root;
        header.insertBefore(btn, header.firstChild);
    });
}

/* -------------------------------------------------------------------------
 * Export symbols (if the project uses a module system).  If not, the functions
 * are left in the global scope for backward compatibility.
 * ------------------------------------------------------------------------- */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        collapseTree,
        expandTree,
        toggleTreeCollapse,
        initialiseTreeCollapseControls
    };
}