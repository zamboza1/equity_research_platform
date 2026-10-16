## REIT modeling primer

Definitions and inputs for reviewing a property business. Updated October 16, 2026.
This is a model reference, not a company valuation.

## Operating performance

| Measure | What it describes | What to check |
| :--- | :--- | :--- |
| Occupancy | The proportion of available units or floor area rented | Use the same denominator and reporting period when comparing properties. |
| Average monthly rent | Rent per occupied unit | Changes can reflect lease renewals, turnover and property mix. |
| Net operating income (NOI) | Property revenue less property operating expenses | Keep corporate expenses, financing costs and income taxes separate. |
| Same-property NOI | NOI for a defined group of properties across periods | Check which acquisitions, disposals and developments the issuer excludes. |

Total NOI can grow through acquisitions even when the existing portfolio is flat.
Use the issuer's same-property definition when assessing operating growth.

## FFO and AFFO

Nareit FFO adjusts US GAAP net income for real-estate depreciation and amortization,
specified gains, losses and impairments, with relevant joint-venture adjustments.
It is a supplemental operating-performance measure. NOI less corporate expenses
and interest alone is not a complete FFO reconciliation.
[Nareit FFO definition](https://www.reit.com/glossary/funds-operation-ffo).

AFFO makes further adjustments that vary by issuer, often including recurring
property expenditures and straight-line rent. There is no standardized AFFO
definition. Read the company's reconciliation before comparing values or using
them to assess distributions.
[Nareit AFFO definition](https://www.reit.com/glossary/adjusted-funds-operations-affo).

Check the reporting framework and issuer's definitions for each company; do not
apply a US GAAP reconciliation unchanged to IFRS statements. FFO and AFFO should
be considered alongside the cash-flow statement and investment requirements.

## Real-estate NAV in Vertige

Open **Valuations → NAV Model → Real estate** and enter verified assumptions:

1. **Annual NOI and cap rate:** property value equals annual NOI divided by the cap rate. Enter the rate as a decimal, for example `0.05` for 5%.
2. **Other assets:** add asset values not already included in capitalized NOI.
3. **Claims:** deduct debt, minority interest and preferred equity.
4. **Shares:** divide equity NAV by diluted shares outstanding.

Money and shares use millions; NAV per share uses currency per share. Keep all
inputs in one currency. Initial inputs are illustrative. The model does not
automatically retrieve property appraisals, build an NOI forecast or reconcile FFO.

For an illustrative annual NOI of 100 and cap rate of 5%, property value is 2,000.
With no other assets, debt of 500, no minority or preferred claims and 100 million
shares, equity NAV is 1,500 and NAV per share is 15. At a 6% cap rate with all
other assumptions unchanged, NAV per share falls to about 11.67.

Cap rates, sustainable NOI, omitted claims and dilution can materially change the
result. Estimated NAV is not a forecast of liquidation proceeds or proof that a
share-price discount is an investment opportunity.
