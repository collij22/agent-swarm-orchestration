# “Countdown” for Windows — Product Requirements Document (PRD)

> Goal: deliver a Windows desktop application that **faithfully simulates the Channel 4 game show _Countdown_** with two play modes (vs. computer and vs. human), authentic rules and pacing, robust matchmaking (open challenges + invite codes), and a persistent **ELO** rating. This document is intentionally explicit so a developer can build from it without guesswork.

---

## 1) Scope & Objectives

- **Platforms:** Windows 10/11 (x64).  
- **Tech stack (suggested):** .NET 8 + WinUI 3 (or WPF) for desktop UI; C# backend; EF Core for local storage; optional lightweight hosted backend (ASP.NET Core) for multiplayer; SignalR for real-time.  
- **Modes:**  
  1) **Play vs. Computer** (Easy / Medium / Hard).  
  2) **Play vs. Human**  
     - **Post a challenge** (public lobby).  
     - **Search open challenges** (filters).  
     - **Join via code** (private match).  
- **Game authenticity:** mirror modern **15-round format** (10 Letters, 4 Numbers, 1 Conundrum) and the round order used on TV; 30-second rounds; alternation of control; scoring as on the show.  
- **Ranking:** Global **ELO** per user across rated matches, with unrated option.  
- **Online/offline:** Full offline vs. CPU. Online required for PvP and rankings.

> ⚠️ **IP & assets:** Don’t ship Channel 4 logos, theme audio, fonts, or screenshots. Emulate **style** (layout, pacing, color mood) with original assets.

---

## 2) Canonical Rules (authoritative for implementation)

### 2.1 Round Set & Order (15-round format)

- Total: **15 rounds** → **10 Letters**, **4 Numbers**, **1 Conundrum**.  
- The app runs the following **order** (no adverts), preserving TV cadence:
  1. Letters  
  2. Letters  
  3. Numbers  
  4. Letters  
  5. Numbers  
  6. Letters  
  7. Numbers  
  8. Letters  
  9. Numbers  
  10. Letters  
  11. Letters  
  12. Letters  
  13. Letters  
  14. Numbers  
  15. Conundrum

- **Control alternates every round** so each contestant gets **5 Letters picks** and **2 Numbers picks**.

### 2.2 Letters Rounds (L)

- **Set-up:** Two pre-shuffled **stacks** per episode: **Vowels** (A, E, I, O, U only) and **Consonants**. The chooser calls “vowel” or “consonant” nine times; the assistant (UI) reveals tiles left→right. Enforce that each 9-letter selection contains **at least 3 vowels** and **at least 4 consonants** (UI prevents illegal choice sequences). Stacks are episode-scoped (not replenished during the episode).  
- **Timing:** Players have **30 seconds** from first letter reveal to enter words.  
- **Word validity:**  
  - Build a single English word using each tile no more times than shown.  
  - No proper nouns, abbreviations, hyphenations, or apostrophes.  
  - UK spelling profile by default; allow a “US spelling” toggle in Settings.  
  - Dictionary packs (see §7.1).
- **Scoring:**  
  - **2–8 letters:** **1 point per letter**.  
  - **9-letter word (“Full Monty”):** **18 points** (double).  
  - **Tie handling:** If both submit valid words of the same length, **both score** that length (or 18 for 9s).

### 2.3 Numbers Rounds (N)

- **Pool:** 24 cards → **20 small** (two each of 1–10) and **4 large** (25, 50, 75, 100).  
- **Chooser selects** 0–4 large; game draws **6 tiles** accordingly (random without replacement). **Numbers pool replenishes each round**. Target is a random **100–999** integer.  
- **Allowed operations:** `+ − × ÷` with parentheses; intermediate results must be **positive integers**; you may use any subset of tiles **once each**. Not all tiles need be used.  
- **Timing:** 30 seconds to reach target or as close as possible.  
- **Scoring:**  
  - **Exact target:** **10 points**.  
  - **Within 1–5:** **7 points**.  
  - **Within 6–10:** **5 points**.  
  - Usually **only the nearer result scores**; **if equal distance** (e.g., both 3 away), **both score** the corresponding band.

