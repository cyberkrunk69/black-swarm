/**
 * Accessibility Enhancements
 *
 * - Press Enter while the chat input is focused to trigger the send action.
 * - Use Tab / Shift+Tab to navigate between interactive nodes.
 * - Press Escape to close any expanded detail panels.
 * - Apply visual focus indicators to interactive elements.
 *
 * This script is loaded after the main application bundle.
 */

(function () {
    // Utility to check if an element is visible
    function isVisible(el) {
        return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    }

    // 1️⃣ ENTER to send chat message
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-btn');

    if (chatInput && sendButton) {
        chatInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); // Prevent newline in textarea/input
                sendButton.click();
            }
        });
    }

    // 2️⃣ TAB navigation between nodes
    // Nodes are any element with the class "node" that is interactive (e.g., clickable)
    const nodeSelector = '.node';
    const focusableSelector = `${nodeSelector}:not([disabled]):not([aria-hidden="true"])`;

    // Ensure nodes are part of the tab order
    function setTabIndexOnNodes() {
        const nodes = document.querySelectorAll(nodeSelector);
        nodes.forEach(node => {
            if (!node.hasAttribute('tabindex')) {
                node.setAttribute('tabindex', '0');
            }
        });
    }

    // Run once at startup
    setTabIndexOnNodes();

    // Re-apply when DOM changes (e.g., dynamic node addition)
    const observer = new MutationObserver(setTabIndexOnNodes);
    observer.observe(document.body, { childList: true, subtree: true });

    // Optional: Visual cue for the currently focused node (handled by CSS)

    // 3️⃣ ESCAPE to close expanded details
    // Expanded panels have class "expanded-detail" and contain a button with class "detail-close"
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            const openDetails = document.querySelectorAll('.expanded-detail');
            openDetails.forEach(panel => {
                if (isVisible(panel)) {
                    const closeBtn = panel.querySelector('.detail-close');
                    if (closeBtn) {
                        closeBtn.click();
                    } else {
                        // Fallback: hide panel directly
                        panel.style.display = 'none';
                    }
                }
            });
        }
    });

    // 4️⃣ Focus indicators (adds a CSS class on focus)
    document.addEventListener('focusin', function (e) {
        const target = e.target;
        if (target.matches('button, a, input, textarea, select, .node')) {
            target.classList.add('focus-visible');
        }
    });

    document.addEventListener('focusout', function (e) {
        const target = e.target;
        if (target.matches('button, a, input, textarea, select, .node')) {
            target.classList.remove('focus-visible');
        }
    });
})();