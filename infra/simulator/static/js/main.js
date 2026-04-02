const AP_RANGE = 280;
let allNodes = [];
let currentNode = null;

let boardX = 0;
let boardY = 0;
let isDraggingBoard = false;
let dragStartX = 0;
let dragStartY = 0;

let draggingNode = null;
let nodeDragOffsetX = 0;
let nodeDragOffsetY = 0;
let hasDraggedNode = false;
let startNodeDragX = 0;
let startNodeDragY = 0;

document.addEventListener("contextmenu", (e) => e.preventDefault());
document.addEventListener("click", () => {
  document.getElementById("context-menu").style.display = "none";
});

function loadTopology() {
  fetch("/api/topology")
    .then((r) => r.json())
    .then((data) => {
      const width = document.getElementById("map-container").clientWidth;
      allNodes = [];

      function parseNodes(nodes, defaultY, role) {
        if (!nodes) return;

        let spreadFactor = 1;

        if (role === "ap") {
          spreadFactor = 0.6;
        }

        const effectiveWidth = width * spreadFactor;
        const offsetX = (width - effectiveWidth) / 2;
        const spacing = effectiveWidth / (nodes.length || 1);

        nodes.forEach((n, idx) => {
          let posX = offsetX + spacing * idx + spacing / 2;
          let posY = defaultY;

          if (n.ui_pos) {
            const parts = n.ui_pos.split(",");
            posX = parseFloat(parts[0]);
            posY = parseFloat(parts[1]);
          }

          allNodes.push({
            id: n.id,
            type: role,
            x: posX,
            y: posY,
            connectedTo: n.connected_to || null,
            ip: n.ip || "",
            realName: n.real_name || n.id,
            ssid: n.ssid || "",
          });
        });
      }

      parseNodes(data.switches, 100, "switch");
      parseNodes(data.access_points, 300, "ap");
      parseNodes(data.stations, 500, "station");

      renderBoard();
    });
}

function renderBoard() {
  const container = document.getElementById("nodes-container");
  const svg = document.getElementById("links-svg");
  container.innerHTML = "";
  let svgHtml = "";

  allNodes.forEach((n) => {
    if (n.type === "ap" || n.type === "station") {
      svgHtml += `<circle cx="${n.x}" cy="${n.y}" r="${AP_RANGE}" fill="rgba(49, 130, 206, 0.05)" stroke="rgba(49, 130, 206, 0.2)" stroke-width="1" stroke-dasharray="5,5" />`;
    }
  });

  allNodes.forEach((n) => {
    if (n.type === "ap" && n.connectedTo) {
      const target = allNodes.find((t) => t.id === n.connectedTo);
      if (target) {
        svgHtml += `<line x1="${n.x}" y1="${n.y}" x2="${target.x}" y2="${target.y}" stroke="#718096" stroke-width="4" />`;
      }
    }
    if (n.type === "station" && n.connectedTo) {
      const target = allNodes.find((t) => t.id === n.connectedTo);
      if (target) {
        svgHtml += `<line x1="${n.x}" y1="${n.y}" x2="${target.x}" y2="${target.y}" stroke="#48bb78" stroke-width="2.5" stroke-dasharray="10,6" />`;
      }
    }
  });
  svg.innerHTML = svgHtml;

  allNodes.forEach((n) => {
    let cssClass = n.type;
    if (n.type === "station" && !n.connectedTo) {
      cssClass = "orphan";
    }

    const el = document.createElement("div");
    el.className = `node ${cssClass}`;
    el.style.left = `${n.x}px`;
    el.style.top = `${n.y}px`;

    let ipText = n.ip ? n.ip.split("/")[0] : "L2 Network";
    el.innerHTML = `
                    <div class="node-box">${n.id.toUpperCase()}</div>
                    <div class="node-info"><strong>${n.realName}</strong><br>${ipText}</div>
                `;

    el.querySelector(".node-box").addEventListener("mousedown", (e) => {
      if (e.button === 2 && !e.ctrlKey) {
        e.stopPropagation();
        if (n.type === "station") {
          draggingNode = n;
          hasDraggedNode = false;
          startNodeDragX = e.clientX;
          startNodeDragY = e.clientY;
          nodeDragOffsetX = e.clientX - boardX - n.x;
          nodeDragOffsetY = e.clientY - boardY - n.y;
        } else {
          showContextMenu(e.clientX, e.clientY, n);
        }
      }
    });

    container.appendChild(el);
  });
}