### 2.4 Conundrum (C)

- **Nine-letter anagram** shown scrambled; **first to buzz** with correct solution within 30 seconds scores **10 points**. One attempt per player; incorrect buzz locks that player out for the remainder of the 30s. If unsolved, 0 points to both.

### 2.5 Endgame & Ties

- Highest total after round 15 wins.  
- **Tie after C:** trigger **“Crucial Conundrum”** sudden-death with fresh scramble; repeat until decided.

---

## 3) Game Flow

1) **Match setup**  
   - Pick mode (CPU / Human).  
   - For Human: pick **Rated** (affects ELO) or **Unrated**.  
   - Time control is fixed to **30s** per round (authentic), with optional **“Practice”** override (untimed) that **never** counts as rated.

2) **Seat & control**  
   - Randomly assign **Champion** (left) and **Challenger** (right).  
   - Alternate chooser control each round (UI banner: “Your pick: Letters / Numbers”).

3) **Section pacing** (no adverts, but preserve rhythm with interstitials):  
   - After R3, R6, R9, show a short **“Teatime-style teaser”** for single-player fun (non-scoring).  
   - After R8, optional **etymology popover** (“Origins of Words”) if the dictionary pack has it. (Toggle in Settings.)

---

## 4) User Interface (authentic look, original assets)

> Design language: cool **blue** palette, soft gradients; rounded rectangles; big “clock” centerpiece animation; **left/right** score to mirror contestants; **board** areas with large tiles and generous spacing. Use a legible geometric sans (e.g., Segoe UI Variable).

### 4.1 Global Layout (Match Screen)

- **Top-center:** Large **circular clock** with tick markers; smooth sweep hand animating a 30-second arc; audible tick and final “whoosh” (original SFX, not the TV jingle).  
- **Upper left/right score pods:**  
  - Avatar, display name, rating (e.g., “ELO 1542”).  
  - Big **score total**; below it **per-round delta** flashes (+7, +18, +10).  
  - Small **“control” lamp** shows who picks this round.  
- **Center board zone:** swaps by round type:  
  - **Letters board:** 9 tile wells in a 3×3 or single row grid, left-to-right reveal animation.  
  - **Numbers board:** 6 face-up tiles on the left; target (100–999) on a **7-segment-style** display on the right.  
  - **Conundrum:** a single 9-tile row, scrambled; large **Buzz** buttons appear for both players (mouse/keyboard hotkey: Space/Enter).  
- **Bottom input zone:**  
  - **Letters:**  
    - Textbox for word entry (auto-validates live against rack letters; dictionary check deferred until time-up or **Submit**).  
    - **Submit** and **Clear**; when submitted, textbox locks; edit allowed until timer hits 0.  
  - **Numbers:**  
    - Expression builder with tiles (drag-drop or click), operators, parentheses, and **Undo**.  
    - Live **current value** preview; prevent illegal moves (reuse, non-integers).  
  - **Conundrum:** No text input; **Buzz** reveals answer field with 5-second sub-timer to type and confirm.  
- **Right sidebar (collapsible):**  
  - Round list with **R1–R15** badges (L/N/C), showing per-round scores and best solutions (post-reveal).  
  - Chat tab (PvP only), emotes toggle, and **report** button.

### 4.2 Letters Round — UI Detail

- **Tile aesthetics:** glossy blue cards; large uppercase letters; small **×count** overlay if letter appears multiple times in the rack history view.  
- **Chooser panel:** “Vowel” and “Consonant” buttons; disable choices that would violate 3-vowel/4-consonant constraint (show inline hint “Need ≥3 vowels”).  
- **Timer behavior:** starts when the **first letter** appears; subtle countdown ticks; last 3 seconds pulse.  
- **Result reveal:**  
  - Show both submitted words side-by-side, highlight longer.  
  - If tie-length, green highlight on both.  
  - Show **Dictionary Corner** pane with **max possible word(s)**.  
  - Animate score increments: +len or +18 for a nine.

