# 6. Inference Evaluation and the Noise Floor

This phase evaluated the diagnostic validity of methods commonly used to claim semantic content in the manuscript. The central question: can current inference methods distinguish the real manuscript from non-semantic controls?

## 6.1 The False Positive Problem

Results prove that flexible transformation models achieve similar confidence scores on randomized noise controls as they do on the real manuscript. This establishes that many published decipherment claims are artifacts of methodology rather than artifacts of data — the methods find "signal" everywhere, including in known noise.

{{figure:results/visuals/phase4_inference/821247f8-748c-cb25-1d5d-5d2877bf7f71_lang_id_comparison.png|Comparative False Positive Rate Evaluation across Diagnostic Methods}}

{{figure:results/publication/assets/inference_floor.png|The Inference Floor: Probability of False Semantic Detection in Structured Noise}}

## 6.2 Method-by-Method Evaluation

Five inference methods were tested against the manuscript and matched non-semantic controls of equal scale:

**Information Clustering (Montemurro-Zanette).** The manuscript shows real avg_info of {{phase4.montemurro.real_avg_info}} bits versus {{phase4.montemurro.shuffled_avg_info}} for shuffled controls — a genuine signal. However, mechanical reuse models also exceed the shuffled baseline, making this metric non-diagnostic for semantics.

**Network Analysis (WAN Metrics).** Voynich clustering ({{phase4.network.voynich_clustering}}) falls between natural language (0.1008) and mechanical reuse (0.3393). The Zipf exponent (0.7738) closely matches Latin (0.7869), but this match is also reproduced by shuffled controls. Network features describe structure but do not distinguish semantic from non-semantic production.

**Topic Modeling.** Voynich shows 5 unique dominant topics across 20 sections, between shuffled (1) and self-citation (9). KL divergence (3.07) is comparable to Latin (2.91). Topic structure exists but is indistinguishable from the structure produced by mechanical processes.

**Language Identification.** Voynich similarity to Latin ({{phase4.lang_id.voynich_latin}}) and English ({{phase4.lang_id.voynich_english}}) are both extremely low. The shuffled baseline produces nearly identical scores, confirming that character n-gram similarity has no diagnostic power at this scale.

**Morphological Analysis.** Voynich morph consistency (0.0711) is close to Latin (0.0846) but also close to shuffled controls (0.0711). Apparent morphological regularity is a structural artifact, not evidence of inflectional grammar.

## 6.3 Determination

Every method tested was classified as **NOT DIAGNOSTIC** for semantic content. Non-semantic generative models (specifically self-citation and mechanical reuse) are sufficient to reproduce every major statistical signal previously cited as evidence of language.

The widely cited studies supporting linguistic hypotheses — while descriptively accurate — do not survive the noise floor test. Their findings are consistent with both semantic and non-semantic production and therefore cannot support an inference of meaning.

## 6.4 Implications

The noise floor analysis does not prove the manuscript lacks meaning. It proves that current diagnostic methods cannot distinguish the manuscript from meaningless controls, and therefore those methods cannot be used as evidence for meaning. The limitation is in the methods, not necessarily in the manuscript. Any future claim of semantic content must demonstrate diagnostic power that exceeds this noise floor.
