/**
 * J.A.R.V.I.S. Main Application Controller
 * Connects HUD UI, Arc Reactor visualizer, Voice Engine, and WebSocket streaming.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const clockEl = document.getElementById('hudClock');
  const dateEl = document.getElementById('hudDate');
  const statusDot = document.getElementById('statusDot');
  const statusLabel = document.getElementById('statusLabel');
  const aiModePill = document.getElementById('aiModePill');
  const aiModeText = document.getElementById('aiModeText');
  const transcriptText = document.getElementById('transcriptText');
  const consoleOutput = document.getElementById('consoleOutput');
  const commandInput = document.getElementById('commandInput');
  const sendBtn = document.getElementById('sendBtn');
  const micToggleBtn = document.getElementById('micToggleBtn');
  const waveBars = document.querySelectorAll('.wave-bar');
  const latencyPill = document.getElementById('latencyPill');
  const latencyVal = document.getElementById('latencyVal');
  const settingsModal = document.getElementById('settingsModal');
  const settingsBtn = document.getElementById('settingsBtn');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalCancelBtn = document.getElementById('modalCancelBtn');
  const modalSaveBtn = document.getElementById('modalSaveBtn');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const toggleVisBtn = document.getElementById('toggleVisBtn');
  const modelSelect = document.getElementById('modelSelect');
  const voiceSelect = document.getElementById('voiceSelect');
  const defaultCityInput = document.getElementById('defaultCityInput');
  const wakeWordToggle = document.getElementById('wakeWordToggle');
  const soundFxToggle = document.getElementById('soundFxToggle');
  const clearLogBtn = document.getElementById('clearLogBtn');
  const testVoiceBtn = document.getElementById('testVoiceBtn');
  const personaSelect = document.getElementById('personaSelect');
  const personaIcon = document.getElementById('personaIcon');
  const modalPersonaSelect = document.getElementById('modalPersonaSelect');

  // Humanoid Voice Persona State
  let currentPersona = localStorage.getItem('jarvis_persona') || 'indian_boy';

  function updatePersonaIcon(persona) {
    if (!personaIcon) return;
    if (persona === 'indian_girl') {
      personaIcon.textContent = '👧';
    } else if (persona === 'indian_boy') {
      personaIcon.textContent = '👦';
    } else {
      personaIcon.textContent = '🤵';
    }
  }

  function setPersona(persona, syncBackend = true) {
    currentPersona = persona;
    localStorage.setItem('jarvis_persona', currentPersona);
    if (personaSelect) personaSelect.value = currentPersona;
    if (modalPersonaSelect) modalPersonaSelect.value = currentPersona;
    updatePersonaIcon(currentPersona);

    if (syncBackend) {
      fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_persona: currentPersona })
      }).catch(console.warn);
    }
  }

  setPersona(currentPersona, false);

  if (personaSelect) {
    personaSelect.addEventListener('change', () => {
      setPersona(personaSelect.value, true);
      const personaName = personaSelect.options[personaSelect.selectedIndex].text;
      logToConsole(`Voice persona switched to: ${personaName}`, 'system');
      if (voice) voice.playBeep(850, 0.08);
    });
  }

  if (modalPersonaSelect) {
    modalPersonaSelect.addEventListener('change', () => {
      setPersona(modalPersonaSelect.value, false);
    });
  }

  // Gauges
  const cpuCircle = document.getElementById('cpuCircle');
  const cpuVal = document.getElementById('cpuVal');
  const cpuCores = document.getElementById('cpuCores');
  const ramCircle = document.getElementById('ramCircle');
  const ramVal = document.getElementById('ramVal');
  const ramDetail = document.getElementById('ramDetail');
  const diskCircle = document.getElementById('diskCircle');
  const diskVal = document.getElementById('diskVal');
  const diskDetail = document.getElementById('diskDetail');
  const batCircle = document.getElementById('batCircle');
  const batVal = document.getElementById('batVal');
  const batStatus = document.getElementById('batStatus');
  const uptimeVal = document.getElementById('uptimeVal');
  const modelVal = document.getElementById('modelVal');

  // Initialize Arc Reactor Visualizer
  const reactor = new ArcReactor('reactorCanvas');

  // Response Latency & Interruption State
  let commandStartTime = null;
  let isProcessing = false;

  function updateLatencyDisplay(ms) {
    if (!latencyVal || !latencyPill) return;
    const val = Math.max(1, Math.round(ms));
    latencyVal.textContent = `${val} ms`;
    latencyPill.className = 'latency-pill';
    if (val < 500) {
      latencyPill.classList.add('fast');
    } else if (val < 1200) {
      latencyPill.classList.add('medium');
    } else {
      latencyPill.classList.add('slow');
    }
  }

  function interruptCurrentTask() {
    const wasBusy = isProcessing || (voice && voice.isSpeaking());
    if (wasBusy) {
      if (voice) voice.stopSpeaking();
      stopWaveformAnimation();
      reactor.setState('idle');
      isProcessing = false;

      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'interrupt' }));
      }
      logToConsole('[INTERRUPT] Speech halted and ongoing processing cancelled.', 'system');
    }
  }

  // Initialize Voice Engine
  let voice;
  voice = new VoiceEngine(
    // On STT transcript recognized
    (transcript) => {
      commandInput.value = transcript;
      sendCommand(transcript);
    },
    // On STT state change
    (state) => {
      if (state === 'listening') {
        micToggleBtn.classList.add('listening');
        reactor.setState('listening');
      } else {
        micToggleBtn.classList.remove('listening');
        if (reactor.state === 'listening') {
          reactor.setState('idle');
        }
      }
    }
  );

  // Barge-in hook: immediately halt Jarvis speech when user starts talking
  voice.onUserSpeechStart = () => {
    interruptCurrentTask();
  };

  // Audio Waveform Animation Controller
  let waveInterval = null;
  function startWaveformAnimation() {
    stopWaveformAnimation();
    waveInterval = setInterval(() => {
      waveBars.forEach((bar) => {
        const h = Math.floor(Math.random() * 20) + 4;
        bar.style.height = `${h}px`;
      });
      reactor.setAudioLevel(Math.random() * 0.7 + 0.3);
    }, 90);
  }

  function stopWaveformAnimation() {
    if (waveInterval) {
      clearInterval(waveInterval);
      waveInterval = null;
    }
    waveBars.forEach((bar) => {
      bar.style.height = '4px';
    });
    reactor.setAudioLevel(0);
  }

  // Live Clock & Date
  function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toTimeString().split(' ')[0];
    const options = { month: 'long', day: '2-digit', year: 'numeric' };
    dateEl.textContent = now.toLocaleDateString('en-US', options).toUpperCase();
  }
  updateClock();
  setInterval(updateClock, 1000);

  // Append entry to Console Output
  function logToConsole(message, type = 'system') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const timestamp = new Date().toTimeString().split(' ')[0];
    entry.textContent = `[${timestamp}] ${message}`;
    consoleOutput.appendChild(entry);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
  }

  // Update SVG Circular Gauge
  function updateGauge(circleEl, valEl, percent) {
    const circumference = 251.2; // 2 * Math.PI * 40
    const clamped = Math.max(0, Math.min(100, percent));
    const offset = circumference - (clamped / 100) * circumference;
    circleEl.style.strokeDashoffset = offset;
    valEl.textContent = `${Math.round(clamped)}%`;
  }

  // Update System Telemetry
  function applyTelemetry(data) {
    if (!data || data.status === 'error') return;

    if (data.cpu) {
      updateGauge(cpuCircle, cpuVal, data.cpu.percent);
      cpuCores.textContent = `${data.cpu.cores} CORES // ${data.cpu.frequency_mhz} MHz`;
    }

    if (data.memory) {
      updateGauge(ramCircle, ramVal, data.memory.percent);
      ramDetail.textContent = `${data.memory.used_gb} / ${data.memory.total_gb} GB`;
    }

    if (data.disk) {
      updateGauge(diskCircle, diskVal, data.disk.percent);
      diskDetail.textContent = `${data.disk.used_gb} / ${data.disk.total_gb} GB`;
    }

    if (data.battery) {
      updateGauge(batCircle, batVal, data.battery.percent);
      batStatus.textContent = data.battery.power_plugged ? 'AC CONNECTED' : 'BATTERY POWER';
    }

    if (data.uptime) {
      uptimeVal.textContent = data.uptime;
    }
  }

  // ==========================================================================
  // WebSocket Connection
  // ==========================================================================
  let socket = null;
  let reconnectTimer = null;

  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    logToConsole(`Attempting neural bus link to ${wsUrl}...`, 'system');
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      statusDot.className = 'status-dot';
      statusLabel.textContent = 'ONLINE // SECURE';
      logToConsole('Neural link established with host system.', 'system');
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleServerMessage(msg);
      } catch (err) {
        console.error("Malformed WebSocket frame:", err);
      }
    };

    socket.onclose = () => {
      statusDot.className = 'status-dot offline';
      statusLabel.textContent = 'DISCONNECTED';
      logToConsole('Neural link severed. Retrying connection in 3 seconds...', 'error');
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(connectWebSocket, 3000);
      }
    };

    socket.onerror = (err) => {
      console.warn("WebSocket error:", err);
    };
  }

  function handleServerMessage(msg) {
    switch (msg.type) {
      case 'system_status':
        if (msg.voice_persona && msg.voice_persona !== currentPersona) {
          setPersona(msg.voice_persona, false);
        }
        if (msg.gemini_online) {
          aiModePill.className = 'ai-mode-pill online';
          aiModeText.textContent = 'GEMINI ONLINE';
          modelVal.textContent = (msg.model || 'GEMINI 3.1 FLASH LITE').toUpperCase();
        } else {
          aiModePill.className = 'ai-mode-pill';
          aiModeText.textContent = 'OFFLINE MODE';
          modelVal.textContent = 'LOCAL INTENT ENGINE';
        }
        break;

      case 'telemetry_update':
        applyTelemetry(msg.data);
        break;

      case 'jarvis_thinking':
        reactor.setState('thinking');
        break;

      case 'startup_greeting':
        const greetingText = msg.response || "Hey! It's me, J.A.R.V.I.S.! How can I help you today?";
        const greetingAudio = msg.audio_url || null;
        transcriptText.textContent = `"${greetingText}"`;
        logToConsole(`[STARTUP WISH]: ${greetingText}`, 'jarvis');
        reactor.setState('speaking');
        startWaveformAnimation();
        voice.speak(
          greetingText,
          greetingAudio,
          () => {},
          () => {
            stopWaveformAnimation();
            reactor.setState('idle');
          }
        );
        break;

      case 'interrupted':
        isProcessing = false;
        stopWaveformAnimation();
        reactor.setState('idle');
        logToConsole('[HALTED] Operation cancelled by user.', 'system');
        break;

      case 'tool_executed':
        logToConsole(`[EXECUTING TOOL] ${msg.tool}(${JSON.stringify(msg.args)})`, 'tool');
        voice.playBeep(987, 0.06);
        break;

      case 'jarvis_reply':
        isProcessing = false;
        const clientLatency = commandStartTime ? Math.round(performance.now() - commandStartTime) : null;
        commandStartTime = null;
        const finalLatency = (msg.latency_ms !== undefined && msg.latency_ms !== null) ? msg.latency_ms : clientLatency;
        if (finalLatency !== null) {
          updateLatencyDisplay(finalLatency);
        }

        const replyText = msg.response;
        const audioUrl = msg.audio_url || null;
        const lang = msg.lang || 'en';
        transcriptText.textContent = `"${replyText}"`;
        logToConsole(`[JARVIS (${lang.toUpperCase()})]: ${replyText}`, 'jarvis');

        // Trigger human neural speech synthesis
        reactor.setState('speaking');
        startWaveformAnimation();
        voice.speak(
          replyText,
          audioUrl,
          () => {
            // on speech start
          },
          () => {
            // on speech end
            stopWaveformAnimation();
            reactor.setState('idle');
          }
        );
        break;
    }
  }

  function sendCommand(text) {
    if (!text || !text.trim()) return;
    const clean = text.trim();

    // Interrupt any active voice playback or prior command
    interruptCurrentTask();

    isProcessing = true;
    commandStartTime = performance.now();

    logToConsole(`[USER]: ${clean}`, 'user');
    commandInput.value = '';
    reactor.setState('thinking');
    voice.playBeep(720, 0.05);

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'user_message',
        text: clean,
        persona: currentPersona
      }));
    } else {
      // HTTP fallback
      fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: clean, persona: currentPersona })
      })
      .then(res => res.json())
      .then(result => {
        handleServerMessage({
          type: 'jarvis_reply',
          response: result.response,
          tools_executed: result.tools_executed,
          mode: result.mode,
          lang: result.lang,
          audio_url: result.audio_url,
          latency_ms: result.latency_ms
        });
      })
      .catch(err => {
        logToConsole(`Command dispatch error: ${err}`, 'error');
        isProcessing = false;
        reactor.setState('idle');
      });
    }
  }


  // ==========================================================================
  // Event Listeners & Controls
  // ==========================================================================
  sendBtn.addEventListener('click', () => sendCommand(commandInput.value));

  commandInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendCommand(commandInput.value);
    } else if (voice && voice.isSpeaking()) {
      interruptCurrentTask();
    }
  });

  commandInput.addEventListener('input', () => {
    if (voice && voice.isSpeaking()) {
      interruptCurrentTask();
    }
  });

  micToggleBtn.addEventListener('click', () => {
    if (voice && (voice.isSpeaking() || isProcessing)) {
      interruptCurrentTask();
    }
    voice.toggleListening();
  });

  // Spacebar push-to-talk when not typing in input
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && document.activeElement !== commandInput && !settingsModal.classList.contains('active')) {
      e.preventDefault();
      if (voice && (voice.isSpeaking() || isProcessing)) {
        interruptCurrentTask();
      }
      voice.toggleListening();
    }
  });

  // Quick Action Chips
  document.querySelectorAll('.chip-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const cmd = btn.getAttribute('data-cmd');
      sendCommand(cmd);
    });
  });

  // Language Selector
  const langSelect = document.getElementById('langSelect');
  if (langSelect) {
    langSelect.addEventListener('change', () => {
      voice.setLanguage(langSelect.value);
      const langName = langSelect.options[langSelect.selectedIndex].text;
      logToConsole(`Voice recognition dialect switched to: ${langName}`, 'system');
      voice.playBeep(750, 0.08);
    });
  }

  clearLogBtn.addEventListener('click', () => {
    consoleOutput.innerHTML = '';
    logToConsole('Diagnostics log cleared.', 'system');
  });

  testVoiceBtn.addEventListener('click', () => {
    const currentLang = langSelect ? langSelect.value.split('-')[0] : 'en';
    let testMsg = "Acoustic neural channel verified, sir. All human speech synthesizers are online and operating with natural cadence.";
    if (currentPersona === 'indian_boy') {
      testMsg = "Arre bhai! Awaaz ekdum crystal clear hai! J.A.R.V.I.S. is ready to rock!";
    } else if (currentPersona === 'indian_girl') {
      testMsg = "Hey there! Voice check bilkul mast hai! J.A.R.V.I.S. is totally ready!";
    } else if (currentLang === 'hi') {
      testMsg = "आवाज की जांच सफल रही, सर। सभी प्रणालियाँ सुचारू रूप से कार्य कर रही हैं।";
    } else if (currentLang === 'es') {
      testMsg = "Canal acústico neuronal verificado, señor. Todos los sistemas funcionan a la perfección.";
    }

    transcriptText.textContent = `"${testMsg}"`;
    reactor.setState('speaking');
    startWaveformAnimation();
    const testAudioUrl = `/api/tts?text=${encodeURIComponent(testMsg)}&lang=${currentLang}&persona=${currentPersona}`;
    voice.speak(testMsg, testAudioUrl, null, () => {
      stopWaveformAnimation();
      reactor.setState('idle');
    });
  });


  // ==========================================================================
  // Settings Modal Handlers
  // ==========================================================================
  settingsBtn.addEventListener('click', () => {
    // Fetch current settings
    fetch('/api/status')
      .then(r => r.json())
      .then(data => {
        modelSelect.value = data.model || 'gemini-3.1-flash-lite';
        defaultCityInput.value = data.default_city || 'London';
        if (modalPersonaSelect) {
          modalPersonaSelect.value = data.voice_persona || currentPersona;
        }
        settingsModal.classList.add('active');
      })
      .catch(() => {
        settingsModal.classList.add('active');
      });
  });

  modalCloseBtn.addEventListener('click', () => settingsModal.classList.remove('active'));
  modalCancelBtn.addEventListener('click', () => settingsModal.classList.remove('active'));

  toggleVisBtn.addEventListener('click', () => {
    if (apiKeyInput.type === 'password') {
      apiKeyInput.type = 'text';
      toggleVisBtn.textContent = 'HIDE';
    } else {
      apiKeyInput.type = 'password';
      toggleVisBtn.textContent = 'SHOW';
    }
  });

  if (voiceSelect) {
    voiceSelect.addEventListener('change', () => {
      if (voiceSelect.value !== 'default') {
        voice.setVoiceByName(voiceSelect.value);
      }
    });
  }

  wakeWordToggle.addEventListener('change', () => {
    voice.wakeWordEnabled = wakeWordToggle.checked;
  });

  soundFxToggle.addEventListener('change', () => {
    voice.soundFxEnabled = soundFxToggle.checked;
  });

  modalSaveBtn.addEventListener('click', () => {
    const selectedPersona = modalPersonaSelect ? modalPersonaSelect.value : currentPersona;
    const payload = {
      model: modelSelect.value,
      default_city: defaultCityInput.value,
      voice_persona: selectedPersona
    };
    if (apiKeyInput.value.trim()) {
      payload.gemini_api_key = apiKeyInput.value.trim();
    }

    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(res => {
      setPersona(selectedPersona, false);
      settingsModal.classList.remove('active');
      logToConsole('System configuration updated successfully.', 'system');
      voice.playChime();
    })
    .catch(err => {
      alert("Failed to save settings: " + err);
    });
  });

  // Start WebSocket connection
  connectWebSocket();
});
