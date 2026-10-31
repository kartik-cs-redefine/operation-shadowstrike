# 🚀 OPERATION SHADOWSTRIKE - PROJECTOR STAGE DECK & SCORING SYSTEM
### ALGO CLUB | PSIT KANPUR
**Date:** 31 OCT 2026 (Saturday) | **Time:** 01:40 PM - 03:10 PM | **Venue:** Computer Lab, PSIT

---

## 🏗️ Project Architecture

```
├── assets/
│   ├── css/
│   │   ├── styles.css              # Main presentation stylesheet (Dark & Light modes)
│   │   └── fonts_local.css         # Local offline fonts loader
│   ├── fonts/                      # Offline WOFF2 fonts (Chakra Petch, Inter, JetBrains Mono, Rajdhani)
│   ├── js/
│   │   └── app.js                  # Deck navigation, reverse timers, join code controller, Web Audio SFX
│   └── images/
│       ├── logos/                  # PSIT, NAAC A+, ALGO Club, CSI logos (2x high-res)
│       ├── hero/                   # Tactical operator artwork
│       └── rounds/                 # Thematic round illustrations
├── scoring_system/                 # Automated 4-Round Wayground scoring & leaderboard engine
│   ├── input/                      # Input directory for master participant list and round exports
│   ├── output/                     # Output directory for reports
│   ├── inspect_input_files.py      # Dynamic Excel schema analyzer
│   ├── leaderboard_engine.py       # Core consolidation, tie-breaking & openpyxl workbook generator
│   └── run_scoring.bat             # 1-Click execution launcher
├── index.html                      # Interactive 16:9 widescreen presentation deck
├── presentation.pptx               # 16:9 Widescreen PowerPoint presentation deck
├── start_projector.bat             # 1-Click standard projector launcher
├── start_fullscreen_kiosk.bat      # 1-Click fullscreen kiosk launcher
└── README.md
```

---

## 📑 16:9 Widescreen Slide Deck

1. **Slide 0: Title & Cover Slide**
   - Symmetrical institutional header (PSIT Kanpur, NAAC A+, ALGO Club, CSI).
   - Tactical hero artwork, directive banner, and live mission status badge.
   - Event coordinates: **31 OCT 2026 (Saturday)**, **01:40 PM – 03:10 PM**, **Computer Lab, PSIT**.

2. **Slide 1: Level 01 – Cipher Decoding & Protocol Extraction**
   - Thematic cyber terminal & cipher decryption illustration.
   - 6-digit Wayground Join Code input with direct on-screen typing.
   - Giant centered reverse countdown timer (**08:00**).

3. **Slide 2: Level 02 – Logical Reasoning & Matrix Blueprint**
   - Tactical chess board, maze blueprint, and coordinate grid visual.
   - 6-digit Wayground Join Code input with direct on-screen typing.
   - Giant centered reverse countdown timer (**08:00**).

4. **Slide 3: Level 03 – C Programming & Runtime Debugging**
   - C programming syntax debugger and terminal visual.
   - 6-digit Wayground Join Code input with direct on-screen typing.
   - Giant centered reverse countdown timer (**11:00**).

5. **Slide 4: Level 04 – Final Digital Incident Simulation**
   - Forensic evidence corkboard and compromised system visual.
   - 6-digit Wayground Join Code input with direct on-screen typing.
   - Giant centered reverse countdown timer (**10:00**).

---

## 🌟 Interactive Stage Features

- **Direct Screen Join Code Input:**
  - 6 large monospace digit slots (`[ · ] [ · ] [ · ] — [ · ] [ · ] [ · ]`).
  - Auto-advance to next slot on typing; backspace navigates to previous slot.
  - Full paste support (Ctrl+V) splits and populates all 6 boxes automatically.
  - Dedicated `Copy` and `Clear` action buttons.
  - Preserved per round across slide switches via `localStorage`.

- **Expandable Stage View Modes:**
  - **`Split View`**: Balanced default display of both Join Code and Countdown Timer.
  - **`Join Code Focus`**: Hides the timer; expands Join Code to massive 54px digits occupying full stage.
  - **`Timer Focus`**: Hides the join code; expands Timer to colossal 136px tabular digits occupying full stage.

- **Tactile Countdown Timer Controls:**
  - Start / Pause toggle button (`▶ Start` / `⏸ Pause`).
  - Reset to round default duration.
  - Time adjusters: `+1m` (add 1 minute) and `-1m` (subtract 1 minute).
  - Visual color shift: normal green ➔ amber at $\le 60\text{s}$ ➔ red pulse at $\le 30\text{s}$.
  - Audible synthesized audio chime at `00:00` ("TIME'S UP!").

- **Dark & Light Mode:**
  - Floating top-right toggle button (`☀️ Light Mode` / `🌙 Dark Mode`).
  - High-contrast color palette optimized for high-lumen projectors.

---

## 🎮 Keyboard Controls & Shortcuts

| Key | Action | Description |
| :---: | :---: | :--- |
| **`→`** / `PageDown` / `Enter` | **Next Slide** | Advance to the next round. |
| **`←`** / `PageUp` / `Backspace` | **Previous Slide** | Return to the previous slide. |
| **`Space`** / **`S`** | **Timer Start / Pause** | Toggle countdown timer. |
| **`R`** | **Reset Timer** | Reset timer to round default. |
| **`+`** / **`=`** | **Add 1 Minute** | Add 60 seconds to timer. |
| **`-`** / **`_`** | **Subtract 1 Minute** | Subtract 60 seconds from timer. |
| **`V`** | **Cycle Stage View** | Cycle: Split View ➔ Join Code Focus ➔ Timer Focus. |
| **`T`** | **Toggle Theme** | Switch between Dark and Light mode. |
| **`F`** / `F11` | **Toggle Fullscreen** | Fullscreen 1080p projector display mode. |

*(Note: Slide navigation shortcuts are safely bypassed while actively typing in the Join Code input slots).*

---

## 📊 Automated Scoring & Leaderboard Engine (`scoring_system/`)

A dedicated pipeline to process Wayground competition results and generate `FINAL_WAYGROUND_LEADERBOARD.xlsx`:
1. Dual-key matching on `Team Name + Participant Name`.
2. Strict non-fabrication policy; absent participants receive `0` marks.
3. Automated tie-breaking by lowest combined submission duration.
4. Generates a 5-sheet competition workbook:
   - **FINAL LEADERBOARD** (with podium highlights)
   - **MASTER DATA**
   - **ROUND-WISE ANALYSIS**
   - **VALIDATION REPORT**
   - **TOP PERFORMERS**
