/* --------------------------------------------------------------
   UX Motion Vision – Core Animation Engine
   -------------------------------------------------------------- */
const canvas = document.getElementById('canvas');
const historyPanel = document.getElementById('history');
const historyList = document.getElementById('history-list');
const statusIndicator = document.getElementById('status-indicator');
const autonomyBtn = document.getElementById('autonomy-toggle');
const historyToggle = document.getElementById('history-toggle');

let nodeIdCounter = 0;
let activeNodes = [];   // stack for LIFO collapse
let autonomy = false;

/* Utility – create a DOM node */
function createNode(type, label) {
    const el = document.createElement('div');
    el.classList.add('node', type, 'active');
    el.dataset.id = ++nodeIdCounter;
    el.textContent = label;
    canvas.appendChild(el);
    return el;
}

/* Positioning – simple left‑to‑right flow */
function layoutNodes() {
    const gap = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--node-gap'));
    let x = gap;
    const y = canvas.clientHeight / 2 - 30; // vertical centre

    activeNodes.forEach(node => {
        node.style.left = `${x}px`;
        node.style.top  = `${y}px`;
        node.style.opacity = '1';
        node.style.transform = 'scale(1)';
        x += node.offsetWidth + gap;
    });
}

/* Spawn a new node (called by the backend via a simple polling loop) */
function spawnNode(type, label) {
    const node = createNode(type, label);
    activeNodes.push(node);
    layoutNodes();
}

/* Collapse sequence – LIFO */
function collapseAll() {
    if (activeNodes.length === 0) return;

    const quips = ['got er done', 'finally', 'done and dusted', 'mission accomplished'];
    const quip = quips[Math.floor(Math.random()*quips.length)];
    statusIndicator.textContent = quip.toUpperCase();

    // Reverse‑order animation
    const nodesToCollapse = [...activeNodes].reverse();
    nodesToCollapse.forEach((node, idx) => {
        const delay = idx * 120; // 120 ms between thunks
        const parent = node.parentNode; // canvas

        // Compute vector toward the parent (center of canvas)
        const rect = node.getBoundingClientRect();
        const parentRect = canvas.getBoundingClientRect();
        const dx = (parentRect.left + parentRect.width/2) - (rect.left + rect.width/2);
        const dy = (parentRect.top + parentRect.height/2) - (rect.top + rect.height/2);
        node.style.setProperty('--collapse-x', `${dx}px`);
        node.style.setProperty('--collapse-y', `${dy}px`);

        setTimeout(() => {
            node.style.animation = `collapse var(--anim-normal) var(--ease-snap) forwards`;
            // After animation, move node to history
            node.addEventListener('animationend', () => {
                node.classList.remove('active');
                node.style.border = 'none';
                node.style.animation = '';
                // Append a compact entry to history
                const li = document.createElement('li');
                li.textContent = `${node.dataset.id}: ${node.textContent}`;
                historyList.prepend(li);
                // Clean up DOM
                node.remove();
            }, {once: true});
        }, delay);
    });

    // Reset stack after the last node finishes
    const totalDelay = nodesToCollapse.length * 120 + 400;
    setTimeout(() => {
        activeNodes = [];
        statusIndicator.textContent = 'Idle';
    }, totalDelay);
}

/* Simple polling mock – replace with real websocket / SSE in production */
function mockBackend() {
    const types = ['understanding', 'worker', 'helper', 'expert'];
    const labels = {
        understanding: '🧩 Understand',
        worker:        '⚙️ Worker',
        helper:        '🔧 Helper',
        expert:        '🧙‍ Expert'
    };
    // Every 2‑3 s spawn a node, after 12 s collapse all
    setInterval(() => {
        const t = types[Math.floor(Math.random()*types.length)];
        spawnNode(t, labels[t]);
    }, 2500);

    setInterval(() => {
        collapseAll();
    }, 12000);
}

/* UI interactions */
autonomyBtn.addEventListener('click', () => {
    autonomy = !autonomy;
    autonomyBtn.textContent = `Autonomy: ${autonomy ? 'ON' : 'OFF'}`;
    // In a real system this would inform the backend
});

