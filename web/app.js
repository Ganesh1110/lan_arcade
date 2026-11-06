/**
 * College LAN Arcade - Web Frontend Client (app.js)
 * Zero external dependencies. Works 100% offline.
 * Strict DOM sanitization using textContent for all user-controlled text.
 */

(function () {
  'use strict';

  // State
  const state = {
    token: null,
    playerId: null,
    playerName: localStorage.getItem('arcade_player_name') || '',
    isHost: false,
    currentGameId: '',
    currentView: null,
    isMyTurn: false,
    turnTimerInterval: null,
    timerSecondsRemaining: 0,
    soundEnabled: localStorage.getItem('arcade_sound_enabled') === 'true',
    eventSource: null,
    unreadChatCount: 0,
    chatOpen: false,
    nativeRenderers: {} // Extensible for Phase 2!
  };

  // DOM Elements
  const elements = {
    statusBanner: document.getElementById('statusBanner'),
    toastContainer: document.getElementById('toastContainer'),
    soundToggleBtn: document.getElementById('soundToggleBtn'),
    chatToggleBtn: document.getElementById('chatToggleBtn'),
    chatBadge: document.getElementById('chatBadge'),
    chatDrawer: document.getElementById('chatDrawer'),
    closeChatBtn: document.getElementById('closeChatBtn'),
    chatMessages: document.getElementById('chatMessages'),
    chatForm: document.getElementById('chatForm'),
    chatInput: document.getElementById('chatInput'),

    // Screens
    joinScreen: document.getElementById('joinScreen'),
    lobbyScreen: document.getElementById('lobbyScreen'),
    gameScreen: document.getElementById('gameScreen'),
    gameOverScreen: document.getElementById('gameOverScreen'),

    // Join Screen
    joinForm: document.getElementById('joinForm'),
    playerNameInput: document.getElementById('playerNameInput'),
    passwordGroup: document.getElementById('passwordGroup'),
    roomPasswordInput: document.getElementById('roomPasswordInput'),
    joinBtn: document.getElementById('joinBtn'),

    // Lobby Screen
    lobbyTitle: document.getElementById('lobbyTitle'),
    lobbyGameBadge: document.getElementById('lobbyGameBadge'),
    hostNotice: document.getElementById('hostNotice'),
    playerCount: document.getElementById('playerCount'),
    playersList: document.getElementById('playersList'),
    gameSelector: document.getElementById('gameSelector'),
    gameSelectorHint: document.getElementById('gameSelectorHint'),
    readyToggleBtn: document.getElementById('readyToggleBtn'),
    hostStartBtn: document.getElementById('hostStartBtn'),

    // Game Screen
    turnBanner: document.getElementById('turnBanner'),
    turnIndicatorIcon: document.getElementById('turnIndicatorIcon'),
    turnIndicatorText: document.getElementById('turnIndicatorText'),
    timerContainer: document.getElementById('timerContainer'),
    turnTimerText: document.getElementById('turnTimerText'),
    viewToggleBtn: document.getElementById('viewToggleBtn'),
    nativeBoardContainer: document.getElementById('nativeBoardContainer'),
    ansiContainer: document.getElementById('ansiContainer'),
    ansiDashboard: document.getElementById('ansiDashboard'),
    promptText: document.getElementById('promptText'),
    actionForm: document.getElementById('actionForm'),
    actionInput: document.getElementById('actionInput'),
    actionSubmitBtn: document.getElementById('actionSubmitBtn'),
    surrenderBtn: document.getElementById('surrenderBtn'),

    // Game Over Screen
    gameOverTitle: document.getElementById('gameOverTitle'),
    gameOverMessage: document.getElementById('gameOverMessage'),
    rematchStatus: document.getElementById('rematchStatus'),
    rematchVotesText: document.getElementById('rematchVotesText'),
    rematchBtn: document.getElementById('rematchBtn'),
    leaveBtn: document.getElementById('leaveBtn')
  };

  // Sound Synthesizer via Web Audio API
  let audioCtx = null;
  function getAudioContext() {
    if (!audioCtx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) audioCtx = new AudioCtx();
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function playSound(type) {
    if (!state.soundEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      const now = ctx.currentTime;

      if (type === 'turn') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, now); // D5
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.15); // A5
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        osc.start(now);
        osc.stop(now + 0.2);
      } else if (type === 'win') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(523.25, now); // C5
        osc.frequency.setValueAtTime(659.25, now + 0.1); // E5
        osc.frequency.setValueAtTime(783.99, now + 0.2); // G5
        osc.frequency.setValueAtTime(1046.50, now + 0.3); // C6
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
        osc.start(now);
        osc.stop(now + 0.6);
      } else if (type === 'error') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(220, now);
        osc.frequency.setValueAtTime(160, now + 0.1);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
        osc.start(now);
        osc.stop(now + 0.25);
      }
    } catch (_) {}
  }

  // Toast Notifications
  function showToast(message, type = 'error', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message; // Safe text
    elements.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      toast.style.transition = 'opacity 0.2s, transform 0.2s';
      setTimeout(() => toast.remove(), 250);
    }, duration);
  }

  // Status Banner
  function showStatusBanner(text, type = '', autoHideMs = 0) {
    elements.statusBanner.textContent = text;
    elements.statusBanner.className = `status-banner ${type}`.trim();
    if (autoHideMs > 0) {
      setTimeout(() => {
        elements.statusBanner.classList.add('hidden');
      }, autoHideMs);
    }
  }

  // Screen Switcher
  function showScreen(name) {
    elements.joinScreen.classList.add('hidden');
    elements.lobbyScreen.classList.add('hidden');
    elements.gameScreen.classList.add('hidden');
    elements.gameOverScreen.classList.add('hidden');

    if (name === 'join') {
      elements.joinScreen.classList.remove('hidden');
      elements.chatToggleBtn.classList.add('hidden');
    } else if (name === 'lobby') {
      elements.lobbyScreen.classList.remove('hidden');
      elements.chatToggleBtn.classList.remove('hidden');
    } else if (name === 'game') {
      elements.gameScreen.classList.remove('hidden');
      elements.chatToggleBtn.classList.remove('hidden');
    } else if (name === 'gameover') {
      elements.gameOverScreen.classList.remove('hidden');
      elements.chatToggleBtn.classList.remove('hidden');
    }
  }

  // API Helpers
  async function apiRequest(endpoint, method = 'POST', data = null) {
    const headers = {
      'Content-Type': 'application/json'
    };
    if (state.token) {
      headers['X-Session-Token'] = state.token;
    }
    const options = {
      method,
      headers
    };
    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }
    const resp = await fetch(endpoint, options);
    const result = await resp.json().catch(() => ({ ok: false, error: 'Network response was not JSON' }));
    if (!resp.ok) {
      throw new Error(result.error || `HTTP ${resp.status}`);
    }
    return result;
  }

  // Connect to SSE stream
  function connectSSE() {
    if (state.eventSource) {
      state.eventSource.close();
      state.eventSource = null;
    }

    const sse = new EventSource('/api/events');
    state.eventSource = sse;

    sse.onopen = function () {
      showStatusBanner('Connected 🟢', 'success', 2000);
    };

    sse.onerror = function () {
      showStatusBanner('Reconnecting to server... 🟡', 'warning');
    };

    sse.onmessage = function (e) {
      try {
        const msg = JSON.parse(e.data);
        handleServerMessage(msg);
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
      }
    };
  }

  // Main Message Router
  function handleServerMessage(msg) {
    const kind = msg.type;

    if (kind === 'lobby') {
      renderLobby(msg);
    } else if (kind === 'start') {
      handleMatchStart(msg);
    } else if (kind === 'turn') {
      handleTurnUpdate(msg);
    } else if (kind === 'action_result') {
      handleActionResult(msg);
    } else if (kind === 'chat') {
      appendChatMessage(msg);
    } else if (kind === 'notice') {
      handleNotice(msg);
    } else if (kind === 'error') {
      playSound('error');
      showToast(msg.message, 'error');
    } else if (kind === 'end') {
      handleGameOver(msg);
    } else if (kind === 'rematch') {
      showToast(msg.message || 'Rematch starting!', 'info');
      elements.rematchBtn.disabled = false;
      elements.rematchBtn.textContent = 'Rematch 🔄';
    } else if (kind === 'host_exit') {
      showToast(msg.message || 'Host returned to main menu.', 'info');
      showScreen('join');
    } else if (kind === 'disconnect') {
      showToast(msg.message || 'Disconnected from host.', 'error');
      showScreen('join');
    }
  }

  // Renderers for Game Lifecycle
  function renderLobby(msg) {
    showScreen('lobby');
    const players = msg.players || [];
    elements.playerCount.textContent = players.length;

    // Clear list safely
    elements.playersList.textContent = '';

    let hostExists = false;
    players.forEach((p, idx) => {
      const isHost = Boolean(p.host);
      const isYou = p.id === state.playerId || p.name === state.playerName;
      if (isYou && isHost) state.isHost = true;
      if (isHost) hostExists = true;

      const li = document.createElement('li');
      li.className = 'player-item';

      const left = document.createElement('div');
      left.className = 'player-name-wrapper';

      const nameSpan = document.createElement('span');
      nameSpan.textContent = `${idx + 1}. ${p.name}`;
      left.appendChild(nameSpan);

      if (isHost) {
        const hSpan = document.createElement('span');
        hSpan.className = 'tag-host';
        hSpan.textContent = '[HOST]';
        left.appendChild(hSpan);
      }
      if (isYou) {
        const ySpan = document.createElement('span');
        ySpan.className = 'tag-you';
        ySpan.textContent = '(you)';
        left.appendChild(ySpan);
      }
      li.appendChild(left);

      const pill = document.createElement('span');
      const isReady = p.ready !== false;
      pill.className = `ready-pill ${isReady ? 'ready' : 'waiting'}`;
      pill.textContent = isReady ? 'READY' : 'WAITING';
      li.appendChild(pill);

      elements.playersList.appendChild(li);
    });

    if (state.isHost) {
      elements.hostNotice.classList.remove('hidden');
      elements.gameSelector.disabled = false;
      elements.gameSelectorHint.textContent = 'You are the host. Choose the game below.';
      elements.hostStartBtn.classList.remove('hidden');
    } else {
      elements.hostNotice.classList.add('hidden');
      elements.gameSelector.disabled = true;
      elements.gameSelectorHint.textContent = 'Only the host can change games.';
      elements.hostStartBtn.classList.add('hidden');
    }
  }

  function handleMatchStart(msg) {
    showScreen('game');
    state.currentGameId = msg.game_id || '';
    state.currentView = msg.view || null;
    elements.rematchBtn.disabled = false;
    elements.rematchBtn.textContent = 'Rematch 🔄';

    renderGameView(msg);
  }

  function handleTurnUpdate(msg) {
    state.currentGameId = msg.game_id || state.currentGameId;
    state.currentView = msg.view || null;
    const currentPid = msg.player_id;
    const currentName = msg.player_name || 'Player';
    state.isMyTurn = currentPid === state.playerId;

    // Turn Banner styling
    if (state.isMyTurn) {
      elements.turnBanner.classList.add('your-turn');
      elements.turnIndicatorIcon.textContent = '▶';
      elements.turnIndicatorText.textContent = `YOUR TURN (${currentName})`;
      elements.actionInput.disabled = false;
      elements.actionSubmitBtn.disabled = false;
      elements.actionInput.focus();
      playSound('turn');
    } else {
      elements.turnBanner.classList.remove('your-turn');
      elements.turnIndicatorIcon.textContent = '⏳';
      elements.turnIndicatorText.textContent = `Waiting for ${currentName}...`;
      elements.actionInput.disabled = true;
      elements.actionSubmitBtn.disabled = true;
    }

    // Turn countdown timer
    const timeoutSec = msg.turn_timeout || 45;
    startTurnTimer(timeoutSec);

    renderGameView(msg);
  }

  function handleActionResult(msg) {
    state.currentGameId = msg.game_id || state.currentGameId;
    state.currentView = msg.view || null;
    renderGameView(msg);
  }

  function renderGameView(msg) {
    // 1. Update Prompt Text safely
    const prompt = msg.prompt || 'Enter your move:';
    elements.promptText.textContent = prompt;

    // 2. Render ANSI Dashboard
    if (msg.rendered_html) {
      elements.ansiDashboard.innerHTML = msg.rendered_html; // Only contains whitelisted safe span tags
    }

    // 3. Delegate to Phase 2 native graphical renderer if registered
    const nativeRenderer = state.nativeRenderers[state.currentGameId];
    if (nativeRenderer && state.currentView) {
      elements.nativeBoardContainer.classList.remove('hidden');
      elements.viewToggleBtn.classList.remove('hidden');
      nativeRenderer(elements.nativeBoardContainer, state.currentView, submitActionString);
    } else {
      elements.nativeBoardContainer.classList.add('hidden');
      elements.ansiContainer.classList.remove('hidden');
      elements.viewToggleBtn.classList.add('hidden');
    }
  }

  function handleGameOver(msg) {
    stopTurnTimer();
    playSound('win');
    showScreen('gameover');

    const message = msg.message || 'Game Over!';
    const winners = msg.winners || [];
    elements.gameOverTitle.textContent = winners.length > 0 ? `🏆 ${winners.join(', ')} Wins!` : 'Match Complete';
    elements.gameOverMessage.textContent = message;
    elements.rematchVotesText.textContent = 'Click Rematch to vote for another round!';
  }

  function handleNotice(msg) {
    const text = msg.message || '';
    if (text) {
      showToast(text, 'info');
      appendChatMessage({ sender: 'Arcade', text });
    }
  }

  // Turn Countdown Timer
  function startTurnTimer(seconds) {
    stopTurnTimer();
    state.timerSecondsRemaining = seconds;
    elements.timerContainer.classList.remove('hidden');
    elements.turnTimerText.textContent = seconds;

    state.turnTimerInterval = setInterval(() => {
      state.timerSecondsRemaining--;
      if (state.timerSecondsRemaining <= 0) {
        elements.turnTimerText.textContent = '0';
        stopTurnTimer();
      } else {
        elements.turnTimerText.textContent = state.timerSecondsRemaining;
      }
    }, 1000);
  }

  function stopTurnTimer() {
    if (state.turnTimerInterval) {
      clearInterval(state.turnTimerInterval);
      state.turnTimerInterval = null;
    }
    elements.timerContainer.classList.add('hidden');
  }

  // Chat Log (Safe textContent)
  function appendChatMessage(msg) {
    const sender = msg.sender || 'Player';
    const text = msg.text || '';
    if (!text) return;

    const div = document.createElement('div');
    div.className = 'chat-entry';

    const senderStrong = document.createElement('strong');
    senderStrong.textContent = `${sender}: `;
    div.appendChild(senderStrong);

    const textSpan = document.createElement('span');
    textSpan.textContent = text;
    div.appendChild(textSpan);

    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    if (!state.chatOpen) {
      state.unreadChatCount++;
      elements.chatBadge.textContent = state.unreadChatCount;
      elements.chatBadge.classList.remove('hidden');
    }
  }

  // Action submission helper (shared by text form & native boards)
  async function submitActionString(actionStr) {
    if (!actionStr && actionStr !== 0) return;
    try {
      await apiRequest('/api/action', 'POST', { action: String(actionStr) });
      elements.actionInput.value = '';
    } catch (err) {
      playSound('error');
      showToast(err.message, 'error');
    }
  }

  // Event Listeners Setup
  function setupEventListeners() {
    // Sound Toggle
    elements.soundToggleBtn.addEventListener('click', () => {
      state.soundEnabled = !state.soundEnabled;
      localStorage.setItem('arcade_sound_enabled', String(state.soundEnabled));
      elements.soundToggleBtn.textContent = state.soundEnabled ? '🔔' : '🔇';
      if (state.soundEnabled) playSound('turn');
    });
    elements.soundToggleBtn.textContent = state.soundEnabled ? '🔔' : '🔇';

    // Chat Drawer Toggle
    elements.chatToggleBtn.addEventListener('click', () => {
      state.chatOpen = true;
      state.unreadChatCount = 0;
      elements.chatBadge.classList.add('hidden');
      elements.chatDrawer.classList.remove('closed');
      elements.chatInput.focus();
    });

    elements.closeChatBtn.addEventListener('click', () => {
      state.chatOpen = false;
      elements.chatDrawer.classList.add('closed');
    });

    // Chat Submit
    elements.chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = elements.chatInput.value.trim();
      if (!text) return;
      try {
        await apiRequest('/api/chat', 'POST', { text });
        elements.chatInput.value = '';
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Join Form Submit
    elements.joinForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = elements.playerNameInput.value.trim();
      if (!name) return;

      const password = elements.roomPasswordInput.value.trim();
      elements.joinBtn.disabled = true;
      elements.joinBtn.textContent = 'Connecting...';

      try {
        const res = await apiRequest('/api/join', 'POST', { name, password });
        state.token = res.token;
        state.playerId = res.player_id;
        state.playerName = res.name;
        localStorage.setItem('arcade_player_name', res.name);

        connectSSE();
      } catch (err) {
        playSound('error');
        showToast(err.message, 'error');
        elements.joinBtn.disabled = false;
        elements.joinBtn.textContent = 'Enter Arcade';
      }
    });

    // Ready Toggle
    elements.readyToggleBtn.addEventListener('click', async () => {
      try {
        await apiRequest('/api/ready');
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Host Start Game
    elements.hostStartBtn.addEventListener('click', async () => {
      try {
        await apiRequest('/api/start_game');
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Host Select Game
    elements.gameSelector.addEventListener('change', async () => {
      const gId = elements.gameSelector.value;
      if (!gId) return;
      try {
        await apiRequest('/api/select_game', 'POST', { game: gId });
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Action Input Form
    elements.actionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const val = elements.actionInput.value.trim();
      if (!val) return;
      await submitActionString(val);
    });

    // Surrender Button
    elements.surrenderBtn.addEventListener('click', async () => {
      if (confirm('Are you sure you want to surrender this match?')) {
        try {
          await apiRequest('/api/surrender');
        } catch (err) {
          showToast(err.message, 'error');
        }
      }
    });

    // Rematch Button
    elements.rematchBtn.addEventListener('click', async () => {
      try {
        await apiRequest('/api/rematch');
        elements.rematchBtn.disabled = true;
        elements.rematchBtn.textContent = 'Vote Sent ✅';
        elements.rematchVotesText.textContent = 'Voted! Waiting for other players...';
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Leave Button
    elements.leaveBtn.addEventListener('click', async () => {
      try {
        await apiRequest('/api/leave');
      } catch (_) {}
      if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
      }
      showScreen('join');
      elements.joinBtn.disabled = false;
      elements.joinBtn.textContent = 'Enter Arcade';
    });

    // View Toggle Button (between Native and Terminal view)
    elements.viewToggleBtn.addEventListener('click', () => {
      const isNativeHidden = elements.nativeBoardContainer.classList.contains('hidden');
      if (isNativeHidden) {
        elements.nativeBoardContainer.classList.remove('hidden');
        elements.ansiContainer.classList.add('hidden');
        elements.viewToggleBtn.textContent = 'Switch to Terminal View';
      } else {
        elements.nativeBoardContainer.classList.add('hidden');
        elements.ansiContainer.classList.remove('hidden');
        elements.viewToggleBtn.textContent = 'Switch to Graphic Board';
      }
    });

    // Initial name prefill
    if (state.playerName) {
      elements.playerNameInput.value = state.playerName;
    }
  }

  // Load server info on startup
  async function checkServerInfo() {
    try {
      const info = await apiRequest('/api/info', 'GET');
      if (info.requires_password) {
        elements.passwordGroup.classList.remove('hidden');
        elements.roomPasswordInput.required = true;
      }

      // Populate game selector
      if (info.games && Array.isArray(info.games)) {
        elements.gameSelector.textContent = '';
        info.games.forEach((g) => {
          const opt = document.createElement('option');
          opt.value = g.id;
          opt.textContent = `${g.name} (${g.min}–${g.max} players)`;
          elements.gameSelector.appendChild(opt);
        });
      }
    } catch (_) {}
  }

  // Expose state and register helper globally for Phase 2 game modules
  window.LANArcade = {
    state,
    submitAction: submitActionString,
    registerRenderer: function (gameId, renderFn) {
      state.nativeRenderers[gameId] = renderFn;
    }
  };

  // Initialize
  setupEventListeners();
  checkServerInfo();
})();
