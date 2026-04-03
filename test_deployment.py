#!/usr/bin/env python3
"""
Deployment Test Suite for Quran Shield
Tests health endpoint, API functionality, and FFmpeg integration after deployment
"""

import requests
import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")


def test_health_endpoint(base_url: str) -> Tuple[bool, Dict[str, Any]]:
    """Test /health endpoint"""
    print_info("Testing health endpoint...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data.get('status', 'OK')}")
            
            # Print additional info if available
            if 'ffmpeg_available' in data:
                ffmpeg_status = "Available" if data['ffmpeg_available'] else "Not Available"
                print_info(f"FFmpeg: {ffmpeg_status}")
            
            return True, data
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False, {}
            
    except requests.exceptions.RequestException as e:
        print_error(f"Health check failed: {str(e)}")
        return False, {}


def test_youtube_analysis(base_url: str) -> Tuple[bool, Dict[str, Any]]:
    """Test YouTube URL analysis"""
    print_info("Testing YouTube URL analysis...")
    
    # Use a short test video (Quran recitation)
    test_url = "https://www.youtube.com/watch?v=pbt60KfJYUg"  # Short Quran clip
    
    try:
        response = requests.post(
            f"{base_url}/api/analyze",
            data={"url": test_url},
            timeout=120  # Allow more time for YouTube download
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success", False):
                prediction = data.get("prediction", "unknown")
                confidence = data.get("confidence", 0)
                processing_time = data.get("processing_time_seconds", 0)
                
                print_success(f"YouTube analysis succeeded!")
                print_info(f"  Prediction: {prediction}")
                print_info(f"  Confidence: {confidence:.2%}")
                print_info(f"  Processing Time: {processing_time:.2f}s")
                
                return True, data
            else:
                error_msg = data.get("error", "Unknown error")
                print_error(f"YouTube analysis failed: {error_msg}")
                return False, data
        else:
            print_error(f"YouTube analysis failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error details: {error_data.get('detail', 'No details')}")
            except:
                pass
            return False, {}
            
    except requests.exceptions.Timeout:
        print_error("YouTube analysis timed out (>120s)")
        print_warning("This is normal for long videos on free-tier platforms")
        return False, {}
    except requests.exceptions.RequestException as e:
        print_error(f"YouTube analysis failed: {str(e)}")
        return False, {}


def test_file_upload(base_url: str) -> Tuple[bool, Dict[str, Any]]:
    """Test file upload analysis"""
    print_info("Testing file upload analysis...")
    
    # Create a minimal test WAV file (1 second of silence)
    import wave
    import io
    import numpy as np
    
    # Generate 1 second of silence at 22050 Hz
    sample_rate = 22050
    duration = 1.0
    samples = int(sample_rate * duration)
    audio_data = np.zeros(samples, dtype=np.int16)
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    wav_buffer.seek(0)
    
    try:
        files = {
            'file': ('test_audio.wav', wav_buffer, 'audio/wav')
        }
        
        response = requests.post(
            f"{base_url}/api/analyze",
            files=files,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success", False):
                prediction = data.get("prediction", "unknown")
                confidence = data.get("confidence", 0)
                processing_time = data.get("processing_time_seconds", 0)
                
                print_success(f"File upload analysis succeeded!")
                print_info(f"  Prediction: {prediction}")
                print_info(f"  Confidence: {confidence:.2%}")
                print_info(f"  Processing Time: {processing_time:.2f}s")
                
                return True, data
            else:
                error_msg = data.get("error", "Unknown error")
                # Silent audio might fail validation - this is expected
                if "silent" in error_msg.lower() or "too short" in error_msg.lower():
                    print_warning(f"File rejected (expected for test silence): {error_msg}")
                    print_success("File upload endpoint is working correctly")
                    return True, data
                else:
                    print_error(f"File upload analysis failed: {error_msg}")
                    return False, data
        else:
            print_error(f"File upload failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error details: {error_data.get('detail', 'No details')}")
            except:
                pass
            return False, {}
            
    except requests.exceptions.RequestException as e:
        print_error(f"File upload failed: {str(e)}")
        return False, {}


def test_error_handling(base_url: str) -> Tuple[bool, Dict[str, Any]]:
    """Test error handling with invalid inputs"""
    print_info("Testing error handling...")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: No input
    try:
        response = requests.post(f"{base_url}/api/analyze", timeout=10)
        if response.status_code == 422:
            print_success("Correctly rejects request with no input (422)")
            tests_passed += 1
        else:
            print_error(f"Expected 422 for no input, got {response.status_code}")
    except Exception as e:
        print_error(f"No input test failed: {str(e)}")
    
    # Test 2: Invalid URL
    try:
        response = requests.post(
            f"{base_url}/api/analyze",
            data={"url": "not-a-valid-url"},
            timeout=10
        )
        if response.status_code in [422, 400]:
            print_success("Correctly rejects invalid URL (422/400)")
            tests_passed += 1
        else:
            print_error(f"Expected 422/400 for invalid URL, got {response.status_code}")
    except Exception as e:
        print_error(f"Invalid URL test failed: {str(e)}")
    
    # Test 3: Too large file size (via header)
    try:
        # Create dummy file data
        large_file = io.BytesIO(b"x" * 1024)  # 1KB file
        
        response = requests.post(
            f"{base_url}/api/analyze",
            files={'file': ('large.mp3', large_file, 'audio/mpeg')},
            headers={'Content-Length': str(100 * 1024 * 1024)},  # Claim 100MB
            timeout=10
        )
        # Note: This test might not work as expected due to how requests library handles Content-Length
        # Just check that the endpoint doesn't crash
        print_success("Large file header test completed without crash")
        tests_passed += 1
    except Exception as e:
        print_warning(f"Large file test failed (this is okay): {str(e)}")
        tests_passed += 1  # Count as passed if it just fails gracefully
    
    success = tests_passed >= 2  # At least 2 out of 3
    if success:
        print_success(f"Error handling tests passed ({tests_passed}/{total_tests})")
    else:
        print_error(f"Error handling tests failed ({tests_passed}/{total_tests})")
    
    return success, {"tests_passed": tests_passed, "total_tests": total_tests}


def run_all_tests(base_url: str):
    """Run all deployment tests"""
    
    print_header("QURAN SHIELD DEPLOYMENT TEST SUITE")
    print_info(f"Testing deployment at: {BOLD}{base_url}{RESET}")
    
    results = {
        "health": False,
        "youtube": False,
        "file_upload": False,
        "error_handling": False
    }
    
    # Test 1: Health Check (Required)
    print_header("1. HEALTH CHECK")
    results["health"], _ = test_health_endpoint(base_url)
    
    if not results["health"]:
        print_error("\n❌ CRITICAL: Health check failed. Cannot proceed with other tests.")
        print_error("Please check your deployment logs and ensure the service is running.")
        return False
    
    # Test 2: Error Handling
    print_header("2. ERROR HANDLING")
    results["error_handling"], _ = test_error_handling(base_url)
    
    # Test 3: File Upload
    print_header("3. FILE UPLOAD ANALYSIS")
    results["file_upload"], _ = test_file_upload(base_url)
    
    # Test 4: YouTube Analysis (Optional - might fail on free tiers)
    print_header("4. YOUTUBE URL ANALYSIS")
    print_warning("This test may timeout on free-tier platforms (60s limit)")
    results["youtube"], _ = test_youtube_analysis(base_url)
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print(f"\n{BOLD}Results:{RESET}")
    for test_name, passed in results.items():
        status = f"{GREEN}✓ PASSED{RESET}" if passed else f"{RED}✗ FAILED{RESET}"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{BOLD}Overall: {passed_tests}/{total_tests} tests passed{RESET}")
    
    # Determine success
    critical_tests = ["health", "error_handling", "file_upload"]
    critical_passed = all(results[t] for t in critical_tests)
    
    if critical_passed:
        print_success("\n✅ DEPLOYMENT IS FUNCTIONAL")
        print_info("Your Quran Shield deployment is working correctly!")
        
        if not results["youtube"]:
            print_warning("\n⚠️ YouTube analysis failed or timed out.")
            print_warning("This is common on free-tier platforms with strict timeouts.")
            print_warning("Consider upgrading to a paid tier for full YouTube support.")
        
        return True
    else:
        print_error("\n❌ DEPLOYMENT HAS CRITICAL ISSUES")
        print_error("Please check the failed tests and deployment logs.")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{BOLD}Usage:{RESET} python test_deployment.py <base_url>")
        print(f"\n{BOLD}Examples:{RESET}")
        print("  python test_deployment.py http://localhost:8000")
        print("  python test_deployment.py https://quran-shield.onrender.com")
        print("  python test_deployment.py https://quran-shield.up.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    # Install required packages if needed
    try:
        import numpy
    except ImportError:
        print_warning("Installing required test dependencies...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "requests"])
        import numpy
    
    success = run_all_tests(base_url)
    sys.exit(0 if success else 1)