historyToggle.addEventListener('click', () => {
    historyPanel.classList.toggle('open');
});

/* Kick‑off */
mockBackend();
/* -------------------------------------------------
   Living Dashboard – Core Animation Orchestration
   ------------------------------------------------- */

const canvas = document.getElementById('canvas');
let nodeIdCounter = 0;
const nodes = {};          // id → element
const connections = [];    // {from, to, el}

/* Utility – create a DOM element with attributes */
function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
  children.forEach(c => e.appendChild(
    typeof c === 'string' ? document.createTextNode(c) : c
  ));
  return e;
}

/* Spawn a node of a given type, optionally linking to a parent */
function spawnNode(type, parentId = null) {
  const id = `node-${nodeIdCounter++}`;
  const node = el('div', {
    class: 'node',
    'data-id': id,
    'data-type': type,
    'data-active': 'false'
  }, type.toUpperCase());

  // Position: start off‑screen left, then slide in
  node.style.left = '-200px';
  node.style.top = `${Math.random() * (canvas.clientHeight - 80)}px`;
  canvas.appendChild(node);
  nodes[id] = node;

  // Animate entrance (CSS handles it)
  requestAnimationFrame(() => {
    node.style.left = `${Object.keys(nodes).length * 180}px`;
    node.dataset.active = 'true';
    node.classList.add('active');
  });

  // If there is a parent, draw a connection line
  if (parentId && nodes[parentId]) {
    const line = el('div', { class: 'connection' });
    canvas.appendChild(line);
    connections.push({ from: parentId, to: id, el: line });
    updateConnection(line, nodes[parentId], node);
  }

  // Auto‑deactivate after a short while (simulates work)
  setTimeout(() => {
    node.classList.remove('active');
    node.dataset.active = 'false';
  }, 2000 + Math.random() * 1000);

  return id;
}

/* Update a connection line between two nodes */
function updateConnection(line, fromEl, toEl) {
  const fromRect = fromEl.getBoundingClientRect();
  const toRect   = toEl.getBoundingClientRect();
  const canvasRect = canvas.getBoundingClientRect();

  const x1 = fromRect.right - canvasRect.left;
  const y1 = fromRect.top + fromRect.height / 2 - canvasRect.top;
  const x2 = toRect.left - canvasRect.left;
  const y2 = toRect.top + toRect.height / 2 - canvasRect.top;

  const length = Math.hypot(x2 - x1, y2 - y1);
  const angle = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI);

  line.style.width = `${length}px`;
  line.style.transform = `translate(${x1}px, ${y1}px) rotate(${angle}deg)`;
}

/* Collapse a completed subtree in LIFO order (“thunk‑thunk‑thunk”) */
function collapseSubtree(rootId) {
  // Gather all descendant IDs (including root) in creation order
  const descendantIds = [];
  function collect(id) {
    descendantIds.push(id);
    connections
      .filter(c => c.from === id)
      .forEach(c => collect(c.to));
  }
  collect(rootId);

  // Reverse for LIFO collapse
  descendantIds.reverse();

  descendantIds.forEach((id, idx) => {
    const node = nodes[id];
    if (!node) return;

    // Calculate movement towards parent (or towards history sidebar if root)
    const parentConn = connections.find(c => c.to === id);
    const dx = parentConn
      ? (nodes[parentConn.from].offsetLeft - node.offsetLeft) + 'px'
      : '-100px';
    const dy = parentConn
      ? (nodes[parentConn.from].offsetTop - node.offsetTop) + 'px'
      : '0px';

    node.style.setProperty('--dx', dx);
    node.style.setProperty('--dy', dy);
    node.style.animation = `thunk-collapse var(--anim-normal) var(--ease-snap) forwards`;
    node.style.animationDelay = `${idx * 120}ms`;

    // After animation, move node to history
    setTimeout(() => {
      const history = document.getElementById('history-content');
      const clone = node.cloneNode(true);
      clone.style.position = 'static';
      clone.style.animation = 'none';
      clone.classList.remove('active');
      history.appendChild(clone);
      node.remove();
      delete nodes[id];
    }, 250 + idx * 120);
  });

  // Show a random completion quip
  const quips = ['got er done', 'finally', 'nailed it', 'mission accomplished'];
  const msg = document.createElement('div');
  msg.className = 'completion-quip';
  msg.textContent = quips[Math.floor(Math.random() * quips.length)];
  msg.style.position = 'absolute';
  msg.style.left = `${nodes[rootId]?.offsetLeft || 0}px`;
  msg.style.top = `${nodes[rootId]?.offsetTop || 0}px`;
  canvas.appendChild(msg);
  setTimeout(() => msg.remove(), 2000);
}

