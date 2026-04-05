from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = DATA_DIR / 'app.db'
STORAGE_DIR = DATA_DIR / 'storage'
UPLOADS_DIR = STORAGE_DIR / 'uploads'
RESULTS_DIR = STORAGE_DIR / 'results'
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
