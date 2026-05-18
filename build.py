#!/usr/bin/env python3
"""
Build a single self-contained index.html from books.json + data/*.json.

Usage:
    python3 build.py

To add a new book later:
    1. Drop chapter JSON files into data/<your-book>/
       (or data/<your-book>/part1/, part2/ — any path works)
    2. Add an entry to books.json with title, description, and an ordered
       list of chapters. Each chapter has a "path" (relative to data/) and
       a "title".
    3. Re-run: python3 build.py
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
BOOKS_FILE = ROOT / "books.json"
OUTPUT = ROOT / "index.html"


def card_id(question: str, answer: str) -> str:
    """Stable per-card ID that survives reordering and book/chapter renames."""
    h = hashlib.sha1((question + "||" + answer[:80]).encode("utf-8")).hexdigest()
    return h[:12]


def load_book(book_meta: dict, book_idx: int) -> dict:
    chapters = []
    for ch_idx, ch in enumerate(book_meta["chapters"]):
        ch_path = DATA_DIR / ch["path"]
        if not ch_path.exists():
            sys.exit(f"ERROR: missing chapter file {ch_path}")
        raw = json.loads(ch_path.read_text(encoding="utf-8"))
        cards = []
        seen = set()
        for card in raw:
            q, a = card["question"], card["answer"]
            cid = card_id(q, a)
            # On rare hash collision within a chapter, append index
            if cid in seen:
                cid = card_id(q + f"#{len(cards)}", a)
            seen.add(cid)
            cards.append({"id": cid, "q": q, "a": a})
        chapters.append({
            "id": f"b{book_idx}c{ch_idx}",
            "title": ch["title"],
            "summary": ch.get("summary", ""),
            "cards": cards,
        })
    return {
        "id": f"b{book_idx}",
        "title": book_meta["title"],
        "description": book_meta["description"],
        "chapters": chapters,
    }


def main():
    books_meta = json.loads(BOOKS_FILE.read_text(encoding="utf-8"))
    books = [load_book(b, i) for i, b in enumerate(books_meta)]

    total_cards = sum(len(c["cards"]) for b in books for c in b["chapters"])
    total_chapters = sum(len(b["chapters"]) for b in books)
    print(f"Loaded {len(books)} books, {total_chapters} chapters, {total_cards} cards")

    data_json = json.dumps({"books": books}, ensure_ascii=False, separators=(",", ":"))
    # Safe-embed inside <script>: only </ is dangerous
    data_json = data_json.replace("</", "<\\/")

    html = TEMPLATE.replace("__DATA__", data_json)
    OUTPUT.write_text(html, encoding="utf-8")
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"Wrote {OUTPUT.name} ({size_kb:.1f} KB)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flashcard Learning</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --glass: rgba(255, 255, 255, 0.10);
    --glass-hover: rgba(255, 255, 255, 0.18);
    --glass-strong: rgba(255, 255, 255, 0.22);
    --white-80: rgba(255, 255, 255, 0.80);
    --white-70: rgba(255, 255, 255, 0.70);
    --white-60: rgba(255, 255, 255, 0.60);
    --green: linear-gradient(90deg, #4ade80, #22c55e);
    --accent: #fde047;
  }
  html, body {
    min-height: 100%;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    color: #fff;
  }
  body {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
    background-attachment: fixed;
    min-height: 100vh;
    padding: 2rem 1rem 4rem;
  }
  .container { max-width: 1200px; margin: 0 auto; }
  header.app-header { text-align: center; margin-bottom: 2rem; }
  header.app-header h1 { font-size: 2.25rem; font-weight: 700; margin-bottom: 0.25rem; }
  header.app-header p { color: var(--white-80); font-size: 1.05rem; }

  .crumb-bar {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--glass); backdrop-filter: blur(10px);
    border-radius: 0.75rem; padding: 1rem 1.25rem; margin-bottom: 1.5rem;
  }
  .crumb-bar h2 { font-size: 1.35rem; font-weight: 600; line-height: 1.3; }
  .crumb-bar p { color: var(--white-80); font-size: 0.95rem; margin-top: 0.1rem; }
  .btn {
    background: var(--glass); border: 0; color: #fff; cursor: pointer;
    padding: 0.55rem 1rem; border-radius: 0.5rem; font-size: 0.9rem;
    transition: background-color 0.15s ease, transform 0.05s ease;
    font-family: inherit;
  }
  .btn:hover:not(:disabled) { background: var(--glass-hover); }
  .btn:active:not(:disabled) { transform: translateY(1px); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-green { background: #16a34a; }
  .btn-green:hover:not(:disabled) { background: #15803d; }
  .btn-red { background: #dc2626; }
  .btn-red:hover:not(:disabled) { background: #b91c1c; }

  .grid {
    display: grid; gap: 1.25rem;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }

  .card-tile {
    background: var(--glass); backdrop-filter: blur(10px);
    border-radius: 0.85rem; padding: 1.25rem; cursor: pointer;
    transition: background-color 0.2s ease, transform 0.15s ease;
    border: 1px solid rgba(255,255,255,0.08);
  }
  .card-tile:hover { background: var(--glass-hover); transform: translateY(-2px); }
  .card-tile h3 { font-size: 1.15rem; font-weight: 600; line-height: 1.3; margin-bottom: 0.5rem; }
  .card-tile .desc { color: var(--white-70); font-size: 0.85rem; line-height: 1.45; margin-bottom: 1rem; }
  .meta-row {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.85rem; margin-bottom: 0.5rem;
  }
  .meta-row .label { color: var(--white-70); }
  .meta-row .done { color: #86efac; font-weight: 500; }
  .progress-track {
    width: 100%; height: 6px; background: rgba(255,255,255,0.18);
    border-radius: 999px; overflow: hidden; margin-top: 0.4rem;
  }
  .progress-bar { height: 100%; background: var(--green); transition: width 0.4s ease; }
  .progress-pct { text-align: center; font-size: 0.8rem; color: var(--white-80); margin-top: 0.5rem; }

  /* Flashcard view */
  .deck-progress {
    background: var(--glass); backdrop-filter: blur(10px);
    border-radius: 0.75rem; padding: 0.9rem 1.25rem; margin-bottom: 1.5rem;
  }
  .deck-progress-head {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.95rem; margin-bottom: 0.5rem;
  }
  .deck-progress-head .right { color: var(--white-70); font-size: 0.85rem; }

  .flashcard-wrap {
    position: relative;
    perspective: 1500px;
    max-width: 720px; margin: 0 auto;
  }
  .card-status-dot {
    position: absolute; top: 0.85rem; right: 0.85rem;
    width: 14px; height: 14px; border-radius: 999px;
    background: transparent;
    border: 2px solid #6b7280;
    z-index: 5; transition: background-color 0.2s ease, border-color 0.2s ease;
    pointer-events: none;
  }
  .card-status-dot.done {
    background: #22c55e; border-color: #15803d;
  }
  .flashcard {
    position: relative; width: 100%; min-height: 22rem;
    transform-style: preserve-3d;
    transition: transform 0.6s cubic-bezier(0.4, 0.0, 0.2, 1);
    cursor: pointer;
  }
  .flashcard.flipped { transform: rotateY(180deg); }
  .face {
    position: absolute; inset: 0;
    backface-visibility: hidden; -webkit-backface-visibility: hidden;
    border-radius: 1rem; padding: 2rem;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
  }
  .face-front { background: rgba(255, 255, 255, 0.97); color: #1f2937; }
  .face-back  {
    background: linear-gradient(135deg, #4ade80 0%, #3b82f6 100%);
    color: #fff; transform: rotateY(180deg);
  }
  .face .pill {
    width: 3rem; height: 3rem; border-radius: 999px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.35rem; font-weight: 700; margin-bottom: 0.75rem;
  }
  .face-front .pill { background: #3b82f6; color: #fff; }
  .face-back .pill { background: rgba(255,255,255,0.25); color: #fff; }
  .face .label-tag { font-size: 0.95rem; color: #6b7280; font-weight: 600; margin-bottom: 0.75rem; }
  .face-back .label-tag { color: rgba(255,255,255,0.85); }
  .face .body-text { font-size: 1.15rem; line-height: 1.6; max-width: 95%; }
  .face .hint { margin-top: 1rem; font-size: 0.85rem; color: #9ca3af; }
  .face-back .hint { color: rgba(255,255,255,0.8); }

  .deck-controls {
    display: flex; justify-content: center; gap: 0.75rem; margin-top: 1.5rem;
    flex-wrap: wrap;
  }

  .completion {
    text-align: center; padding: 2rem;
    background: var(--glass); backdrop-filter: blur(10px);
    border-radius: 1rem; margin-top: 2rem;
  }
  .completion .emoji { font-size: 3rem; margin-bottom: 0.5rem; }
  .completion h3 { font-size: 1.5rem; margin-bottom: 0.5rem; }
  .completion p { color: var(--white-80); margin-bottom: 1rem; }

  /* app footer */
  .app-footer {
    text-align: center; color: var(--white-60);
    font-size: 0.82rem; margin-top: 3rem;
    padding-top: 1.25rem; border-top: 1px solid rgba(255,255,255,0.08);
  }

  /* completed dot on tiles */
  .completed-dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 999px; background: #4ade80; margin-left: 0.4rem;
    vertical-align: middle;
  }

  /* description paragraph under chapter titles on tiles */
  .tile-summary {
    color: var(--white-70); font-size: 0.84rem;
    line-height: 1.5; margin-bottom: 0.9rem;
  }

  /* collapsible "About this chapter" panel above the deck */
  .learn-panel {
    background: var(--glass); backdrop-filter: blur(10px);
    border-radius: 0.75rem; padding: 0.85rem 1.25rem; margin-bottom: 1.25rem;
    border: 1px solid rgba(255,255,255,0.08);
  }
  .learn-panel > summary {
    cursor: pointer; list-style: none;
    font-weight: 600; font-size: 0.98rem; color: #fff;
    display: flex; align-items: center; justify-content: space-between;
    user-select: none;
  }
  .learn-panel > summary::-webkit-details-marker { display: none; }
  .learn-panel > summary::after {
    content: "▾"; font-size: 0.8rem; color: var(--white-70);
    transition: transform 0.2s ease;
  }
  .learn-panel:not([open]) > summary::after { transform: rotate(-90deg); }
  .learn-panel .panel-summary {
    color: var(--white-80); font-size: 0.95rem;
    margin: 0.75rem 0 0.1rem; line-height: 1.55;
  }

  /* Mobile tweaks */
  @media (max-width: 600px) {
    header.app-header h1 { font-size: 1.7rem; }
    .crumb-bar { flex-direction: column; gap: 0.75rem; align-items: flex-start; }
    .flashcard { min-height: 26rem; }
    .face .body-text { font-size: 1rem; }
  }
</style>
</head>
<body>
  <div class="container">
    <header class="app-header">
      <h1>Flashcard Learning</h1>
    </header>
    <div id="app"></div>
    <footer class="app-footer">Built by Hamza Mhedhbi</footer>
  </div>

<script id="flashcard-data" type="application/json">__DATA__</script>
<script>
(function () {
  "use strict";

  const DATA = JSON.parse(document.getElementById("flashcard-data").textContent);
  const STORAGE_KEY = "flashcard-progress-v1";
  const app = document.getElementById("app");

  // ---------- progress (localStorage) ----------
  function loadProgress() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (_) { return {}; }
  }
  function saveProgress(p) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(p)); } catch (_) {}
  }
  let progress = loadProgress();

  function isDone(cardId) { return progress[cardId] === true; }
  function setDone(cardId, done) {
    if (done) progress[cardId] = true;
    else delete progress[cardId];
    saveProgress(progress);
  }
  function chapterStats(ch) {
    let done = 0;
    for (const c of ch.cards) if (isDone(c.id)) done++;
    return { total: ch.cards.length, done };
  }
  function bookStats(b) {
    let total = 0, done = 0;
    for (const ch of b.chapters) {
      const s = chapterStats(ch);
      total += s.total; done += s.done;
    }
    return { total, done };
  }

  // ---------- view state ----------
  const state = { view: "books", bookIdx: 0, chapterIdx: 0, cardIdx: 0, flipped: false, justFinished: false };

  function go(view, opts) {
    state.view = view;
    if (opts) Object.assign(state, opts);
    state.flipped = false;
    state.justFinished = false;
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ---------- helpers ----------
  function el(tag, attrs, children) {
    const e = document.createElement(tag);
    if (attrs) {
      for (const k in attrs) {
        const v = attrs[k];
        if (v == null) continue;
        if (k === "class") e.className = v;
        else if (k === "onclick") e.addEventListener("click", v);
        else if (k === "html") e.innerHTML = v;
        else e.setAttribute(k, v);
      }
    }
    if (children) {
      for (const c of children) {
        if (c == null) continue;
        e.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
      }
    }
    return e;
  }
  function pct(done, total) { return total === 0 ? 0 : Math.round((done / total) * 100); }

  function progressBlock(done, total) {
    const p = pct(done, total);
    return el("div", null, [
      el("div", { class: "meta-row" }, [
        el("span", { class: "label" }, ["Cards"]),
        el("span", null, [String(total)]),
      ]),
      el("div", { class: "meta-row" }, [
        el("span", { class: "label" }, ["Done"]),
        el("span", { class: "done" }, [String(done)]),
      ]),
      el("div", { class: "progress-track" }, [
        el("div", { class: "progress-bar", style: "width:" + p + "%" }),
      ]),
      el("div", { class: "progress-pct" }, [p + "% complete"]),
    ]);
  }

  // ---------- views ----------
  function renderBooks() {
    const grid = el("div", { class: "grid" });
    DATA.books.forEach(function (b, i) {
      const s = bookStats(b);
      const tile = el("div", { class: "card-tile", onclick: function () { go("chapters", { bookIdx: i }); } }, [
        el("h3", null, [b.title]),
        el("p", { class: "desc" }, [b.description]),
        progressBlock(s.done, s.total),
      ]);
      grid.appendChild(tile);
    });
    return el("div", null, [
      el("div", { class: "crumb-bar" }, [
        el("div", null, [
          el("h2", null, ["Choose a book"]),
          el("p", null, [DATA.books.length + " books — pick one to start"]),
        ]),
      ]),
      grid,
    ]);
  }

  function renderChapters() {
    const book = DATA.books[state.bookIdx];
    const grid = el("div", { class: "grid" });
    book.chapters.forEach(function (ch, i) {
      const s = chapterStats(ch);
      const headerKids = [ch.title];
      if (s.total > 0 && s.done === s.total) headerKids.push(el("span", { class: "completed-dot", title: "Completed" }));
      const tile = el("div", { class: "card-tile", onclick: function () { go("cards", { chapterIdx: i, cardIdx: 0 }); } }, [
        el("h3", null, headerKids),
        ch.summary ? el("p", { class: "tile-summary" }, [ch.summary]) : null,
        progressBlock(s.done, s.total),
      ]);
      grid.appendChild(tile);
    });
    return el("div", null, [
      el("div", { class: "crumb-bar" }, [
        el("div", null, [
          el("h2", null, [book.title]),
          el("p", null, ["Choose a chapter"]),
        ]),
        el("button", { class: "btn", onclick: function () { go("books"); } }, ["← Books"]),
      ]),
      grid,
    ]);
  }

  function renderCards() {
    const book = DATA.books[state.bookIdx];
    const ch = book.chapters[state.chapterIdx];
    if (!ch.cards.length) {
      return el("div", { class: "crumb-bar" }, [el("p", null, ["This chapter has no cards yet."])]);
    }
    const idx = state.cardIdx;
    const card = ch.cards[idx];
    const total = ch.cards.length;
    const stats = chapterStats(ch);

    const flashcard = el("div", { class: "flashcard" + (state.flipped ? " flipped" : "") }, [
      el("div", { class: "face face-front" }, [
        el("div", { class: "pill" }, ["?"]),
        el("div", { class: "label-tag" }, ["Question"]),
        el("p", { class: "body-text" }, [card.q]),
        el("p", { class: "hint" }, ["Click to reveal answer"]),
      ]),
      el("div", { class: "face face-back" }, [
        el("div", { class: "pill" }, ["✓"]),
        el("div", { class: "label-tag" }, ["Answer"]),
        el("p", { class: "body-text" }, [card.a]),
        el("p", { class: "hint" }, ["Click to flip back"]),
      ]),
    ]);
    flashcard.addEventListener("click", function () {
      state.flipped = !state.flipped;
      flashcard.classList.toggle("flipped");
    });

    function next() {
      // Auto-mark current card as complete and advance.
      setDone(card.id, true);
      if (idx < total - 1) {
        state.cardIdx = idx + 1; state.flipped = false; state.justFinished = false;
      } else {
        state.justFinished = true;
      }
      render();
    }
    function prev() {
      if (idx > 0) {
        state.cardIdx = idx - 1; state.flipped = false; state.justFinished = false;
        render();
      }
    }
    function resetChapter() {
      if (!confirm("Reset progress for this chapter?")) return;
      for (const c of ch.cards) setDone(c.id, false);
      state.cardIdx = 0; state.flipped = false; state.justFinished = false;
      render();
    }

    const isLast = idx === total - 1;
    const allDone = stats.done === total;
    const cardDone = isDone(card.id);

    const controls = el("div", { class: "deck-controls" }, [
      el("button", { class: "btn", onclick: function () { go("chapters"); } }, ["← Chapters"]),
      el("button", { class: "btn", onclick: prev, disabled: idx === 0 ? "" : null }, ["← Previous"]),
      el("button", { class: "btn", onclick: resetChapter }, ["↻ Reset"]),
      el("button", { class: "btn btn-green", onclick: next }, [isLast ? "✓ Finish" : "✓ Got it →"]),
    ]);

    const completion = (state.justFinished && allDone)
      ? el("div", { class: "completion" }, [
          el("div", { class: "emoji" }, ["🎉"]),
          el("h3", null, ["Chapter complete!"]),
          el("p", null, ["You've marked every card in this chapter."]),
          el("button", { class: "btn", onclick: function () { go("chapters"); } }, ["Back to chapters"]),
        ])
      : null;

    const learnPanel = ch.summary
      ? el("details", { class: "learn-panel", open: "" }, [
          el("summary", null, ["📖 About this chapter"]),
          el("p", { class: "panel-summary" }, [ch.summary]),
        ])
      : null;

    const p = pct(stats.done, total);
    return el("div", null, [
      el("div", { class: "crumb-bar" }, [
        el("div", null, [
          el("h2", null, [ch.title]),
          el("p", null, [book.title]),
        ]),
        el("button", { class: "btn", onclick: function () { go("chapters"); } }, ["← Chapters"]),
      ]),
      learnPanel,
      el("div", { class: "deck-progress" }, [
        el("div", { class: "deck-progress-head" }, [
          el("span", null, ["Card " + (idx + 1) + " of " + total + (cardDone ? " ✓" : "")]),
          el("span", { class: "right" }, [stats.done + " / " + total + " completed (" + p + "%)"]),
        ]),
        el("div", { class: "progress-track" }, [
          el("div", { class: "progress-bar", style: "width:" + p + "%" }),
        ]),
      ]),
      el("div", { class: "flashcard-wrap" }, [
        el("div", {
          class: "card-status-dot" + (cardDone ? " done" : ""),
          title: cardDone ? "Marked complete" : "Not yet marked",
        }),
        flashcard,
      ]),
      controls,
      completion,
    ]);
  }

  function render() {
    app.innerHTML = "";
    let view;
    if (state.view === "books") view = renderBooks();
    else if (state.view === "chapters") view = renderChapters();
    else view = renderCards();
    app.appendChild(view);
  }

  // ---------- keyboard nav ----------
  document.addEventListener("keydown", function (e) {
    if (state.view !== "cards") return;
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) return;
    const book = DATA.books[state.bookIdx];
    const ch = book.chapters[state.chapterIdx];
    const card = ch.cards[state.cardIdx];
    if (e.key === "ArrowRight") {
      // Auto-mark complete and advance (matches Next button).
      setDone(card.id, true);
      if (state.cardIdx < ch.cards.length - 1) {
        state.cardIdx++; state.flipped = false; state.justFinished = false;
      } else {
        state.justFinished = true;
      }
      render();
    } else if (e.key === "ArrowLeft") {
      if (state.cardIdx > 0) {
        state.cardIdx--; state.flipped = false; state.justFinished = false;
        render();
      }
    } else if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      state.flipped = !state.flipped;
      render();
    }
  });

  render();
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