const mapContainer = document.getElementById("map-container");
const boardTransform = document.getElementById("board-transform");

mapContainer.addEventListener("mousedown", (e) => {
  if (e.button === 2 && e.ctrlKey) {
    isDraggingBoard = true;
    dragStartX = e.clientX - boardX;
    dragStartY = e.clientY - boardY;
    mapContainer.classList.add("grabbing-board");
  }
});

window.addEventListener("mousemove", (e) => {
  if (isDraggingBoard) {
    boardX = e.clientX - dragStartX;
    boardY = e.clientY - dragStartY;
    boardTransform.style.transform = `translate(${boardX}px, ${boardY}px)`;
  }

  if (draggingNode) {
    if (
      Math.abs(e.clientX - startNodeDragX) > 3 ||
      Math.abs(e.clientY - startNodeDragY) > 3
    ) {
      hasDraggedNode = true;
    }
    if (hasDraggedNode) {
      draggingNode.x = e.clientX - boardX - nodeDragOffsetX;
      draggingNode.y = e.clientY - boardY - nodeDragOffsetY;
      renderBoard();
    }
  }
});

window.addEventListener("mouseup", (e) => {
  if (isDraggingBoard) {
    isDraggingBoard = false;
    mapContainer.classList.remove("grabbing-board");
  }

  if (draggingNode) {
    if (!hasDraggedNode) {
      showContextMenu(e.clientX, e.clientY, draggingNode);
    } else {
      if (draggingNode.connectedTo) {
        let currentAP = allNodes.find(
          (ap) => ap.id === draggingNode.connectedTo,
        );
        if (currentAP) {
          const dist = Math.sqrt(
            Math.pow(draggingNode.x - currentAP.x, 2) +
              Math.pow(draggingNode.y - currentAP.y, 2),
          );
          if (dist > AP_RANGE) {
            draggingNode.connectedTo = null;
          }
        } else {
          draggingNode.connectedTo = null;
        }
      }

      fetch("/api/update_node", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: draggingNode.id,
          connectedTo: draggingNode.connectedTo,
          x: draggingNode.x,
          y: draggingNode.y,
        }),
      }).then(() => renderBoard());
    }
    draggingNode = null;
  }
});

function showContextMenu(x, y, node) {
  const menu = document.getElementById("context-menu");
  menu.innerHTML = "";

  const items = [
    { label: "Information", action: () => openModal(node, "info") },
    { label: "Terminal", action: () => openModal(node, "terminal") },
  ];

  if (node.type === "station") {
    items.push({
      label: "Scan Networks",
      action: () => openModal(node, "scan"),
    });
    if (node.connectedTo) {
      items.push({
        label: "Disconnect",
        isDanger: true,
        action: () => disconnectNode(node),
      });
    }
  }

  items.forEach((item) => {
    const el = document.createElement("div");
    el.className = `context-menu-item ${item.isDanger ? "danger" : ""}`;
    el.innerText = item.label;
    el.onclick = () => {
      menu.style.display = "none";
      item.action();
    };
    menu.appendChild(el);
  });

  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
  menu.style.display = "block";
}

function disconnectNode(node) {
  node.connectedTo = null;
  fetch("/api/update_node", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: node.id,
      connectedTo: null,
      x: node.x,
      y: node.y,
    }),
  }).then(() => renderBoard());
}

