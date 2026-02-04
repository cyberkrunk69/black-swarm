/**
 * dashboard_vision.js
 *
 * Handles visual interactions for dashboard nodes, including drag‑and‑drop
 * repositioning with a dedicated drag handle.
 *
 * The implementation follows the UI/UX Interaction Specification (section 1):
 *  • A three‑dot handle (⋮) appears in the top‑right corner of each node.
 *  • Clicking/touching the handle enables click‑and‑drag repositioning.
 *  • While dragging the node scales up slightly and receives a shadow for
 *    visual feedback.
 *  • Nodes are constrained to stay within the viewport boundaries.
 */

/* Global drag state – holds the node currently being dragged and the
 * offset between the pointer and the node's top‑left corner. */
const dragState = {
    node: null,
    offsetX: 0,
    offsetY: 0,
};

/**
 * Initialise drag capability for all nodes present in the dashboard.
 *
 * For each element with the class `.node` a drag‑handle element is created
 * and attached. Event listeners for the drag lifecycle are bound to the
 * handle.
 */
function setupNodeDrag() {
    const nodes = document.querySelectorAll('.node');

    nodes.forEach(node => {
        // Ensure the node can be positioned absolutely.
        node.style.position = 'absolute';

        // Create the three‑dot drag handle.
        const handle = document.createElement('div');
        handle.className = 'drag-handle';
        // Unicode vertical ellipsis (⋮) – looks like three stacked dots.
        handle.innerHTML = '&#x22EE;';
        Object.assign(handle.style, {
            position: 'absolute',
            top: '4px',
            right: '4px',
            cursor: 'grab',
            fontSize: '12px',
            userSelect: 'none',
            lineHeight: '1',
        });

        // Append the handle to the node.
        node.appendChild(handle);

        // Bind mouse / touch events to start the drag operation.
        handle.addEventListener('mousedown', startNodeDrag);
        handle.addEventListener('touchstart', startNodeDrag, { passive: false });
    });
}

/**
 * Begin dragging a node.
 *
 * @param {MouseEvent|TouchEvent} e The initiating event.
 */
function startNodeDrag(e) {
    e.preventDefault();

    const handle = e.currentTarget;
    const node = handle.parentElement;
    const rect = node.getBoundingClientRect();

    // Determine pointer coordinates (mouse or first touch point).
    const clientX = e.type.startsWith('touch') ? e.touches[0].clientX : e.clientX;
    const clientY = e.type.startsWith('touch') ? e.touches[0].clientY : e.clientY;

    // Store the node and the offset between pointer and node origin.
    dragState.node = node;
    dragState.offsetX = clientX - rect.left;
    dragState.offsetY = clientY - rect.top;

    // Visual feedback: slight scale + shadow.
    node.style.transition = 'transform 0.1s, box-shadow 0.1s';
    node.style.transform = 'scale(1.05)';
    node.style.boxShadow = '0 8px 16px rgba(0,0,0,0.3)';

    // Register global listeners to track movement and termination.
    document.addEventListener('mousemove', handleNodeDrag);
    document.addEventListener('touchmove', handleNodeDrag, { passive: false });
    document.addEventListener('mouseup', stopNodeDrag);
    document.addEventListener('touchend', stopNodeDrag);
}

/**
 * Handle the node being dragged – updates its position while respecting
 * viewport bounds.
 *
 * @param {MouseEvent|TouchEvent} e The move event.
 */
function handleNodeDrag(e) {
    if (!dragState.node) return;

    e.preventDefault();

    const clientX = e.type.startsWith('touch') ? e.touches[0].clientX : e.clientX;
    const clientY = e.type.startsWith('touch') ? e.touches[0].clientY : e.clientY;

    // Compute new top‑left coordinates.
    let newLeft = clientX - dragState.offsetX;
    let newTop = clientY - dragState.offsetY;

    const node = dragState.node;
    const nodeRect = node.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Clamp within viewport.
    if (newLeft < 0) newLeft = 0;
    if (newTop < 0) newTop = 0;
    if (newLeft + nodeRect.width > viewportWidth) {
        newLeft = viewportWidth - nodeRect.width;
    }
    if (newTop + nodeRect.height > viewportHeight) {
        newTop = viewportHeight - nodeRect.height;
    }

    node.style.left = `${newLeft}px`;
    node.style.top = `${newTop}px`;
}

/**
 * End the drag operation – clean up listeners and reset visual cues.
 *
 * @param {MouseEvent|TouchEvent} e The termination event.
 */
function stopNodeDrag(e) {
    if (!dragState.node) return;

    const node = dragState.node;

    // Reset visual feedback.
    node.style.transform = 'scale(1)';
    node.style.boxShadow = '';
    node.style.transition = '';

    // Remove global listeners.
    document.removeEventListener('mousemove', handleNodeDrag);
    document.removeEventListener('touchmove', handleNodeDrag);
    document.removeEventListener('mouseup', stopNodeDrag);
    document.removeEventListener('touchend', stopNodeDrag);

    // Clear drag state.
    dragState.node = null;
}

/* Export functions if the module system is used elsewhere. */
export {
    setupNodeDrag,
    handleNodeDrag,
    stopNodeDrag,
};