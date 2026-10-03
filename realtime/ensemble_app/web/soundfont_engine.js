import { WorkletSynthesizer } from "https://cdn.jsdelivr.net/npm/spessasynth_lib@4.3.14/+esm";

const PROCESSOR_URL =
  "https://cdn.jsdelivr.net/npm/spessasynth_lib@4.3.14/dist/spessasynth_processor.min.js";

export class RealSoloSoundFontEngine {
  constructor(audioContext) {
    this.context = audioContext;
    this.synth = null;
    this.ready = false;
    this.bankName = "";
  }

  async load(arrayBuffer, bankName = "user-bank") {
    if (!this.context.audioWorklet) {
      throw new Error("AudioWorklet is not available in this browser.");
    }
    if (!this.synth) {
      await this.context.audioWorklet.addModule(PROCESSOR_URL);
      this.synth = new WorkletSynthesizer(this.context);
      await this.synth.isReady;
    }
    await this.synth.soundBankManager.addSoundBank(arrayBuffer, bankName);
    this.bankName = bankName;
    this._configureGM();
    this.ready = true;
  }

  _configureGM() {
    // GM: ch 1 piano, ch 2 acoustic bass, ch 3 tenor sax, ch 10 drums.
    this.synth.sendMessage([0xC0, 0]);       // Acoustic Grand Piano
    this.synth.sendMessage([0xC1, 32]);      // Acoustic Bass
    this.synth.sendMessage([0xC2, 66]);      // Tenor Sax
    this.synth.sendMessage([0xC9, 0]);       // Standard drum program
    this.synth.controllerChange(0, 7, 92);
    this.synth.controllerChange(1, 7, 102);
    this.synth.controllerChange(2, 7, 96);
    this.synth.controllerChange(9, 7, 94);
  }

  note(channel, midi, velocity, when, duration) {
    if (!this.ready) return false;
    const start = Math.max(this.context.currentTime, when);
    const stop = start + Math.max(0.03, duration);
    this.synth.noteOn(channel, midi, velocity, { time: start });
    this.synth.noteOff(channel, midi, { time: stop });
    return true;
  }

  piano(midi, velocity, when, duration) {
    return this.note(0, midi, velocity, when, duration);
  }

  bass(midi, velocity, when, duration) {
    return this.note(1, midi, velocity, when, duration);
  }

  solo(midi, velocity, when, duration) {
    return this.note(2, midi, velocity, when, duration);
  }

  drum(midi, velocity, when, duration = 0.12) {
    return this.note(9, midi, velocity, when, duration);
  }

  panic() {
    if (this.synth) this.synth.stopAll(true);
  }

  destroy() {
    if (this.synth) {
      this.synth.destroy();
      this.synth = null;
    }
    this.ready = false;
  }
}

window.RealSoloSoundFontEngine = RealSoloSoundFontEngine;
window.dispatchEvent(new CustomEvent("realsolo-soundfont-module-ready"));
