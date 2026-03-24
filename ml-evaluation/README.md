# Otto Model Evaluation Suite

Evaluation scripts for Otto's RAG pipeline.

## Setup
pip install -r requirements.txt

## Scripts
- `run_validation.py` — validates model against held-out queries, CI/CD gate
- `run_ragas_eval.py` — RAGAS scores across prompt versions V1-V4
- `run_sensitivity.py` — temperature and top-k sensitivity analysis
- `run_bias_eval.py` — bias detection across language and repo section slices
- `plot_results.py` — generates bar charts from experiments log
- `select_prompt_version.py` — selects best prompt version from results

## Running
python run_validation.py