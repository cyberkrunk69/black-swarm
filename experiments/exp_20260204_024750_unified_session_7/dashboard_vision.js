/**
 * Dashboard Vision – Floating Chat Implementation
 *
 * This file provides two core functions:
 *   1. createFloatingChat() – builds a draggable, minimizable chat widget.
 *   2. setupChatDrag(chatContainer, dragHandle) – wires mouse/touch events to enable dragging.
 *
 * The UI follows the specification in UIUX_INTERACTION_SPEC.md §3:
 *   - A semi‑transparent backdrop with a blur effect separates the chat from the page.
 *   - Header contains a title and a minimize/restore button.
 *   - The entire header acts as a drag handle.
 *   - Input field + send button at the bottom.
 *
 * The implementation is vanilla JavaScript, no external dependencies.
 */

(() => {
  /**
   * Creates and injects a floating chat widget into the DOM.
   *
   * @returns {HTMLElement} The root container of the chat widget.
   */
  function createFloatingChat() {
    // Root container – fixed positioned, with backdrop blur.
    const chatRoot = document.createElement('div');
    chatRoot.id = 'floating-chat-root';
    Object.assign(chatRoot.style, {
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      width: '320px',
      maxHeight: '480px',
      display: 'flex',
      flexDirection: 'column',
      background: 'rgba(255,255,255,0.85)',
      borderRadius: '12px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      backdropFilter: 'blur(8px)', // visual separation
      fontFamily: `'Helvetica Neue', Helvetica, Arial, sans-serif`,
      zIndex: 9999,
      overflow: 'hidden',
    });

    // Header – contains title and minimize button, also acts as drag handle.
    const header = document.createElement('div');
    header.id = 'floating-chat-header';
    Object.assign(header.style, {
      flex: '0 0 40px',
      background: 'rgba(0, 123, 255, 0.9)',
      color: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 12px',
      cursor: 'move',
      userSelect: 'none',
    });

    const title = document.createElement('span');
    title.textContent = 'Assistant';
    title.style.fontWeight = '600';
    header.appendChild(title);

    const minimizeBtn = document.createElement('button');
    minimizeBtn.id = 'floating-chat-minimize';
    minimizeBtn.innerHTML = '&#x2212;'; // minus sign
    Object.assign(minimizeBtn.style, {
      background: 'transparent',
      border: 'none',
      color: '#fff',
      fontSize: '18px',
      cursor: 'pointer',
      lineHeight: '1',
    });
    header.appendChild(minimizeBtn);

    // Content area – placeholder for future messages.
    const content = document.createElement('div');
    content.id = 'floating-chat-content';
    Object.assign(content.style, {
      flex: '1 1 auto',
      padding: '8px',
      overflowY: 'auto',
    });
    content.textContent = ''; // start empty

    // Footer – input field + send button.
    const footer = document.createElement('div');
    footer.id = 'floating-chat-footer';
    Object.assign(footer.style, {
      flex: '0 0 48px',
      display: 'flex',
      borderTop: '1px solid rgba(0,0,0,0.1)',
      background: 'rgba(250,250,250,0.9)',
    });

    const input = document.createElement('input');
    input.type = 'text';
    input.id = 'floating-chat-input';
    input.placeholder = 'Type a message…';
    Object.assign(input.style, {
      flex: '1',
      border: 'none',
      padding: '0 12px',
      fontSize: '14px',
      outline: 'none',
      background: 'transparent',
    });

    const sendBtn = document.createElement('button');
    sendBtn.id = 'floating-chat-send';
    sendBtn.textContent = 'Send';
    Object.assign(sendBtn.style, {
      flex: '0 0 60px',
      border: 'none',
      background: '#007bff',
      color: '#fff',
      cursor: 'pointer',
      fontWeight: '600',
    });

    footer.appendChild(input);
    footer.appendChild(sendBtn);

    // Assemble the widget.
    chatRoot.appendChild(header);
    chatRoot.appendChild(content);
    chatRoot.appendChild(footer);
    document.body.appendChild(chatRoot);

    // Minimize/restore logic.
    let isMinimized = false;
    const restoreHeight = chatRoot.style.maxHeight;
    minimizeBtn.addEventListener('click', () => {
      if (isMinimized) {
        // Restore
        content.style.display = 'block';
        footer.style.display = 'flex';
        chatRoot.style.maxHeight = restoreHeight;
        minimizeBtn.innerHTML = '&#x2212;'; // minus
      } else {
        // Minimize – hide content/footer, shrink height.
        content.style.display = 'none';
        footer.style.display = 'none';
        chatRoot.style.maxHeight = '40px';
        minimizeBtn.innerHTML = '&#x25A1;'; // square (restore)
      }
      isMinimized = !isMinimized;
    });

    // Simple send handler – echoes the message into the content area.
    sendBtn.addEventListener('click', () => {
      const msg = input.value.trim();
      if (!msg) return;
      const msgEl = document.createElement('div');
      msgEl.textContent = msg;
      msgEl.style.padding = '4px 0';
      content.appendChild(msgEl);
      input.value = '';
      content.scrollTop = content.scrollHeight;
    });

    // Enable dragging via the header.
    setupChatDrag(chatRoot, header);

    return chatRoot;
  }

  /**
   * Attaches mouse/touch listeners to enable dragging of the chat widget.
   *
   * @param {HTMLElement} chatContainer – The root element that will be moved.
   * @param {HTMLElement} dragHandle – The element that initiates the drag (header).
   */
  function setupChatDrag(chatContainer, dragHandle) {
    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let startLeft = 0;
    let startTop = 0;

    const onMouseDown = (e) => {
      e.preventDefault();
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      const rect = chatContainer.getBoundingClientRect();
      startLeft = rect.left;
      startTop = rect.top;
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    };

    const onTouchStart = (e) => {
      if (e.touches.length !== 1) return;
      const touch = e.touches[0];
      isDragging = true;
      startX = touch.clientX;
      startY = touch.clientY;
      const rect = chatContainer.getBoundingClientRect();
      startLeft = rect.left;
      startTop = rect.top;
      document.addEventListener('touchmove', onTouchMove, { passive: false });
      document.addEventListener('touchend', onTouchEnd);
    };

    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      chatContainer.style.left = `${startLeft + dx}px`;
      chatContainer.style.top = `${startTop + dy}px`;
      chatContainer.style.right = 'auto';
      chatContainer.style.bottom = 'auto';
    };

    const onTouchMove = (e) => {
      if (!isDragging) return;
      e.preventDefault(); // prevent scrolling while dragging
      const touch = e.touches[0];
      const dx = touch.clientX - startX;
      const dy = touch.clientY - startY;
      chatContainer.style.left = `${startLeft + dx}px`;
      chatContainer.style.top = `${startTop + dy}px`;
      chatContainer.style.right = 'auto';
      chatContainer.style.bottom = 'auto';
    };

    const endDrag = () => {
      isDragging = false;
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('touchmove', onTouchMove);
      document.removeEventListener('touchend', onTouchEnd);
    };

    const onMouseUp = () => endDrag();
    const onTouchEnd = () => endDrag();

    dragHandle.addEventListener('mousedown', onMouseDown);
    dragHandle.addEventListener('touchstart', onTouchStart, { passive: false });
  }

  // Export to global scope for other modules / debugging.
  window.createFloatingChat = createFloatingChat;
  window.setupChatDrag = setupChatDrag;

  // Auto‑initialize if the page loads and the function is available.
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    createFloatingChat();
  } else {
    window.addEventListener('DOMContentLoaded', createFloatingChat);
  }
})();