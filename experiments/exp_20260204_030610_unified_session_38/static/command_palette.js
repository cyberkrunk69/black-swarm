/**
 * Admin Command Palette
 * Press Ctrl+K to open a modal that allows fuzzy searching of admin commands.
 * Commands are executed via fetch calls to the backend API.
 */

(() => {
    const COMMANDS = [
        { name: 'restart swarm', endpoint: '/api/admin/restart_swarm' },
        { name: 'clear logs', endpoint: '/api/admin/clear_logs' },
        { name: 'export stats', endpoint: '/api/admin/export_stats' },
        { name: 'pause workers', endpoint: '/api/admin/pause_workers' },
    ];

    // Create modal elements
    const modal = document.createElement('div');
    modal.id = 'admin-command-palette';
    modal.style.cssText = `
        position: fixed; top:0; left:0; width:100%; height:100%;
        background: rgba(0,0,0,0.5); display:none; align-items:center;
        justify-content:center; z-index:10000;
    `;

    const container = document.createElement('div');
    container.style.cssText = `
        background:#fff; padding:20px; border-radius:8px;
        width:400px; max-height:60vh; overflow:auto;
        box-shadow:0 4px 12px rgba(0,0,0,0.15);
    `;

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Type a command...';
    input.style.cssText = `
        width:100%; padding:8px; font-size:16px; margin-bottom:10px;
        box-sizing:border-box;
    `;

    const list = document.createElement('ul');
    list.style.cssText = `
        list-style:none; padding:0; margin:0;
    `;

    container.appendChild(input);
    container.appendChild(list);
    modal.appendChild(container);
    document.body.appendChild(modal);

    // Simple fuzzy search
    function fuzzyMatch(term, str) {
        term = term.toLowerCase();
        str = str.toLowerCase();
        let ti = 0, si = 0;
        while (ti < term.length && si < str.length) {
            if (term[ti] === str[si]) ti++;
            si++;
        }
        return ti === term.length;
    }

    function renderList(filter = '') {
        list.innerHTML = '';
        const filtered = COMMANDS.filter(c => fuzzyMatch(filter, c.name));
        filtered.forEach(c => {
            const li = document.createElement('li');
            li.textContent = c.name;
            li.style.cssText = `
                padding:6px 8px; cursor:pointer;
            `;
            li.addEventListener('mouseenter', () => li.style.background = '#f0f0f0');
            li.addEventListener('mouseleave', () => li.style.background = 'transparent');
            li.addEventListener('click', () => executeCommand(c));
            list.appendChild(li);
        });
    }

    function openPalette() {
        modal.style.display = 'flex';
        input.value = '';
        renderList();
        input.focus();
    }

    function closePalette() {
        modal.style.display = 'none';
    }

    async function executeCommand(command) {
        try {
            const response = await fetch(command.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
            });
            if (!response.ok) throw new Error(`Server responded ${response.status}`);
            const data = await response.json();
            alert(`Command "${command.name}" executed successfully.\n${JSON.stringify(data)}`);
        } catch (e) {
            alert(`Failed to execute "${command.name}": ${e.message}`);
        } finally {
            closePalette();
        }
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            openPalette();
        } else if (e.key === 'Escape' && modal.style.display === 'flex') {
            closePalette();
        }
    });

    // Input handling
    input.addEventListener('input', () => renderList(input.value));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const first = list.firstChild;
            if (first) {
                const cmdName = first.textContent;
                const cmd = COMMANDS.find(c => c.name === cmdName);
                if (cmd) executeCommand(cmd);
            }
        }
    });
})();