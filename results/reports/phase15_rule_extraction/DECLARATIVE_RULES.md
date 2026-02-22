# Phase 15: Declarative Rule Table (Voynich Engine)

This document defines the explicit transition logic of the reconstructed mechanical generator. A third party can reproduce the manuscript's structure by following these rules.

## 1. Physical Transition Table
| Current Window | Chosen Token | Next Window |
| :--- | :--- | :--- |
| 19 | `'ed'` | 19 |
| 36 | `???` | 36 |
| 25 | `???cheeo` | 25 |
| 21 | `???cheor` | 21 |
| 3 | `???eocthy` | 3 |
| 29 | `???oiin` | 29 |
| 7 | `???ooooooooolar` | 7 |
| 49 | `???opcheol` | 49 |
| 31 | `???teo` | 31 |
| 40 | `??olkechdylo` | 40 |
| 17 | `?ain` | 17 |
| 13 | `?chey` | 13 |
| 38 | `?dy` | 38 |
| 31 | `?keeeos` | 31 |
| 25 | `?l` | 25 |
| 17 | `?lshey` | 17 |
| 39 | `?okeeol` | 39 |
| 32 | `?or` | 32 |
| 4 | `?saiin` | 4 |
| 44 | `?sodaiindy` | 44 |
| 13 | `@135odaiin` | 13 |
| 19 | `@135otchoshor` | 19 |
| 23 | `@136yfchedy` | 23 |
| 47 | `@137chol` | 47 |
| 29 | `@138aiin` | 29 |
| 32 | `@138chor` | 32 |
| 47 | `@147` | 47 |
| 30 | `@150tol` | 30 |
| 1 | `@152aiin` | 1 |
| 48 | `@153` | 48 |
| 40 | `@156cho` | 40 |
| 48 | `@159chair` | 48 |
| 39 | `@161char` | 39 |
| 20 | `@163schoraiin` | 20 |
| 12 | `@169v` | 12 |
| 49 | `@170` | 49 |
| 30 | `@171` | 30 |
| 2 | `@171ar` | 2 |
| 36 | `@172` | 36 |
| 37 | `@174` | 37 |
| 5 | `@176orain` | 5 |
| 10 | `@177ykedy` | 10 |
| 8 | `@183olc@133heol` | 8 |
| 16 | `@184cheolain` | 16 |
| 4 | `@185arally` | 4 |
| 0 | `@187arar` | 0 |
| 10 | `@189shxam` | 10 |
| 1 | `@190cheekchy` | 1 |
| 4 | `@199aiindar` | 4 |
| 37 | `@200phol` | 37 |
| 21 | `@201or` | 21 |
| 37 | `@206aiin` | 37 |
| 19 | `@206ar` | 19 |
| 1 | `@211y` | 1 |
| 17 | `@231@232@233@234` | 17 |
| 49 | `@240` | 49 |
| 38 | `@241` | 38 |
| 5 | `@243` | 5 |
| 16 | `@246?` | 16 |
| 37 | `@246khey` | 37 |
| 12 | `@246thhey` | 12 |
| 1 | `A` | 1 |
| 31 | `I` | 31 |
| 7 | `ThPchear` | 7 |
| 35 | `a` | 35 |
| 46 | `a@175` | 46 |
| 2 | `aal` | 2 |
| 11 | `above` | 11 |
| 37 | `acthhy` | 37 |
| 19 | `adairchdy` | 19 |
| 41 | `adam` | 41 |
| 35 | `adeeodyykecthey` | 35 |
| 32 | `adoldy` | 32 |
| 13 | `ador` | 13 |
| 16 | `aedaiin` | 16 |
| 43 | `aedy` | 43 |
| 30 | `aeeody` | 30 |
| 34 | `after` | 34 |
| 38 | `ag` | 38 |
| 30 | `ai'he` | 30 |
| 19 | `aiar` | 19 |
| 38 | `aickyy` | 38 |
| 38 | `aifhhy` | 38 |
| 2 | `aig` | 2 |
| 43 | `aiichy` | 43 |
| 12 | `aiicthy` | 12 |
| 37 | `aiidy` | 37 |
| 23 | `aiiikheedy` | 23 |
| 16 | `aiiiky` | 16 |
| 30 | `aiiil` | 30 |
| 36 | `aiiin` | 36 |
| 17 | `aiiinol` | 17 |
| 16 | `aiiinytey` | 16 |
| 29 | `aiiiro` | 29 |
| 41 | `aiikam` | 41 |
| 31 | `aiil` | 31 |
| 1 | `aiildy` | 1 |
| 12 | `aiily` | 12 |
| 1 | `aiim` | 1 |
| 36 | `aiin` | 36 |

... [Table Truncated for Readability. Full CSV available in logic export] ...

## 2. Global State Invariants
- **Deterministic Reset:** Every line returns the carriage to a start position (Window 0).
- **Window Adjacency:** Scribe selection is restricted to the window exposed by the previous token's transition rule.
