# 3. The Foundational Ledger

The first step was to establish a deterministic, reproducible digital ledger of the text. The data ingestion pipeline utilizes deterministic ID generation via the EVA transcription system to ensure 100% reproducibility of the digital record.

## 3.1 Corpus Statistics

Our analysis of the 222-folio corpus reveals a Token Repetition Rate of {{phase1.repetition_rate}}, a figure vastly higher than any known natural language (typically 20-30%). This extreme repetition is not an artifact of transcription but a fundamental property of the system. The text is built from a highly constrained set of recurring tokens.

Initial Zipfian analysis demonstrates a vocabulary profile consistent with constrained mechanical selection rather than the open-ended generativity of human language.

{{figure:results/visuals/phase1_foundation/41f398bc-9623-2b2d-bada-5bd4dc226e64_repetition_rate_dist_voynich_real.png|Distribution of Token Repetition Rates across the Corpus}}

## 3.2 Distributional Profile

The distributional profile serves as the baseline for all subsequent admissibility tests. Any candidate production model must, at minimum, predict this level of token concentration and the specific shape of the frequency distribution.
