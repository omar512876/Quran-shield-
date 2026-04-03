# Quran Shield - FFmpeg Auto-Download System

## Overview

This document explains the comprehensive FFmpeg auto-download system implemented in Quran Shield.

---

## Architecture

### Components

1. **FFmpegManager** (`backend/app/utils/ffmpeg_manager.py`)
   - Core module that manages FFmpeg binaries
   - Handles download, extraction, and verification
   - Platform-specific logic for Windows, Linux, macOS

2. **FFmpegConfig** (`backend/app/utils/ffmpeg_config.py`)
   - Wrapper around FFmpegManager
   - Provides backward compatibility
   - Configures pydub and yt-dlp

3. **Download Sources**
   - **Windows/Linux**: [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds)
   - **macOS**: [evermeet.cx](https://evermeet.cx/ffmpeg/)

---

## Detection & Download Flow

```
┌─────────────────────────────────────────┐
│    Application Starts                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  FFmpegManager.ensure_ffmpeg()           │
└──────────────┬───────────────────────────┘
               │
               ▼
    ┌─────────────────────┐
    │ Check Local         │ ← backend/bin/ffmpeg/
    │ (Project Dir)       │
    └─────────┬───────────┘
              │
         Found? ──YES──> ✅ Use Local
              │
             NO
              │
              ▼
    ┌─────────────────────┐
    │ Try imageio-ffmpeg  │ ← pip package
    │ (if installed)      │
    └─────────┬───────────┘
              │
         Found? ──YES──> ✅ Use imageio-ffmpeg
              │
             NO
              │
              ▼
    ┌─────────────────────┐
    │ Check System PATH   │ ← system install
    │                     │
    └─────────┬───────────┘
              │
         Found? ──YES──> ✅ Use System FFmpeg
              │
             NO
              │
              ▼
    ┌─────────────────────────────────┐
    │ Download FFmpeg                 │
    │ - Platform detection            │
    │ - Download archive              │
    │ - Extract binaries              │
    │ - Set permissions               │
    │ - Verify installation           │
    └─────────┬───────────────────────┘
              │
         Success? ──YES──> ✅ Use Downloaded
              │
             NO
              │
              ▼
            ❌ Error
```

---

## Platform-Specific Details

### Windows

- **Download**: FFmpeg-Builds latest Windows 64-bit GPL build
- **Format**: ZIP archive
- **Extraction**: `ffmpeg.exe` and `ffprobe.exe` extracted from `bin/` folder
- **Permissions**: Not required (Windows .exe)
- **Location**: `backend\bin\ffmpeg\ffmpeg.exe`

### Linux

- **Download**: FFmpeg-Builds latest Linux 64-bit GPL build
- **Format**: TAR.XZ archive
- **Extraction**: `ffmpeg` and `ffprobe` extracted from `bin/` folder
- **Permissions**: Execute bit set with `chmod +x`
- **Location**: `backend/bin/ffmpeg/ffmpeg`

### macOS

- **Download**: Two separate downloads from evermeet.cx
  - FFmpeg binary
  - FFprobe binary
- **Format**: ZIP archives (one per binary)
- **Extraction**: Direct binary extraction
- **Permissions**: Execute bit set with `chmod +x`
- **Location**: `backend/bin/ffmpeg/ffmpeg`

---

## File Structure

```
Quran-shield-/
├── backend/
│   ├── bin/
│   │   └── ffmpeg/              ← Download location
│   │       ├── ffmpeg           ← Auto-downloaded
│   │       └── ffprobe          ← Auto-downloaded
│   ├── app/
│   │   ├── utils/
│   │   │   ├── ffmpeg_manager.py    ← Core download logic
│   │   │   └── ffmpeg_config.py     ← Configuration wrapper
│   │   └── ...
│   └── tests/
│       └── test_ffmpeg_manager.py   ← Unit tests
```

---

## API Usage

### Simple Usage

```python
from backend.app.utils.ffmpeg_manager import ensure_ffmpeg

# Get FFmpeg paths (downloads if necessary)
ffmpeg_path, ffprobe_path = ensure_ffmpeg()

if ffmpeg_path:
    print(f"FFmpeg available at: {ffmpeg_path}")
else:
    print("FFmpeg not available")
```

### Advanced Usage

```python
from backend.app.utils.ffmpeg_manager import FFmpegManager
from pathlib import Path

# Create manager with custom install directory
manager = FFmpegManager(install_dir=Path("custom/path"))

# Ensure FFmpeg is available
ffmpeg, ffprobe = manager.ensure_ffmpeg()

# Get version
version = manager.get_version()
print(f"FFmpeg version: {version}")
```

### Integration with pydub

```python
from backend.app.utils.ffmpeg_config import get_ffmpeg_config
from pydub import AudioSegment

# Get config (auto-downloads if needed)
config = get_ffmpeg_config()

# Configure pydub
config.configure_pydub()

# Now pydub uses the correct FFmpeg
audio = AudioSegment.from_mp3("file.mp3")
```

---

## Error Handling

### Download Failures

If automatic download fails, the system:

1. **Logs detailed error messages**
   ```
   ERROR - Download failed: URLError('Network unreachable')
   ERROR - FFmpeg not found and auto-download failed!
   ```

2. **Provides fallback instructions**
   ```
   Please check your internet connection and try again,
   or install FFmpeg manually: https://ffmpeg.org/download.html
   ```

3. **Continues without crashing** (graceful degradation)

### Verification

After download, the system verifies:
- ✅ Files exist
- ✅ Files are executable (Unix)
- ✅ FFmpeg version can be retrieved

---

## Testing

### Unit Tests

```bash
cd backend
pytest tests/test_ffmpeg_manager.py -v
```

Tests cover:
- Platform detection
- Local binary detection
- System FFmpeg detection
- Permission setting (Unix)
- Executable verification
- Manager singleton pattern

### Manual Testing

```bash
# Remove existing binaries
rm -rf backend/bin/ffmpeg/

# Start application (should auto-download)
cd backend
python -m uvicorn app.main:app

# Check logs for download progress
# Verify binaries exist
ls -lh backend/bin/ffmpeg/
```

---

## Security Considerations

### Download Sources

- **BtbN/FFmpeg-Builds**: Official GitHub releases, widely used
- **evermeet.cx**: Trusted macOS FFmpeg distribution

### Verification

Currently implements:
- ✅ HTTPS downloads
- ✅ File existence checks
- ✅ Executable permission verification

Could be enhanced with:
- ⚠️ SHA256 checksum verification
- ⚠️ GPG signature verification
- ⚠️ Version pinning

---

## Performance

### First Run (Download)
- **Windows**: ~60-90 seconds (70MB download)
- **Linux**: ~60-90 seconds (80MB download)
- **macOS**: ~30-45 seconds (50MB + 40MB downloads)

### Subsequent Runs
- **Detection**: <100ms (local file check)
- **No network calls** after initial download

---

## Troubleshooting

### Download Hangs

**Cause**: Slow internet or firewall blocking GitHub/evermeet.cx

**Solution**:
```bash
# Test connectivity
curl -I https://github.com
curl -I https://evermeet.cx

# Manual download and extract to backend/bin/ffmpeg/
```

### Permission Denied (Unix)

**Cause**: Binary not executable

**Solution**:
```bash
chmod +x backend/bin/ffmpeg/ffmpeg
chmod +x backend/bin/ffmpeg/ffprobe
```

### Wrong Architecture

**Cause**: Running on ARM/32-bit system (auto-download is x64 only)

**Solution**: Install system FFmpeg manually
```bash
# Linux
sudo apt install ffmpeg

# macOS ARM (M1/M2)
brew install ffmpeg
```

---

## Future Enhancements

1. **Checksum Verification**: Add SHA256 hash verification
2. **Version Pinning**: Pin to specific FFmpeg versions for reproducibility
3. **Progress Callbacks**: Show download progress in UI
4. **Architecture Detection**: Support ARM, 32-bit systems
5. **Offline Installer**: Bundle FFmpeg with release packages
6. **Update Mechanism**: Check for and download FFmpeg updates

---

## Conclusion

The FFmpeg auto-download system provides:

✅ **Zero manual setup** for users
✅ **Cross-platform support** (Windows, Linux, macOS)
✅ **Offline capability** after first run
✅ **Graceful fallbacks** (imageio-ffmpeg, system FFmpeg)
✅ **Comprehensive error handling**
✅ **Production-ready** logging and verification

Users can now clone the repository, run `pip install -r requirements.txt`, and immediately use all features without any manual FFmpeg installation!
