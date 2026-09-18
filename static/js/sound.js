/* =========================================================
   DRAW THE SONG - SYNTHESIZED SOUND EFFECTS ENGINE
   Uses native HTML5 Web Audio API - Zero External Dependencies
   ========================================================= */

class SoundEngine {
  constructor() {
    this.enabled = localStorage.getItem("dts_sound_enabled") !== "false";
    this.ctx = null;
    this.initAudioContext();
  }

  initAudioContext() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.ctx = new AudioContext();
      }
    } catch (e) {
      console.warn("Web Audio API not supported on this browser:", e);
    }
  }

  ensureContext() {
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  toggle() {
    this.enabled = !this.enabled;
    localStorage.setItem("dts_sound_enabled", this.enabled);
    if (this.enabled) {
      this.ensureContext();
      this.playTone(523.25, 0.15, "sine"); // Confirmation beep
    }
    return this.enabled;
  }

  playTone(freq, duration, type = "sine", gainVal = 0.15) {
    if (!this.enabled || !this.ctx) return;
    this.ensureContext();

    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = type;
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

    gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

    osc.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start();
    osc.stop(this.ctx.currentTime + duration);
  }

  playTick() {
    // Subtle wooden clock tick
    this.playTone(880, 0.05, "sine", 0.08);
  }

  playCorrect() {
    // Triumphant ascending arpeggio: C5 -> E5 -> G5 -> C6
    if (!this.enabled || !this.ctx) return;
    this.ensureContext();

    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 0.25, "triangle", 0.2);
      }, idx * 75);
    });
  }

  playClose() {
    // Two-tone warm clue
    this.playTone(440, 0.1, "sine", 0.1);
    setTimeout(() => this.playTone(554.37, 0.15, "sine", 0.12), 100);
  }

  playRoundEnd() {
    // Warm harmonic chord
    this.playTone(440, 0.4, "sine", 0.15);
    this.playTone(554.37, 0.4, "sine", 0.12);
    this.playTone(659.25, 0.5, "sine", 0.1);
  }

  playGameOver() {
    // Grand victory fanfare
    const notes = [523.25, 659.25, 783.99, 1046.50, 1318.51];
    notes.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 0.4, "triangle", 0.22);
      }, idx * 110);
    });
  }
}

window.soundEngine = new SoundEngine();

// UI sound toggle hook
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("soundToggleBtn");
  if (toggleBtn) {
    const updateIcon = () => {
      toggleBtn.textContent = window.soundEngine.enabled ? "🔊" : "🔇";
      toggleBtn.title = window.soundEngine.enabled ? "Sound: ON" : "Sound: OFF";
    };
    updateIcon();
    toggleBtn.addEventListener("click", () => {
      window.soundEngine.toggle();
      updateIcon();
    });
  }
});
