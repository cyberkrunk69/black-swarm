/* -------------------------------------------------------------
   Dashboard orchestration – creates nodes, animates them,
   draws connections, and handles the “thunk‑thunk‑thunk” collapse.
   ------------------------------------------------------------- */

const svg = document.getElementById('task-canvas');
const statusEl = document.getElementById('status-indicator');
const taskCountEl = document.getElementById('task-count');
const historyList = document.getElementById('history-list');
const historyToggle = document.getElementById('history-toggle');
const historyPanel = document.getElementById('history-dashboard');

let nodeId = 0;
const nodes = [];          // flat list of all nodes
const activeNodes = [];    // nodes currently “running”

/* ---------- Helper utilities ---------- */
function createSVGElement(tag, attrs = {}) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    return el;
}

/* ---------- Node definition ---------- */
class Node {
    constructor(type, parent = null) {
        this.id = ++nodeId;
        this.type = type;               // understanding | worker | helper | expert
        this.parent = parent;           // null for root
        this.children = [];
        this.x = 0;
        this.y = 0;
        this.radius = 24;
        this.svgGroup = null;           // <g> containing circle & label
        this.active = false;
    }

    /* Position node based on parent + gap */
    computePosition(index) {
        const baseX = 80;
        const baseY = 80;
        const gapX = 120;
        const gapY = 80;

        if (!this.parent) {
            this.x = baseX;
            this.y = baseY + index * (this.radius * 2 + parseInt(getComputedStyle(document.documentElement).getPropertyValue('--node-gap')));
        } else {
            this.x = this.parent.x + gapX;
            this.y = this.parent.y + (index - Math.floor(this.parent.children.length / 2)) * (this.radius * 2 + parseInt(getComputedStyle(document.documentElement).getPropertyValue('--node-gap')));
        }
    }

    render() {
        const g = createSVGElement('g', { class: `node ${this.type}`, 'data-id': this.id });
        const circle = createSVGElement('circle', {
            cx: this.x,
            cy: this.y,
            r: this.radius,
            class: this.active ? 'active-rainbow' : ''
        });
        const label = createSVGElement('text', {
            x: this.x,
            y: this.y + 4,
            'text-anchor': 'middle',
            'font-size': '10px',
            fill: '#fff',
            'pointer-events': 'none'
        });
        label.textContent = this.type[0].toUpperCase();

        g.appendChild(circle);
        g.appendChild(label);
        svg.appendChild(g);
        this.svgGroup = g;
    }

    activate() {
        this.active = true;
        this.svgGroup.querySelector('circle').classList.add('active-rainbow');
        statusEl.textContent = `Running node ${this.id}`;
    }

    deactivate() {
        this.active = false;
        const circle = this.svgGroup.querySelector('circle');
        circle.classList.remove('active-rainbow');
        statusEl.textContent = `Idle`;
    }

    /* Animate collapse (thunk) */
    collapse(callback) {
        this.svgGroup.classList.add('collapse-anim');
        setTimeout(() => {
            this.svgGroup.remove();
            if (callback) callback();
        }, parseInt(getComputedStyle(document.documentElement).getPropertyValue('--anim-normal')));
    }
}

/* ---------- Connection line ---------- */
function drawLink(parentNode, childNode) {
    const line = createSVGElement('path', {
        class: 'link',
        d: `M${parentNode.x},${parentNode.y} C${parentNode.x + 40},${parentNode.y} ${childNode.x - 40},${childNode.y} ${childNode.x},${childNode.y}`
    });
    svg.appendChild(line);
}

/* ---------- Simulation of work flow ---------- */
function spawnWorkflow() {
    // Root understanding node
    const root = new Node('understanding');
    root.computePosition(0);
    root.render();
    nodes.push(root);
    activeNodes.push(root);
    root.activate();
    taskCountEl.textContent = nodes.length;

    // Simulate spawning of child nodes over time
    const types = ['worker', 'helper', 'expert'];
    let spawnIndex = 0;

    const spawnInterval = setInterval(() => {
        if (spawnIndex >= 6) {
            clearInterval(spawnInterval);
            // After spawning, start collapse sequence
            setTimeout(() => startCollapseSequence(root), 2000);
            return;
        }

        const type = types[spawnIndex % types.length];
        const parent = nodes[Math.floor(Math.random() * nodes.length)];
        const child = new Node(type, parent);
        parent.children.push(child);
        child.computePosition(parent.children.length - 1);
        child.render();
        drawLink(parent, child);
        nodes.push(child);
        activeNodes.push(child);
        child.activate();

        taskCountEl.textContent = nodes.length;
        spawnIndex++;
    }, 800);
}

/* ---------- Collapse (thunk‑thunk‑thunk) ---------- */
function startCollapseSequence(rootNode) {
    // Gather nodes in reverse spawn order (LIFO)
    const collapseOrder = [...activeNodes].reverse();

    collapseOrder.forEach((node, idx) => {
        setTimeout(() => {
            node.deactivate();
            node.collapse(() => {
                // Add entry to history
                const li = document.createElement('li');
                li.textContent = `Node ${node.id} (${node.type}) – ${['got er done','finally','done!'][idx % 3]}`;
                historyList.prepend(li);
            });
        }, idx * (parseInt(getComputedStyle(document.documentElement).getPropertyValue('--anim-normal')) + 120));
    });

    // Finally collapse root into history panel
    setTimeout(() => {
        rootNode.deactivate();
        rootNode.collapse(() => {
            const li = document.createElement('li');
            li.textContent = `Root node ${rootNode.id} (understanding) – finally`;
            historyList.prepend(li);
        });
    }, collapseOrder.length * (parseInt(getComputedStyle(document.documentElement).getPropertyValue('--anim-normal')) + 120));
}

/* ---------- UI interactions ---------- */
historyToggle.addEventListener('click', () => {
    historyPanel.classList.toggle('collapsed');
});

/* Kick‑off demo */
spawnWorkflow();