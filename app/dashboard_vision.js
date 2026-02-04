/**
 * dashboard_vision.js
 *
 * This module handles the visual representation of the dashboard nodes and
 * provides drag‑and‑drop functionality for repositioning them.
 *
 * The implementation below adds a drag‑handle (three vertical dots) to each
 * node, enables click‑and‑drag repositioning with visual feedback (scale +
 * shadow), and ensures nodes stay within the viewport boundaries.
 *
 * Functions implemented:
 *   - setupNodeDrag()
 *   - handleNodeDrag(event)
 *   - stopNodeDrag(event)
 *
 * The drag lifecycle:
 *   1. User presses mouse button on the drag‑handle → start dragging.
 *   2. While mouse moves → node follows cursor, constrained to viewport.
 *   3. On mouse release → drag ends, visual feedback is cleared.
 *
 * The code assumes that each dashboard node has the CSS class `node`.
 * Drag‑handle markup and minimal styling are injected dynamically.
 */

(() => {
  // -------------------------------------------------------------------------
  // Drag state (module‑level, shared across all nodes)
  // -------------------------------------------------------------------------
  let activeNode = null;      // The node currently being dragged
  let offsetX = 0;            // Cursor offset within the node (X)
  let offsetY = 0;            // Cursor offset within the node (Y)

  /**
   * Adds a drag‑handle to each node and wires up the necessary event listeners.
   * Called once after the dashboard UI has been rendered.
   */
  function setupNodeDrag() {
    const nodes = document.querySelectorAll('.node');

    nodes.forEach(node => {
      // Ensure the node is positioned absolutely/fixed for manual placement.
      const style = window.getComputedStyle(node);
      if (style.position === 'static') {
        node.style.position = 'relative';
      }

      // -----------------------------------------------------------------------
      // Create / reuse the drag handle (three vertical dots)
      // -----------------------------------------------------------------------
      let handle = node.querySelector('.drag-handle');
      if (!handle) {
        handle = document.createElement('div');
        handle.className = 'drag-handle';
        // Simple three‑dot representation
        handle.innerHTML = '&#x2022;&#x2022;&#x2022;';
        // Position the handle in the top‑right corner
        handle.style.position = 'absolute';
        handle.style.top = '4px';
        handle.style.right = '4px';
        handle.style.cursor = 'grab';
        handle.style.userSelect = 'none';
        handle.style.fontSize = '14px';
        handle.style.lineHeight = '1';
        handle.style.color = '#666';
        node.appendChild(handle);
      }

      // -----------------------------------------------------------------------
      // Attach mousedown listener to start dragging
      // -----------------------------------------------------------------------
      handle.addEventListener('mousedown', (e) => {
        e.stopPropagation(); // Prevent node‑level click handlers from firing
        e.preventDefault();  // Avoid text selection

        // Record the node being dragged and cursor offset
        activeNode = node;
        const rect = node.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;

        // Apply visual feedback
        node.classList.add('dragging');
        node.style.transition = 'transform 0.1s, box-shadow 0.1s';
        node.style.transform = 'scale(1.05)';
        node.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';

        // Change cursor for the handle while dragging
        handle.style.cursor = 'grabbing';

        // Register global listeners for move / up events
        document.addEventListener('mousemove', handleNodeDrag);
        document.addEventListener('mouseup', stopNodeDrag);
      });
    });
  }

  /**
   * Handles mousemove events while a node is being dragged.
   *
   * @param {MouseEvent} e
   */
  function handleNodeDrag(e) {
    if (!activeNode) return;

    // Compute new top/left values based on cursor position minus the original offset
    const newLeft = e.clientX - offsetX;
    const newTop = e.clientY - offsetY;

    // -----------------------------------------------------------------------
    // Constrain the node within the viewport boundaries
    // -----------------------------------------------------------------------
    const nodeRect = activeNode.getBoundingClientRect();
    const nodeWidth = nodeRect.width;
    const nodeHeight = nodeRect.height;

    const maxLeft = window.innerWidth - nodeWidth;
    const maxTop = window.innerHeight - nodeHeight;

    const clampedLeft = Math.max(0, Math.min(newLeft, maxLeft));
    const clampedTop = Math.max(0, Math.min(newTop, maxTop));

    // Apply the new position. We use `style.left` / `style.top` assuming the node
    // is positioned relatively/absolutely.
    activeNode.style.position = 'absolute';
    activeNode.style.left = `${clampedLeft}px`;
    activeNode.style.top = `${clampedTop}px`;
  }

  /**
   * Cleans up after a drag operation ends (mouse up).
   *
   * @param {MouseEvent} e
   */
  function stopNodeDrag(e) {
    if (!activeNode) return;

    // Remove visual feedback
    activeNode.classList.remove('dragging');
    activeNode.style.transform = 'scale(1)';
    activeNode.style.boxShadow = 'none';
    activeNode.style.transition = '';

    // Reset cursor on the handle
    const handle = activeNode.querySelector('.drag-handle');
    if (handle) {
      handle.style.cursor = 'grab';
    }

    // Clean up listeners and state
    document.removeEventListener('mousemove', handleNodeDrag);
    document.removeEventListener('mouseup', stopNodeDrag);
    activeNode = null;
    offsetX = 0;
    offsetY = 0;
  }

  // Export functions for external modules (if needed)
  window.DashboardVision = {
    setupNodeDrag,
    handleNodeDrag,
    stopNodeDrag,
  };

  // Auto‑initialize when the DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupNodeDrag);
  } else {
    setupNodeDrag();
  }
})();
/* ---------- Real‑Time Workers Grid View ---------- */

