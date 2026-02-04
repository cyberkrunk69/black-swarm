/**
 * Admin Command Palette
 * - Press Ctrl+K to open
 * - Fuzzy search through admin commands
 * - Executes commands via backend API
 *
 * Dependencies: Assumes the main app includes this script and has a global `fetch` API.
 */

(() => {
    const COMMANDS = [
        { name: "Restart Swarm", action: "restart_swarm" },
        { name: "Clear Logs", action: "clear_logs" },
        { name: "Export Stats", action: "export_stats" },
        { name: "Pause Workers", action: "pause_workers" },
        { name: "Resume Workers", action: "resume_workers" },
        { name: "Shutdown System", action: "shutdown_system" },
    ];

    // Simple fuzzy match (case‑insensitive, contains)
    function fuzzyMatch(query, str) {
        query = query.toLowerCase();
        str = str.toLowerCase();
        let qIdx = 0;
        for (let i = 0; i < str.length && qIdx < query.length; i++) {
            if (str[i] === query[qIdx]) qIdx++;
        }
        return qIdx === query.length;
    }

    // Create palette DOM
    const palette = document.createElement('div');
    palette.id = 'admin-command-palette';
    palette.style.cssText = `
        position: fixed; top: 20%; left: 50%; transform: translateX(-50%);
        width: 400px; max-height: 50vh; overflow-y: auto;
        background: #1e1e1e; color: #fff; border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        font-family: sans-serif; z-index: 10000; display:none;
    `;

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Admin command...';
    input.style.cssText = `
        width: 100%; padding: 12px; box-sizing: border-box;
        border:none; outline:none; background:#2e2e2e; color:#fff;
        font-size:16px; border-top-left-radius:8px; border-top-right-radius:8px;
    `;

    const list = document.createElement('ul');
    list.style.cssText = `
        list-style:none; margin:0; padding:0; max-height:300px; overflow:auto;
    `;

    palette.appendChild(input);
    palette.appendChild(list);
    document.body.appendChild(palette);

    function renderList(filter = '') {
        list.innerHTML = '';
        const filtered = COMMANDS.filter(c => fuzzyMatch(filter, c.name));
        filtered.forEach(c => {
            const li = document.createElement('li');
            li.textContent = c.name;
            li.style.cssText = `
                padding: 8px 12px; cursor:pointer;
            `;
            li.addEventListener('click', () => executeCommand(c));
            li.addEventListener('mouseenter', () => li.style.background = '#3e3e3e');
            li.addEventListener('mouseleave', () => li.style.background = 'transparent');
            list.appendChild(li);
        });
    }

    function executeCommand(command) {
        fetch('/api/admin/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: command.action })
        })
        .then(res => res.json())
        .then(data => {
            alert(`Command "${command.name}" executed: ${data.status}`);
            hidePalette();
        })
        .catch(err => {
            alert(`Error executing command: ${err}`);
            hidePalette();
        });
    }

    function showPalette() {
        palette.style.display = 'block';
        input.value = '';
        renderList();
        input.focus();
    }

    function hidePalette() {
        palette.style.display = 'none';
    }

    // Global shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+K opens palette (ignore if already typing in an input/textarea)
        if (e.ctrlKey && e.key.toLowerCase() === 'k' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            showPalette();
        }
        // Escape closes
        if (e.key === 'Escape' && palette.style.display === 'block') {
            hidePalette();
        }
    });

    // Input handling
    input.addEventListener('input', (e) => {
        renderList(e.target.value);
    });

    // Enter key executes first filtered command
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const first = list.querySelector('li');
            if (first) {
                const cmdName = first.textContent;
                const cmd = COMMANDS.find(c => c.name === cmdName);
                if (cmd) executeCommand(cmd);
            }
        }
    });
})();