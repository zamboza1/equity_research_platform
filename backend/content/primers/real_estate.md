## REIT Modeling Primer (CAPREIT example)

*A plain-English guide to what each metric means, why it matters, and where it shows up in your model.*
**Version date: 2025-12-27**

---

## 1) What you are building (the big picture)
A REIT model is a way to explain:
1. **How the buildings perform** (rent, occupancy, expenses)
2. **How that performance turns into cash for unitholders** (FFO/AFFO, distributions)
3. **What the portfolio is worth today** (NAV)

You will use two connected views:
### Operating view (income engine)
**Occupancy + rent growth + expenses → NOI → (G&A, interest, adjustments) → FFO/AFFO → distributions**

### Asset value view (what it’s worth)
**Stabilized NOI ÷ cap rate → property value → NAV per unit**

---

## 2) Key terms (simple definitions + the nuance)

### Core operating metrics
| Term | Simple meaning | Nuance |
| :--- | :--- | :--- |
| **Occupancy** | % of suites (or sqft) rented | Small changes matter due to turnover costs. |
| **Occupied AMR** | Avg Monthly Rent on occupied suites | Mixes existing rent bumps + turnover lift. |
| **Turnover** | % moving out | Drives "mark-to-market" but increases costs. |

### Profit metrics
| Term | Simple meaning | Nuance |
| :--- | :--- | :--- |
| **NOI** | Property-level profit | The "real estate engine". Keep separate from corporate G&A. |
| **Same-Property NOI** | NOI for constant set of properties | Shows organic growth (strips out buy/sell noise). |

### Valuation metrics
| Term | Simple meaning | Nuance |
| :--- | :--- | :--- |
| **NAV per unit** | (Asset value - Debt) / Units | Very sensitive to Cap Rate assumptions. |
| **Cap rate** | NOI / Value | Lower cap rate = Higher value. Driven by rates + growth. |

---

## 3) How specific tabs work
- **NOI Drivers**: Unit economics. Inputs: `units`, `occupancy`, `AMR growth`. Output: `NOI`.
- **FFO Bridge**: `NOI - G&A - Interest`. Output: `FFO/share`.
- **NAV**: `Stabilized NOI / Cap Rate`. Output: `NAV/share` and `Upside %`.

## 4) Common Pitfalls
> [!WARNING]
> **Mixing NOI and FFO**: Don't put Interest Expense in NOI.
> **Total vs Same-Property**: Total NOI grows if you buy buildings; SP-NOI grows if you manage better.
