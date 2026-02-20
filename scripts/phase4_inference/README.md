# Phase 4: Inference Admissibility

## Intent
Phase 4 does not ask "What does the book mean?" but rather "Are the methods used to find meaning valid?" We prove that widely-cited decipherment tools often find high-confidence matches in complete random noise, establishing a statistical "Noise Floor" that invalidates many existing "solutions."

## How to Replicate
Execute the standardized replication script:
```bash
python3 scripts/phase4_inference/replicate.py
```

Optional bounded projection diagnostic:
```bash
python3 scripts/phase4_inference/run_projection_bounded.py
```

Optional bounded discrimination diagnostic:
```bash
python3 scripts/phase4_inference/run_discrimination_check.py
```
Variant with order-sensitive ngrams (example: bigrams):
```bash
python3 scripts/phase4_inference/run_discrimination_check.py --ngram-min 2 --ngram-max 2 --output-name discrimination_check_bigram.json
```

Optional bounded order-constraint diagnostic:
```bash
python3 scripts/phase4_inference/run_order_constraints_check.py --permutations 50 --token-limit 120000 --vocab-limit 500
```

Stronger non-semantic control (line-reset Markov) benchmark:
```bash
python3 scripts/phase4_inference/run_line_reset_markov_check.py
```

Simple Kolmogorov-complexity proxy (compression + shuffled baseline):
```bash
python3 scripts/phase4_inference/run_kolmogorov_proxy_check.py --permutations 30 --token-limit 120000 --codecs zlib,lzma
```

NCD matrix + bootstrap rank confidence (includes line-reset Markov control):
```bash
python3 scripts/phase4_inference/run_ncd_matrix_check.py --bootstraps 60 --token-limit 80000 --block-size 512
```

Format-agnostic image-encoding hypothesis check:
```bash
python3 scripts/phase4_inference/run_image_encoding_hypothesis_check.py --max-images 24 --resize-width 256 --quant-levels 16
```
Note: image bins are remapped onto frequent Voynich tokens to avoid trivial out-of-vocabulary separation.

Music-like non-text hypothesis check:
```bash
python3 scripts/phase4_inference/run_music_hypothesis_check.py --target-tokens 230000 --motif-count 48
```

Hybrid line-reset backoff benchmark:
```bash
python3 scripts/phase4_inference/run_line_reset_backoff_check.py --target-tokens 230000
```

Reference-number relevance check (default target: 42):
```bash
python3 scripts/phase4_inference/run_reference_42_check.py --target 42 --window-radius 6
```

Boundary persistence sweep (find best rho, then benchmark):
```bash
python3 scripts/phase4_inference/run_boundary_persistence_sweep.py --rho-values 0.00,0.10,0.20,0.30,0.40,0.50,0.60 --trigram-use-probs 0.45,0.55,0.65 --unigram-noise-probs 0.01,0.03,0.05
```

Boundary persistence holdout checkpoint (fit on train folios, test on unseen folios):
```bash
python3 scripts/phase4_inference/run_boundary_persistence_holdout_check.py --holdout-fraction 0.20 --ncd-bootstraps 30
```

Boundary persistence section-holdout checkpoint (hold out entire sections):
```bash
python3 scripts/phase4_inference/run_boundary_persistence_section_holdout_check.py --sections herbal,astronomical,biological,cosmological,pharmaceutical,stars
```
Section-aware persistence override example (use different persistence params for herbal holdout):
```bash
python3 scripts/phase4_inference/run_boundary_persistence_section_holdout_check.py --persistence-section-overrides "herbal:0.10:0.65:0.05"
```

## Key Tests & Diagnostics
*   **Flexible Transform Analysis**: Shows how AI-based language ID tools "find" Latin or Hebrew in gibberish controls.
*   **Montemurro Diagnostics**: Evaluates keyword-clustering claims against algorithmic noise.
*   **False Positive Rate (FPR)**: Establishes that a confidence score of < 0.70 is statistically indistinguishable from random chance.
*   **Bounded Projection Check**: Uses PCA/t-SNE/(optional UMAP) only as descriptive aids and validates separability with permutation baselines.
*   **Bounded Discrimination Check**: Evaluates which matched corpus families Voynich is closest to in held-out TF-IDF space.
*   **Bounded Order-Constraint Check**: Tests transition entropy and mutual information against shuffled null baselines.
*   **Line-Reset Markov Control Check**: Generates a stronger non-semantic control and tests whether it closes the gap to Voynich.
*   **Kolmogorov Proxy Check**: Uses compression as a bounded proxy for algorithmic complexity, compared to shuffled-token nulls.
*   **NCD Matrix Check**: Uses pairwise compression distance with bootstrap rank confidence to test closeness stability.
*   **Image-Encoding Hypothesis Check**: Tests decoded-image symbolic streams (format-agnostic) against the same structural diagnostics.
*   **Music-Like Hypothesis Check**: Tests motif/transposition non-text controls against the same structural diagnostics.
*   **Line-Reset Backoff Check**: Tests whether moderate higher-order backoff closes the remaining gap to Voynich.
*   **Reference-Number Check**: Tests whether a target integer (default 42) is unusually over-represented in line/page/section structural counts.
*   **Boundary Persistence Sweep**: Optimizes line-boundary memory strength (`rho`) and benchmarks the best hybrid model.
*   **Boundary Persistence Holdout Check**: Tests whether the persistence signal survives on unseen folios (out-of-sample checkpoint).
*   **Boundary Persistence Section-Holdout Check**: Tests whether the persistence signal survives when entire manuscript sections are held out.

## Expected Results
*   **Method Admissibility Matrix**: A report in `results/reports/phase4_inference/` classifying which inference methods are diagnostic and which are "pattern-finding machines."
*   **Statistical Noise Floor**: Quantitative data proving that Voynich language scores fall below the threshold of significance.