function openModal(node, view) {
  currentNode = node;
  document.getElementById("modal-overlay").style.display = "block";
  document.getElementById("node-title").innerText =
    "Node: " + node.id.toUpperCase();

  document.getElementById("info-area").style.display = "none";
  document.getElementById("scan-area").style.display = "none";
  document.getElementById("terminal-area").style.display = "none";

  if (view === "info") {
    document.getElementById("info-area").style.display = "block";
    let status =
      node.type === "station"
        ? node.connectedTo
          ? `Connected to ${node.connectedTo.toUpperCase()}`
          : "Disconnected"
        : "Active";
    document.getElementById("info-content").innerHTML = `
                    <p><strong>ID:</strong> ${node.id.toUpperCase()}</p>
                    <p><strong>Name:</strong> ${node.realName}</p>
                    <p><strong>Type:</strong> ${node.type.toUpperCase()}</p>
                    <p><strong>IP Address:</strong> ${node.ip || "N/A"}</p>
                    <p><strong>Status:</strong> ${status}</p>
                `;
  } else if (view === "scan") {
    document.getElementById("scan-area").style.display = "block";
    document.getElementById("scan-results").innerHTML = "";
  } else if (view === "terminal") {
    document.getElementById("terminal-area").style.display = "block";
    document.getElementById("term-prompt").innerText = `root@${node.id}:~#`;
    document.getElementById("term-history").innerHTML = "";
    document.getElementById("cmd-input").value = "";
    document.getElementById("cmd-input").disabled = false;
    setTimeout(() => document.getElementById("cmd-input").focus(), 100);
  }
}

function closeModal() {
  document.getElementById("modal-overlay").style.display = "none";
}

function scanNetwork() {
  document.getElementById("scan-results").innerHTML =
    "<p>Scanning for wireless networks...</p>";

  setTimeout(() => {
    let visibleSsids = [];

    allNodes.forEach((ap) => {
      if (ap.type === "ap") {
        const dist = Math.sqrt(
          Math.pow(currentNode.x - ap.x, 2) + Math.pow(currentNode.y - ap.y, 2),
        );
        if (dist <= AP_RANGE) {
          if (ap.ssid && !visibleSsids.find((s) => s.ssid === ap.ssid)) {
            visibleSsids.push({ ssid: ap.ssid, id: ap.id });
          }
        }
      }
    });

    if (visibleSsids.length === 0) {
      document.getElementById("scan-results").innerHTML =
        "<p style='color:#e53e3e;'>No networks found in range!</p>";
      return;
    }

    let html = "<div style='border: 1px solid #e2e8f0; border-radius: 8px;'>";
    visibleSsids.forEach((net) => {
      html += `
                    <div class="scan-item">
                        <strong>${net.ssid}</strong>
                        <button onclick="connectWifi('${net.ssid}', '${net.id}')">Connect</button> 
                    </div>`;
    });
    html += "</div>";
    document.getElementById("scan-results").innerHTML = html;
  }, 600);
}

function connectWifi(ssid, apId) {
  fetch("/api/connect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ station: currentNode.id, ssid: ssid, ap_id: apId }),
  })
    .then((r) => r.json())
    .then((data) => {
      loadTopology();
      closeModal();
    });
}

document.getElementById("cmd-input").addEventListener("keydown", function (e) {
  if (e.key === "Enter") {
    const cmd = this.value;
    if (!cmd.trim()) return;

    const inputEl = this;
    const historyDiv = document.getElementById("term-history");
    const prompt = document.getElementById("term-prompt").innerText;

    historyDiv.innerHTML += `<div><span class="term-prompt">${prompt}</span><span style="color:#48bb78">${cmd}</span></div>`;
    inputEl.value = "";
    inputEl.disabled = true;

    fetch("/api/terminal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ node: currentNode.id, command: cmd }),
    })
      .then((r) => r.json())
      .then((data) => {
        historyDiv.innerHTML += `<div class="term-output">${data.output}</div>`;
        inputEl.disabled = false;
        inputEl.focus();
        const wrapper = document.getElementById("terminal-wrapper");
        wrapper.scrollTop = wrapper.scrollHeight;
      });
  }
});

loadTopology();
