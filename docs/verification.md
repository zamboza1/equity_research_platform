# Verification

Release 1.2.0 was checked on October 5, 2026. The tested source is identified by
`source-manifest.json`; its file hashes cover the application, tests, dependency
locks and startup scripts. Documentation of the evidence is excluded from that
fingerprint to avoid a circular hash. This is a dated verification record, not a
claim that every possible defect has been found.

## Environment

macOS 14.6.1, Python 3.13.0, Node 25.2.1, Next 15.5.27 and React 18.3.1.
Chrome exercised the production frontend on port 3347 against FastAPI on 8347.
An isolated SQLite database held synthetic research cases. Earlier offline
valuation checks used ports 3327 and 8327. Original project files were preserved.

## Automated checks

- 88 backend tests passed. One Starlette/httpx deprecation warning remains.
- Frontend type checking, lint and production build passed.
- npm audit reported zero vulnerabilities; pip-audit reported zero known
  vulnerabilities across 53 Python packages. `uv pip check` found no dependency
  conflicts. These results describe the installed locks on the test date.
- Backend tests block outbound networking. Independent calculations check DCF
  values, scenario weighting, sensitivity and statement reconciliations.
- Formula regressions cover dependency order, missing references, cycles, syntax,
  blank versus zero inputs, supported functions and excessive numeric operations.
- Independent checks cover multi-year cash flow, scenario overrides, sensitivity,
  seeded simulation, relative valuation, matched benchmark intervals, rolling
  volatility, partial provider failure and Treasury spread units.

## Real browser checks

| Workflow | Observed result |
| --- | --- |
| DCF and sensitivity | A one-year synthetic case produced FCFF 14.2, enterprise value 188.41, equity value 168.41 and price 16.84. The sensitivity center matched. Invalid WACC cleared prior output and showed an error. Save/reload/restore retained inputs. |
| Monte Carlo | Seeded 1,000-draw run: mean 16.99, 5th–95th percentiles 15.08–19.09, zero excluded draws. These are scenario outcomes. |
| Dividend and NAV models | Gordon value 67.20; zero high-growth-rate multistage value 34.58. Real-estate NAV value 15 and resource example 235. Invalid cap rate rejected. |
| Linked statements | Default and imported CSV cases reconciled. Save/restore retained day-based drivers; inconsistent opening balances were rejected. |
| Research cases | Created and revised synthetic company research. Bear/base/bull values 13.06 / 16.84 / 23.15 at weights 25% / 50% / 25% produced 17.47. Invalid weights were rejected without saving results. |
| Evidence and revisions | Saved thesis, risks, invalidation notes, source link, catalyst and review date. Two-tab conflicting saves returned 409 and retained the losing draft. Comparing the latest revision allowed an explicit merge. Browser draft recovery retained unsaved text and date. Revision 1 remained unchanged after revision 6. |
| Reports and import | Opened the exact revision report, downloaded and inspected its JSON, then imported it through the browser as a separate case. The new case started at revision 1 and recalculated to 17.47. Archiving and library filters worked, including no-match results. |
| Formula builder | Edited revenue from 100 to 120, yielding revenue 132 and EBIT 33. Added a tax input and formula yielding 24.75. Missing references, cycles, blank inputs and malformed syntax showed readable errors. Save/restore and downloaded JSON import returned EBIT 33. |
| Builder examples and functions | Dividend perpetuity returned 62.5; operating-profit bridge returned 100. `round(sum([1.111, 2.222]), 2)` returned 3.33. List multiplication was rejected before allocation. Labels now identify decimal rates. |
| Multi-year builder | The five-year template returned forecast PV 64.545455. Changing year-two growth to 5% returned 62.694215, independently reproduced from annual cash flows. Revenue overrides 80/100/120 returned 50.155372/62.694215/75.233058. Input search/filter controls worked. |
| Advanced builder analysis | Two-way revenue/tax sensitivity matched the baseline center; malformed value lists cleared results and showed errors. Uniform opening revenue 90–110, 100 draws, seed 7 returned mean 62.492106 and P5/P95 56.868841/68.070342. Named templates retained settings through reload, reproduced the simulation and supported a separate saved copy. CSV contained inputs, formulas, settings and results. |
| Custom comparables | A live AAPL/MSFT/GOOGL basket loaded source periods and multiples. Excluding AAPL cleared old valuation results; EPS 4 with the two remaining peers returned 89.77/90.39/91.01. Downloaded data independently reproduced these values. Saved basket exclusions survived reload. The EBITDA bridge also calculated through the UI. |
| Quantitative analysis | AAPL one-year observations, optional S&P 500 benchmark, performance/drawdown/rolling-risk/distribution views and three-month/risk-free settings worked. Editing cleared old results; saved settings restored. All 250 exported returns, drawdowns and rolling windows agreed with independent calculations within 1e-10. Beta 0.711300, Sharpe 1.047502 and tracking error 0.232298 matched the displayed rounding. |
| Macro exploration | Longer history, unemployment/rate selectors, observation table and CSV worked. Exported CPI independently reproduced US 3.353016% and Canada 3.033981%. Same-date Treasury yields on 2026-10-01 were 4.78% for 2Y and 5.24% for 10Y, producing 46 basis points. Missing year-ago CPI remained unavailable. |
| Provider-to-research handoff | Start research from MSFT prefilled identity. Loading a live provider baseline supplied financial inputs and a dated source note. The saved case remained illustrative because forecast assumptions and diluted shares still require review. |
| DCF simulation and JSON | With 20 draws, seed 7 and both dispersions zero, the five-year illustrative case returned 21.08 for deterministic value, mean and both percentiles. Browser export, editing revenue and pasted JSON import restored revenue 1,000 and recalculated 21.08. Blank annual growth removed results and triggered required-field validation. |
| Layout | Five arranged graph cards measured 250 × 109 px with no pairwise overlap. Zoom changed card width to 300 px; fit restored the overview. At a 390 px viewport, the builder document stayed 390 px wide and the graph canvas was 292 px wide. The report also stayed within 390 px, with tables scrolling inside their containers. Mobile navigation opened and closed. |
| Expanded layouts | At 390 px, the builder simulation chart measured 283 px, statistics and macro charts 294 px. A reproduced comparables overflow (1,030 px document) was corrected with a shrinkable fieldset; the retest kept the document at 390 px and scrolled its 950 px table inside a 294 px container. |
| Failure states and content | Exercised offline provider errors, unsupported sector errors and recovery, educational example labels, and primer navigation. Unavailable data did not become invented rows or charts. |

