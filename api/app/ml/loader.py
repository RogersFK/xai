import pickle
from pathlib import Path

_artifacts = None

def get_artifacts():
    global _artifacts
    if _artifacts is None:
        path = Path(__file__).parent / "artifacts" / "model.pkl"
        with open(path, "rb") as f:
            _artifacts = pickle.load(f)
    return _artifacts