/* Global state for active workers */
const activeWorkers = new Map();   // key: workerId, value: { taskId, status, startTime, action }

/* Utility: format elapsed time */
function formatElapsed(ms) {
    const totalSec = Math.floor(ms / 1000);
    const hrs = Math.floor(totalSec / 3600).toString().padStart(2, '0');
    const mins = Math.floor((totalSec % 3600) / 60).toString().padStart(2, '0');
    const secs = (totalSec % 60).toString().padStart(2, '0');
    return `${hrs}:${mins}:${secs}`;
}

/* Create or retrieve the grid container */
function getWorkersGridContainer() {
    let container = document.getElementById('workers-grid');
    if (!container) {
        container = document.createElement('div');
        container.id = 'workers-grid';
        container.style.display = 'grid';
        container.style.gap = '8px';
        container.style.padding = '8px';
        // Auto‑scale columns based on number of workers (min 150px per cell)
        container.style.gridTemplateColumns = 'repeat(auto-fill, minmax(150px, 1fr))';
        // Insert the grid container just below the main dashboard header (if present)
        const header = document.querySelector('#dashboard-header') || document.body;
        header.parentNode.insertBefore(container, header.nextSibling);
    }
    return container;
}

/* Render the grid based on current activeWorkers */
function renderWorkersGrid() {
    const container = getWorkersGridContainer();
    // Clear previous cells
    container.innerHTML = '';

    const now = Date.now();
    activeWorkers.forEach((info, workerId) => {
        const cell = document.createElement('div');
        cell.style.border = '1px solid #ccc';
        cell.style.borderRadius = '4px';
        cell.style.padding = '6px';
        cell.style.backgroundColor = '#fafafa';
        cell.style.fontFamily = 'sans-serif';
        cell.style.fontSize = '0.9rem';

        // Color‑code status
        let statusColor = '#999';
        switch (info.status) {
            case 'running':   statusColor = '#4caf50'; break;   // green
            case 'waiting':   statusColor = '#ff9800'; break;   // orange
            case 'error':     statusColor = '#f44336'; break;   // red
            case 'completed': statusColor = '#2196f3'; break;   // blue
        }

        const elapsed = now - info.startTime;

        cell.innerHTML = `
            <div><strong>Worker:</strong> ${workerId}</div>
            <div><strong>Task:</strong> ${info.taskId}</div>
            <div><strong>Status:</strong> <span style="color:${statusColor}">${info.status}</span></div>
            <div><strong>Elapsed:</strong> ${formatElapsed(elapsed)}</div>
            <div><strong>Action:</strong> ${info.action || '—'}</div>
        `;
        container.appendChild(cell);
    });
}

/* SSE connection to receive live worker updates */
function initWorkersSSE() {
    const evtSource = new EventSource('/workers/stream'); // endpoint must stream JSON lines

    evtSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            // Expected payload: { workerId, taskId, status, action, timestamp }
            const { workerId, taskId, status, action, timestamp } = data;
            if (!workerId) return;

            if (status === 'removed' || status === 'completed') {
                activeWorkers.delete(workerId);
            } else {
                const startTime = activeWorkers.has(workerId)
                    ? activeWorkers.get(workerId).startTime
                    : (timestamp ? new Date(timestamp).getTime() : Date.now());
                activeWorkers.set(workerId, {
                    taskId: taskId || '—',
                    status: status || 'unknown',
                    action: action || '',
                    startTime: startTime
                });
            }
            renderWorkersGrid();
        } catch (e) {
            console.error('Failed to process worker SSE message', e);
        }
    };

    evtSource.onerror = function(err) {
        console.error('Workers SSE connection error', err);
        // Auto‑reconnect after a short delay
        setTimeout(initWorkersSSE, 3000);
    };
}

/* Initialise the grid and SSE when dashboard loads */
document.addEventListener('DOMContentLoaded', () => {
    getWorkersGridContainer();   // ensure container exists
    initWorkersSSE();            // start listening for updates
    // also start a timer to refresh elapsed times every second
    setInterval(renderWorkersGrid, 1000);
});