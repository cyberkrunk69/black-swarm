/**
 * dashboard_vision.js
 *
 * This module provides UI utilities for the vision dashboard, including a
 * draggable, floating chat panel that can be minimized and interacts with the
 * rest of the UI via a blurred backdrop for visual separation.
 *
 * The implementation follows the specifications described in
 * UIUX_INTERACTION_SPEC.md §3.
 */

 // ---------------------------------------------------------------------------
 // Helper utilities
 // ---------------------------------------------------------------------------

 /**
  * Creates the floating chat UI component and injects it into the DOM.
  *
  * The chat consists of:
  *   - A header bar containing the title and a minimize button.
  *   - A body area that holds a scrollable message list.
  *   - An input area with a text field and a send button.
  *
  * The whole container has a subtle backdrop blur to keep the chat visually
  * separated from the underlying dashboard.
  *
  * @returns {HTMLElement} The root element of the floating chat.
  */
function createFloatingChat() {
    // Root container
    const chatRoot = document.createElement('div');
    chatRoot.id = 'floating-chat';
    chatRoot.style.position = 'fixed';
    chatRoot.style.bottom = '20px';
    chatRoot.style.right = '20px';
    chatRoot.style.width = '320px';
    chatRoot.style.maxHeight = '480px';
    chatRoot.style.display = 'flex';
    chatRoot.style.flexDirection = 'column';
    chatRoot.style.background = 'rgba(255,255,255,0.85)';
    chatRoot.style.borderRadius = '8px';
    chatRoot.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    chatRoot.style.backdropFilter = 'blur(8px)';
    chatRoot.style.zIndex = '1000';
    chatRoot.style.overflow = 'hidden';
    chatRoot.style.fontFamily = 'sans-serif';

    // Header (drag handle + title + minimize button)
    const header = document.createElement('div');
    header.id = 'floating-chat-header';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.justifyContent = 'space-between';
    header.style.padding = '8px 12px';
    header.style.cursor = 'move';
    header.style.background = 'rgba(0,0,0,0.05)';
    header.style.userSelect = 'none';

    const title = document.createElement('span');
    title.textContent = 'Chat';
    title.style.fontWeight = '600';
    title.style.fontSize = '14px';
    title.style.color = '#333';

    const minimizeBtn = document.createElement('button');
    minimizeBtn.id = 'floating-chat-minimize';
    minimizeBtn.textContent = '–'; // en‑dash as a minimize glyph
    minimizeBtn.title = 'Minimize';
    minimizeBtn.style.border = 'none';
    minimizeBtn.style.background = 'transparent';
    minimizeBtn.style.fontSize = '16px';
    minimizeBtn.style.cursor = 'pointer';
    minimizeBtn.style.lineHeight = '1';
    minimizeBtn.style.padding = '0';
    minimizeBtn.style.color = '#555';

    // Body – holds messages
    const body = document.createElement('div');
    body.id = 'floating-chat-body';
    body.style.flex = '1';
    body.style.padding = '8px 12px';
    body.style.overflowY = 'auto';
    body.style.display = 'flex';
    body.style.flexDirection = 'column';
    body.style.gap = '6px';
    body.style.background = 'transparent';

    // Input container
    const inputContainer = document.createElement('div');
    inputContainer.id = 'floating-chat-input-container';
    inputContainer.style.display = 'flex';
    inputContainer.style.padding = '8px 12px';
    inputContainer.style.borderTop = '1px solid rgba(0,0,0,0.1)';

    const inputField = document.createElement('input');
    inputField.id = 'floating-chat-input';
    inputField.type = 'text';
    inputField.placeholder = 'Type a message…';
    inputField.style.flex = '1';
    inputField.style.border = '1px solid #ccc';
    inputField.style.borderRadius = '4px';
    inputField.style.padding = '6px 8px';
    inputField.style.fontSize = '13px';
    inputField.style.outline = 'none';

    const sendBtn = document.createElement('button');
    sendBtn.id = 'floating-chat-send';
    sendBtn.textContent = 'Send';
    sendBtn.style.marginLeft = '6px';
    sendBtn.style.padding = '6px 12px';
    sendBtn.style.border = 'none';
    sendBtn.style.borderRadius = '4px';
    sendBtn.style.background = '#0069d9';
    sendBtn.style.color = '#fff';
    sendBtn.style.cursor = 'pointer';
    sendBtn.style.fontSize = '13px';

    // Assemble input container
    inputContainer.appendChild(inputField);
    inputContainer.appendChild(sendBtn);

    // Assemble header
    header.appendChild(title);
    header.appendChild(minimizeBtn);

    // Assemble root
    chatRoot.appendChild(header);
    chatRoot.appendChild(body);
    chatRoot.appendChild(inputContainer);

    // Append to DOM
    document.body.appendChild(chatRoot);

    // Minimize / expand logic
    let isMinimized = false;
    const toggleMinimize = () => {
        isMinimized = !isMinimized;
        if (isMinimized) {
            body.style.display = 'none';
            inputContainer.style.display = 'none';
            minimizeBtn.textContent = '+';
            minimizeBtn.title = 'Expand';
        } else {
            body.style.display = 'flex';
            inputContainer.style.display = 'flex';
            minimizeBtn.textContent = '–';
            minimizeBtn.title = 'Minimize';
        }
    };
    minimizeBtn.addEventListener('click', toggleMinimize);

    // Simple send handler (placeholder – can be replaced by real messaging logic)
    sendBtn.addEventListener('click', () => {
        const msg = inputField.value.trim();
        if (!msg) return;
        const msgEl = document.createElement('div');
        msgEl.textContent = msg;
        msgEl.style.alignSelf = 'flex-end';
        msgEl.style.background = '#e1f5fe';
        msgEl.style.padding = '6px 10px';
        msgEl.style.borderRadius = '12px';
        msgEl.style.maxWidth = '80%';
        body.appendChild(msgEl);
        body.scrollTop = body.scrollHeight;
        inputField.value = '';
    });

    // Allow pressing Enter to send
    inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendBtn.click();
        }
    });

    // Return the root element for further manipulation (e.g., dragging)
    return chatRoot;
}

