import os

ASSETS_DIR = r"C:\Users\MOUSHIMI\.gemini\antigravity\scratch\aegis\assets"
B64_PATH = os.path.join(ASSETS_DIR, "b64.txt")

with open(B64_PATH, "r", encoding="utf-8") as f:
    b64 = f.read().strip()

template = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DisasterSignal · Tactical Emergency Triage & LoRa Mesh Command Center</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg-black: #06080d;
        --card-bg: rgba(14, 18, 27, 0.88);
        --card-border: rgba(255, 255, 255, 0.08);
        --cyan: #00e5ff;
        --teal: #10b981;
        --red: #ef4444;
        --amber: #f59e0b;
        --text-white: #f8fafc;
        --text-dim: #94a3b8;
        --text-muted: #64748b;
        --font-sans: 'Inter', -apple-system, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
      }

      *, *::before, *::after {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }

      body {
        background-color: var(--bg-black);
        color: var(--text-white);
        font-family: var(--font-sans);
        overflow-x: hidden;
        min-height: 100vh;
        -webkit-font-smoothing: antialiased;
        user-select: none;
      }

      /* Top Tactical Navigation */
      header.tactical-header {
        position: relative;
        z-index: 50;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 28px;
        background: rgba(6, 8, 13, 0.94);
        border-bottom: 1px solid var(--card-border);
        backdrop-filter: blur(12px);
      }

      .brand-box {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 800;
        font-size: 1.05rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #fff;
      }

      .brand-logo-icon {
        width: 20px;
        height: 20px;
        color: #f59e0b;
        filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.6));
      }

      .nav-links {
        display: flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.04);
        padding: 4px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.06);
      }

      .nav-tab {
        padding: 6px 16px;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-dim);
        border-radius: 6px;
        text-decoration: none;
        transition: all 0.2s;
        cursor: pointer;
      }

      .nav-tab.active, .nav-tab:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
      }

      .header-meta {
        display: flex;
        align-items: center;
        gap: 14px;
      }

      .badge-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        color: #e2e8f0;
      }

      .badge-operational {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        color: #34d399;
      }

      .badge-operational::before {
        content: '';
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 6px #10b981;
      }

      /* Center Hero 3D Terrain Stage with Exact Picture */
      .stage-wrapper {
        position: relative;
        width: 100%;
        height: 58vh;
        min-height: 440px;
        background-color: #06080d;
        overflow: hidden;
      }

      .hero-bg-img {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center top;
        filter: contrast(1.15) brightness(0.95) saturate(1.2);
        opacity: 0.95;
      }

      .hero-vignette {
        position: absolute;
        inset: 0;
        background: 
          radial-gradient(circle at 50% 50%, transparent 40%, rgba(6, 8, 13, 0.8) 95%),
          linear-gradient(to bottom, rgba(6, 8, 13, 0.6) 0%, transparent 20%, transparent 75%, #06080d 100%);
        pointer-events: none;
      }

      /* Left Side HUD Telemetry Dock */
      .left-hud-dock {
        position: absolute;
        top: 24px;
        left: 28px;
        z-index: 20;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .sector-title h1 {
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #fff;
      }

      .sector-title p {
        font-size: 0.78rem;
        color: var(--text-muted);
        font-family: var(--font-mono);
        margin-top: 2px;
      }

      .dock-items {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 8px;
      }

      .dock-node {
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(14, 18, 27, 0.75);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 6px 12px;
        border-radius: 999px;
        width: fit-content;
        transition: all 0.2s;
        cursor: pointer;
      }

      .dock-node:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(0, 229, 255, 0.3);
      }

      .dock-icon-circle {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.08);
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .dock-icon-circle svg {
        width: 12px;
        height: 12px;
        fill: currentColor;
      }

      .dock-label {
        font-size: 0.74rem;
        color: var(--text-dim);
        font-weight: 500;
      }

      .dock-status {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
      }

      .dock-status.online {
        color: #34d399;
        background: rgba(16, 185, 129, 0.15);
      }

      .dock-status.offline {
        color: #f87171;
        background: rgba(239, 68, 68, 0.15);
      }

      /* Center Floating Interactive Target Card */
      .floating-hud-widget {
        position: absolute;
        top: 32px;
        right: 48px;
        z-index: 25;
        width: 390px;
        background: rgba(13, 17, 26, 0.88);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(0, 229, 255, 0.35);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 30px rgba(0, 229, 255, 0.15);
      }

      .widget-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
      }

      .widget-target-name {
        font-size: 0.95rem;
        font-weight: 700;
        color: #fff;
      }

      .widget-freq {
        font-family: var(--font-mono);
        font-size: 0.74rem;
        color: var(--cyan);
        margin-top: 2px;
      }

      .widget-tier-badge {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid var(--red);
        color: #fca5a5;
        font-size: 0.78rem;
        font-weight: 800;
        padding: 4px 8px;
        border-radius: 6px;
      }

      /* Circular Radial Target in Card */
      .target-radar-display {
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        height: 120px;
        margin: 10px 0;
      }

      .target-center-circle {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(239, 68, 68, 0.3) 0%, rgba(13, 17, 26, 0.8) 70%);
        border: 1px solid var(--red);
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: radar-ping 2s infinite;
      }

      @keyframes radar-ping {
        0%, 100% { transform: scale(0.96); box-shadow: 0 0 12px rgba(239, 68, 68, 0.4); }
        50% { transform: scale(1.05); box-shadow: 0 0 24px rgba(239, 68, 68, 0.8); }
      }

      .radial-btn {
        position: absolute;
        padding: 4px 10px;
        font-size: 0.7rem;
        font-weight: 600;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #e2e8f0;
        cursor: pointer;
        transition: all 0.2s;
      }

      .radial-btn:hover {
        background: rgba(0, 229, 255, 0.2);
        border-color: var(--cyan);
        color: #fff;
      }

      .radial-btn.top-left { top: 10px; left: 16px; }
      .radial-btn.top-right { top: 10px; right: 16px; background: rgba(239, 68, 68, 0.2); border-color: var(--red); color: #fca5a5; }
      .radial-btn.bottom-left { bottom: 10px; left: 16px; }
      .radial-btn.bottom-right { bottom: 10px; right: 16px; }

      .widget-summary {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 0.76rem;
        color: #e2e8f0;
        line-height: 1.4;
      }

      .widget-summary em {
        color: var(--cyan);
        font-style: normal;
      }

      /* Bottom Tactical Control Deck */
      .tactical-deck {
        display: grid;
        grid-template-columns: 340px 240px 1fr 340px;
        gap: 16px;
        padding: 20px 28px;
        background: #080c14;
        border-top: 1px solid var(--card-border);
      }

      .deck-box {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 10px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .deck-box h4 {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
        display: flex;
        justify-content: space-between;
      }

      .tac-grid-btns {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
      }

      .tac-action-btn {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: var(--text-dim);
        padding: 8px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 600;
        cursor: pointer;
        text-align: center;
        transition: all 0.2s;
      }

      .tac-action-btn:hover, .tac-action-btn.active {
        background: rgba(0, 229, 255, 0.15);
        border-color: var(--cyan);
        color: #fff;
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
      }

      .deck-radar-mini {
        position: relative;
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(239, 68, 68, 0.08) 0%, rgba(8, 12, 20, 0.95) 70%);
        border: 1px solid rgba(239, 68, 68, 0.35);
        margin: 0 auto;
        overflow: hidden;
      }

      .radar-sweep-beam {
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: conic-gradient(from 0deg, rgba(239, 68, 68, 0.45) 0deg, transparent 50deg);
        animation: radar-sweep-rotate 3s linear infinite;
      }

      @keyframes radar-sweep-rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }

      .radar-target-dot {
        position: absolute;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--red);
        box-shadow: 0 0 8px var(--red);
      }

      .radar-target-dot.d1 { top: 40%; left: 55%; }
      .radar-target-dot.d2 { top: 60%; left: 35%; background: var(--amber); box-shadow: 0 0 8px var(--amber); }

      .stats-table {
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 0.74rem;
      }

      .stat-item {
        display: flex;
        justify-content: space-between;
        color: var(--text-dim);
      }

      .stat-item strong {
        color: #fff;
        font-family: var(--font-mono);
      }

      .packet-snippet-box {
        background: rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 8px;
        border-radius: 6px;
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--cyan);
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .primary-launch-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 10px;
        border-radius: 6px;
        background: var(--red);
        color: #fff;
        font-size: 0.78rem;
        font-weight: 700;
        text-decoration: none;
        transition: all 0.2s;
        margin-top: auto;
      }

      .primary-launch-btn:hover {
        background: #dc2626;
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.5);
      }

      @media (max-width: 1100px) {
        .tactical-deck {
          grid-template-columns: 1fr 1fr;
        }
      }

      @media (max-width: 768px) {
        .tactical-deck {
          grid-template-columns: 1fr;
        }
        .floating-hud-widget {
          position: static;
          width: calc(100% - 32px);
          margin: 16px auto;
        }
        .left-hud-dock {
          position: static;
          padding: 16px;
        }
        .stage-wrapper {
          height: 40vh;
        }
      }
    </style>
  </head>
  <body>
    <!-- Top Header Navigation -->
    <header class="tactical-header">
      <div class="brand-box">
        <svg class="brand-logo-icon" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2a10 10 0 0 0-7.07 17.07l1.41-1.41A8 8 0 1 1 12 20v2a10 10 0 0 0 0-20z" />
          <path d="M12 6a6 6 0 0 0-4.24 10.24l1.41-1.41A4 4 0 1 1 12 16v2a6 6 0 0 0 0-12z" />
        </svg>
        DisasterSignal
      </div>

      <nav class="nav-links">
        <a class="nav-tab active" href="#">Dashboard</a>
        <a class="nav-tab" href="http://localhost:5173" target="_blank">Triage Map</a>
        <a class="nav-tab" href="#optical">Acoustic Whisper</a>
        <a class="nav-tab" href="#radars">RF LoRa Mesh</a>
        <a class="nav-tab" href="#statistics">Statistics</a>
      </nav>

      <div class="header-meta">
        <div class="badge-btn">
          <span>▲ District Control 01</span>
        </div>
        <div class="badge-operational">
          <span>Operational</span>
        </div>
      </div>
    </header>

    <!-- Center Stage with Exact High-Fidelity 3D Terrain Picture -->
    <main class="stage-wrapper">
      <img
        class="hero-bg-img"
        src="data:image/jpeg;base64,""" + b64 + """"
        alt="DisasterSignal 3D Topographic Mesh Telemetry"
      />
      <div class="hero-vignette"></div>

      <!-- Left HUD Telemetry Dock -->
      <aside class="left-hud-dock">
        <div class="sector-title">
          <h1>District Control 01</h1>
          <p>Sundarbans River Delta · 60 Villages Active</p>
        </div>

        <div class="dock-items">
          <div class="dock-node">
            <span class="dock-icon-circle">
              <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.93V18h-2v-1.07A6 6 0 0 1 6.07 12H5v-2h1.07A6 6 0 0 1 11 4.07V3h2v1.07A6 6 0 0 1 17.93 10H19v2h-1.07A6 6 0 0 1 13 16.93z"/></svg>
            </span>
            <span class="dock-label">Cellular 4G/5G</span>
            <span class="dock-status offline">Offline</span>
          </div>

          <div class="dock-node">
            <span class="dock-icon-circle">
              <svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 0-9 9v7h4v-5H5v-2a7 7 0 1 1 14 0v2h-2v5h4v-7a9 9 0 0 0-9-9z"/></svg>
            </span>
            <span class="dock-label">GSM Voice/SMS</span>
            <span class="dock-status offline">Offline</span>
          </div>

          <div class="dock-node">
            <span class="dock-icon-circle">
              <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            </span>
            <span class="dock-label">865MHz LoRa Mesh</span>
            <span class="dock-status online">Online</span>
          </div>

          <div class="dock-node">
            <span class="dock-icon-circle">
              <svg viewBox="0 0 24 24"><path d="M12 7V3m0 18v-4m8-5h4M0 12h4m14.07-5.07l2.83-2.83M3.1 18.9l2.83-2.83m0-8.14L3.1 5.1m16.8 13.8l-2.83-2.83"/></svg>
            </span>
            <span class="dock-label">Solar Battery Relay</span>
            <span class="dock-status online">Online</span>
          </div>

          <div class="dock-node">
            <span class="dock-icon-circle">
              <svg viewBox="0 0 24 24"><path d="M19 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm-7 11a3 3 0 1 1 3-3 3 3 0 0 1-3 3z"/></svg>
            </span>
            <span class="dock-label">District Central Gateway</span>
            <span class="dock-status online">Online</span>
          </div>
        </div>
      </aside>

      <!-- Center Floating Tactical Targeting HUD -->
      <section class="floating-hud-widget">
        <div class="widget-top">
          <div>
            <div class="widget-target-name">RF LoRa IN865 · Node 105</div>
            <div class="widget-freq">Location: 22.31°N, 87.92°E · Freq: 865.2 MHz · SF9</div>
          </div>
          <div class="widget-tier-badge">CRITICAL · 91.0</div>
        </div>

        <!-- Target Reticle & Radial Buttons -->
        <div class="target-radar-display">
          <button class="radial-btn top-left" onclick="alert('Verification factor V=1.0 confirmed via 4 independent reports.')">
            Verify (4x)
          </button>
          <a href="http://localhost:5173" target="_blank" class="radial-btn top-right">
            Deploy NDRF Boat
          </a>

          <div class="target-center-circle">
            <svg style="width: 28px; height: 28px; fill: #ef4444;" viewBox="0 0 24 24">
              <path d="M12 2L1 21h22L12 2zm0 3.99L19.53 19H4.47L12 5.99zM11 10h2v4h-2zm0 6h2v2h-2z"/>
            </svg>
          </div>

          <button class="radial-btn bottom-left" onclick="alert('Priority elevated via Rule 1: Threat to life (L=1.00) forces CRITICAL.')">
            Mark Priority
          </button>
          <button class="radial-btn bottom-right" onclick="alert('IVR automated callback dispatched in Bengali & Hindi.')">
            IVR Call-Back
          </button>
        </div>

        <div class="widget-summary">
          <strong>Bengal Speech-to-Text:</strong> "ছাদে ৫ জন আটকে, জল বাড়ছে"<br />
          <em>IndicTrans2 Translated:</em> "5 people stuck on roof, water rising fast. Threat to life L=1.00."
        </div>
      </section>
    </main>

    <!-- Bottom Tactical Control Deck -->
    <footer class="tactical-deck">
      <!-- 1. Triage Control -->
      <div class="deck-box">
        <h4>
          Triage Control
          <span style="color: var(--cyan); font-family: var(--font-mono);">IN865 MESH</span>
        </h4>
        <div class="stat-item" style="margin-bottom: 4px;">
          <span>Hop Count: <strong>2 / 7 Max</strong></span>
          <span>Duty Cycle: <strong>1.1% / 2.5%</strong></span>
        </div>
        <div class="tac-grid-btns">
          <button class="tac-action-btn active" onclick="alert('6 LoRa Packets injected! Rooftop Rescue prioritised to #1 CRITICAL (Score 91.0).')">
            Load 6-Pkt Demo
          </button>
          <button class="tac-action-btn" onclick="alert('Auto-Triage active: Severity-First queue discipline running.')">
            Auto-Triage
          </button>
          <button class="tac-action-btn" onclick="alert('Injecting 20-byte base64 SMS frame into gateway.')">
            Inject 20B SMS
          </button>
          <button class="tac-action-btn" onclick="alert('SF9 Mesh relay active: 486 reports/h capacity.')">
            SF9 Relay Mode
          </button>
        </div>
      </div>

      <!-- 2. Radar Target Detection -->
      <div class="deck-box">
        <h4>Radar</h4>
        <div class="deck-radar-mini">
          <div class="radar-sweep-beam"></div>
          <div class="radar-target-dot d1" title="Node 105 (Critical)"></div>
          <div class="radar-target-dot d2" title="Node 104 (High)"></div>
        </div>
        <div style="display: flex; justify-content: space-around; font-size: 0.72rem; color: var(--text-dim);">
          <span>Targets: <strong style="color:#fff">2 Active</strong></span>
          <span>Threat: <strong style="color:#f87171">CRITICAL</strong></span>
        </div>
      </div>

      <!-- 3. Severity Breakdown S(c) -->
      <div class="deck-box">
        <h4>Severity Telemetry S(c)</h4>
        <div class="stats-table">
          <div class="stat-item">
            <span>Threat to Life (L = 1.00)</span>
            <strong style="color: #f87171">40.0 pts (Rule 1)</strong>
          </div>
          <div class="stat-item">
            <span>Urgency / Rise (U = 0.95)</span>
            <strong>19.0 pts</strong>
          </div>
          <div class="stat-item">
            <span>Verification (V = 1.00)</span>
            <strong style="color: #34d399">15.0 pts (4 Corroborations)</strong>
          </div>
          <div class="stat-item">
            <span>People + Isolation (P + A)</span>
            <strong>16.9 pts (5 People, Cut-off)</strong>
          </div>
        </div>
      </div>

      <!-- 4. 20-Byte Packet & Dashboard Launcher -->
      <div class="deck-box">
        <h4>20-Byte Packet Inspector</h4>
        <div class="packet-snippet-box">
          <div>SIZE: 20 BYTES (CRC-16 OK)</div>
          <div>SMS: <span style="color:#facc15;">wQMABc8hV6xk91kAARk=</span></div>
          <div>FLAGS: L=1 · U=1 · A=1 · Hops=2</div>
        </div>
        <a href="http://localhost:5173" class="primary-launch-btn" target="_blank">
          Open Authority Dashboard →
        </a>
      </div>
    </footer>
  </body>
</html>
"""

landing_path = r"C:\Users\MOUSHIMI\.gemini\antigravity\scratch\aegis\landing\index.html"
root_path = r"C:\Users\MOUSHIMI\.gemini\antigravity\scratch\aegis\index.html"

with open(landing_path, "w", encoding="utf-8") as f:
    f.write(template)

with open(root_path, "w", encoding="utf-8") as f:
    f.write(template)

print("Generated both HTML files successfully.")