/* Demo sequence – runs once on page load */
function demoSequence() {
  const u = spawnNode('understanding');
  const w1 = spawnNode('worker', u);
  const h1 = spawnNode('helper', w1);
  const e1 = spawnNode('expert', h1);
  const w2 = spawnNode('worker', u);
  const h2 = spawnNode('helper', w2);

  // Collapse after a short while
  setTimeout(() => collapseSubtree(u), 5000);
}

/* -------------------------------------------------
   Event Listeners (minimal for spec compliance)
   ------------------------------------------------- */
document.getElementById('autonomy-toggle').addEventListener('click', (e) => {
  const on = e.target.textContent.includes('OFF');
  e.target.textContent = `Autonomy: ${on ? 'ON' : 'OFF'}`;
});

document.getElementById('history-toggle').addEventListener('click', () => {
  document.getElementById('history').classList.toggle('collapsed');
});

document.getElementById('send-btn').addEventListener('click', () => {
  const input = document.getElementById('chat-input');
  if (input.value.trim()) {
    // Placeholder – in a real system this would forward to the backend
    console.log('User message:', input.value);
    input.value = '';
  }
});

window.addEventListener('load', demoSequence);
/* -------------------------------------------------
   dashboard_vision.js – minimal but functional animation
   ------------------------------------------------- */

const canvas = document.getElementById('canvas');
const historyContent = document.getElementById('history-content');
let nodeIdCounter = 0;
const activeNodes = [];

/* ---- Helper: create a node element ---- */
function createNode(type, label) {
  const node = document.createElement('div');
  node.classList.add('node', type, 'active');
  node.id = `node-${nodeIdCounter++}`;
  node.textContent = label;

  // Position: spawn from left, spaced by --node-gap
  const x = 20;
  const y = activeNodes.length * (node.offsetHeight + parseInt(getComputedStyle(document.documentElement).getPropertyValue('--node-gap')));
  node.style.left = `${x}px`;
  node.style.top = `${y}px`;

  canvas.appendChild(node);
  // trigger entrance transition
  requestAnimationFrame(() => {
    node.style.opacity = '1';
    node.style.transform = 'scale(1)';
  });

  activeNodes.push(node);
  return node;
}

/* ---- Simulated workflow ---- */
function simulateWorkflow() {
  // spawn a few nodes of different types
  const types = [
    {type:'indigo', label:'Understanding'},
    {type:'purple', label:'Worker 1'},
    {type:'cyan',   label:'Helper A'},
    {type:'amber',  label:'Expert X'},
    {type:'purple', label:'Worker 2'}
  ];
  let delay = 0;
  types.forEach(item => {
    setTimeout(() => createNode(item.type, item.label), delay);
    delay += 800;
  });

  // after all spawned, start collapse sequence
  setTimeout(startCollapseSequence, delay + 1200);
}

/* ---- Collapse (thunk‑thunk‑thunk) ---- */
function startCollapseSequence() {
  const quips = ['got er done', 'finally', 'all wrapped up', 'mission accomplished'];
  const total = activeNodes.length;
  const baseDelay = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--anim-normal'));

  // LIFO order
  for (let i = total - 1; i >= 0; i--) {
    const node = activeNodes[i];
    const thunkDelay = (total - 1 - i) * (baseDelay + 120); // 120ms between thunks
    setTimeout(() => {
      node.classList.remove('active');
      node.classList.add('collapse');
      // after animation, move to history
      setTimeout(() => {
        const clone = node.cloneNode(true);
        clone.classList.remove('collapse', 'active');
        clone.style.position = 'relative';
        clone.style.left = '0';
        clone.style.top = '0';
        clone.style.transform = 'none';
        clone.style.opacity = '1';
        historyContent.appendChild(clone);
        node.remove();

        // add a random quip once per collapse batch
        if (i === 0) {
          const quip = document.createElement('div');
          quip.textContent = quips[Math.floor(Math.random()*quips.length)];
          quip.style.fontStyle = 'italic';
          quip.style.marginTop = '8px';
          historyContent.appendChild(quip);
        }
      }, parseInt(getComputedStyle(document.documentElement).getPropertyValue('--anim-slow')));
    }, thunkDelay);
  }

  // clear activeNodes after all have collapsed
  setTimeout(() => { activeNodes.length = 0; }, total * (baseDelay + 120));
}

