/**
 * J.A.R.V.I.S. Voice Engine & Neural Acoustic Synthesizer
 * Supports Hyper-Realistic Human Voice Streaming (via Edge Neural TTS),
 * Multilingual Speech Recognition (STT), and Web Audio SFX.
 */

class VoiceEngine {
  constructor(onResultCallback, onStateChangeCallback, onAudioLevelCallback) {
    this.onResult = onResultCallback;
    this.onStateChange = onStateChangeCallback;
    this.onAudioLevel = onAudioLevelCallback;
    this.onUserSpeechStart = null;
    this.isListening = false;
    this.wakeWordEnabled = true;
    this.soundFxEnabled = true;
    this.selectedVoice = null;
    this.selectedLang = 'auto';
    this.audioCtx = null;
    this.currentAudio = null;

    // Speech Recognition
    this.recognition = null;
    this._initRecognition();

    // Browser Speech Synthesis (Fallback)
    this.synth = window.speechSynthesis;
    this._initVoices();
  }

  _initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("Speech Recognition API not supported in this browser.");
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = false;
    this.recognition.lang = (this.selectedLang === 'auto') ? (navigator.language || 'en-US') : this.selectedLang;

    this.recognition.onstart = () => {
      this.isListening = true;
      if (this.onStateChange) this.onStateChange('listening');
    };

    this.recognition.onspeechstart = () => {
      if (this.onUserSpeechStart) {
        this.onUserSpeechStart();
      }
    };

    this.recognition.onresult = (event) => {
      const lastResultIndex = event.results.length - 1;
      const transcript = event.results[lastResultIndex][0].transcript.trim();
      if (!transcript) return;

      console.log("[STT Recognized]:", transcript);

      if (this.wakeWordEnabled) {
        const lower = transcript.toLowerCase();
        if (lower.includes("jarvis") || lower.includes("hey jarvis") || lower.includes("जार्विस")) {
          this.playBeep(880, 0.1);
          if (this.onResult) this.onResult(transcript);
        } else {
          if (this.onResult) this.onResult(transcript);
        }
      } else {
        if (this.onResult) this.onResult(transcript);
      }
    };

    this.recognition.onerror = (event) => {
      console.warn("[STT Error]:", event.error);
      if (event.error === 'not-allowed') {
        this.isListening = false;
        if (this.onStateChange) this.onStateChange('idle');
      }
    };

