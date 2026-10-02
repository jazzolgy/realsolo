export class RealSoloApprovedSampleEngine {
  constructor(context, baseUrl = "/assets/") {
    this.context = context;
    this.baseUrl = baseUrl;
    this.manifest = null;
    this.buffers = new Map();
    this.rr = new Map();
    this.ready = false;
  }

  async init() {
    const r = await fetch(this.baseUrl + "realsolo_manifest.json", {cache:"no-store"});
    if (!r.ok) throw new Error("approved sample pack is not installed");
    this.manifest = await r.json();
    this.ready = true;
    return this;
  }

  async _buffer(sample) {
    if (this.buffers.has(sample)) return this.buffers.get(sample);
    const promise = fetch(this.baseUrl + sample.split("/").map(encodeURIComponent).join("/"))
      .then(r => {
        if (!r.ok) throw new Error("sample fetch failed: " + sample);
        return r.arrayBuffer();
      })
      .then(b => this.context.decodeAudioData(b));
    this.buffers.set(sample, promise);
    return promise;
  }

  _select(rows, midi, velocity, key) {
    const matches = rows.filter(r =>
      midi >= r.lokey && midi <= r.hikey &&
      velocity >= r.lovel && velocity <= r.hivel
    );
    if (!matches.length) return null;
    const rrKey = key + ":" + midi + ":" + Math.floor(velocity / 16);
    const idx = this.rr.get(rrKey) || 0;
    this.rr.set(rrKey, idx + 1);
    return matches[idx % matches.length];
  }

  async _play(row, midi, velocity, when, duration, pitched) {
    if (!row) return false;
    const buffer = await this._buffer(row.sample);
    const src = this.context.createBufferSource();
    const gain = this.context.createGain();
    src.buffer = buffer;
    if (pitched) src.playbackRate.value = Math.pow(2, (midi - row.pitch_keycenter) / 12);
    gain.gain.value = Math.max(0.03, Math.min(1, velocity / 127));
    src.connect(gain);
    gain.connect(this.context.destination);
    const start = Math.max(this.context.currentTime + 0.005, when);
    src.start(start);
    if (pitched && duration) {
      gain.gain.setValueAtTime(gain.gain.value, start + Math.max(.03, duration - .04));
      gain.gain.exponentialRampToValueAtTime(.0001, start + Math.max(.05, duration));
      src.stop(start + Math.max(.08, duration + .05));
    }
    return true;
  }

  async piano(midi, velocity, when, duration) {
    const pack = this.manifest.packs.piano;
    if (!pack || !pack.regions) return false;
    const rows = pack.regions;
    return this._play(
      this._select(rows, midi, velocity, "piano"),
      midi,
      velocity,
      when,
      duration,
      true
    );
  }


  _soloFamily(pack, articulation) {
    const tags = new Set((articulation || []).map(x => String(x).toLowerCase()));
    const order = [
      ["growl", "growl"],
      ["subtone", "subtone"],
      ["short", "short"],
      ["staccato", "short"],
      ["accent", "short"],
      ["vibrato", "vibrato"],
    ];
    for (const [tag, family] of order) {
      if (tags.has(tag) && pack.articulations && pack.articulations[family]) return family;
    }
    return "sustain";
  }

  async _playSolo(row, midi, velocity, when, duration, articulation, family, hints = {}) {
    if (!row) return false;
    const buffer = await this._buffer(row.sample);
    const src = this.context.createBufferSource();
    const gain = this.context.createGain();
    src.buffer = buffer;
    src.playbackRate.value = Math.pow(2, (midi - row.pitch_keycenter) / 12);

    const tags = new Set((articulation || []).map(x => String(x).toLowerCase()));
    let level = Math.max(0.03, Math.min(1, velocity / 127));
    if (tags.has("breathy") || tags.has("breath")) level *= 0.88;
    gain.gain.value = .0001;

    src.connect(gain);
    gain.connect(this.context.destination);
    const start = Math.max(this.context.currentTime + 0.005, when);
    const releaseShape = hints.release_shape || "normal";
    const connected = tags.has("legato") || releaseShape === "connected";
    const effectiveDuration = connected ? duration * 1.08 : duration;
    const end = start + Math.max(.08, effectiveDuration);
    const attackScale = Math.max(.2, Math.min(1.5, hints.attack_scale || 1));
    const tongued = tags.has("tongued");
    const attackTime = tongued
      ? Math.max(.003, .007 / attackScale)
      : (connected ? .018 : (.008 + (1 - Math.min(1, attackScale)) * .045));
    gain.gain.setValueAtTime(.0001, start);
    if (tongued) {
      const tonguePeak = Math.min(1, level * 1.07);
      gain.gain.exponentialRampToValueAtTime(Math.max(.001, tonguePeak), start + attackTime);
      gain.gain.linearRampToValueAtTime(level, start + attackTime + .014);
    } else {
      gain.gain.exponentialRampToValueAtTime(Math.max(.001, level), start + attackTime);
    }

    if (src.detune) {
      if (tags.has("scoop")) {
        src.detune.setValueAtTime(-90, start);
        src.detune.linearRampToValueAtTime(0, start + Math.min(.12, duration * .28));
      } else {
        src.detune.setValueAtTime(0, start);
      }
      if (tags.has("fall")) {
        const fallStart = Math.max(start, end - Math.min(.18, duration * .3));
        src.detune.setValueAtTime(0, fallStart);
        src.detune.linearRampToValueAtTime(-280, end);
      }
    }

    let vibrato = null, vibratoDepth = null;
    if (tags.has("vibrato") && family !== "vibrato" && src.detune) {
      vibrato = this.context.createOscillator();
      vibratoDepth = this.context.createGain();
      vibrato.frequency.value = 5.2;
      vibratoDepth.gain.setValueAtTime(0, start);
      vibratoDepth.gain.linearRampToValueAtTime(14, start + Math.min(.35, duration * .45));
      vibrato.connect(vibratoDepth);
      vibratoDepth.connect(src.detune);
      vibrato.start(start);
      vibrato.stop(end + .02);
    }

    src.start(start);
    const releaseTime = releaseShape === "open" ? .11 : (connected ? .025 : .05);
    const releaseStart = Math.max(start + attackTime, end - releaseTime);
    gain.gain.setValueAtTime(level, releaseStart);
    gain.gain.exponentialRampToValueAtTime(.0001, end);
    src.stop(end + .03);
    return true;
  }

  async solo(instrument, midi, velocity, when, duration, articulation = [], hints = {}) {
    const key = instrument === "trumpet" ? "solo_trumpet" : "solo_sax";
    const pack = this.manifest.packs[key];
    if (!pack || !pack.articulations) return false;
    const family = this._soloFamily(pack, articulation);
    const rows = pack.articulations[family] || pack.articulations.sustain || [];
    const selected = this._select(rows, midi, velocity, key + ":" + family);
    return this._playSolo(selected, midi, velocity, when, duration, articulation, family, hints);
  }

  async bass(midi, velocity, when, duration, articulation = []) {
    const rows = this.manifest.packs.bass.regions;
    const tags = new Set(articulation || []);
    // Articulation is currently a renderer hint. We do not pretend that the
    // pizzicato pack contains a dedicated ghost/dead-note sample that it does not.
    let playedVelocity = velocity;
    let playedDuration = duration;
    if (tags.has("short")) playedDuration *= 0.68;
    if (tags.has("connected")) playedDuration *= 1.04;
    if (tags.has("ghosted") || tags.has("dead")) {
      playedVelocity *= 0.72;
      playedDuration *= 0.46;
    }
    playedVelocity = Math.max(1, Math.min(127, Math.round(playedVelocity)));
    playedDuration = Math.max(0.04, playedDuration);
    return this._play(
      this._select(rows, midi, playedVelocity, "bass"),
      midi,
      playedVelocity,
      when,
      playedDuration,
      true
    );
  }

  async drum(midi, velocity, when, duration) {
    const pack = this.manifest.packs.drums;
    const articulation = pack.gm_map[String(midi)];
    const rows = articulation ? pack.articulations[articulation] : null;
    if (!rows) return false;
    return this._play(this._select(rows, 60, velocity, articulation), 60, velocity, when, duration, false);
  }

  async warmup() {
    const jobs = [];
    const piano = this.manifest.packs.piano && this.manifest.packs.piano.regions || [];
    for (const midi of [48,55,60,64,67,72,76,79]) {
      const row = this._select(piano, midi, 76, "warmpiano");
      if (row) jobs.push(this._buffer(row.sample));
    }
    for (const key of ["solo_sax", "solo_trumpet"]) {
      const pack = this.manifest.packs[key];
      const rows = pack && pack.articulations && pack.articulations.sustain || [];
      for (const midi of [48,55,60,64,67,72]) {
        const row = this._select(rows, midi, 80, "warm:"+key);
        if (row) jobs.push(this._buffer(row.sample));
      }
    }
    const bass = this.manifest.packs.bass.regions;
    for (const midi of [28, 31, 33, 36, 40, 43, 45, 48]) {
      const row = this._select(bass, midi, 80, "warmbass");
      if (row) jobs.push(this._buffer(row.sample));
    }
    for (const art of ["ride","hat_closed","kick","snare"]) {
      const rows = this.manifest.packs.drums.articulations[art] || [];
      for (const v of [48,80,112]) {
        const row = this._select(rows, 60, v, "warm:"+art);
        if (row) jobs.push(this._buffer(row.sample));
      }
    }
    await Promise.allSettled(jobs);
  }
}

window.RealSoloApprovedSampleEngine = RealSoloApprovedSampleEngine;
window.dispatchEvent(new CustomEvent("realsolo-approved-sample-module-ready"));