/* ---- UI interactions ---- */
document.getElementById('history-toggle').addEventListener('click', () => {
  document.getElementById('history').classList.toggle('collapsed');
});

document.getElementById('send-btn').addEventListener('click', () => {
  const input = document.getElementById('chat-input');
  if (input.value.trim()) {
    // For demo purposes we just spawn a generic node
    createNode('cyan', input.value.trim());
    input.value = '';
  }
});

/* ---- Kick‑off demo on load ---- */
window.addEventListener('load', simulateWorkflow);
/* ==== Utility ==== */
const svgNS = "http://www.w3.org/2000/svg";

/* ==== State ==== */
let nodeCounter = 0;
const nodes = {};          // id → DOM element
const edges = [];          // {from, to, line}

/* ==== DOM References ==== */
const canvas = document.getElementById('canvas');
const historyContent = document.getElementById('historyContent');
const toggleSidebar = document.getElementById('toggleSidebar');
const sidebar = document.getElementById('sidebar');

/* ==== Layout helpers ==== */
function getNodePosition(id) {
  const el = nodes[id];
  const rect = el.getBoundingClientRect();
  const parentRect = canvas.getBoundingClientRect();
  return {
    x: rect.left + rect.width / 2 - parentRect.left,
    y: rect.top + rect.height / 2 - parentRect.top
  };
}

/* ==== Node creation ==== */
function createNode(type, label) {
  const id = `node-${nodeCounter++}`;
  const div = document.createElement('div');
  div.className = `node node-${type} rainbow`;
  div.id = id;
  div.textContent = label;
  // spawn from left side, then slide into place
  div.style.left = `-150px`;
  div.style.top = `${Math.random() * (canvas.clientHeight - 60)}px`;
  canvas.appendChild(div);
  // animate entrance
  requestAnimationFrame(() => {
    div.style.transition = `transform var(--anim-fast) var(--ease-bounce)`;
    div.style.transform = `translateX(${150 + Math.random() * 30}px)`;
  });
  nodes[id] = div;
  return id;
}

/* ==== Edge creation ==== */
function connectNodes(parentId, childId) {
  const line = document.createElementNS(svgNS, 'line');
  line.setAttribute('stroke', '#888');
  line.setAttribute('stroke-width', '2');
  canvas.appendChild(line);
  edges.push({ from: parentId, to: childId, line });
  updateEdge(line, parentId, childId);
}

/* ==== Edge updater ==== */
function updateEdge(line, fromId, toId) {
  const fromPos = getNodePosition(fromId);
  const toPos   = getNodePosition(toId);
  line.setAttribute('x1', fromPos.x);
  line.setAttribute('y1', fromPos.y);
  line.setAttribute('x2', toPos.x);
  line.setAttribute('y2', toPos.y);
}

/* ==== Periodic edge refresh (for moving nodes) ==== */
function refreshEdges() {
  edges.forEach(e => updateEdge(e.line, e.from, e.to));
  requestAnimationFrame(refreshEdges);
}
refreshEdges();