    this.recognition.onend = () => {
      if (this.isListening) {
        try {
          this.recognition.start();
        } catch (e) {
          this.isListening = false;
          if (this.onStateChange) this.onStateChange('idle');
        }
      } else {
        if (this.onStateChange) this.onStateChange('idle');
      }
    };
  }

  setLanguage(langCode) {
    this.selectedLang = langCode;
    if (this.recognition) {
      const wasListening = this.isListening;
      if (wasListening) {
        try { this.recognition.stop(); } catch (e) {}
      }
      this.recognition.lang = (langCode === 'auto') ? (navigator.language || 'en-US') : langCode;
      if (wasListening) {
        setTimeout(() => {
          try { this.recognition.start(); } catch (e) {}
        }, 200);
      }
    }
  }

  /**
   * Immediately abort any ongoing speech playback or synthesis (barge-in interruption)
   */
  stopSpeaking() {
    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
        this.currentAudio.currentTime = 0;
        this.currentAudio = null;
      } catch (e) {}
    }
    if (this.synth) {
      try {
        this.synth.cancel();
      } catch (e) {}
    }
  }

  /**
   * Check if speech output is actively playing
   */
  isSpeaking() {
    return (this.currentAudio !== null && !this.currentAudio.paused) || (Boolean(this.synth && this.synth.speaking));
  }

  _initVoices() {
    if (!this.synth) return;
    const populate = () => {
      const voices = this.synth.getVoices();
      const voiceSelect = document.getElementById('voiceSelect');
      if (voiceSelect) {
        voiceSelect.innerHTML = '<option value="neural">Azure Neural Human Voice (Ultra-Realistic)</option>';
        voices.forEach((v) => {
          const opt = document.createElement('option');
          opt.value = v.name;
          opt.textContent = `${v.name} (${v.lang})`;
          voiceSelect.appendChild(opt);
        });
      }

      const preferred = voices.find(v => 
        (v.lang.includes('en-GB') || v.name.includes('UK') || v.name.includes('British') || v.name.includes('George') || v.name.includes('Ryan') || v.name.includes('Daniel')) &&
        (v.name.includes('Male') || v.name.includes('Natural') || !v.name.includes('Female'))
      ) || voices.find(v => v.lang.startsWith('en'));

      this.selectedVoice = preferred || null;
    };

    populate();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = populate;
    }
  }

  setVoiceByName(name) {
    if (!this.synth) return;
    const voices = this.synth.getVoices();
    this.selectedVoice = voices.find(v => v.name === name) || this.selectedVoice;
  }

  toggleListening() {
    if (!this.recognition) {
      alert("Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
      return;
    }

    if (this.isListening) {
      this.isListening = false;
      try { this.recognition.stop(); } catch (e) {}
      if (this.onStateChange) this.onStateChange('idle');
      this.playBeep(440, 0.1);
    } else {
      this.isListening = true;
      try { this.recognition.start(); } catch (e) {}
      if (this.onStateChange) this.onStateChange('listening');
      this.playChime();
    }
  }

  /**
   * Speak using Neural Human Voice stream (edge-tts), with fallback to browser SpeechSynthesis.
   */
  speak(text, audioUrl = null, onStart = null, onEnd = null) {
    // Stop any currently playing audio
    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
        this.currentAudio = null;
      } catch (e) {}
    }
    if (this.synth) {
      this.synth.cancel();
    }

    // Try Neural Audio stream if URL provided
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      this.currentAudio = audio;

      let isFinished = false;
      const finish = () => {
        if (!isFinished) {
          isFinished = true;
          this.currentAudio = null;
          if (onEnd) onEnd();
        }
      };

      audio.onplay = () => {
        if (onStart) onStart();
      };

      audio.onended = finish;

      audio.onerror = (e) => {
        console.warn("Neural audio streaming error, engaging browser voice fallback:", e);
        finish();
        this.speakBrowserFallback(text, onStart, onEnd);
      };

      // Play with promise handling
      audio.play().catch((err) => {
        console.warn("Audio autoplay constraint or error:", err);
        this.speakBrowserFallback(text, onStart, onEnd);
      });
    } else {
      this.speakBrowserFallback(text, onStart, onEnd);
    }
  }

  speakBrowserFallback(text, onStart, onEnd) {
    if (!this.synth) {
      if (onEnd) onEnd();
      return;
    }

    const cleanText = text.replace(/[*_#`~\[\]]/g, ' ').replace(/\s+/g, ' ').trim();
    if (!cleanText) {
      if (onEnd) onEnd();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    if (this.selectedVoice) {
      utterance.voice = this.selectedVoice;
    }
    utterance.rate = 1.05;
    utterance.pitch = 0.95;

    utterance.onstart = () => {
      if (onStart) onStart();
    };

    utterance.onend = () => {
      if (onEnd) onEnd();
    };

    utterance.onerror = () => {
      if (onEnd) onEnd();
    };

    this.synth.speak(utterance);
  }

  // Web Audio SFX
  _getAudioContext() {
    if (!this.audioCtx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioCtx();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  playBeep(freq = 600, duration = 0.08) {
    if (!this.soundFxEnabled) return;
    try {
      const ctx = this._getAudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.06, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch (e) {}
  }

  playChime() {
    if (!this.soundFxEnabled) return;
    try {
      const ctx = this._getAudioContext();
      [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, ctx.currentTime + i * 0.07);
        gain.gain.setValueAtTime(0.08, ctx.currentTime + i * 0.07);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.07 + 0.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + i * 0.07);
        osc.stop(ctx.currentTime + i * 0.07 + 0.25);
      });
    } catch (e) {}
  }
}
