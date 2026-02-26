# Monitoring report (example)

Generated: 2026-02-26T09:30:00+00:00

> This file is a **sample artifact** committed for portfolio browsing.  
> Run `make demo` to generate fresh artifacts into `./outputs/`.

## Freshness
- Max event timestamp: `2026-02-26 09:28:41.123+00:00`
- Lag (hours): `0.02` (threshold `24.0`)
- Status: **PASS**

## Conversion anomaly (z-score)
| variant | day | starters | rate | mean | std | z |
|---|---:|---:|---:|---:|---:|---:|
| control | 2026-02-26 | 1,225 | 0.1886 | 0.1879 | 0.0065 | 0.11 |
| treatment | 2026-02-26 | 1,261 | 0.2010 | 0.1891 | 0.0067 | 1.78 |

## Alerts
- None