/* ==== Thunk‑collapse rhythm ==== */
function collapseNode(id, delay = 0) {
  const el = nodes[id];
  if (!el) return;
  setTimeout(() => {
    // compute direction toward parent (if any)
    const edge = edges.find(e => e.to === id);
    if (edge) {
      const parentPos = getNodePosition(edge.from);
      const childPos  = getNodePosition(id);
      const dx = parentPos.x - childPos.x;
      const dy = parentPos.y - childPos.y;
      el.style.setProperty('--dx', `${dx}px`);
      el.style.setProperty('--dy', `${dy}px`);
    } else {
      el.style.setProperty('--dx', `0px`);
      el.style.setProperty('--dy', `0px`);
    }
    el.classList.add('collapse');
    // after animation, move to history
    setTimeout(() => {
      const clone = el.cloneNode(true);
      clone.classList.remove('rainbow', 'collapse');
      clone.style.position = 'static';
      clone.style.transform = 'none';
      historyContent.prepend(clone);
      el.remove();
      delete nodes[id];
      // optional quip
      const quip = ['got er done', 'finally', 'nailed it', 'done!'][Math.floor(Math.random()*4)];
      const note = document.createElement('div');
      note.textContent = quip;
      note.style.fontStyle = 'italic';
      note.style.fontSize = '0.8rem';
      historyContent.prepend(note);
    }, parseInt(getComputedStyle(document.documentElement).getPropertyValue('--anim-normal')));
  }, delay);
}

/* ==== Collapse whole tree (LIFO) ==== */
function collapseAll() {
  const ids = Object.keys(nodes).reverse(); // LIFO order
  ids.forEach((id, idx) => {
    collapseNode(id, idx * 120); // 120ms stagger
  });
}

/* ==== UI Handlers ==== */
document.getElementById('sendBtn').addEventListener('click', () => {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;
  const parentId = Object.keys(nodes).pop(); // last node as parent (if any)
  const newId = createNode('worker', text);
  if (parentId) connectNodes(parentId, newId);
  input.value = '';
});

document.getElementById('micBtn').addEventListener('click', () => {
  alert('Mic not implemented in this demo.');
});

toggleSidebar.addEventListener('click', () => {
  sidebar.classList.toggle('collapsed');
});

/* ==== Demo: auto‑spawn a few nodes then collapse ==== */
function demoSequence() {
  const root = createNode('understanding', 'Start');
  setTimeout(() => {
    const n1 = createNode('worker', 'Task A');
    connectNodes(root, n1);
    setTimeout(() => {
      const n2 = createNode('helper', 'Sub‑task A1');
      connectNodes(n1, n2);
      setTimeout(() => {
        const n3 = createNode('expert', 'Specialized X');
        connectNodes(n2, n3);
        // after a while, trigger collapse
        setTimeout(collapseAll, 3000);
      }, 800);
    }, 800);
  }, 800);
}
demoSequence();
/* --------------------------------------------------------------
   UX Motion Vision – Living Dashboard Logic
   -------------------------------------------------------------- */
