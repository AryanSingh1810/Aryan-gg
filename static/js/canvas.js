/* =========================================================
   DRAW THE SONG - HTML5 CANVAS DRAWING ENGINE
   High-performance vector stroke synchronization
   ========================================================= */

class DrawingCanvas {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext("2d");
    this.isDrawing = false;
    this.canDraw = false; // Only active drawer can draw
    
    // Virtual Coordinate System (1200 x 800) for cross-device consistency
    this.virtualWidth = 1200;
    this.virtualHeight = 800;

    // Current Tool State
    this.currentTool = "pencil"; // pencil, eraser
    this.currentColor = "#000000";
    this.currentSize = 6;
    
    // Stroke tracking
    this.lastX = 0;
    this.lastY = 0;
    this.history = []; // Array of complete stroke actions for undo
    this.currentPath = [];
    this.redoStack = [];

    this.initCanvas();
    this.bindEvents();
  }

  initCanvas() {
    this.canvas.width = this.virtualWidth;
    this.canvas.height = this.virtualHeight;
    this.clearCanvas(false);
  }

  clearCanvas(broadcast = true) {
    this.ctx.fillStyle = "#ffffff";
    this.ctx.fillRect(0, 0, this.virtualWidth, this.virtualHeight);
    this.history = [];
    this.redoStack = [];

    if (broadcast && this.canDraw) {
      window.gameSocket.sendClear();
    }
  }

  setCanDraw(status) {
    this.canDraw = status;
    const toolbar = document.getElementById("canvasToolbar");
    if (toolbar) {
      toolbar.style.display = status ? "flex" : "none";
    }
    this.canvas.style.cursor = status ? "crosshair" : "default";
  }

  getVirtualCoordinates(e) {
    const rect = this.canvas.getBoundingClientRect();
    let clientX = e.clientX;
    let clientY = e.clientY;
    if (clientX === undefined && e.touches && e.touches[0]) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    }
    clientX = (clientX !== undefined) ? clientX : 0;
    clientY = (clientY !== undefined) ? clientY : 0;

    const width = rect.width > 0 ? rect.width : this.virtualWidth;
    const height = rect.height > 0 ? rect.height : this.virtualHeight;

    const scaleX = this.virtualWidth / width;
    const scaleY = this.virtualHeight / height;

    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY
    };
  }

  bindEvents() {
    // Pointer Events support Mouse, Touch, and Pen uniformly
    this.canvas.addEventListener("pointerdown", (e) => this.handlePointerDown(e));
    this.canvas.addEventListener("pointermove", (e) => this.handlePointerMove(e));
    this.canvas.addEventListener("pointerup", (e) => this.handlePointerUp(e));
    this.canvas.addEventListener("pointercancel", (e) => this.handlePointerUp(e));
    this.canvas.addEventListener("pointerleave", (e) => this.handlePointerUp(e));

    // Prevent scrolling while drawing on touch devices
    this.canvas.addEventListener("touchstart", (e) => {
      if (this.canDraw) e.preventDefault();
    }, { passive: false });

    // Toolbar Buttons Hooks
    this.bindToolbarControls();
  }

  handlePointerDown(e) {
    if (!this.canDraw) return;
    this.isDrawing = true;
    const coords = this.getVirtualCoordinates(e);
    this.lastX = coords.x;
    this.lastY = coords.y;

    this.currentPath = [{
      x: coords.x,
      y: coords.y,
      color: this.currentColor,
      size: this.currentSize,
      tool: this.currentTool
    }];

    // Draw initial point dot
    this.drawSegment(coords.x, coords.y, coords.x + 0.1, coords.y + 0.1, this.currentColor, this.currentSize, this.currentTool);
    
    // Broadcast stroke start dot
    window.gameSocket.sendStroke({
      x: coords.x + 0.1,
      y: coords.y + 0.1,
      px: coords.x,
      py: coords.y,
      color: this.currentColor,
      size: this.currentSize,
      tool: this.currentTool
    });
  }

  handlePointerMove(e) {
    if (!this.canDraw || !this.isDrawing) return;
    const coords = this.getVirtualCoordinates(e);

    this.drawSegment(this.lastX, this.lastY, coords.x, coords.y, this.currentColor, this.currentSize, this.currentTool);

    // Transmit compact vector stroke packet
    window.gameSocket.sendStroke({
      x: coords.x,
      y: coords.y,
      px: this.lastX,
      py: this.lastY,
      color: this.currentColor,
      size: this.currentSize,
      tool: this.currentTool
    });

    this.currentPath.push({
      x: coords.x,
      y: coords.y,
      px: this.lastX,
      py: this.lastY,
      color: this.currentColor,
      size: this.currentSize,
      tool: this.currentTool
    });

    this.lastX = coords.x;
    this.lastY = coords.y;
  }

  handlePointerUp(e) {
    if (!this.isDrawing) return;
    this.isDrawing = false;
    if (this.currentPath.length > 0) {
      this.history.push([...this.currentPath]);
      this.currentPath = [];
      this.redoStack = []; // Clear redo stack on new action
    }
  }

  drawSegment(x1, y1, x2, y2, color, size, tool) {
    this.ctx.save();
    this.ctx.beginPath();
    this.ctx.moveTo(x1, y1);
    this.ctx.lineTo(x2, y2);

    if (tool === "eraser") {
      this.ctx.strokeStyle = "#ffffff";
      this.ctx.lineWidth = size * 2.5; // Eraser gets slightly larger stroke
    } else {
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = size;
    }

    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";
    this.ctx.stroke();
    this.ctx.restore();
  }

  // Called when remote stroke packet is received over WebSocket
  receiveStroke(data) {
    this.drawSegment(data.px, data.py, data.x, data.y, data.color, data.size, data.tool);
  }

  // Redraw full history (for undo or syncing new players)
  syncStrokes(strokes) {
    this.ctx.fillStyle = "#ffffff";
    this.ctx.fillRect(0, 0, this.virtualWidth, this.virtualHeight);
    if (!strokes || !strokes.length) return;

    for (const s of strokes) {
      this.drawSegment(s.px || s.x, s.py || s.y, s.x, s.y, s.color, s.size, s.tool);
    }
  }

  undo(broadcast = true) {
    if (this.history.length === 0) return;
    const lastStroke = this.history.pop();
    this.redoStack.push(lastStroke);

    // Replay remaining history
    this.ctx.fillStyle = "#ffffff";
    this.ctx.fillRect(0, 0, this.virtualWidth, this.virtualHeight);

    for (const path of this.history) {
      for (const s of path) {
        this.drawSegment(s.px || s.x, s.py || s.y, s.x, s.y, s.color, s.size, s.tool);
      }
    }

    if (broadcast && this.canDraw) {
      window.gameSocket.sendUndo();
    }
  }

  redo() {
    if (this.redoStack.length === 0) return;
    const stroke = this.redoStack.pop();
    this.history.push(stroke);

    for (const s of stroke) {
      this.drawSegment(s.px || s.x, s.py || s.y, s.x, s.y, s.color, s.size, s.tool);
      if (this.canDraw) {
        window.gameSocket.sendStroke(s);
      }
    }
  }

  bindToolbarControls() {
    // Tool buttons (pencil, eraser)
    const pencilBtn = document.getElementById("pencilToolBtn");
    const eraserBtn = document.getElementById("eraserToolBtn");

    if (pencilBtn && eraserBtn) {
      pencilBtn.addEventListener("click", () => {
        this.currentTool = "pencil";
        pencilBtn.classList.add("active");
        eraserBtn.classList.remove("active");
      });
      eraserBtn.addEventListener("click", () => {
        this.currentTool = "eraser";
        eraserBtn.classList.add("active");
        pencilBtn.classList.remove("active");
      });
    }

    // Brush Sizes
    document.querySelectorAll(".size-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        document.querySelectorAll(".size-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.currentSize = parseInt(btn.dataset.size, 10) || 6;
      });
    });

    // Color Swatches
    document.querySelectorAll(".color-swatch").forEach((swatch) => {
      swatch.addEventListener("click", () => {
        document.querySelectorAll(".color-swatch").forEach(s => s.classList.remove("active"));
        swatch.classList.add("active");
        this.currentColor = swatch.dataset.color || "#000000";
        if (this.currentTool === "eraser" && pencilBtn) {
          pencilBtn.click(); // Switch back to pencil when color picked
        }
      });
    });

    // Clear, Undo, Redo
    const clearBtn = document.getElementById("clearCanvasBtn");
    if (clearBtn) clearBtn.addEventListener("click", () => this.clearCanvas(true));

    const undoBtn = document.getElementById("undoCanvasBtn");
    if (undoBtn) undoBtn.addEventListener("click", () => this.undo(true));

    const redoBtn = document.getElementById("redoCanvasBtn");
    if (redoBtn) redoBtn.addEventListener("click", () => this.redo());
  }
}

window.DrawingCanvas = DrawingCanvas;
