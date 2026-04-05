"""Tests for the /api/analyze endpoint"""
import io
import time
import pytest
import numpy as np
from scipy.io import wavfile


class TestAnalyzeEndpoint:
    """Tests for POST /api/analyze"""

    def test_no_input(self, client):
        """POST /api/analyze with no file and no URL should return 400 or 422"""
        response = client.post("/api/analyze")
        assert response.status_code in (400, 422)
        data = response.json()
        assert data["success"] is False

    def test_invalid_url(self, client):
        """POST /api/analyze with invalid URL should return 422"""
        response = client.post("/api/analyze", data={"url": "not-a-url"})
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    def test_non_youtube_url(self, client):
        """POST /api/analyze with non-YouTube URL should return 422"""
        response = client.post(
            "/api/analyze", 
            data={"url": "https://example.com/audio.mp3"}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "YouTube" in data["error"]

    def test_file_too_large(self, client):
        """POST /api/analyze with file > 50MB should return 413"""
        # Create a 51MB file of zero bytes
        large_file = io.BytesIO(b"\x00" * (51 * 1024 * 1024))
        large_file.name = "large.wav"
        
        response = client.post(
            "/api/analyze",
            files={"file": ("large.wav", large_file, "audio/wav")}
        )
        assert response.status_code == 413
        data = response.json()
        assert data["success"] is False

    def test_unsupported_mime(self, client):
        """POST /api/analyze with unsupported MIME type should return 415"""
        # Create a small file with PDF content type
        small_file = io.BytesIO(b"small content for testing")
        
        response = client.post(
            "/api/analyze",
            files={"file": ("test.pdf", small_file, "application/pdf")}
        )
        assert response.status_code == 415
        data = response.json()
        assert data["success"] is False
        assert "Unsupported file type" in data["error"]

    def test_valid_wav_upload(self, client):
        """POST /api/analyze with valid WAV file should return 202 and complete successfully"""
        # Generate a 2-second 440 Hz sine wave
        sample_rate = 44100
        duration = 2.0
        frequency = 440.0
        
        t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        
        # Write to BytesIO as WAV
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, sample_rate, audio_data)
        wav_buffer.seek(0)
        
        # Submit the file
        response = client.post(
            "/api/analyze",
            files={"file": ("test_sine.wav", wav_buffer, "audio/wav")}
        )
        
        # Should return 202 with task_id
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data
        assert data["status"] == "processing"
        
        task_id = data["task_id"]
        
        # Poll for result (max 30 attempts, 1 second apart)
        final_result = None
        for _ in range(30):
            time.sleep(1)
            result_response = client.get(f"/api/result/{task_id}")
            
            if result_response.status_code == 202:
                # Still processing
                continue
            elif result_response.status_code == 200:
                # Done
                final_result = result_response.json()
                break
            elif result_response.status_code == 500:
                # Error
                final_result = result_response.json()
                break
            else:
                pytest.fail(f"Unexpected status code: {result_response.status_code}")
        
        assert final_result is not None, "Task did not complete within 30 seconds"
        
        # Check that required keys are present
        assert "verdict" in final_result
        assert "confidence" in final_result
        assert "duration" in final_result
        assert "segments" in final_result
        assert "summary" in final_result


class TestResultEndpoint:
    """Tests for GET /api/result/{task_id}"""

    def test_result_not_found(self, client):
        """GET /api/result with nonexistent ID should return 404"""
        response = client.get("/api/result/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()