(() => {
    const canvas = document.getElementById('dv-canvas');
    const historySidebar = document.getElementById('dv-history');
    const historyContent = historySidebar.querySelector('.dv-history-content');
    const statusText = document.getElementById('dv-status-text');
    const taskCounter = document.getElementById('dv-tasks');
    const uptimeEl = document.getElementById('dv-uptime');
    const autonomyBtn = document.getElementById('dv-autonomy-toggle');
    const historyToggle = document.getElementById('dv-history-toggle');

    let nodeId = 0;
    let activeNodes = []; // stack for LIFO collapse
    let totalTasks = 0;
    let startTime = Date.now();

    // -----------------------------------------------------------------
    // Helper: create a node element
    // -----------------------------------------------------------------
    function createNode(type, label, parent = null) {
        const el = document.createElement('div');
        const id = `node-${nodeId++}`;
        el.id = id;
        el.className = `dv-node ${type} active`;
        el.textContent = label;
        // Position: spawn from left, offset by nodeGap * index
        const x = parent ? parent.dataset.x : 40;
        const y = (activeNodes.length * parseInt(getComputedStyle(document.documentElement).getPropertyValue('--node-gap'))) + 40;
        el.dataset.x = x;
        el.dataset.y = y;
        el.style.left = `${x}px`;
        el.style.top = `${y}px`;
        canvas.appendChild(el);
        activeNodes.push({el, type, parent});
        // draw connector if there is a parent
        if (parent) drawConnector(parent, el);
        // update UI counters
        totalTasks++;
        taskCounter.textContent = `Tasks: ${totalTasks}`;
        return el;
    }

    // -----------------------------------------------------------------
    // Helper: draw a simple SVG line between two nodes
    // -----------------------------------------------------------------
    function drawConnector(fromEl, toEl) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.classList.add('dv-connector');
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.position = 'absolute';
        svg.style.left = 0;
        svg.style.top = 0;
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.appendChild(line);
        canvas.appendChild(svg);
        const update = () => {
            const fromRect = fromEl.getBoundingClientRect();
            const toRect = toEl.getBoundingClientRect();
            const canvasRect = canvas.getBoundingClientRect();
            const x1 = fromRect.left + fromRect.width/2 - canvasRect.left;
            const y1 = fromRect.top + fromRect.height/2 - canvasRect.top;
            const x2 = toRect.left + toRect.width/2 - canvasRect.left;
            const y2 = toRect.top + toRect.height/2 - canvasRect.top;
            line.setAttribute('x1', x1);
            line.setAttribute('y1', y1);
            line.setAttribute('x2', x2);
            line.setAttribute('y2', y2);
            line.setAttribute('stroke', '#555');
            line.setAttribute('stroke-width', '2');
        };
        update();
        // keep line updated on window resize
        window.addEventListener('resize', update);
    }

    // -----------------------------------------------------------------
    // Simulated workflow – you can replace this with real backend events
    // -----------------------------------------------------------------
    function simulateWorkflow() {
        // Example flow: Understanding → Worker → Helper → Expert
        const u = createNode('indigo', 'Understanding');
        setTimeout(() => {
            const w = createNode('purple', 'Worker', u);
            setTimeout(() => {
                const h = createNode('cyan', 'Helper', w);
                setTimeout(() => {
                    const e = createNode('amber', 'Expert', h);
                    // after some work, start collapse
                    setTimeout(() => collapseNodes(), 2000);
                }, 800);
            }, 800);
        }, 800);
    }

    // -----------------------------------------------------------------
    // Collapse routine – LIFO, thunk‑thunk‑thunk rhythm
    // -----------------------------------------------------------------
    function collapseNodes() {
        statusText.textContent = 'Collapsing…';
        const quips = ['got er done', 'finally', 'phew, that was a ride', 'mission accomplished'];
        const total = activeNodes.length;
        activeNodes.reverse().forEach((nodeObj, idx) => {
            const {el, type, parent} = nodeObj;
            const delay = idx * 120; // 120ms between thunks
            setTimeout(() => {
                // compute movement toward parent (or history pane)
                const target = parent || historySidebar;
                const targetRect = target.getBoundingClientRect();
                const elRect = el.getBoundingClientRect();
                const dx = targetRect.left - elRect.left;
                const dy = targetRect.top - elRect.top;
                el.style.setProperty('--dx', `${dx}px`);
                el.style.setProperty('--dy', `${dy}px`);
                el.style.animation = `thunk-collapse var(--anim-normal) forwards`;
                // after animation, move to history
                setTimeout(() => {
                    el.remove();
                    const histItem = document.createElement('div');
                    histItem.textContent = `${type.toUpperCase()}: ${el.textContent} – ${quips[Math.floor(Math.random()*quips.length)]}`;
                    histItem.style.padding = '4px 8px';
                    historyContent.appendChild(histItem);
                    // if this was the last node, restore status
                    if (idx === total - 1) {
                        statusText.textContent = 'Idle';
                        // auto‑expand history to show the final entry
                        historySidebar.classList.remove('collapsed');
                    }
                }, parseInt(getComputedStyle(document.documentElement).getPropertyValue('--anim-normal')));
            }, delay);
        });
        // reset stack for next round
        activeNodes = [];
    }

    // -----------------------------------------------------------------
    // UI interactions
    // -----------------------------------------------------------------
    document.getElementById('dv-send-btn').addEventListener('click', () => {
        simulateWorkflow();
    });
    document.getElementById('dv-chat-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') simulateWorkflow();
    });
    autonomyBtn.addEventListener('click', () => {
        const on = autonomyBtn.textContent.includes('OFF');
        autonomyBtn.textContent = `Autonomy: ${on ? 'ON' : 'OFF'}`;
        autonomyBtn.style.background = on ? '#4caf50' : '#555';
    });
    historyToggle.addEventListener('click', () => {
        historySidebar.classList.toggle('collapsed');
        historyToggle.textContent = historySidebar.classList.contains('collapsed') ? '▶ History' : '◀ History';
    });

    // -----------------------------------------------------------------
    // Uptime ticker
    // -----------------------------------------------------------------
    setInterval(() => {
        const secs = Math.floor((Date.now() - startTime) / 1000);
        uptimeEl.textContent = `Uptime: ${secs}s`;
    }, 1000);
})();
/* -------------------------------------------------
   Living Dashboard – JS orchestration
   ------------------------------------------------- */
