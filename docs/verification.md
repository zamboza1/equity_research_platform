# Verification

The latest targeted check is [NAV draft persistence, October 26, 2026](nav-drafts-verification.md).
The October 16 record below is retained as historical evidence; its dependency
audit and broader provider checks were not rerun for the NAV change.

The October 16, 2026 follow-up starts from commit
`c7d5c62b1869aadd85307688861a0f2e25cd7f28`. `source-manifest.json` identifies the
checked source files, tests, locks and startup scripts. The manifest and this
report are excluded from the fingerprint to avoid a circular hash. The October 5
verification remains in that base commit; its broader historical coverage is not
presented as a new test run here.

## Environment and automated checks

macOS 14.6.1, Python 3.13.0, Node 25.2.1, Next 15.5.27 and React 18.3.1.
An isolated checkout used Chrome, the production frontend on localhost:3357 and
FastAPI on localhost:8357. A separate SQLite database held illustrative research
cases. Offline calculations and live-provider checks were separate phases.

- 105 backend tests passed in the locked Python environment. One existing
  Starlette/httpx deprecation warning remains.
- Frontend type checking, lint and the production build passed. The build retains
  the existing warning that the Next ESLint plugin is not configured.
- Exact dependency locks installed successfully; `uv pip check` found no conflicts.
  npm audit reported zero vulnerabilities; pip-audit reported zero known
  vulnerabilities across 53 Python packages. No dependency versions changed.
  Recharts 2.15.4 and ESLint 9.39.5 have registry deprecation notices; zero reported
  vulnerabilities does not establish ongoing support.
- Ten regression cases cover the legacy macro helper's OLS p-value, invalid input
  and insufficient inference data. An independent three-point case gives beta
  0.5, R² 0.25 and p-value 2/3. This helper is not the routed macro dashboard.
- Seven workbook cases cover 1/5/30-year horizons, numeric cells, negative and zero
  flows, fractional capex, statement ties, literal user labels, unset day drivers
  and rejected missing, unbalanced or inconsistent inputs.

## Real browser checks

| Workflow | Observed result |
| --- | --- |
| DCF | One-year illustrative case: FCFF 14.2, enterprise value 188.41, equity value 168.41 and price 16.84; sensitivity center matched. Save/change/restore returned WACC to 10%. Malformed pasted JSON and WACC equal to terminal growth showed errors. |
| DCF simulation | 1,000 draws with the default seed and dispersions returned mean 16.99, P5/P95 15.08/19.09 and no excluded draws. These are assumed scenario outcomes. |
| DDM and NAV | Gordon 67.20; zero dividend 0.00; zero high-growth-rate multistage 34.58. Real-estate NAV 15 and resource NAV 235. Blank fields remained blank and were rejected; zero cap rate was rejected. |
| Statements | Default and fractional growth-capex 0.5 cases reconciled. Blank annual growth, COGS, capex and fixed expenses failed validation. Save/change/restore retained day-based assumptions and removed stale results. |
| Excel download | The actual browser download contains four formatted tabs, years across columns, numeric amounts, accounting formats, frozen labels/headers, recorded assumptions and reconciliation differences. All tabs were rendered and inspected. Year-one revenue is 1,100,000; capex is -33,000.5; stored depreciation is 39,567.52375 and displays as 39,567.52. The original download stored financial values as text. |
| Model guides | DDM guide opens with labelled step controls. Tab and Shift+Tab stay within the dialog; Escape closes it and returns focus to the opener. The statement formula now includes depreciation. |
| Model Builder | Five-year forecast PV 64.545455; year-two growth of 5% gave 62.694215. Revenue overrides 80/100/120 gave 50.155372/62.694215/75.233058. Two-way sensitivity matched these points. Uniform revenue 90–110, seed 7 and 100 draws gave mean 62.492106 and P5/P95 56.868841/68.070342. Save/change/restore recovered revenue 100. Dependency graph and simulation histogram rendered. |
| Research and report | Created an illustrative case; saved thesis, risks, invalidation condition, a source reference and catalyst as revision 2. Revision history retained revision 1. The exact revision report displayed the saved notes, source caveat and 21.87 scenario-weighted value. Markdown download was exercised. |
| Responsive layouts | Actual viewport and document width were both 390 px for valuations, projected statements and the REIT primer. Statement tables stayed within their scroll containers. Navigation opened, selected the primer and closed; the guide formula wrapped within the mobile dialog. Desktop checks used 1440 px. |
| Education | The revised REIT primer rendered the current NAV controls, Nareit definition links and the independently checked 15 / 11.67 illustrative NAV examples. |

## Separate live-provider checks

The existing FRED credential was loaded privately, remained ignored by Git and
was not changed. With `VERTIGE_OFFLINE=0`, the browser status showed providers
enabled and FRED configured. Earlier deliberate offline mode was clearly labelled.

- Macro observations loaded US CPI growth 3.72%, Canadian CPI growth 3.03%, US
  unemployment 4.20% and Canadian unemployment 6.40%. The page dated US CPI and
  unemployment to September 2026 and Canadian CPI/unemployment to August 2026.
  The unemployment selector, chart and observation table rendered missing records
  as unavailable, not zero.
- The Treasury curve used October 14, 2026 observations: 2Y 4.82%, 10Y 5.19% and
  their 37-basis-point spread. Source-series links and the common observation date
  were visible.
- Quant statistics loaded 251 AAPL returns and matched benchmark intervals through
  October 16. Rolling-risk and distribution views rendered and observations were
  downloaded. Displayed beta was 0.65 and Sharpe ratio 1.32; these latest live
  values were smoke-checked, not independently rederived in this follow-up.
- AAPL/MSFT/GOOGL comparables loaded financial periods and currencies. Excluding
  AAPL left two peers; assumed EPS 4 produced 89.11 / 89.24 / 89.38 at the 25th,
  median and 75th peer percentiles. Source periods remained visible.

## Limits

Native file-picker imports and native print-to-PDF output remain unverified in
this follow-up. A whole-Chrome accessibility inspection was rejected because it
could expose unrelated private tabs; further work used owned-page APIs only.
No broader browser access was used to bypass that restriction. Backend import
checks do not substitute for a native browser import test.

Installed extensions produced a content-script error and message-channel errors.
No application calculation crash was observed. This is not a comprehensive
accessibility, browser-extension compatibility or absence-of-defects claim.
FinBERT, live sentiment, broad symbol/provider coverage, touch dragging and every
research conflict/recovery branch were not rerun. Earlier results remain dated.

Excel exports are calculated snapshots, not linked Excel models. Native Excel
print pagination was not checked. Monetary units and relative years are retained;
no currency, scale or calendar year is inferred. Excel's numeric precision limit
still applies. The app remains local without authentication; model assumptions
and retained legacy helper limits are in `model-conventions.md`.