### 4.3 Numbers Round — UI Detail

- **Picker:** Buttons for 0,1,2,3,4 **Large** (with tooltips naming 25/50/75/100).  
- **Tiles:** Flip animation from a face-down stack; smalls show “×2 for each 1–10” in Help.  
- **Expression Builder:**  
  - Drag tiles into a vertical **working** area; operators sit between tiles; auto-insert parentheses; disallow division that yields non-integer.  
   - “Try another line” button opens a second scratch line.  
- **Post-timer:** Each player independently **locks** a line to submit.  
- **Reveal:**  
  - Show distances; award **10/7/5** according to proximity; if equal distance in same band, both score.  
  - Assistant panel shows a known exact method if players missed.

### 4.4 Conundrum — UI Detail

- **Scramble display:** nine tiles with gentle random jitter (to feel “alive”).  
- **Buzz affordances:** Big circular **BUZZ** buttons (keyboard shortcuts too).  
- **Lockouts:** Incorrect buzz greys out that side until 00:00.  
- **Reveal:** Flip tiles into the solution in order; award **+10** to the solver; “Crucial Conundrum” banner if needed for ties.

---

## 5) Single-Player AI (Easy / Medium / Hard)

### 5.1 Letters AI

- **Core:** Precomputed **anagram solver** on dictionary (multiset of rack letters → solution set).  
- **Difficulty shaping:**  
  - **Easy:** sample from **P(choose length L) proportional to freq(L)** with cap at 5–6 letters; 10–20% chance to “miss” a found word; mild time penalty simulation.  
  - **Medium:** bias to 6–8 letters; 5% miss; prefers common words (frequency list weight).  
  - **Hard:** searches all max words; 85–95% chance to pick a **max**; rarely misses a nine (configurable rate for realism).  
- **Timing:** AI “thinks” for 3–7 seconds (Easy), 7–15 (Medium), 15–25 (Hard) before submitting.

### 5.2 Numbers AI

- **Core solver:** bounded search (BFS/DFS with memoization) over expression states with pruning:  
  - States: remaining multiset, current value set.  
  - Operations generate new integers only (discard non-integers and ≤0).  
  - Stop early if **exact** found.  
- **Difficulty shaping:**  
  - **Easy:** limit search depth/time; accept first 6–10-away; sometimes fail to submit.  
  - **Medium:** extend depth; accept ≤5-away if no exact within ~1s.  
  - **Hard:** near-optimal; exhaustive within 30s wall clock; small chance to land 1–5-away instead of exact.

### 5.3 Conundrum AI

- **Core:** shuffle the answer character set until match; effectively instant dictionary lookup.  
- **Difficulty shaping:** random **reaction delay** (e.g., Hard 0.7–1.4s; Medium 1.5–3s; Easy 3–6s); small chance to pass.

---

## 6) Multiplayer

### 6.1 Matchmaking

- **Open Challenges:**  
  - Create a lobby entry: Rated/Unrated, region (auto), min/max rating (optional), privacy (Public/Code).  
  - **Search** by rating band, region, friends-only filter.  
- **Invite via Code:** Generate a 6–8 char alphanumeric **Match Code**; second player joins by entering code.  
- **Fairness:** Server seeds episode stacks/targets; server adjudicates timing and validity; alternation enforced.

### 6.2 Real-Time

- **Transport:** SignalR (WebSockets) with deterministic server-side clock; clients drift-corrected.  
- **Input windows:** Client submits during 30s; server hard-stops at 30.000s (±100 ms tolerance).  
- **Disconnects:** 15-second grace; if not resumed, forfeit this round as **no submission**; full match forfeit after 60 seconds offline.

### 6.3 Anti-Cheat