const canvas = document.getElementById('canvas');
const historyContent = document.getElementById('history-content');
let nodeIdCounter = 0;
let activeNodes = [];

/* Utility: create a node element */
function createNode(type, label, parent = null) {
    const node = document.createElement('div');
    node.className = `node ${type}`;
    node.id = `node-${nodeIdCounter++}`;
    node.textContent = label;
    // Positioning – simple left‑to‑right flow
    const left = parent ? parseInt(parent.style.left) + 150 : 20;
    const top = parent ? parseInt(parent.style.top) + 80 : 20 + (activeNodes.length * 80);
    node.style.left = `${left}px`;
    node.style.top = `${top}px`;
    canvas.appendChild(node);
    // Trigger entrance animation
    requestAnimationFrame(() => node.classList.add('active'));
    activeNodes.push({el: node, type, parent});
    return node;
}

/* Simulated workflow – for demo purposes */
function demoWorkflow() {
    const root = createNode('understanding', 'Understand');
    setTimeout(() => createNode('worker', 'Worker‑1', root), 600);
    setTimeout(() => createNode('helper', 'Helper‑A', root), 1200);
    setTimeout(() => createNode('expert', 'Expert‑X', root), 1800);
    setTimeout(() => completeWorkflow(), 3000);
}

/* Collapse (thunk‑thunk‑thunk) */
function completeWorkflow() {
    // Reverse order (LIFO)
    const nodesToCollapse = [...activeNodes].reverse();
    nodesToCollapse.forEach((nodeObj, idx) => {
        const {el, type} = nodeObj;
        // Random quip selection
        const quips = ['got er done', 'finally', 'mission accomplished', 'boom'];
        const quip = quips[Math.floor(Math.random()*quips.length)];
        setTimeout(() => {
            el.classList.add('collapse');
            // Show quip briefly
            const bubble = document.createElement('div');
            bubble.textContent = quip;
            bubble.style.position = 'absolute';
            bubble.style.left = '0';
            bubble.style.top = '-20px';
            bubble.style.fontSize = '0.7rem';
            bubble.style.opacity = '0';
            bubble.style.transition = `opacity var(--anim-fast)`;
            el.appendChild(bubble);
            requestAnimationFrame(() => bubble.style.opacity = '1');
            setTimeout(() => bubble.remove(), 800);
        }, idx * 120);
        // After animation, move to history
        setTimeout(() => {
            el.remove();
            const histItem = document.createElement('div');
            histItem.textContent = `${type.toUpperCase()}: ${el.textContent}`;
            histItem.style.padding = '0.4rem 0';
            historyContent.prepend(histItem);
        }, idx * 120 + 250 + 300); // collapse duration + small buffer
    });
    // Reset active nodes list after all collapses
    setTimeout(() => { activeNodes = []; }, nodesToCollapse.length * 120 + 600);
}

/* UI interactions */
document.getElementById('history-toggle').addEventListener('click', () => {
    document.getElementById('history').classList.toggle('open');
});
document.getElementById('autonomy-toggle').addEventListener('click', (e) => {
    const on = e.target.textContent.includes('OFF');
    e.target.textContent = `Autonomy: ${on ? 'ON' : 'OFF'}`;
});
document.getElementById('send-btn').addEventListener('click', () => {
    // For demo we just start the workflow
    demoWorkflow();
});
document.getElementById('chat-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') document.getElementById('send-btn').click();
});

/* Kick off a demo on load */
window.addEventListener('load', demoWorkflow);