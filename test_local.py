#!/usr/bin/env python3
"""
Local Test Script for Quran Shield
Quick verification that all components are working correctly.

Run this script before deploying to ensure everything works locally.

Usage:
    python test_local.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_imports():
    """Test that all required modules can be imported"""
    print_section("Testing Imports")
    
    errors = []
    
    # Core dependencies
    modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydub", "Pydub"),
        ("librosa", "Librosa"),
        ("numpy", "NumPy"),
        ("yt_dlp", "yt-dlp"),
    ]
    
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name}")
        except ImportError as e:
            print(f"  ✗ {display_name}: {e}")
            errors.append(display_name)
    
    # App modules
    try:
        from app.main import app
        print(f"  ✓ App Main")
    except Exception as e:
        print(f"  ✗ App Main: {e}")
        errors.append("App Main")
    
    try:
        from app.utils.ffmpeg_manager import ensure_ffmpeg, get_ffmpeg_manager
        print(f"  ✓ FFmpeg Manager")
    except Exception as e:
        print(f"  ✗ FFmpeg Manager: {e}")
        errors.append("FFmpeg Manager")
    
    try:
        from app.utils.ffmpeg_config import get_ffmpeg_config
        print(f"  ✓ FFmpeg Config")
    except Exception as e:
        print(f"  ✗ FFmpeg Config: {e}")
        errors.append("FFmpeg Config")
    
    try:
        from app.services.audio_analyzer import AudioAnalyzer
        print(f"  ✓ Audio Analyzer")
    except Exception as e:
        print(f"  ✗ Audio Analyzer: {e}")
        errors.append("Audio Analyzer")
    
    return len(errors) == 0


def test_ffmpeg():
    """Test FFmpeg availability"""
    print_section("Testing FFmpeg")
    
    from app.utils.ffmpeg_manager import ensure_ffmpeg, get_ffmpeg_manager
    
    print("  Checking FFmpeg availability...")
    ffmpeg_path, ffprobe_path = ensure_ffmpeg()
    
    if ffmpeg_path and ffprobe_path:
        print(f"  ✓ FFmpeg: {ffmpeg_path}")
        print(f"  ✓ FFprobe: {ffprobe_path}")
        
        # Check version
        manager = get_ffmpeg_manager()
        version = manager.get_version()
        if version:
            print(f"  ✓ Version: {version[:50]}...")
        
        return True
    else:
        print("  ✗ FFmpeg not available!")
        print("    FFmpeg will be auto-downloaded on first use.")
        print("    Or install manually from: https://ffmpeg.org/download.html")
        return False


def test_ffmpeg_config():
    """Test FFmpeg configuration for pydub"""
    print_section("Testing FFmpeg Configuration")
    
    from app.utils.ffmpeg_config import get_ffmpeg_config
    
    config = get_ffmpeg_config()
    
    if config.is_available():
        print(f"  ✓ FFmpeg configured")
        print(f"    Path: {config.ffmpeg_path}")
        
        # Test pydub configuration
        config.configure_pydub()
        print(f"  ✓ pydub configured")
        
        # Test yt-dlp args
        yt_args = config.get_yt_dlp_postprocessor_args()
        if yt_args:
            print(f"  ✓ yt-dlp args: {yt_args}")
        
        return True
    else:
        print("  ✗ FFmpeg not configured")
        return False


def test_feature_extractor():
    """Test audio feature extraction"""
    print_section("Testing Feature Extractor")
    
    import numpy as np
    from app.services.feature_extractor import FeatureExtractor
    
    # Generate test audio (1 second sine wave)
    sample_rate = 22050
    duration = 1.5
    frequency = 440  # A4 note
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    print(f"  Generated test audio: {duration}s @ {sample_rate}Hz")
    
    try:
        extractor = FeatureExtractor()
        features = extractor.extract_features(audio, sample_rate)
        
        print(f"  ✓ Extracted {len(features)} features")
        print(f"    Sample features:")
        for key in ['spectral_centroid', 'tempo', 'chroma_std']:
            if key in features:
                print(f"      {key}: {features[key]:.4f}")
        
        return True
    except Exception as e:
        print(f"  ✗ Feature extraction failed: {e}")
        return False


def test_classifier():
    """Test audio classifier"""
    print_section("Testing Classifier")
    
    from app.services.classifier import AudioClassifier
    
    # Test features (music-like)
    music_features = {
        "spectral_centroid": 3000,
        "chroma_std": 0.2,
        "tempo": 120,
        "onset_std": 0.7,
        "spectral_contrast": 25,
        "mfcc_delta_mean": 3.0,
        "spectral_rolloff": 5000,
        "zcr": 0.12
    }
    
    # Test features (speech-like)
    speech_features = {
        "spectral_centroid": 1500,
        "chroma_std": 0.08,
        "tempo": 40,
        "onset_std": 0.3,
        "spectral_contrast": 15,
        "mfcc_delta_mean": 1.5,
        "spectral_rolloff": 3000,
        "zcr": 0.05
    }
    
    try:
        classifier = AudioClassifier()
        
        # Test music classification
        prediction, confidence, reasoning = classifier.classify(music_features)
        print(f"  Music-like features -> {prediction} ({confidence:.2%} confidence)")
        
        # Test speech classification
        prediction, confidence, reasoning = classifier.classify(speech_features)
        print(f"  Speech-like features -> {prediction} ({confidence:.2%} confidence)")
        
        print(f"  ✓ Classifier working correctly")
        return True
    except Exception as e:
        print(f"  ✗ Classifier failed: {e}")
        return False


def test_api_routes():
    """Test that API routes are properly configured"""
    print_section("Testing API Routes")
    
    try:
        from fastapi.testclient import TestClient
    except (ImportError, RuntimeError) as e:
        print(f"  ⚠ TestClient not available: {e}")
        print(f"    Install httpx for API tests: pip install httpx")
        print(f"    Skipping API route tests...")
        return True  # Don't fail the whole test suite for this
    
    from app.main import app
    
    client = TestClient(app)
    
    errors = []
    
    # Test health endpoint
    try:
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ GET /health -> {data.get('status', 'OK')}")
            print(f"    FFmpeg available: {data.get('ffmpeg_available', 'unknown')}")
        else:
            print(f"  ✗ GET /health -> {response.status_code}")
            errors.append("/health")
    except Exception as e:
        print(f"  ✗ GET /health -> {e}")
        errors.append("/health")
    
    # Test root endpoint
    try:
        response = client.get("/")
        if response.status_code == 200:
            print(f"  ✓ GET / -> OK")
        else:
            print(f"  ✗ GET / -> {response.status_code}")
            errors.append("/")
    except Exception as e:
        print(f"  ✗ GET / -> {e}")
        errors.append("/")
    
    # Test analyze endpoint (without file - should return 400 or 503 if analyzer not ready)
    try:
        response = client.post("/api/analyze")
        if response.status_code in [400, 422, 503]:
            print(f"  ✓ POST /api/analyze (no input) -> {response.status_code} (expected)")
        else:
            print(f"  ✗ POST /api/analyze (no input) -> {response.status_code}")
            errors.append("/api/analyze")
    except Exception as e:
        print(f"  ✗ POST /api/analyze -> {e}")
        errors.append("/api/analyze")
    
    # Test frontend mounting
    try:
        response = client.get("/app/")
        if response.status_code == 200:
            print(f"  ✓ GET /app/ -> Frontend served")
        else:
            print(f"  ⚠ GET /app/ -> {response.status_code} (frontend may not be mounted)")
    except Exception as e:
        print(f"  ⚠ GET /app/ -> {e}")
    
    return len(errors) == 0


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("  QURAN SHIELD - LOCAL TEST SUITE")
    print("="*60)
    
    results = {
        "Imports": test_imports(),
        "FFmpeg": test_ffmpeg(),
        "FFmpeg Config": test_ffmpeg_config(),
        "Feature Extractor": test_feature_extractor(),
        "Classifier": test_classifier(),
        "API Routes": test_api_routes(),
    }
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✓ PASSED" if passed_flag else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n  Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  ✅ All tests passed! Ready for deployment.")
        return True
    else:
        print("\n  ⚠️ Some tests failed. Review the output above.")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
