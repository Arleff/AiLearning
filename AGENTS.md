# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is **AiLearning** by ApacheCN — an educational repository for Machine Learning, Deep Learning, and NLP. It is **not** a traditional application with backend services. It consists of:

- **Python scripts** in `src/py3.x/` implementing ML/DL/NLP algorithms (each chapter is standalone)
- **Datasets** in `data/` (text files used by the scripts)
- **Docsify documentation** served from `index.html` at the repo root

### Running scripts

Most Python scripts in `src/py3.x/ml/` use **relative paths** starting with `data/`, so they must be run from the **repository root** (`/workspace`):

```bash
cd /workspace
python3 src/py3.x/ml/2.KNN/kNN.py
```

### Running the documentation site

```bash
docsify serve . --port 3000
```

### Key caveats

- **No `requirements.txt` exists.** Dependencies are inferred from imports. Core: `numpy`, `scikit-learn`, `matplotlib`. Extended: `torch`, `jieba`, `gensim`, `feedparser`, `beautifulsoup4`, `nltk`.
- **Some scripts have Python 2 remnants** (e.g. `dict.has_key()` in `11.Apriori/apriori.py`, missing `from numpy import mat` in `10.kmeans/kMeans.py`). These are known issues in the codebase.
- **No test framework or linter is configured.** Validation is done by running individual scripts.
- **Matplotlib** runs in non-interactive (Agg) mode in headless environments. Use `matplotlib.use('Agg')` and `plt.savefig()` instead of `plt.show()`.
- **No build step required.** Scripts are run directly with `python3`.
