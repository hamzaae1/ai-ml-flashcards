# Flashcard Learning

A single self-contained HTML file with **1,721 flashcards** from three AI/ML books:

- 📘 *AI Engineering* — Chip Huyen (2025)
- 📗 *Hands-On Large Language Models* — Jay Alammar & Maarten Grootendorst (2024)
- 📕 *Hands-On Machine Learning* — Aurélien Géron (2019/2020)

No backend, no install, works offline. Progress saves per browser in `localStorage`.

## Use it

Open [`index.html`](./index.html) in any browser. That's it.

Or [download](./index.html) the file and double-click — no internet needed after that.

## Add your own book

1. Drop chapter JSON files into `data/<your-book>/` (any nested path works).
   Each file is an array of `{ "question": "...", "answer": "..." }`.
2. Add an entry to `books.json` with the book's title, description, and an
   ordered list of chapters (each chapter needs a `path` and `title`,
   optionally a `summary`).
3. Run `python3 build.py`. A new `index.html` is generated.

## License

MIT.
