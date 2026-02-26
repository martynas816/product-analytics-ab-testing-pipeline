# A/B test decision — `new_checkout` (example)

Generated: 2026-02-26T09:30:00+00:00

> This file is a **sample artifact** committed for portfolio browsing.  
> Run `make demo` to generate fresh artifacts into `./outputs/`.

## Primary metric
**Metric:** checkout → purchase conversion within **24h**

| variant | checkout users | purchasers | conversion |
|---|---:|---:|---:|
| control | 5,842 | 1,091 | 0.1867 |
| treatment | 5,911 | 1,178 | 0.1993 |

## Effect size
- Uplift (abs): **0.0126**
- Uplift (rel): **6.75%**
- 95% CI (abs): **[0.0021, 0.0231]**

## Guardrail
- AOV control: `58.41`
- AOV treatment: `58.03`
- AOV change: `-0.65%`

## Decision
**SHIP** — uplift CI is above 0 and guardrail is acceptable.

## Notes
- This decision is computed from tracked events defined in `spec/event_tracking.md`.
- For a deeper dive, see `experiment/ab_test_analysis.ipynb`.
