/**
 * OPERATION SHADOWSTRIKE - PROJECTOR PRESENTATION DECK CONTROLLER
 * ALGO CLUB | PSIT KANPUR
 * 5 Slides: Intro -> Round 1 (8m) -> Round 2 (8m) -> Round 3 (11m) -> Round 4 (10m)
 * Supports Dark & Light Modes with Top Toggle
 */

(function () {
  'use strict';

  // --- AUDIO SYNTHESIS ENGINE (Web Audio API - 100% Offline) ---
  class SoundFX {
    constructor() {
      this.ctx = null;
      this.muted = false;
    }

    init() {
      if (!this.ctx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioContext();
      }
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playClick() {
      if (this.muted) return;
      this.init();
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1320, this.ctx.currentTime + 0.04);
      gain.gain.setValueAtTime(0.06, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.04);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.04);
    }

    playTimeUp() {
      this.init();
      const now = this.ctx.currentTime;
      [440, 660, 880, 1100].forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + idx * 0.12);
        gain.gain.setValueAtTime(0.18, now + idx * 0.12);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.12 + 0.3);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now + idx * 0.12);
        osc.stop(now + idx * 0.12 + 0.3);
      });
    }
  }

  const sfx = new SoundFX();

  // --- THEME ENGINE (Dark / Light Mode) ---
  const btnThemeToggle = document.getElementById('btn-theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  const themeLabel = document.getElementById('theme-label');

  function applyTheme(isLight) {
    if (isLight) {
      document.body.classList.add('theme-light');
      if (themeIcon) themeIcon.textContent = '🌙';
      if (themeLabel) themeLabel.textContent = 'Dark Mode';
    } else {
      document.body.classList.remove('theme-light');
      if (themeIcon) themeIcon.textContent = '☀️';
      if (themeLabel) themeLabel.textContent = 'Light Mode';
    }
  }

  function toggleTheme() {
    const isLight = document.body.classList.contains('theme-light');
    const newTheme = !isLight;
    applyTheme(newTheme);
    localStorage.setItem('shadowstrike_theme', newTheme ? 'light' : 'dark');
    sfx.playClick();
  }

  // --- ROUND TIMERS CONFIGURATION ---
  const ROUNDS_CONFIG = {
    1: { durationSec: 8 * 60, remaining: 8 * 60, interval: null, running: false, label: "8m" },
    2: { durationSec: 8 * 60, remaining: 8 * 60, interval: null, running: false, label: "8m" },
    3: { durationSec: 11 * 60, remaining: 11 * 60, interval: null, running: false, label: "11m" },
    4: { durationSec: 10 * 60, remaining: 10 * 60, interval: null, running: false, label: "10m" },
  };

  // --- SLIDE NAVIGATION DECK ---
  let currentSlide = 0;
  const totalSlides = 5;

  const slides = [
    document.getElementById('slide-0'),
    document.getElementById('slide-1'),
    document.getElementById('slide-2'),
    document.getElementById('slide-3'),
    document.getElementById('slide-4'),
  ];

  const navPills = [
    document.getElementById('pill-slide-0'),
    document.getElementById('pill-slide-1'),
    document.getElementById('pill-slide-2'),
    document.getElementById('pill-slide-3'),
    document.getElementById('pill-slide-4'),
  ];

  const btnPrev = document.getElementById('btn-deck-prev');
  const btnNext = document.getElementById('btn-deck-next');
  const btnFs = document.getElementById('btn-deck-fs');

  function goToSlide(index) {
    if (index < 0 || index >= totalSlides) return;

    slides[currentSlide].classList.remove('active');
    if (navPills[currentSlide]) navPills[currentSlide].classList.remove('active');

    currentSlide = index;
    slides[currentSlide].classList.add('active');
    if (navPills[currentSlide]) navPills[currentSlide].classList.add('active');

    if (btnPrev) btnPrev.disabled = (currentSlide === 0);
    if (btnNext) {
      if (currentSlide === totalSlides - 1) {
        btnNext.innerHTML = 'Finish <span>✓</span>';
      } else {
        btnNext.innerHTML = 'Next <span>→</span>';
      }
    }

    sfx.playClick();
  }

  function nextSlide() {
    if (currentSlide < totalSlides - 1) {
      goToSlide(currentSlide + 1);
    }
  }

  function prevSlide() {
    if (currentSlide > 0) {
      goToSlide(currentSlide - 1);
    }
  }

  // --- REVERSE TIMER CONTROLLER ---
  function formatTime(totalSeconds) {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  function updateTimerDisplay(roundNum) {
    const config = ROUNDS_CONFIG[roundNum];
    const displayEl = document.getElementById(`timer-digits-${roundNum}`);
    const progressEl = document.getElementById(`timer-progress-${roundNum}`);

    if (displayEl) {
      displayEl.textContent = formatTime(config.remaining);

      displayEl.classList.remove('warning', 'danger');
      if (config.remaining <= 30 && config.remaining > 0) {
        displayEl.classList.add('danger');
      } else if (config.remaining <= 60 && config.remaining > 0) {
        displayEl.classList.add('warning');
      } else if (config.remaining === 0) {
        displayEl.classList.add('danger');
        displayEl.textContent = "00:00 TIME'S UP!";
      }
    }

    if (progressEl) {
      const pct = (config.remaining / config.durationSec) * 100;
      progressEl.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    }
  }

  function toggleRoundTimer(roundNum) {
    const config = ROUNDS_CONFIG[roundNum];
    const btn = document.getElementById(`btn-start-round-${roundNum}`);
    const displayEl = document.getElementById(`timer-digits-${roundNum}`);

    if (config.running) {
      // Pause
      clearInterval(config.interval);
      config.running = false;
      if (btn) {
        btn.innerHTML = `<span class="btn-icon">▶</span><span>Resume Timer</span>`;
        btn.classList.remove('is-running');
      }
      if (displayEl) displayEl.classList.remove('running');
    } else {
      // Start
      if (config.remaining <= 0) {
        config.remaining = config.durationSec;
      }
      config.running = true;
      if (btn) {
        btn.innerHTML = `<span class="btn-icon">⏸</span><span>Pause Timer</span>`;
        btn.classList.add('is-running');
      }
      if (displayEl) displayEl.classList.add('running');

      config.interval = setInterval(() => {
        if (config.remaining > 0) {
          config.remaining--;
          updateTimerDisplay(roundNum);

          if (config.remaining === 0) {
            clearInterval(config.interval);
            config.running = false;
            if (btn) {
              btn.innerHTML = `<span class="btn-icon">🔄</span><span>Restart Timer</span>`;
              btn.classList.remove('is-running');
            }
            if (displayEl) displayEl.classList.remove('running');
            sfx.playTimeUp();
          }
        }
      }, 1000);
    }
    sfx.playClick();
  }

  function resetRoundTimer(roundNum) {
    const config = ROUNDS_CONFIG[roundNum];
    const btn = document.getElementById(`btn-start-round-${roundNum}`);
    const displayEl = document.getElementById(`timer-digits-${roundNum}`);

    clearInterval(config.interval);
    config.running = false;
    config.remaining = config.durationSec;

    if (btn) {
      btn.innerHTML = `<span class="btn-icon">▶</span><span>Start ${config.label} Timer</span>`;
      btn.classList.remove('is-running');
    }
    if (displayEl) displayEl.classList.remove('running');
    updateTimerDisplay(roundNum);
    sfx.playClick();
  }

  function addOneMinute(roundNum) {
    const config = ROUNDS_CONFIG[roundNum];
    config.remaining += 60;
    updateTimerDisplay(roundNum);
    sfx.playClick();
  }

  function subtractOneMinute(roundNum) {
    const config = ROUNDS_CONFIG[roundNum];
    if (config.remaining > 60) {
      config.remaining -= 60;
    } else {
      config.remaining = 0;
    }
    updateTimerDisplay(roundNum);
    sfx.playClick();
  }

  // --- FULLSCREEN TOGGLE ---
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => console.log(err));
      if (btnFs) btnFs.textContent = '✕';
    } else {
      if (document.exitFullscreen) document.exitFullscreen();
      if (btnFs) btnFs.textContent = '⛶';
    }
    sfx.playClick();
  }

  // --- WAYGROUND 6-DIGIT JOIN CODE CONTROLLER ---
  function initJoinCodes() {
    for (let r = 1; r <= 4; r++) {
      const wrapper = document.getElementById(`jc-wrapper-${r}`);
      const parentCard = wrapper ? wrapper.closest('.stage-join-code-block') : null;
      const slots = [];
      for (let i = 0; i < 6; i++) {
        const slot = document.getElementById(`jc-${r}-${i}`);
        if (slot) slots.push(slot);
      }

      const btnCopy = document.getElementById(`btn-copy-code-${r}`);
      const btnClear = document.getElementById(`btn-clear-code-${r}`);

      function getCode() {
        return slots.map(s => s.value.trim()).join('');
      }

      function updateState() {
        const full = getCode();
        localStorage.setItem(`shadowstrike_code_${r}`, full);
        slots.forEach(s => {
          if (s.value.trim()) s.classList.add('has-val');
          else s.classList.remove('has-val');
        });
        if (parentCard) {
          if (full.length === 6) {
            parentCard.classList.add('is-filled');
          } else {
            parentCard.classList.remove('is-filled');
          }
        }
      }

      // Restore saved code from localStorage
      const saved = localStorage.getItem(`shadowstrike_code_${r}`);
      if (saved && saved.length > 0) {
        for (let i = 0; i < Math.min(slots.length, saved.length); i++) {
          slots[i].value = saved[i];
        }
        updateState();
      }

      // Slot event listeners
      slots.forEach((slot, idx) => {
        slot.addEventListener('focus', () => {
          slot.select();
        });

        slot.addEventListener('input', () => {
          let val = slot.value.toUpperCase().replace(/[^0-9A-Z]/g, '');
          if (val.length > 1) {
            val = val.slice(-1);
          }
          slot.value = val;
          updateState();

          if (val && idx < 5) {
            slots[idx + 1].focus();
            slots[idx + 1].select();
          }
          sfx.playClick();
        });

        slot.addEventListener('keydown', (e) => {
          if (e.key === 'Backspace') {
            if (!slot.value && idx > 0) {
              e.preventDefault();
              slots[idx - 1].value = '';
              slots[idx - 1].focus();
              updateState();
            }
          } else if (e.key === 'ArrowLeft' && idx > 0) {
            e.preventDefault();
            slots[idx - 1].focus();
            slots[idx - 1].select();
          } else if (e.key === 'ArrowRight' && idx < 5) {
            e.preventDefault();
            slots[idx + 1].focus();
            slots[idx + 1].select();
          }
        });

        slot.addEventListener('paste', (e) => {
          e.preventDefault();
          const pasted = (e.clipboardData || window.clipboardData).getData('text');
          const clean = pasted.toUpperCase().replace(/[^0-9A-Z]/g, '');
          if (!clean) return;

          for (let i = 0; i < slots.length; i++) {
            slots[i].value = clean[i] || '';
          }
          updateState();
          const nextFocus = Math.min(slots.length - 1, clean.length);
          slots[nextFocus].focus();
          slots[nextFocus].select();
          sfx.playClick();
        });
      });

      // Clear button
      if (btnClear) {
        btnClear.addEventListener('click', () => {
          slots.forEach(s => s.value = '');
          updateState();
          slots[0].focus();
          sfx.playClick();
        });
      }

      // Copy button
      if (btnCopy) {
        btnCopy.addEventListener('click', () => {
          const code = getCode();
          if (code) {
            navigator.clipboard.writeText(code).then(() => {
              btnCopy.textContent = 'Copied! ✓';
              setTimeout(() => {
                btnCopy.textContent = 'Copy';
              }, 1800);
            }).catch(() => {});
          }
          sfx.playClick();
        });
      }
    }
  }

  // --- STAGE VIEW MODES CONTROLLER (SPLIT / CODE ONLY / TIMER ONLY) ---
  const roundViewModes = { 1: 'split', 2: 'split', 3: 'split', 4: 'split' };

  function setStageViewMode(roundNum, mode, playAudio = true) {
    const pane = document.getElementById(`command-pane-${roundNum}`);
    const btnSplit = document.getElementById(`btn-view-split-${roundNum}`);
    const btnCode = document.getElementById(`btn-view-code-${roundNum}`);
    const btnTimer = document.getElementById(`btn-view-timer-${roundNum}`);
    const btnToggleTimer = document.getElementById(`btn-toggle-timer-${roundNum}`);
    const btnToggleCode = document.getElementById(`btn-toggle-code-${roundNum}`);

    if (!pane) return;

    roundViewModes[roundNum] = mode;
    localStorage.setItem(`shadowstrike_viewmode_${roundNum}`, mode);

    // Reset classes
    pane.classList.remove('mode-code-only', 'mode-timer-only');
    [btnSplit, btnCode, btnTimer].forEach(b => { if (b) b.classList.remove('active'); });

    if (mode === 'code') {
      pane.classList.add('mode-code-only');
      if (btnCode) btnCode.classList.add('active');
      if (btnToggleTimer) btnToggleTimer.textContent = 'Show Timer';
      if (btnToggleCode) btnToggleCode.textContent = 'Hide Code';
    } else if (mode === 'timer') {
      pane.classList.add('mode-timer-only');
      if (btnTimer) btnTimer.classList.add('active');
      if (btnToggleCode) btnToggleCode.textContent = 'Show Code';
      if (btnToggleTimer) btnToggleTimer.textContent = 'Hide Timer';
    } else {
      // Split view (default)
      if (btnSplit) btnSplit.classList.add('active');
      if (btnToggleTimer) btnToggleTimer.textContent = 'Hide Timer';
      if (btnToggleCode) btnToggleCode.textContent = 'Hide Code';
    }

    if (playAudio) sfx.playClick();
  }

  function cycleStageViewMode(roundNum) {
    const current = roundViewModes[roundNum] || 'split';
    if (current === 'split') {
      setStageViewMode(roundNum, 'code');
    } else if (current === 'code') {
      setStageViewMode(roundNum, 'timer');
    } else {
      setStageViewMode(roundNum, 'split');
    }
  }

  function initViewModes() {
    for (let r = 1; r <= 4; r++) {
      const btnSplit = document.getElementById(`btn-view-split-${r}`);
      const btnCode = document.getElementById(`btn-view-code-${r}`);
      const btnTimer = document.getElementById(`btn-view-timer-${r}`);
      const btnToggleTimer = document.getElementById(`btn-toggle-timer-${r}`);
      const btnToggleCode = document.getElementById(`btn-toggle-code-${r}`);

      if (btnSplit) btnSplit.addEventListener('click', () => setStageViewMode(r, 'split'));
      if (btnCode) btnCode.addEventListener('click', () => setStageViewMode(r, 'code'));
      if (btnTimer) btnTimer.addEventListener('click', () => setStageViewMode(r, 'timer'));

      if (btnToggleTimer) {
        btnToggleTimer.addEventListener('click', () => {
          const current = roundViewModes[r] || 'split';
          if (current === 'code') {
            setStageViewMode(r, 'split');
          } else {
            setStageViewMode(r, 'code');
          }
        });
      }

      if (btnToggleCode) {
        btnToggleCode.addEventListener('click', () => {
          const current = roundViewModes[r] || 'split';
          if (current === 'timer') {
            setStageViewMode(r, 'split');
          } else {
            setStageViewMode(r, 'timer');
          }
        });
      }

      // Restore saved view mode
      const saved = localStorage.getItem(`shadowstrike_viewmode_${r}`) || 'split';
      setStageViewMode(r, saved, false);
    }
  }

  // --- INITIALIZATION ---
  function init() {
    // 1. Initial theme from localStorage
    const savedTheme = localStorage.getItem('shadowstrike_theme');
    applyTheme(savedTheme === 'light');

    if (btnThemeToggle) {
      btnThemeToggle.addEventListener('click', toggleTheme);
    }

    // 2. Start at Slide 0
    goToSlide(0);

    // 3. Initialize Round Timers
    for (let r = 1; r <= 4; r++) {
      updateTimerDisplay(r);

      const startBtn = document.getElementById(`btn-start-round-${r}`);
      const resetBtn = document.getElementById(`btn-reset-round-${r}`);
      const subBtn = document.getElementById(`btn-sub1-round-${r}`);
      const addBtn = document.getElementById(`btn-add1-round-${r}`);

      if (startBtn) startBtn.addEventListener('click', () => toggleRoundTimer(r));
      if (resetBtn) resetBtn.addEventListener('click', () => resetRoundTimer(r));
      if (subBtn) subBtn.addEventListener('click', () => subtractOneMinute(r));
      if (addBtn) addBtn.addEventListener('click', () => addOneMinute(r));
    }

    // 4. Initialize Join Codes for Rounds 1-4
    initJoinCodes();

    // 5. Initialize Stage View Modes (Split / Code / Timer)
    initViewModes();

    // 6. Navigation bindings
    if (btnPrev) btnPrev.addEventListener('click', prevSlide);
    if (btnNext) btnNext.addEventListener('click', nextSlide);
    if (btnFs) btnFs.addEventListener('click', toggleFullscreen);

    navPills.forEach((pill, idx) => {
      if (pill) {
        pill.addEventListener('click', () => goToSlide(idx));
      }
    });

    // 7. Keyboard Navigation (ignoring inputs)
    window.addEventListener('keydown', (e) => {
      const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      if (activeTag === 'input' || activeTag === 'textarea') {
        return;
      }

      const key = e.key;

      if (key === 'ArrowRight' || key === 'PageDown' || key === 'Enter') {
        e.preventDefault();
        nextSlide();
      } else if (key === 'ArrowLeft' || key === 'PageUp' || key === 'Backspace') {
        e.preventDefault();
        prevSlide();
      } else if (key === 'f' || key === 'F') {
        e.preventDefault();
        toggleFullscreen();
      } else if (key === 't' || key === 'T') {
        e.preventDefault();
        toggleTheme();
      } else if (key === 'v' || key === 'V') {
        if (currentSlide >= 1 && currentSlide <= 4) {
          e.preventDefault();
          cycleStageViewMode(currentSlide);
        }
      } else if (key === 's' || key === 'S' || key === ' ') {
        if (currentSlide >= 1 && currentSlide <= 4) {
          e.preventDefault();
          toggleRoundTimer(currentSlide);
        }
      } else if (key === 'r' || key === 'R') {
        if (currentSlide >= 1 && currentSlide <= 4) {
          e.preventDefault();
          resetRoundTimer(currentSlide);
        }
      } else if (key === '+' || key === '=') {
        if (currentSlide >= 1 && currentSlide <= 4) {
          e.preventDefault();
          addOneMinute(currentSlide);
        }
      } else if (key === '-' || key === '_') {
        if (currentSlide >= 1 && currentSlide <= 4) {
          e.preventDefault();
          subtractOneMinute(currentSlide);
        }
      }
    });

    console.log("Operation ShadowStrike Presentation Deck Initialized with View Focus Modes.");
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
