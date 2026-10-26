# NAV draft verification — October 26, 2026

Base revision: `812a0008fdec2701b6a914335e3d27f4e82b56e1`. The runtime files,
tests, locks and startup scripts are identified in `nav-draft-source-manifest.json`.
This is a targeted follow-up to the October 17 workflow audit, not a new audit of
every model. GitHub main was still `c7d5c62b1869aadd85307688861a0f2e25cd7f28`.

## Change and evidence

The audit reproduced NAV inputs resetting when its component unmounted on a model
switch. The valuation page now retains separate real-estate and resource drafts.
Explicit save/restore uses a versioned browser snapshot, validates its shape and
preserves incomplete fields as null rather than zero. Restoring or editing clears
derived results. Leaving a pending calculation cancels the client request.

Fault injection also reproduced a startup crash: the shared assumptions provider
read browser storage outside its error guard. The read now occurs inside the
guard, so denied storage does not prevent the NAV screen from loading. NAV save
and restore still report their own storage errors and retain the current inputs.
No backend formula, dependency version or brand palette changed.

## Environment and checks

macOS 14.6.1, Python 3.13.0, Node 25.2.1, Next 15.5.27, React 18.3.1 and Chrome
155.0.8059.85. Isolated checkout; production frontend `127.0.0.1:3367`, API on
8367, offline providers, and a separate test database path. All examples below
are synthetic. No live financial data or credentials were required.

- 105 locked backend tests passed. Four new frontend persistence tests passed:
  separate drafts and blank/zero round trips; missing/malformed/incompatible
  records; read/write failures; independent initial input objects.
- Type checking, lint and production build passed after the startup guard fix.
  Existing warnings remain for Starlette/httpx and the missing Next ESLint plugin.
- Actual Chrome navigation through DCF and DDM retained NAV drafts. A pending
  calculation showed disabled fields/save/restore and the calculating state;
  switching models preserved inputs, and the cancelled response did not reappear.
- NOI 0.6m, cap rate 5%, debt 7m, other assets/claims zero and 1m shares produced
  asset value 12m, equity 5m and value/share 5. Changing the cap rate to 6% cleared
  the old result, then produced 10m, 3m and 3.
- Separate resource inputs of 2m units, value 10, cost 4, exploration 0,
  liabilities 2m and 2m shares produced reserve value 12m, equity 10m and
  value/share 5. Both model drafts and the selected mode restored after reload.
- Blank NOI survived switching, saving and restoring; browser required-field
  validation blocked calculation. Zero cap rate returned API validation while
  preserving inputs. Missing storage showed a clear empty-state message.
- An isolated test proxy injected denied storage, quota errors and malformed
  saved JSON into the production page. Each error was visible and left current
  inputs intact. The initial denied-storage crash was reproduced before the guard
  fix, and loading/save/restore were checked again after rebuilding.
- Stopping the test API produced a visible HTTP 500 failure, cleared the previous
  result and retained the draft. The proxy's error wording is still generic.
- Desktop width was 1440px. A Chrome iframe with a measured 390×844 inner viewport
  exercised restore and calculation: document width 390px, input widths 244px,
  readable single-column fields and stacked results, with no horizontal overflow.
  The browser viewport override did not change measured dimensions, so the
  iframe fixture was used and its actual dimensions were recorded.
- Browser logs included extension Datadog, window-mode and message-channel
  errors. Intentional storage faults and the stopped API are recorded separately;
  no further application crash was observed after the guard fix.

The local evidence record contains 23 browser observations, desktop/mobile
screenshots and the isolated fault/viewport fixtures. The immutable publication
handoff records the final commit and source fingerprint.

## Limits

Browser save is explicit and replaces one snapshot; it is neither automatic draft
recovery across routes nor multiuser synchronization. Unsaved inputs remain only
while the valuation page is mounted. Results require recalculation after restore
or returning to NAV. Mobile checks used Chrome responsive rendering, not physical
touch devices or Safari. Full keyboard/screen-reader accessibility, native file
imports, print-to-PDF, optional sentiment and the broader research-workflow backlog
were outside this change. Prior live-provider and dependency-audit results remain
dated October 16; they are not new results for this follow-up.
