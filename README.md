# Vertige Research Platform

A local equity research workspace for company notes, scenario valuations and financial models. Save the evidence behind a thesis, compare bear/base/bull cases, and export a report with the assumptions used for each revision.

## How It Works

**Research desk:** Keep company research, sources, catalysts, risks and review dates together. Three editable DCF scenarios produce a weighted value and sensitivity table. Saved revisions retain their inputs and results; conflicting edits are rejected. Browser drafts can be recovered, and JSON imports recalculate the supplied assumptions.

**Model builder:** Create formulas or start with a one-to-ten-year cash-flow schedule. Edit annual drivers, compare input scenarios, run two-variable sensitivity and seeded simulations, and save named templates with their analysis settings. JSON preserves the model; CSV exports record the calculation inputs and results.

**Research tools:** Build custom peer baskets, exclude unsuitable companies and apply earnings, book-value or EBITDA multiples. Explore historical returns, benchmark exposure, drawdowns and rolling volatility. Macro tools provide monthly histories and a dated Treasury curve. Tables export to CSV with source information. A peer can seed a research case with provider inputs; forecasts remain illustrative until reviewed.

**Backend:** FastAPI provides DCF, dividend and asset valuations, linked financial statements, a bounded formula graph, and SQLite research storage. Yahoo Finance supplies optional company data. FRED supplies US macro data and Canadian unemployment and bond yields; Bank of Canada supplies Statistics Canada CPI.

**Frontend:** Next.js provides the research library, model editors, calculation tables and charts. Reports open as printable pages and export to Markdown or JSON. The interface follows Vertige's navy, blue and gold palette, with text navigation and visible source dates.

## Engineering Standards

**Mathematics:** Independent reference calculations cover valuation outputs and accounting reconciliations. Units, terminal assumptions and limitations are documented in [Model conventions](docs/model-conventions.md).

**Resilience:** Invalid inputs do not produce saved results. Optimistic revision checks protect concurrent work, and changes hide outdated valuations. Provider failures remain visible; missing data is not replaced with invented figures. An on-screen status distinguishes offline mode from missing configuration.

**Scope:** This is a local application without authentication, not a public multiuser service. Research inputs and weights are analyst assumptions. Source links are references, not independent verification. Legacy LBO, M&A and accounting-conversion helpers are not complete workflows.

## Run It Yourself

Use Python 3.13 and Node 20.9 or later.

```sh
python3.13 -m venv backend/.venv313
backend/.venv313/bin/python -m pip install -r backend/requirements-lock.txt
cd frontend
npm ci
cd ..
./start.sh
```

Open [Vertige locally](http://127.0.0.1:3327). The backend uses port 8327. Both bind to loopback. Set `BACKEND_PORT`, `FRONTEND_PORT` or `BACKEND_PYTHON` to override the defaults.

For macro data, copy `backend/.env.example` to `backend/.env`, add your FRED key, and restart. Keys stay on the backend; `.env` files are excluded from Git. Yahoo Finance and Bank of Canada do not require keys. `VERTIGE_OFFLINE=1 ./start.sh` explicitly disables external data for testing; use `VERTIGE_OFFLINE=0` for live providers. Environment variables take precedence over `.env`.

Research cases are stored in `backend/data/research.sqlite3`; `VERTIGE_RESEARCH_DB` can set a different path. Back up the database while the backend is stopped, or export individual cases. JSON import creates a separate case and recalculates it with the current engine. It does not import another case's revision history.

For a production frontend, set `BACKEND_URL=http://127.0.0.1:8327` before `npm run build`, then use `npm start -- --hostname 127.0.0.1 --port 3327` from `frontend`. Start the backend separately. Keep the service local unless authentication and deployment controls are added.

## Testing

```sh
cd backend
.venv313/bin/python -m pytest tests -q
cd ../frontend
npm run typecheck
npm run lint
npm run build
```

Automated tests use fixtures with outbound networking blocked. Real browser workflows and separate live-provider checks are documented in [Verification](docs/verification.md). Optional FinBERT requires separately installed `transformers` and `torch` plus `VERTIGE_ENABLE_FINBERT=1`; the default news method is labeled keyword-based sentiment.

## License

[MIT](LICENSE) - Built for learning. Not financial advice.