- **Letters:** Prevent changing submission after 0.000s; server validates rack→word multiset.  
- **Numbers:** Server re-evaluates expression; flags non-integer steps.  
- **Conundrum:** Buzz timestamps authoritative on server; wrong buzz locks out.  
- **Heuristics:** Repeated superhuman play (e.g., 95% nines, consistent sub-1s conundrums) → **integrity score**; escalate: warnings, shadow-ban from rated.

---

## 7) Content: Dictionaries & Conundrums

### 7.1 Dictionary Packs (pluggable)

- **Default:** Ship with a permissively licensed English wordlist (e.g., SCOWL-derived).  
- **Optional add-on:** Allow users to install licensed packs (e.g., Oxford/Collins) if they provide credentials/license files—_we do not ship them_.  
- **Profiles:** “**UK**” vs “**US**” spelling toggles; **Proper Nouns** disabled.

### 7.2 Word Rules Engine

- **Valid if:** in current pack (base form or permitted inflection), not proper noun, no hyphen/apostrophe.  
- **Adjudication UI:** When rejected, show “Not in dictionary” or “Invalid letters used”.  
- **Max word finder:** For post-round “Dictionary Corner” showcase.

### 7.3 Letters Stacks Generation

- At episode start, **pre-deal** Vowel and Consonant stacks per letter frequency tables (Scrabble-like weights).  
- Persist for the entire match; **no replenishment** between letters rounds.

### 7.4 Conundrums

- Curated list of 9-letter answers (frequency-weighted).  
- Scrambler must avoid trivially revealing patterns (no identical bigrams adjacent; ensure min edit distance from original).  
- Mark some entries as **“Crucial-grade”** for tie-breaks.

---

## 8) Scoring, Ratings & Leaderboards

### 8.1 Round & Match Scoring

- Letters: **len** (2–8) or **18** for nines; tie-length → both score.  
- Numbers: **10/7/5** per bands; equal distance in same band → both score; otherwise only nearer scores.  
- Conundrum: **+10** first correct buzz.

### 8.2 ELO System

- **Single global rating** per account (optionally extend later to Letters/Numbers/Conundrum subscores).  
- **Base:** Classic ELO (or Glicko variant); start **1500**.  
- **K-factor:**  
  - Provisional (<30 rated games): **K=40**  
  - 1500–1999: **K=24**  
  - ≥2000 or <1200: **K=16**  
- **Result mapping:** Win = 1, Loss = 0, Draw = 0.5 (only if total scores equal after any tie-break conundrums were exhausted—rare).  
- **Rated eligibility:** Only **public** or **code** matches with integrity score ≥ threshold; **Practice** and **vs. CPU** are **unrated**.  
- **Decay:** None by default; optional seasonal soft-decay (−10 if inactive for 90 days).

### 8.3 Leaderboards

- Global Top-100; regional; friends; weekly resets for **seasonal tables** (ratings persist).  
- Anti-cheat filters applied before display.

---

## 9) Navigation & Non-Match Screens

- **Home:** “Play vs Computer”, “Play vs Human”, “Practice”, “How to Play”, recent matches, rating.  
- **Lobby:** Tabs for **Open Challenges** (filters: Rated, Region, Rating band), **Friends**, **Create Match**, **Join by Code**.  
- **Profile:** Avatar, bio, ELO history sparkline, W-L, average letters length, numbers exact-rate, conundrum avg buzz time.  
- **Settings:** Dictionary pack, spelling profile, audio levels, color-blind safe palette, input shortcuts, telemetry opt-in.

---

## 10) Data & Persistence

### 10.1 Local (SQLite via EF Core)

- **Users** (local id, username, avatar, ELO, privacy flags).  
- **Matches** (id, timestamp, rated?, opponent id, result, per-round data snapshot).  
- **Rounds** (type, chooser, rack/tiles/target, submissions, validation results, scores).  
- **Dictionaries** (installed packs metadata + hash).  
- **Integrity** (client metrics).

