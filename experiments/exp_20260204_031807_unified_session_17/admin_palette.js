/**
 * Admin Command Palette
 *
 * This module adds a global command palette that can be opened with Ctrl+K.
 * Users can type commands such as:
 *   - restart swarm
 *   - clear logs
 *   - export stats
 *   - pause workers
 *
 * The palette uses a simple fuzzy search over a static command list and
 * triggers the appropriate backend API via `fetch`.
 *
 * Integration:
 *   - Include this script in your main HTML (e.g., <script src="admin_palette.js"></script>)
 *   - Ensure the backend routes exist:
 *       POST /api/admin/restart-swarm
 *       POST /api/admin/clear-logs
 *       POST /api/admin/export-stats
 *       POST /api/admin/pause-workers
 *
 * No external dependencies are required.
 */

(() => {
  // ----- Command Definitions -----
  const COMMANDS = [
    {
      name: 'restart swarm',
      description: 'Restarts the swarm of workers',
      endpoint: '/api/admin/restart-swarm',
    },
    {
      name: 'clear logs',
      description: 'Clears all application logs',
      endpoint: '/api/admin/clear-logs',
    },
    {
      name: 'export stats',
      description: 'Exports current statistics as JSON',
      endpoint: '/api/admin/export-stats',
    },
    {
      name: 'pause workers',
      description: 'Pauses all background workers',
      endpoint: '/api/admin/pause-workers',
    },
  ];

  // ----- Utility: Simple Fuzzy Match -----
  function fuzzyMatch(query, str) {
    query = query.toLowerCase();
    str = str.toLowerCase();
    let qi = 0;
    for (let si = 0; si < str.length && qi < query.length; si++) {
      if (str[si] === query[qi]) qi++;
    }
    return qi === query.length;
  }

  // ----- UI Creation -----
  const paletteOverlay = document.createElement('div');
  paletteOverlay.style.position = 'fixed';
  paletteOverlay.style.top = '0';
  paletteOverlay.style.left = '0';
  paletteOverlay.style.width = '100vw';
  paletteOverlay.style.height = '100vh';
  paletteOverlay.style.background = 'rgba(0,0,0,0.4)';
  paletteOverlay.style.display = 'none';
  paletteOverlay.style.alignItems = 'center';
  paletteOverlay.style.justifyContent = 'center';
  paletteOverlay.style.zIndex = '9999';
  document.body.appendChild(paletteOverlay);

  const paletteBox = document.createElement('div');
  paletteBox.style.minWidth = '300px';
  paletteBox.style.maxWidth = '600px';
  paletteBox.style.background = '#1e1e1e';
  paletteBox.style.borderRadius = '8px';
  paletteBox.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
  paletteBox.style.padding = '12px';
  paletteBox.style.fontFamily = 'sans-serif';
  paletteOverlay.appendChild(paletteBox);

  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'Type a command...';
  input.style.width = '100%';
  input.style.padding = '8px';
  input.style.border = 'none';
  input.style.outline = 'none';
  input.style.background = '#2d2d2d';
  input.style.color = '#fff';
  input.style.fontSize = '14px';
  paletteBox.appendChild(input);

  const resultsList = document.createElement('ul');
  resultsList.style.listStyle = 'none';
  resultsList.style.margin = '8px 0 0 0';
  resultsList.style.padding = '0';
  resultsList.style.maxHeight = '200px';
  resultsList.style.overflowY = 'auto';
  paletteBox.appendChild(resultsList);

  // ----- Rendering -----
  function renderResults(filter) {
    resultsList.innerHTML = '';
    const filtered = COMMANDS.filter(c => fuzzyMatch(filter, c.name));
    filtered.forEach((cmd, idx) => {
      const li = document.createElement('li');
      li.textContent = cmd.name;
      li.title = cmd.description;
      li.style.padding = '6px 8px';
      li.style.cursor = 'pointer';
      li.style.color = '#ddd';
      li.dataset.index = idx;
      li.addEventListener('mouseenter', () => setActiveIndex(idx));
      li.addEventListener('click', () => executeCommand(cmd));
      resultsList.appendChild(li);
    });
    setActiveIndex(0);
  }

  // ----- Keyboard Navigation -----
  let activeIndex = -1;
  function setActiveIndex(idx) {
    const items = resultsList.querySelectorAll('li');
    if (items.length === 0) return;
    activeIndex = ((idx % items.length) + items.length) % items.length;
    items.forEach((el, i) => {
      el.style.background = i === activeIndex ? '#094771' : '';
    });
  }

  function handleKeyDown(e) {
    if (!paletteOverlay.style.display || paletteOverlay.style.display === 'none') return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(activeIndex + 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(activeIndex - 1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const items = resultsList.querySelectorAll('li');
      if (items[activeIndex]) {
        const cmdName = items[activeIndex].textContent;
        const cmd = COMMANDS.find(c => c.name === cmdName);
        if (cmd) executeCommand(cmd);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      closePalette();
    }
  }

  // ----- Open / Close Palette -----
  function openPalette() {
    paletteOverlay.style.display = 'flex';
    input.value = '';
    renderResults('');
    input.focus();
  }

  function closePalette() {
    paletteOverlay.style.display = 'none';
    input.value = '';
  }

  // ----- Command Execution -----
  async function executeCommand(cmd) {
    closePalette();
    try {
      const response = await fetch(cmd.endpoint, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) throw new Error(`Server responded ${response.status}`);
      const data = await response.json();
      console.log(`Command "${cmd.name}" executed successfully:`, data);
      alert(`✅ ${cmd.name} executed.`);
    } catch (err) {
      console.error(`Error executing ${cmd.name}:`, err);
      alert(`❌ Failed to execute "${cmd.name}". See console for details.`);
    }
  }

  // ----- Global Listeners -----
  document.addEventListener('keydown', (e) => {
    // Ctrl+K opens the palette (ignore when typing in an input/textarea)
    if (e.ctrlKey && e.key.toLowerCase() === 'k' && !e.repeat) {
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable)) {
        // let the element handle the shortcut
        return;
      }
      e.preventDefault();
      openPalette();
    }
  });

  input.addEventListener('input', (e) => renderResults(e.target.value));
  document.addEventListener('keydown', handleKeyDown);
})();