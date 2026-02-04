/**
 * Accessibility Enhancements
 *
 * - Press Enter while focus is on the chat input to send the message.
 * - Use Tab / Shift+Tab to navigate between interactive "node" elements.
 * - Press Escape to close any expanded details panel.
 * - Adds focus-visible styling to interactive elements.
 *
 * This script should be imported once (e.g., in the main entry point) after the DOM is ready.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Helper: find the currently focused element
  const getFocused = () => document.activeElement;

  // 1. Enter to send chat
  const chatInput = document.getElementById('chat-input');
  const chatSendButton = document.getElementById('chat-send');

  if (chatInput && chatSendButton) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatSendButton.click();
      }
    });
  }

  // 2. Tab navigation between nodes
  const focusableNodeSelector = '.node[tabindex="-1"], .node[tabindex="0"]';
  const getAllNodes = () => Array.from(document.querySelectorAll(focusableNodeSelector));

  // Ensure each node is focusable
  const initNodeFocus = () => {
    const nodes = getAllNodes();
    nodes.forEach((node) => {
      if (!node.hasAttribute('tabindex')) {
        node.setAttribute('tabindex', '0');
      }
    });
  };
  initNodeFocus();

  // Optional: Re‑run when the DOM changes (e.g., new nodes added)
  const observer = new MutationObserver(() => initNodeFocus());
  observer.observe(document.body, { childList: true, subtree: true });

  // 3. Escape to close expanded details
  const closeExpandedDetails = () => {
    const expanded = document.querySelector('.details-panel.expanded');
    if (expanded) {
      // Assuming the panel can be closed by removing the 'expanded' class
      expanded.classList.remove('expanded');
      // Return focus to a sensible element (e.g., the previously focused node)
      const previouslyFocused = getFocused();
      if (previouslyFocused && previouslyFocused.classList.contains('node')) {
        previouslyFocused.focus();
      }
    }
  };

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeExpandedDetails();
    }
  });

  // 4. Focus indicator styling (adds a class for :focus-visible fallback)
  const styleFocus = () => {
    const style = document.createElement('style');
    style.textContent = `
      .focus-visible {
        outline: 2px solid #0066ff;
        outline-offset: 2px;
      }
    `;
    document.head.appendChild(style);
  };
  styleFocus();

  // Apply .focus-visible class on focus if the browser doesn't support :focus-visible
  const applyFocusVisible = (e) => {
    if (e.type === 'focus') {
      e.target.classList.add('focus-visible');
    } else if (e.type === 'blur') {
      e.target.classList.remove('focus-visible');
    }
  };

  // Attach to all interactive elements (buttons, inputs, links, nodes)
  const interactiveSelector = 'button, [role="button"], a, input, textarea, select, .node';
  const interactiveElements = Array.from(document.querySelectorAll(interactiveSelector));
  interactiveElements.forEach((el) => {
    el.addEventListener('focus', applyFocusVisible);
    el.addEventListener('blur', applyFocusVisible);
  });

  // Observe future additions of interactive elements
  const interactiveObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        if (node.matches && node.matches(interactiveSelector)) {
          node.addEventListener('focus', applyFocusVisible);
          node.addEventListener('blur', applyFocusVisible);
        }
        // Also check descendants
        const descendants = node.querySelectorAll?.(interactiveSelector);
        if (descendants?.length) {
          descendants.forEach((desc) => {
            desc.addEventListener('focus', applyFocusVisible);
            desc.addEventListener('blur', applyFocusVisible);
          });
        }
      });
    });
  });
  interactiveObserver.observe(document.body, { childList: true, subtree: true });
});