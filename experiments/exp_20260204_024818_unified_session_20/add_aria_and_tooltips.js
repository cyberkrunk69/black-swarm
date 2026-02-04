/**
 * add_aria_and_tooltips.js
 *
 * This script enhances UI control buttons (collapse, expand, drag, minimize) with:
 *   - `title` attributes (native tooltip support)
 *   - `aria-label` attributes (screen‑reader accessibility)
 *
 * It is intended to be loaded after the UI components are rendered.
 * The script is deliberately lightweight and does not modify any core files.
 */

(() => {
  // Mapping of button selector → { title, ariaLabel }
  const BUTTON_CONFIG = [
    {
      // Collapse button – typically a chevron or minus icon
      selector: '.btn-collapse',
      title: 'Collapse panel',
      ariaLabel: 'Collapse panel'
    },
    {
      // Expand button – typically a plus or expand icon
      selector: '.btn-expand',
      title: 'Expand panel',
      ariaLabel: 'Expand panel'
    },
    {
      // Drag handle – often an icon used to move a window/panel
      selector: '.btn-drag',
      title: 'Drag to reposition',
      ariaLabel: 'Drag to reposition'
    },
    {
      // Minimize button – usually a dash or minimize icon
      selector: '.btn-minimize',
      title: 'Minimize panel',
      ariaLabel: 'Minimize panel'
    }
  ];

  /**
   * Apply the configured attributes to each matching element.
   */
  const applyAttributes = () => {
    BUTTON_CONFIG.forEach(({ selector, title, ariaLabel }) => {
      const elements = document.querySelectorAll(selector);
      elements.forEach(el => {
        // Only set if not already present to avoid overwriting custom values
        if (!el.hasAttribute('title')) {
          el.setAttribute('title', title);
        }
        if (!el.hasAttribute('aria-label')) {
          el.setAttribute('aria-label', ariaLabel);
        }
        // Ensure the element is focusable for keyboard users
        if (!el.hasAttribute('tabindex')) {
          el.setAttribute('tabindex', '0');
        }
      });
    });
  };

  // Run once the DOM is fully loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyAttributes);
  } else {
    applyAttributes();
  }

  // Observe future additions (e.g., dynamic panels) and apply attributes automatically
  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.addedNodes.length) {
        applyAttributes();
      }
    });
  });

  observer.observe(document.body, { childList: true, subtree: true });
})();