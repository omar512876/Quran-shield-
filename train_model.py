"""
train_model.py — Quran Shield
==============================
Use this script once you have a labelled dataset to train a real RandomForest
classifier. The trained model replaces the hand-tuned weighted scorer in
main.py with a learned decision boundary.

Dataset layout expected on disk:
  data/
    quran/       ← .mp3 / .wav files of Quran recitation
    music/       ← .mp3 / .wav files of music (with or without background)

Run:
  python train_model.py

Output:
  model.joblib   ← drop this next to main.py and load it there
"""

import os
import pickle
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report


# ── 1. Feature extraction (must match main.py exactly) ───────────────────────

def extract_features(y: np.ndarray, sr: int) -> np.ndarray:
    """
    Returns a 1-D feature vector matching the order used in main.py.
    IMPORTANT: keep this in sync with main.py's extract_features().
    """
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_delta = librosa.feature.delta(mfccs)

    centroid  = librosa.feature.spectral_centroid(y=y, sr=sr)
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    rolloff   = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
    contrast  = librosa.feature.spectral_contrast(y=y, sr=sr)
    chroma    = librosa.feature.chroma_stft(y=y, sr=sr)
    zcr       = librosa.feature.zero_crossing_rate(y)
    rms       = librosa.feature.rms(y=y)
    tempo, _  = librosa.beat.beat_track(y=y, sr=sr)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    return np.array([
        np.mean(mfccs),
        np.std(mfccs),
        np.mean(np.abs(mfcc_delta)),
        np.mean(centroid),
        np.mean(bandwidth),
        np.mean(rolloff),
        np.mean(contrast),
        np.mean(chroma),
        np.std(chroma),
        np.mean(zcr),
        np.mean(rms),
        float(tempo),
        np.mean(onset_env),
        np.std(onset_env),
    ])


AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}


def load_dataset(data_dir: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Walk data_dir expecting subdirectories as class labels.
    Returns (X, y) arrays.
    """
    X, y = [], []
    label_map = {}  # folder name → integer

    for label_name in sorted(os.listdir(data_dir)):
        class_path = os.path.join(data_dir, label_name)
        if not os.path.isdir(class_path):
            continue

        label_id = label_map.setdefault(label_name, len(label_map))
        print(f"Loading class '{label_name}' (id={label_id}) ...")

        for fname in os.listdir(class_path):
            if os.path.splitext(fname)[1].lower() not in AUDIO_EXTENSIONS:
                continue

            fpath = os.path.join(class_path, fname)
            try:
                audio, sr = librosa.load(fpath, sr=None, mono=True, duration=30)
                features = extract_features(audio, sr)
                X.append(features)
                y.append(label_id)
                print(f"  ✓ {fname}")
            except Exception as e:
                print(f"  ✗ {fname}: {e}")

    print(f"\nLabels: {label_map}")
    return np.array(X), np.array(y), label_map


# ── 2. Train ──────────────────────────────────────────────────────────────────

def train(data_dir: str = "data", output_path: str = "model.joblib"):
    X, y, label_map = load_dataset(data_dir)

    if len(X) == 0:
        raise ValueError("No audio files found. Check your data/ folder structure.")

    print(f"\nDataset: {len(X)} samples, {len(label_map)} classes")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pipeline: StandardScaler + RandomForest
    # RandomForest is robust, interpretable, and needs no hyperparameter tuning
    # to give good results on small datasets.
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_split=2,
            class_weight="balanced",  # handles uneven class sizes
            random_state=42,
            n_jobs=-1,
        )),
    ])

    # Cross-validation on training set first
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="f1_weighted")
    print(f"5-fold CV F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Final fit on full training set
    pipeline.fit(X_train, y_train)

    # Evaluation on held-out test set
    y_pred = pipeline.predict(X_test)
    print("\nTest set report:")
    print(classification_report(y_test, y_pred, target_names=list(label_map.keys())))

    # Save: model + label_map together
    bundle = {"pipeline": pipeline, "label_map": label_map}
    with open(output_path, "wb") as f:
        pickle.dump(bundle, f)

    print(f"\n✓ Model saved to {output_path}")
    print("  Drop it next to main.py and update classify_audio() to load it.")


# ── 3. How to load the model in main.py ───────────────────────────────────────
#
# Add this near the top of main.py:
#
#   import pickle, numpy as np
#   with open("model.joblib", "rb") as f:
#       _bundle = pickle.load(f)
#   _pipeline  = _bundle["pipeline"]
#   _label_map = {v: k for k, v in _bundle["label_map"].items()}   # int → name
#
# Then replace classify_audio() with:
#
#   def classify_audio_ml(features: dict) -> tuple[str, float, dict]:
#       vec = np.array(list(features.values())).reshape(1, -1)
#       label_id   = int(_pipeline.predict(vec)[0])
#       proba      = _pipeline.predict_proba(vec)[0]
#       confidence = float(proba.max())
#       return _label_map[label_id], round(confidence, 3), {}


if __name__ == "__main__":
    train()