"""Audio analysis data models"""
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field


class FeatureData(BaseModel):
    """Acoustic features extracted from audio"""
    mfcc_mean: float = Field(description="Mean of MFCC coefficients")
    mfcc_std: float = Field(description="Standard deviation of MFCC coefficients")
    mfcc_delta_mean: float = Field(description="Mean of MFCC delta (rate of change)")
    spectral_centroid: float = Field(description="Brightness of sound (Hz)")
    spectral_bandwidth: float = Field(description="Spread of spectrum")
    spectral_rolloff: float = Field(description="Frequency rolloff point (Hz)")
    spectral_contrast: float = Field(description="Peak-valley energy difference")
    chroma_mean: float = Field(description="Mean pitch class energy")
    chroma_std: float = Field(description="Pitch class energy variation")
    zcr: float = Field(description="Zero crossing rate")
    rms: float = Field(description="Root mean square energy")
    tempo: float = Field(description="Estimated tempo (BPM)")
    onset_mean: float = Field(description="Mean onset strength")
    onset_std: float = Field(description="Onset strength variation")


class ReasoningData(BaseModel):
    """Per-feature reasoning for classification decision"""
    value: float = Field(description="Feature value")
    vote: float = Field(description="Signed vote contribution")


class AnalysisResult(BaseModel):
    """Complete audio analysis result"""
    source: Literal["file", "youtube"] = Field(description="Input source type")
    prediction: Literal["music", "quran/speech"] = Field(description="Classification result")
    confidence: float = Field(ge=0, le=1, description="Classification confidence")
    features: Dict[str, float] = Field(description="Extracted acoustic features")
    reasoning: Dict[str, ReasoningData] = Field(description="Classification reasoning")
    filename: Optional[str] = Field(default=None, description="Original filename (if file upload)")
    url: Optional[str] = Field(default=None, description="Source URL (if YouTube)")
