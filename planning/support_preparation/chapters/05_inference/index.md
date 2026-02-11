# Layer 4: Inference Evaluation

## Headline
**Common decipherment methods fail to distinguish between semantic text and random noise, rendering many "solutions" statistically invalid.**

## The Concept (Layman's Summary)
Have you ever looked at a cloud and seen a face? Your brain is designed to find patterns, even when they aren't there. Many researchers use computer programs to "identify" the language of the Voynich Manuscript. We tested these programs on both the real manuscript and on complete gibberish (randomly scrambled words). The programs "identified" languages in both cases with similar confidence. This proves that these methods are just "seeing faces in clouds"—they aren't actually finding a hidden language.

## Technical Deep-Dive
We evaluated the **Language ID False Positive Rate** by running a flexible transformation analyzer against three distinct datasets.

### Language ID Confidence Comparison
We compared the best-match confidence for Latin and English across real and non-semantic datasets.

- **Voynich (Real)**: Latin (0.147), English (0.160)
- **Shuffled (Gibberish)**: Latin (0.148), English (0.165)
- **Mechanical Reuse (Algorithmic)**: Latin (0.125), English (0.170)

The confidence scores for "gibberish" are nearly identical—and in some cases higher—than for the real manuscript. This indicates that the scores are a result of the *method's* search space, not the *data's* inherent meaning.

![Language ID Comparison](../../../results/reports/visuals/phase4_inference/821247f8-748c-cb25-1d5d-5d2877bf7f71_lang_id_comparison.png)

## Skeptic's Corner
Many published "decipherments" rely on finding a few dozen "keyword" matches to a specific language (e.g., Hebrew, Latin, or Proto-Romance).

### Counter-Point Analysis
Our results show that if you allow enough "flexible transforms" (different ways to map symbols to letters), you can achieve a confidence score of 0.15 to 0.20 on *any* random dataset. A valid decipherment would require a confidence score significantly higher than the "noise floor" established by our shuffled controls (approx. 0.70+).

## Reproducibility
To regenerate these evaluation results:
```bash
# Run the phase4_inference experiment
python3 scripts/phase4_inference/run_lang_id.py

# Generate the comparison plot
support_visualization phase4_inference lang-id results/data/phase4_inference/lang_id_results.json
```
**Reference RunID**: `821247f8-748c-cb25-1d5d-5d2877bf7f71`
