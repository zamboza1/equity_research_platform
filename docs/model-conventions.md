# Model conventions

- DCF money and shares use millions; output price uses currency per share. Annual growth and margins are editable. The UI selects `nwc_treatment=balance_ratio`, so FCFF deducts the change in operating working capital. Legacy API requests that omit this field retain the original annual-investment-ratio treatment. Gordon terminal cash flow uses normalized stable growth. Midyear timing applies to forecast cash flows; terminal value is discounted from the final year end. The equity bridge includes net debt, minority interest, preferred equity and nonoperating assets.
- DCF Monte Carlo uses independent normal shocks to WACC and a common shift in annual revenue growth. Users set standard deviations, draw count and seed. Zero dispersion holds that input fixed. Invalid draws are excluded and counted. Percentiles are scenario outcomes, not a statistical confidence interval.
- Dividend models use annual dividends per share. Required return must exceed perpetual dividend growth.
- NAV uses explicit asset values and claims. The resource estimate excludes production timing and discounting.
- Statement models use a single user-selected currency and consistent scale. Ratios are decimals. Opening balances must reconcile. Interest uses average debt, and revolver capacity limits funding. New capex uses half-year depreciation; opening net PP&E uses the entered remaining life. Tax losses receive no immediate benefit or carryforward schedule.
- Standalone valuation cases and graph assumptions save in browser storage. Research desk cases use server-side SQLite with immutable revisions. DCF cases also import/export JSON. Statement imports accept complete CSV/XLSX opening-period rows, using the sample API field names; exports contain calculated values.

The graph engine accepts bounded arithmetic expressions, not executable Python. News sentiment defaults to a labeled keyword method. Optional FinBERT needs separately installed `transformers` and `torch` plus `VERTIGE_ENABLE_FINBERT=1`; it was not validated in this review.

Legacy LBO, M&A, filing and accounting-conversion helpers remain in source but are not complete user workflows. REIT portfolio examples require an explicit API example flag. Sector pages provide educational notes, not fabricated market metrics.


## Formula builder

Formula references define calculation dependencies, independent of node order. The graph view derives arrows from those references; imported drawing edges are rebuilt from formulas in the editor. The API continues to accept explicit dependency edges in addition to inferred references. Cycles, missing references, syntax errors and non-finite results are rejected.

The revenue/EBIT and operating-profit examples are calculation fragments, not full DCF or three-statement models. The dividend perpetuity example uses decimal rates. The general arithmetic engine does not infer economic constraints from a formula; use the dedicated valuation models for model-specific validation.

Graph drafts and saved graphs are local to the browser. JSON exports are portable. Loading an example explicitly replaces the current graph; save or export it first. Legacy browser graphs can be restored.

The cash-flow template supports one to ten years. Each year has its own growth and EBIT margin. It deducts the change in operating NWC, gives losses no immediate tax credit, and discounts at year end. Its output is the present value of the forecast period only: no terminal value or enterprise-to-equity bridge is included. Common drivers and every formula remain editable.

Scenario overrides change selected inputs without rewriting the baseline. Two-way sensitivity accepts explicit values for two distinct inputs. Builder simulations support independent normal, uniform and triangular distributions, a saved seed, 10–10,000 draws and at most 200,000 node evaluations. Any invalid graph draw fails the run; it does not silently drop observations. The reported standard deviation describes the simulated population. Correlated input distributions are not implemented.

Named templates retain formulas, notes and analysis settings. Saving checks the loaded browser revision before overwriting it; this is not an atomic multiuser database guarantee. Saving a new template creates a separate entry. Restored analysis settings require recalculation. CSV exports include baseline inputs, formulas, settings and the selected analysis result.

Arithmetic uses finite scalar floating-point values. Literal lists are accepted by
aggregate functions such as `sum`, but cannot be multiplied or used as arithmetic
operands. Exponents are limited to magnitude 16; rounding precision must be an
integer from -308 to 308. The limits prevent unbounded list allocation and integer
growth; they do not turn the builder into a symbolic or arbitrary-precision engine.

## Comparables, statistics and macro data

Peer baskets contain up to twelve user-selected tickers. Forward and trailing P/E remain separate. Only positive, available multiples from included peers enter unweighted, linearly interpolated P25/median/P75 calculations. EPS and book value per share multiply directly; EBITDA multiples produce enterprise value, then subtract net debt and other entered claims and divide by diluted shares. Target measures are analyst inputs. The range describes peer dispersion, not forecast uncertainty. Periods, accounting and currency definitions still require review.

Statistics use adjusted daily closes, simple returns, 252 trading days, arithmetic annual return and sample volatility. The risk-free assumption is an annual effective rate converted to its daily equivalent. Downside deviation includes zero contributions from positive excess returns. Drawdown retains opening wealth; rolling volatility requires 21 returns. Benchmark statistics match both the start and end of each return interval, excluding unmatched sessions. Returns remain in native currency with no FX conversion. These are historical estimates, not forecasts.

Monthly CPI growth compares the same month one year earlier; missing observations remain gaps. US CPI is seasonally adjusted, while Canadian CPI is not. Raw index bases differ. US Fed Funds and Canadian ten-year bond yields are different instruments. Treasury yields use the latest common date across available tenors and show missing tenors explicitly. The 10Y–2Y spread converts percentage points to basis points. Constant-maturity yields are not a bootstrapped spot curve. Source definitions: [FRED Treasury yields](https://fred.stlouisfed.org/series/DGS2) and [Bank of Canada CPI](https://www.bankofcanada.ca/rates/price-indexes/cpi/).

Provider baseline loading supplies revenue, quote, shares and net debt with retrieval and financial-period dates. It does not verify diluted shares or forecast assumptions, and a new research case remains marked illustrative. Linked sources are references, not independent verification of their content.