/**
 * Enables drag‑and‑drop repositioning of the floating chat panel.
 *
 * The header element acts as the drag handle. The function attaches the
 * necessary mouse listeners, updates the element's `left` and `top` CSS
 * properties while preserving the panel within the viewport, and cleans up
 * listeners on mouse release.
 *
 * @param {HTMLElement} chatRoot - The root element returned by
 *                                 `createFloatingChat()`.
 */
function setupChatDrag(chatRoot) {
    const header = chatRoot.querySelector('#floating-chat-header');
    if (!header) return;

    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let startLeft = 0;
    let startTop = 0;

    const onMouseDown = (e) => {
        // Only react to primary (left) button
        if (e.button !== 0) return;
        e.preventDefault();

        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;

        // Compute current offsets (fallback to 0)
        const rect = chatRoot.getBoundingClientRect();
        startLeft = rect.left;
        startTop = rect.top;

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    };

    const onMouseMove = (e) => {
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;

        let newLeft = startLeft + dx;
        let newTop = startTop + dy;

        // Constrain within viewport bounds
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const chatRect = chatRoot.getBoundingClientRect();

        // Left / right boundaries
        if (newLeft < 0) newLeft = 0;
        if (newLeft + chatRect.width > vw) newLeft = vw - chatRect.width;

        // Top / bottom boundaries
        if (newTop < 0) newTop = 0;
        if (newTop + chatRect.height > vh) newTop = vh - chatRect.height;

        chatRoot.style.left = `${newLeft}px`;
        chatRoot.style.top = `${newTop}px`;
        chatRoot.style.right = 'auto';
        chatRoot.style.bottom = 'auto';
    };

    const onMouseUp = () => {
        if (!isDragging) return;
        isDragging = false;
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    };

    // Ensure the element is positioned with left/top for dragging
    const initPosition = () => {
        const rect = chatRoot.getBoundingClientRect();
        chatRoot.style.left = `${rect.left}px`;
        chatRoot.style.top = `${rect.top}px`;
        chatRoot.style.right = 'auto';
        chatRoot.style.bottom = 'auto';
    };
    initPosition();

    header.addEventListener('mousedown', onMouseDown);
}

// ---------------------------------------------------------------------------
// Export / initialization (if using module system)
// ---------------------------------------------------------------------------
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createFloatingChat,
        setupChatDrag
    };
} else {
    // Auto‑initialize when script is loaded directly in the browser
    const chatEl = createFloatingChat();
    setupChatDrag(chatEl);
}