### 10.2 Server

- Auth (email + magic link or OAuth).  
- Match state (authoritative), chat (ephemeral), ratings updates (transactional), leaderboards.  
- GDPR: data export & delete endpoints.

---

## 11) Accessibility

- Full keyboard support; large text mode; dyslexia-friendly font option; color-blind palettes; screen reader labels for tiles and timers; haptics toggle (if device supports).

---

## 12) Audio/FX (original)

- **Clock ticks** (soft, non-copyright), final “time!” stinger.  
- Subtle flip sounds for tiles; success chimes for scoring bands (distinct tones for +5/+7/+10 and for +18 letters nine).  
- Mute & per-channel sliders.

---

## 13) Performance & QA

- **Targets:** steady 60 FPS animations; clock drift < ±30 ms across 30 s.  
- **Tests:**  
  - Unit: dictionary validation, anagram solver, numbers search legality, ELO maths.  
  - Simulation: 100k generated rounds (letters/ numbers) — ensure scoring bands correct, solver stability.  
  - Multiplayer soak with 500 concurrent matches; network lag injection (±200 ms).  
- **Logging:** Deterministic seeds per match to reproduce bugs.

---

## 14) Edge Cases & Rule Clarifications

- **Letters constraints:** If chooser attempts a selection that would break 3/4 minimums, auto-flip to the only legal choice and show inline tip.  
- **Numbers legality:** Disallow intermediate negatives or non-integers; division must divide exactly.  
- **Tie logic:**  
  - Letters equal length → both score.  
  - Numbers equal distance in same band → both score; otherwise only nearer scores.  
- **Conundrum mis-buzz:** Wrong answer → lockout; other player can continue; if both wrong, round ends 0–0.  
- **Abandoned match:** Mark as **loss** for leaver in rated PvP after grace windows.  
- **Dictionary disputes:** Show **source pack** and a **“Challenge decision”** dialog that cites pack and entry form; allow post-match export of a “decision log”.

---

## 15) Developer Notes & Implementation Tips

- **Episode seeds:** For authenticity, generate an **Episode object** with:  
  - Pre-shuffled Vowel/Consonant stacks for 10 letters rounds (plus buffer).  
  - Numbers draws are fresh per round (replenished).  
- **Numbers solver:** Cache sub-results (e.g., all pairwise ops results) to avoid blow-ups; canonicalize commutative operations; prune duplicates by multiset + value hashing.  
- **Anagram index:** Use a sorted-letters key → word list map; store by length for quick max retrieval; keep frequency metadata for AI choices.  
- **Latency:** Server decides **clock start** and **time-up**; client shows predictive clock but submits with server cutoff.

---

## 16) Milestones (suggested)

1. **Core engine** (rules, solvers, scoring).  
2. **Local UI** (practice mode).  
3. **CPU AI** (E/M/H) + polish of inputs.  
4. **Online PvP** (codes + open challenges).  
5. **ELO + leaderboards + profiles.**  
6. **Accessibility & localization (EN first, then PL/DE/FR ready).**  
7. **Beta hardening** (anti-cheat, logs, crash reporting).

---

## 17) Legal & Branding

- Use **original** UI assets and audio. Avoid Channel 4/Countdown names in app title/branding; e.g., ship as **“Letters & Numbers Arena”** and describe as “a game _inspired by_ the classic TV format.”  
- Provide a clear disclaimer in About.

---

## 18) Acceptance Criteria (high-level)

- All rounds follow rule set above; order is exactly as specified; timers exact to ±0.03 s.  
- Letters 9s always score 18; Numbers uses 10/7/5 with fair tie rules; Conundrum is +10 first-buzz.  
- Alternating control; each contestant gets 5 Letters and 2 Numbers picks.  
- CPU difficulty feels distinct and realistic.  
- PvP supports open challenges, search, and join-by-code; rated updates ELO.  
- No dictionary lookups allow improper nouns/hyphens; numbers solver rejects illegal steps.
