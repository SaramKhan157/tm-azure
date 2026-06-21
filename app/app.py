import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "/tmp/tasks.db")


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )"""
        )


init_db()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Task Manager</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b1120;
      --bg-elevated: #131c2e;
      --bg-input: #0e1626;
      --border: #1f2a3d;
      --border-hover: #334a6b;
      --text: #e6edf6;
      --text-muted: #8a99b3;
      --text-dim: #5a6a85;
      --azure: #0078d4;
      --azure-light: #50e6ff;
      --azure-glow: rgba(0, 120, 212, 0.4);
      --danger: #f87171;
      --success: #34d399;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      background-image:
        radial-gradient(circle at 15% -10%, rgba(0, 120, 212, 0.18), transparent 45%),
        radial-gradient(circle at 95% 8%, rgba(80, 230, 255, 0.10), transparent 40%);
    }

    .topbar {
      display: flex; align-items: center; justify-content: space-between;
      padding: 1.25rem 2rem;
      border-bottom: 1px solid var(--border);
      backdrop-filter: blur(8px);
    }
    .brand { display: flex; align-items: center; gap: 0.75rem; font-weight: 700; font-size: 1.05rem; letter-spacing: -0.01em; }
    .brand-logo {
      width: 32px; height: 32px;
      border-radius: 8px;
      background: linear-gradient(135deg, var(--azure), var(--azure-light));
      display: grid; place-items: center;
      font-size: 1rem;
      box-shadow: 0 4px 16px var(--azure-glow);
    }
    .topbar-meta { display: flex; align-items: center; gap: 1.5rem; font-size: 0.82rem; color: var(--text-muted); }
    .pill {
      display: inline-flex; align-items: center; gap: 0.4rem;
      padding: 0.3rem 0.7rem;
      background: rgba(52, 211, 153, 0.08);
      color: var(--success);
      border: 1px solid rgba(52, 211, 153, 0.25);
      border-radius: 9999px;
      font-size: 0.72rem; font-weight: 500;
    }
    .pill-dot {
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
      animation: pulse 2s infinite;
    }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.45; } }

    .hero {
      max-width: 760px; margin: 4rem auto 2.5rem; padding: 0 1.5rem; text-align: center;
    }
    .hero h1 {
      font-size: clamp(2rem, 5vw, 3rem);
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(180deg, #ffffff, #cbd5e1);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      margin-bottom: 0.75rem;
    }
    .hero p { color: var(--text-muted); font-size: 1rem; max-width: 520px; margin: 0 auto; }

    .container { max-width: 760px; margin: 0 auto 4rem; padding: 0 1.5rem; }

    .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1.25rem; }
    .stat {
      background: var(--bg-elevated); border: 1px solid var(--border);
      border-radius: 12px; padding: 1rem 1.25rem;
      transition: border-color 0.15s ease;
    }
    .stat:hover { border-color: var(--border-hover); }
    .stat-label { color: var(--text-dim); font-size: 0.72rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; }
    .stat-value { font-size: 1.6rem; font-weight: 700; margin-top: 0.2rem; letter-spacing: -0.02em; }

    .add-card {
      background: var(--bg-elevated); border: 1px solid var(--border);
      border-radius: 12px; padding: 0.5rem;
      display: flex; gap: 0.5rem; align-items: stretch;
      margin-bottom: 1.25rem;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .add-card:focus-within { border-color: var(--azure); box-shadow: 0 0 0 3px var(--azure-glow); }
    .add-card input {
      flex: 1; padding: 0.7rem 0.9rem;
      border: none; outline: none;
      background: transparent; color: var(--text);
      font-size: 0.95rem; font-family: inherit;
    }
    .add-card input::placeholder { color: var(--text-dim); }
    .add-btn {
      padding: 0.6rem 1.2rem;
      background: linear-gradient(135deg, var(--azure), #2090e0);
      color: #fff; border: none; border-radius: 8px;
      font-weight: 600; font-size: 0.9rem; font-family: inherit;
      cursor: pointer; transition: transform 0.1s ease, filter 0.15s ease;
      display: inline-flex; align-items: center; gap: 0.4rem;
    }
    .add-btn:hover { filter: brightness(1.1); }
    .add-btn:active { transform: scale(0.97); }

    .filters { display: flex; gap: 0.4rem; margin-bottom: 0.75rem; padding: 0.3rem; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 10px; width: fit-content; }
    .filter {
      padding: 0.4rem 0.9rem;
      background: transparent; border: none;
      color: var(--text-muted); font-size: 0.82rem; font-weight: 500; font-family: inherit;
      cursor: pointer; border-radius: 7px;
      transition: background 0.15s ease, color 0.15s ease;
    }
    .filter:hover { color: var(--text); }
    .filter.active { background: var(--azure); color: #fff; }

    .task-list { background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
    .task-item {
      display: flex; align-items: center; gap: 0.85rem;
      padding: 0.9rem 1.1rem;
      border-bottom: 1px solid var(--border);
      transition: background 0.15s ease;
      animation: slideIn 0.2s ease;
    }
    @keyframes slideIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
    .task-item:last-child { border-bottom: none; }
    .task-item:hover { background: rgba(255, 255, 255, 0.02); }
    .task-item input[type=checkbox] {
      appearance: none;
      width: 20px; height: 20px;
      border: 1.5px solid var(--border-hover);
      border-radius: 6px;
      cursor: pointer;
      position: relative;
      flex-shrink: 0;
      transition: all 0.15s ease;
    }
    .task-item input[type=checkbox]:hover { border-color: var(--azure); }
    .task-item input[type=checkbox]:checked {
      background: var(--azure);
      border-color: var(--azure);
    }
    .task-item input[type=checkbox]:checked::after {
      content: '✓';
      color: #fff;
      font-size: 0.85rem; font-weight: 700;
      position: absolute; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
    }
    .task-title { flex: 1; font-size: 0.95rem; transition: color 0.2s ease; }
    .task-title.done { text-decoration: line-through; color: var(--text-dim); }
    .delete-btn {
      background: transparent; border: none;
      color: var(--text-dim); cursor: pointer;
      width: 28px; height: 28px; border-radius: 6px;
      display: grid; place-items: center;
      font-size: 0.95rem;
      opacity: 0; transition: all 0.15s ease;
    }
    .task-item:hover .delete-btn { opacity: 1; }
    .delete-btn:hover { background: rgba(248, 113, 113, 0.1); color: var(--danger); }

    .empty { text-align: center; padding: 3.5rem 1.5rem; color: var(--text-muted); }
    .empty-icon {
      width: 56px; height: 56px;
      margin: 0 auto 1rem;
      border-radius: 14px;
      background: rgba(0, 120, 212, 0.1);
      display: grid; place-items: center;
      font-size: 1.5rem;
      color: var(--azure-light);
    }
    .empty-title { color: var(--text); font-weight: 600; margin-bottom: 0.3rem; font-size: 0.95rem; }
    .empty-text { font-size: 0.85rem; color: var(--text-dim); }

    footer {
      max-width: 760px; margin: 0 auto; padding: 1.5rem;
      border-top: 1px solid var(--border);
      display: flex; justify-content: space-between; align-items: center;
      color: var(--text-dim); font-size: 0.78rem;
    }
    footer a { color: var(--text-muted); text-decoration: none; }
    footer a:hover { color: var(--azure-light); }

    .stack {
      max-width: 760px;
      margin: 0 auto 3rem;
      padding: 0 1.5rem;
    }
    .stack-label {
      text-align: center;
      color: var(--text-dim);
      font-size: 0.72rem;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      margin-bottom: 1rem;
    }
    .stack-row {
      display: flex; flex-wrap: wrap; justify-content: center;
      gap: 0.5rem;
    }
    .tech {
      display: inline-flex; align-items: center; gap: 0.45rem;
      padding: 0.45rem 0.85rem;
      background: var(--bg-elevated);
      border: 1px solid var(--border);
      border-radius: 9999px;
      font-size: 0.78rem; font-weight: 500;
      color: var(--text-muted);
      transition: all 0.15s ease;
    }
    .tech:hover {
      color: var(--text);
      border-color: var(--border-hover);
      transform: translateY(-1px);
    }
    .tech svg { width: 14px; height: 14px; flex-shrink: 0; }
    .tech .ico-azure   { color: #50e6ff; }
    .tech .ico-tf      { color: #a78bfa; }
    .tech .ico-docker  { color: #4dabf7; }
    .tech .ico-gh      { color: #e6edf6; }
    .tech .ico-py      { color: #facc15; }
    .tech .ico-flask   { color: #e6edf6; }
    .tech .ico-sqlite  { color: #38bdf8; }

    @media (max-width: 600px) {
      .topbar { padding: 1rem 1.25rem; }
      .topbar-meta { gap: 0.75rem; font-size: 0.75rem; }
      .hero { margin-top: 2rem; }
      .stack { margin-bottom: 2rem; }
      .stats { grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
      .stat { padding: 0.85rem; }
      .stat-value { font-size: 1.3rem; }
      .add-card { flex-direction: column; }
      footer { flex-direction: column; gap: 0.5rem; }
    }
  </style>
</head>
<body>
  <div class="topbar">
    <div class="brand">
      <div class="brand-logo">✓</div>
      <span>Task Manager</span>
    </div>
    <div class="topbar-meta">
      <span class="pill"><span class="pill-dot"></span>Live</span>
      <span>Azure Container Apps · UK South</span>
    </div>
  </div>

  <section class="hero">
    <h1>Stay on top of what matters.</h1>
    <p>A tiny, fast task tracker running on Azure Container Apps with managed HTTPS and Terraform-defined infrastructure.</p>
  </section>

  <section class="stack">
    <div class="stack-label">Built with</div>
    <div class="stack-row">
      <span class="tech">
        <svg class="ico-azure" viewBox="0 0 24 24" fill="currentColor"><path d="M5.483 21.3H24l-9.864-17.082-2.42 6.522 5.585 6.626H8.41l-2.927 3.934Zm.21-13.747L0 17.86h6.486l9.97-17.16H10.99L5.693 7.553Z"/></svg>
        Azure Container Apps
      </span>
      <span class="tech">
        <svg class="ico-azure" viewBox="0 0 24 24" fill="currentColor"><path d="M5.483 21.3H24l-9.864-17.082-2.42 6.522 5.585 6.626H8.41l-2.927 3.934Zm.21-13.747L0 17.86h6.486l9.97-17.16H10.99L5.693 7.553Z"/></svg>
        Container Registry
      </span>
      <span class="tech">
        <svg class="ico-tf" viewBox="0 0 24 24" fill="currentColor"><path d="M1.44 0v7.575l6.561 3.79V3.787zm21.12 4.227l-6.561 3.791v7.574l6.56-3.787zM8.72 4.23v7.575l6.561 3.787V8.018zm0 8.405v7.575L15.28 24v-7.578z"/></svg>
        Terraform
      </span>
      <span class="tech">
        <svg class="ico-docker" viewBox="0 0 24 24" fill="currentColor"><path d="M13.983 11.078h2.119a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2.119a.185.185 0 0 0-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 0 0 .186-.186V3.574a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185.186m0 2.716h2.118a.187.187 0 0 0 .186-.186V6.29a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 0 0 .184-.186V6.29a.185.185 0 0 0-.185-.185H8.1a.185.185 0 0 0-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 0 0 .185-.186V6.29a.185.185 0 0 0-.185-.185H5.136a.186.186 0 0 0-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 0 0 .185-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.186.186 0 0 0-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 0 0-.75.748 11.376 11.376 0 0 0 .692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 0 0 3.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z"/></svg>
        Docker
      </span>
      <span class="tech">
        <svg class="ico-gh" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>
        GitHub Actions
      </span>
      <span class="tech">
        <svg class="ico-py" viewBox="0 0 24 24" fill="currentColor"><path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/></svg>
        Python · Flask
      </span>
      <span class="tech">
        <svg class="ico-sqlite" viewBox="0 0 24 24" fill="currentColor"><path d="M21.678.343c-.747-.665-1.65-.4-2.543.392l-.001.002a8.526 8.526 0 0 0-.524.516c-2.034 2.165-3.93 6.034-4.52 8.989a8.34 8.34 0 0 1 .53 1.466c.034.128.066.254.094.376.067.293.105.483.105.483s-.024-.093-.122-.376a3.55 3.55 0 0 0-.04-.108 1.84 1.84 0 0 0-.034-.087 7.948 7.948 0 0 0-.518-1.108c-.213.063-1.084.404-2.045 1.553-.906 1.083-1.483 2.62-1.711 3.27-.218-.795-.444-1.617-.515-1.918-.038-.158-.082-.347-.121-.547-.143-.708-.227-1.524-.069-2.058a.96.96 0 0 1 .057-.16c.146-.397.484-.7.99-.785.969-.162 2.292.193 4.305 2.063A21.71 21.71 0 0 1 17 16.31c.286.557.526 1.078.717 1.547.073-.186.142-.378.207-.575 1.247-3.74 1.673-9.046 1.673-9.046s2.146 3.876-1.5 12.518c2.117-.388 4.073-1.51 5.566-3.155-.07-.39-.21-.798-.42-1.21a23.97 23.97 0 0 0-1.51-2.42c-.564-.81-1.123-1.553-1.594-2.207-.65-.91-1.146-1.677-1.146-1.677s.34.39.86.992c.51.595 1.184 1.39 1.844 2.255 1.305 1.71 2.518 3.51 2.79 4.337A8.06 8.06 0 0 0 24.001 12c0-4.418-3.578-8-7.997-8z" opacity=".8"/><path d="M14.405 12.488c-.18.215-.31.426-.39.625-.124.305-.13.59.044.81.024.03.05.057.078.082.018-.043.04-.087.06-.13.13-.265.323-.518.547-.762.227-.245.486-.485.766-.722-.13-.057-.275-.082-.422-.073-.234.014-.453.115-.683.17z"/></svg>
        SQLite
      </span>
    </div>
  </section>

  <main class="container">
    <div class="stats">
      <div class="stat"><div class="stat-label">Total</div><div class="stat-value" id="statTotal">0</div></div>
      <div class="stat"><div class="stat-label">Active</div><div class="stat-value" id="statActive">0</div></div>
      <div class="stat"><div class="stat-label">Done</div><div class="stat-value" id="statDone">0</div></div>
    </div>

    <div class="add-card">
      <input type="text" id="taskInput" placeholder="What needs doing?" onkeydown="if(event.key==='Enter') addTask()" />
      <button class="add-btn" onclick="addTask()">＋ Add task</button>
    </div>

    <div class="filters">
      <button class="filter active" data-filter="all" onclick="setFilter('all')">All</button>
      <button class="filter" data-filter="active" onclick="setFilter('active')">Active</button>
      <button class="filter" data-filter="done" onclick="setFilter('done')">Done</button>
    </div>

    <div class="task-list" id="taskList"></div>
  </main>

  <footer>
    <span>Deployed via GitHub Actions · Terraform · Azure Container Apps</span>
    <a href="/health" target="_blank">/health</a>
  </footer>

  <script>
    let currentFilter = 'all';
    let allTasks = [];

    function setFilter(f) {
      currentFilter = f;
      document.querySelectorAll('.filter').forEach(b => b.classList.toggle('active', b.dataset.filter === f));
      render();
    }

    function render() {
      const list = document.getElementById('taskList');
      const visible = allTasks.filter(t =>
        currentFilter === 'all' ? true :
        currentFilter === 'active' ? !t.completed :
        t.completed
      );
      const total = allTasks.length;
      const done = allTasks.filter(t => t.completed).length;
      document.getElementById('statTotal').textContent = total;
      document.getElementById('statActive').textContent = total - done;
      document.getElementById('statDone').textContent = done;

      if (!visible.length) {
        const msg = currentFilter === 'all'
          ? { title: 'No tasks yet', text: 'Add your first task above to get started.' }
          : currentFilter === 'active'
          ? { title: 'Nothing to do', text: 'All your tasks are done. Nice work.' }
          : { title: 'No completed tasks', text: 'Tick something off to see it here.' };
        list.innerHTML = `
          <div class="empty">
            <div class="empty-icon">✓</div>
            <div class="empty-title">${msg.title}</div>
            <div class="empty-text">${msg.text}</div>
          </div>`;
        return;
      }
      list.innerHTML = visible.map(t => `
        <div class="task-item" id="task-${t.id}">
          <input type="checkbox" ${t.completed ? 'checked' : ''} onchange="toggle(${t.id}, this.checked)" />
          <span class="task-title ${t.completed ? 'done' : ''}">${escapeHtml(t.title)}</span>
          <button class="delete-btn" onclick="del(${t.id})" aria-label="Delete task">✕</button>
        </div>`).join('');
    }

    function escapeHtml(s) {
      return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    async function load() {
      const res = await fetch('/tasks');
      allTasks = await res.json();
      render();
    }
    async function addTask() {
      const input = document.getElementById('taskInput');
      const title = input.value.trim();
      if (!title) return;
      await fetch('/tasks', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({title}) });
      input.value = '';
      load();
    }
    async function toggle(id, completed) {
      await fetch(`/tasks/${id}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({completed}) });
      load();
    }
    async function del(id) {
      await fetch(`/tasks/${id}`, { method: 'DELETE' });
      load();
    }
    load();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
    }


@app.route("/tasks", methods=["GET"])
def list_tasks():
    with db() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return jsonify([row_to_task(r) for r in rows])


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, completed, created_at) VALUES (?, 0, ?)",
            (title, datetime.utcnow().isoformat()),
        )
        task_id = cur.lastrowid
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_task(row)), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(force=True)
    with db() as conn:
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not existing:
            return jsonify({"error": "not found"}), 404
        if "completed" in data:
            conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (1 if data["completed"] else 0, task_id))
        if "title" in data:
            conn.execute("UPDATE tasks SET title = ? WHERE id = ?", (data["title"], task_id))
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_task(row))


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with db() as conn:
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not existing:
            return jsonify({"error": "not found"}), 404
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return "", 204


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
