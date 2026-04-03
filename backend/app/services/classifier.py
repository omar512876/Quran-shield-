"""Audio classification service"""
import logging
from typing import Dict, Tuple, List
from ..config import settings

logger = logging.getLogger(__name__)


class AudioClassifier:
    """
    Multi-feature weighted classifier for audio categorization.
    
    This classifier uses a rule-based approach with calibrated thresholds
    for each acoustic feature. Each feature contributes a signed vote:
    - Positive votes indicate music-like characteristics
    - Negative votes indicate speech/Quran characteristics
    
    The final classification is based on the sum of all votes.
    """
    
    def __init__(self, threshold: float = None):
        """
        Initialize the classifier.
        
        Args:
            threshold: Decision threshold (score > threshold = music)
        """
        self.threshold = threshold or settings.MUSIC_THRESHOLD
    
    def _vote(self, value: float, thresholds: List[Tuple[float, float]]) -> float:
        """
        Map a feature value to a vote using stepwise thresholds.
        
        Args:
            value: Feature value to evaluate
            thresholds: List of (upper_bound, vote) tuples, sorted descending
            
        Returns:
            Vote contribution for this feature
        """
        for bound, vote in thresholds:
            if value > bound:
                return vote
        return thresholds[-1][1]
    
    def classify(self, features: Dict[str, float]) -> Tuple[str, float, Dict]:
        """
        Classify audio based on extracted features.
        
        Args:
            features: Dictionary of feature names to values
            
        Returns:
            Tuple of (prediction, confidence, reasoning_dict)
            - prediction: "music" or "quran/speech"
            - confidence: Float in [0, 1]
            - reasoning: Per-feature breakdown
            
        Raises:
            ValueError: If features dictionary is invalid or missing required keys
        """
        # Validate input
        if not features or not isinstance(features, dict):
            raise ValueError("Features must be a non-empty dictionary")
        
        required_features = [
            "spectral_centroid", "chroma_std", "tempo", "onset_std",
            "spectral_contrast", "mfcc_delta_mean", "spectral_rolloff", "zcr"
        ]
        
        missing = [f for f in required_features if f not in features]
        if missing:
            raise ValueError(f"Missing required features: {', '.join(missing)}")
        
        logger.info(f"Classifying audio with {len(features)} features")
        
        score = 0.0
        reasoning = {}
        
        # === Feature 1: Spectral Centroid (HIGH WEIGHT) ===
        # Music tends to have higher frequency content
        vote = self._vote(features["spectral_centroid"], [
            (3500, +2.5),
            (2500, +1.5),
            (1800, +0.5),
            (1200, -0.5),
            (-999, -1.5),
        ])
        score += vote
        reasoning["spectral_centroid"] = {
            "value": round(features["spectral_centroid"], 1),
            "vote": vote
        }
        
        # === Feature 2: Chroma Std (HIGH WEIGHT) ===
        # Music has richer harmonic variation
        vote = self._vote(features["chroma_std"], [
            (0.22, +2.0),
            (0.16, +1.0),
            (0.10,  0.0),
            (-999, -1.0),
        ])
        score += vote
        reasoning["chroma_std"] = {
            "value": round(features["chroma_std"], 4),
            "vote": vote
        }
        
        # === Feature 3: Tempo (HIGH WEIGHT) ===
        # Music has clear rhythmic pulse
        vote = self._vote(features["tempo"], [
            (100, +2.0),
            (70,  +1.0),
            (50,  +0.5),
            (30,  -0.5),
            (-999, -1.0),
        ])
        score += vote
        reasoning["tempo"] = {
            "value": round(features["tempo"], 1),
            "vote": vote
        }
        
        # === Feature 4: Onset Strength Std (MEDIUM WEIGHT) ===
        # Regular beats produce high onset variation
        vote = self._vote(features["onset_std"], [
            (0.8, +1.5),
            (0.5, +0.5),
            (-999, -0.5),
        ])
        score += vote
        reasoning["onset_std"] = {
            "value": round(features["onset_std"], 4),
            "vote": vote
        }
        
        # === Feature 5: Spectral Contrast (MEDIUM WEIGHT) ===
        # Musical harmonics create strong peaks
        vote = self._vote(features["spectral_contrast"], [
            (30, +1.5),
            (20, +0.5),
            (10, -0.5),
            (-999, -1.0),
        ])
        score += vote
        reasoning["spectral_contrast"] = {
            "value": round(features["spectral_contrast"], 2),
            "vote": vote
        }
        
        # === Feature 6: MFCC Delta (MEDIUM WEIGHT) ===
        # Music has faster timbral changes
        vote = self._vote(features["mfcc_delta_mean"], [
            (5.0, +1.0),
            (2.0, +0.5),
            (-999, -0.5),
        ])
        score += vote
        reasoning["mfcc_delta_mean"] = {
            "value": round(features["mfcc_delta_mean"], 4),
            "vote": vote
        }
        
        # === Feature 7: Spectral Rolloff (MEDIUM WEIGHT) ===
        # Music extends into higher frequencies
        vote = self._vote(features["spectral_rolloff"], [
            (6000, +1.5),
            (4000, +0.5),
            (2500,  0.0),
            (-999, -0.5),
        ])
        score += vote
        reasoning["spectral_rolloff"] = {
            "value": round(features["spectral_rolloff"], 1),
            "vote": vote
        }
        
        # === Feature 8: Zero Crossing Rate (LOW WEIGHT) ===
        # High ZCR indicates percussion/noise
        vote = self._vote(features["zcr"], [
            (0.15, +1.0),
            (0.08,  0.0),
            (-999, -0.5),
        ])
        score += vote
        reasoning["zcr"] = {
            "value": round(features["zcr"], 4),
            "vote": vote
        }
        
        # === Calculate Confidence ===
        max_possible_score = 13.0  # Sum of maximum positive votes
        confidence = min(abs(score) / max_possible_score, 1.0)
        
        # === Make Prediction ===
        prediction = "music" if score > self.threshold else "quran/speech"
        
        logger.info(f"Classification result: {prediction} (score={score:.2f}, confidence={confidence:.3f})")
        
        return prediction, round(confidence, 3), reasoning
