/* --------------------------------------------------------------
   Dashboard orchestration – living, breathing UI
   -------------------------------------------------------------- */
class Node {
    constructor({x, y, type, parent = null, label = ''}) {
        this.x = x;
        this.y = y;
        this.type = type;          // 'indigo' | 'purple' | 'cyan' | 'amber'
        this.parent = parent;      // reference to parent Node (if any)
        this.label = label;
        this.el = document.createElement('div');
        this.el.classList.add('node', this.type);
        this.el.style.left = `${x}px`;
        this.el.style.top  = `${y}px`;
        this.el.textContent = label;
        document.getElementById('canvas').appendChild(this.el);
    }

    activate() {
        this.el.classList.add('rainbow');
    }

    deactivate() {
        this.el.classList.remove('rainbow');
    }

    collapse(delay = 0) {
        const parentPos = this.parent
            ? {x: this.parent.x + 24, y: this.parent.y + 24}
            : {x: this.x, y: this.y};

        const dx = parentPos.x - this.x;
        const dy = parentPos.y - this.y;

        this.el.style.setProperty('--collapse-x', `${dx}px`);
        this.el.style.setProperty('--collapse-y', `${dy}px`);
        this.el.style.transitionDelay = `${delay}ms`;
        this.el.classList.add('collapse');

        // Remove from DOM after transition
        setTimeout(() => this.el.remove(), parseInt(getComputedStyle(this.el).transitionDuration) + delay);
    }
}

/* --------------------------------------------------------------
   Dashboard manager
   -------------------------------------------------------------- */
class Dashboard {
    constructor() {
        this.nodes = [];
        this.svg = document.querySelector('.connections');
        this.historyList = document.getElementById('historyList');
        this.statusEl = document.getElementById('status-indicator');
        this.statsEl = document.querySelector('.stats');
        this.autonomy = false;
        this._setupListeners();
    }

    _setupListeners() {
        document.getElementById('autonomyBtn').addEventListener('click', () => {
            this.autonomy = !this.autonomy;
            document.getElementById('autonomyBtn').textContent = `Autonomy: ${this.autonomy ? 'ON' : 'OFF'}`;
        });

        document.getElementById('historyToggle').addEventListener('click', () => {
            document.getElementById('history').classList.toggle('collapsed');
        });

        document.getElementById('sendBtn').addEventListener('click', () => this._handleChat());
        document.getElementById('chatInput').addEventListener('keypress', e => {
            if (e.key === 'Enter') this._handleChat();
        });
    }

    _handleChat() {
        const input = document.getElementById('chatInput');
        if (!input.value.trim()) return;
        this.spawnTaskFlow();
        input.value = '';
    }

    /* ----------------------------------------------------------
       PUBLIC API – spawn a demo task flow
       ---------------------------------------------------------- */
    spawnTaskFlow() {
        const startX = 40;
        const startY = 80;
        const gapX = 120;
        const gapY = 80;

        // 1. Understanding node (primary)
        const uNode = this._createNode({
            x: startX,
            y: startY,
            type: 'indigo',
            label: 'U'
        });
        uNode.activate();

        // 2. Worker node
        const wNode = this._createNode({
            x: startX + gapX,
            y: startY,
            type: 'purple',
            parent: uNode,
            label: 'W'
        });
        this._drawLine(uNode, wNode);

        // 3. Helper node
        const hNode = this._createNode({
            x: startX + gapX * 2,
            y: startY + gapY,
            type: 'cyan',
            parent: wNode,
            label: 'H'
        });
        this._drawLine(wNode, hNode);

        // 4. Expert node
        const eNode = this._createNode({
            x: startX + gapX * 3,
            y: startY,
            type: 'amber',
            parent: hNode,
            label: 'E'
        });
        this._drawLine(hNode, eNode);

        // Simulate work completion after a short delay
        setTimeout(() => this._completeFlow([eNode, hNode, wNode, uNode]), 2000);
    }

    _createNode({x, y, type, parent = null, label = ''}) {
        const node = new Node({x, y, type, parent, label});
        this.nodes.push(node);
        this._updateStats();
        return node;
    }

    _drawLine(fromNode, toNode) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', fromNode.x + 24);
        line.setAttribute('y1', fromNode.y + 24);
        line.setAttribute('x2', toNode.x + 24);
        line.setAttribute('y2', toNode.y + 24);
        line.setAttribute('stroke', '#777');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('stroke-dasharray', '4 2');
        line.style.transition = 'stroke-dashoffset 0.5s ease';
        this.svg.appendChild(line);
        // animate dash offset to give a “drawing” feel
        setTimeout(() => line.style.strokeDashoffset = '0', 50);
    }

    _completeFlow(nodeStack) {
        const quips = ['got er done', 'finally', 'done & dusted', 'mission complete'];
        const quip = quips[Math.floor(Math.random()*quips.length)];
        this.statusEl.textContent = quip;

        nodeStack.forEach((node, idx) => {
            const delay = idx * 120; // 120ms between each thunk
            setTimeout(() => {
                node.collapse(delay);
                // after collapse, push entry to history
                if (idx === nodeStack.length - 1) {
                    this._addToHistory(`Task ${quip}`);
                }
            }, delay);
        });
    }

    _addToHistory(text) {
        const li = document.createElement('li');
        li.textContent = text;
        this.historyList.appendChild(li);
    }

    _updateStats() {
        const active = this.nodes.filter(n => !n.el.classList.contains('collapse')).length;
        this.statsEl.textContent = `🗂️ ${active} tasks`;
    }
}

/* --------------------------------------------------------------
   Initialise dashboard
   -------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});