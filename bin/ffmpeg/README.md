# FFmpeg Binaries

This folder should contain the bundled ffmpeg binaries for out-of-the-box Windows support.

## Required Files

Place the following files in this directory:
- `ffmpeg.exe` (~80MB)
- `ffprobe.exe` (~80MB)

## Download Instructions

### Quick Download

1. **Download**: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
2. **Extract** the ZIP file
3. **Copy** `ffmpeg.exe` and `ffprobe.exe` from the `bin/` folder to this directory

### Manual Steps

```powershell
# Download and extract ffmpeg (Windows)
# Then copy binaries:
Copy-Item "path\to\ffmpeg-build\bin\ffmpeg.exe" "."
Copy-Item "path\to\ffmpeg-build\bin\ffprobe.exe" "."
```

## Verification

After placing the binaries, this folder should contain:
```
bin/ffmpeg/
├── .gitignore
├── README.md (this file)
├── ffmpeg.exe      ← You need to download this
└── ffprobe.exe     ← You need to download this
```

## Why Bundled FFmpeg?

- ✅ **Out-of-the-box experience**: Users don't need to install ffmpeg system-wide
- ✅ **No PATH configuration**: Works immediately after cloning
- ✅ **Portable**: Self-contained application
- ✅ **No conflicts**: Independent of system ffmpeg installation

## For Developers

The application automatically detects these binaries at startup:
- See `backend/app/utils/ffmpeg_config.py` for detection logic
- Logs will show: `✅ Using bundled ffmpeg: ...`

## Size Considerations

FFmpeg binaries are ~160MB total, which is why they're excluded from git.
Users need to download them once during setup.

## Alternative: System FFmpeg

If bundled ffmpeg is not found, the app will fall back to system PATH.
Windows users can install ffmpeg system-wide from: https://ffmpeg.org/download.html

---

**For detailed setup instructions, see: `FFMPEG_SETUP.md` in the project root.**