Chrome's installed extensions produced content-script and message-channel errors
during the latest checks. No application calculation crash was observed. A prior
fresh production smoke check returned no console warnings or errors. This is not
a browser-extension compatibility or comprehensive accessibility certification.

## Live data checks

Live tests were separate from the synthetic valuation cases. The initial disabled
state came from the audit server's `VERTIGE_OFFLINE=1` setting and missing local
configuration in the isolated copy. The existing FRED key was restored locally;
it is excluded from Git. The status endpoint exposes configuration booleans only.

On October 5, Yahoo Finance returned an AAPL quote through the API. The macro page
rendered US CPI growth 3.35%, unemployment 4.2%, Canadian CPI growth 3.03% and
unemployment 6.4%. Source observations were August or September 2026 and the page
displayed those dates. Canadian CPI uses Bank of Canada series V41690973, sourced
from Statistics Canada, replacing an invalid/stale FRED series. A failed Canadian
request no longer hides available US data.

## Limits

Native browser file-picker testing of standalone DCF JSON import and statement
XLSX imports/downloads was interrupted by tool timeouts. DCF browser download and
paste import, backend export checks and research/builder JSON browser round trips
passed; they do not establish the remaining native file workflows. The printable report page was inspected, but
native print-to-PDF output was not checked. FinBERT, live news sentiment, broad
provider and symbol coverage, touch dragging and full keyboard/screen
reader behavior remain unverified. Current provider availability and future data
updates are not guaranteed.

The app remains local and has no authentication. Simplified financial conventions
and incomplete legacy helpers are described in `model-conventions.md`.
