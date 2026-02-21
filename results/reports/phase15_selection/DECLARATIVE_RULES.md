# Phase 15: Declarative Rule Table (Voynich Engine)

This document defines the explicit transition logic of the reconstructed mechanical generator. A third party can reproduce the manuscript's structure by following these rules.

## 1. Physical Transition Table
| Current Window | Chosen Token | Next Window |
| :--- | :--- | :--- |
| 23 | `#oe` | 23 |
| 47 | `$` | 47 |
| 41 | `%c79` | 41 |
| 41 | `%c89` | 41 |
| 41 | `%c9` | 41 |
| 40 | `%coy` | 40 |
| 8 | `%oe` | 8 |
| 33 | `%oy` | 33 |
| 5 | `(` | 5 |
| 41 | `*` | 41 |
| 5 | `+c9` | 5 |
| 40 | `+co` | 40 |
| 23 | `+o` | 23 |
| 45 | `+oe` | 45 |
| 2 | `1` | 2 |
| 31 | `179` | 31 |
| 23 | `17ae` | 23 |
| 47 | `17ap` | 47 |
| 2 | `17ay` | 2 |
| 9 | `18` | 9 |
| 31 | `189` | 31 |
| 31 | `18ae` | 31 |
| 1 | `18am` | 1 |
| 2 | `18an` | 2 |
| 46 | `18ap` | 46 |
| 31 | `18ay` | 31 |
| 8 | `18oy` | 8 |
| 31 | `19` | 31 |
| 14 | `19h9` | 14 |
| 21 | `19k9` | 21 |
| 8 | `1Ae` | 8 |
| 40 | `1C79` | 40 |
| 15 | `1C89` | 15 |
| 31 | `1C9` | 31 |
| 15 | `1Ch9` | 15 |
| 15 | `1Co` | 15 |
| 1 | `1Coe` | 1 |
| 14 | `1Coy` | 14 |
| 31 | `1Cs` | 31 |
| 45 | `1D` | 45 |
| 16 | `1G9` | 16 |
| 45 | `1H79` | 45 |
| 14 | `1H89` | 14 |
| 46 | `1H9` | 46 |
| 16 | `1Hae` | 16 |
| 14 | `1Hc89` | 14 |
| 15 | `1Hc9` | 15 |
| 17 | `1Hoe` | 17 |
| 27 | `1J9` | 27 |
| 46 | `1K` | 46 |
| 31 | `1K9` | 31 |
| 2 | `1Kc89` | 2 |
| 15 | `1Kc9` | 15 |
| 8 | `1L9` | 8 |
| 8 | `1S` | 8 |
| 15 | `1aN` | 15 |
| 31 | `1ae` | 31 |
| 14 | `1ae9` | 14 |
| 15 | `1am` | 15 |
| 31 | `1an` | 31 |
| 8 | `1ap` | 8 |
| 31 | `1ay` | 31 |
| 22 | `1ay9` | 22 |
| 40 | `1c(` | 40 |
| 8 | `1c69` | 8 |
| 41 | `1c7` | 41 |
| 31 | `1c79` | 31 |
| 9 | `1c79<$>` | 9 |
| 15 | `1c7ae` | 15 |
| 45 | `1c7am` | 45 |
| 2 | `1c7an` | 2 |
| 40 | `1c7ay` | 40 |
| 1 | `1c8` | 1 |
| 8 | `1c8(` | 8 |
| 45 | `1c8,am` | 45 |
| 31 | `1c89` | 31 |
| 1 | `1c89<$>` | 1 |
| 15 | `1c8ae` | 15 |
| 45 | `1c8am` | 45 |
| 1 | `1c8an` | 1 |
| 9 | `1c8ap` | 9 |
| 31 | `1c8ay` | 31 |
| 8 | `1c8oe` | 8 |
| 31 | `1c9` | 31 |
| 14 | `1c9<$>` | 14 |
| 23 | `1cAe` | 23 |
| 8 | `1cAy` | 8 |
| 31 | `1cH9` | 31 |
| 8 | `1cHc9` | 8 |
| 1 | `1cK9` | 1 |
| 31 | `1cae` | 31 |
| 49 | `1cae9` | 49 |
| 23 | `1cap` | 23 |
| 31 | `1cay` | 31 |
| 22 | `1cc79` | 22 |
| 15 | `1cc89` | 15 |
| 31 | `1cc9` | 31 |
| 31 | `1cch9` | 31 |
| 47 | `1cck9` | 47 |
| 40 | `1cco89` | 40 |

... [Table Truncated for Readability. Full CSV available in logic export] ...

## 2. Global State Invariants
- **Deterministic Reset:** Every line returns the carriage to a start position (Window 0).
- **Window Adjacency:** Scribe selection is restricted to the window exposed by the previous token's transition rule.
