from pathlib import Path
import re
import joblib
import pandas as pd
import numpy as np
from django.conf import settings

BASE_MODEL_PATH = Path(settings.BASE_DIR) / 'ml_models' / 'chronic_disease_rf.joblib'

NUMERICAL = [
    'age','age_normalized','bmi','HbA1c_level','glucose','cholesterol','sleep_hours',
    'triglycerides','blood_pressure','crp_level','homocysteine_level','systolic_bp',
    'diastolic_bp','alcohol_intake','salt_intake','heart_rate','hdl','ldl'
]
CATEGORICAL = [
    'age_level','gender','bmi_level','smoking','physical_activity','family_history',
    'stress_level','low_hdl_cholesterol','high_ldl_cholesterol','high_blood_pressure',
    'sugar_consumption','education_level','employment_status'
]
FEATURES = NUMERICAL + CATEGORICAL
CLASSES = ['DI','DI_HY','HY','N']

_model_cache = None
_model_cache_path = None
_model_cache_mtime = None


def _latest_model_path():
    """Use the newest aggregated global model when available, otherwise v1 base model."""
    media_root = Path(settings.MEDIA_ROOT)
    candidates = []
    if media_root.exists():
        for path in media_root.glob('global_model_round_*.joblib'):
            match = re.search(r'global_model_round_(\d+)\.joblib$', path.name)
            if match:
                candidates.append((int(match.group(1)), path))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    return BASE_MODEL_PATH


def clear_model_cache():
    global _model_cache, _model_cache_path, _model_cache_mtime
    _model_cache = None
    _model_cache_path = None
    _model_cache_mtime = None


def load_model():
    global _model_cache, _model_cache_path, _model_cache_mtime
    path = _latest_model_path()
    mtime = path.stat().st_mtime_ns
    if _model_cache is None or _model_cache_path != path or _model_cache_mtime != mtime:
        _model_cache = joblib.load(path)
        _model_cache_path = path
        _model_cache_mtime = mtime
    return _model_cache


def predict_one(payload):
    bundle = load_model()
    pipe = bundle['pipeline']
    encoder = bundle['label_encoder']
    row = {k: payload[k] for k in FEATURES}
    frame = pd.DataFrame([row])
    pred_code = int(pipe.predict(frame)[0])
    probs = pipe.predict_proba(frame)[0]
    labels = encoder.inverse_transform(np.arange(len(probs)))
    probability_map = {str(label): float(prob) for label, prob in zip(labels, probs)}
    label = str(encoder.inverse_transform([pred_code])[0])
    confidence = float(np.max(probs))
    return label, confidence, probability_map


def model_info():
    bundle = load_model()
    pipe = bundle['pipeline']
    rf = pipe.named_steps['classifier']
    active_path = _latest_model_path()
    return {
        'version': bundle.get('model_version', 'v1.0.0'),
        'trees': len(rf.estimators_),
        'processed_features': bundle.get('feature_schema', {}).get('processed_features', 55),
        'classes': bundle.get('feature_schema', {}).get('classes', CLASSES),
        'artifact': active_path.name,
    }
