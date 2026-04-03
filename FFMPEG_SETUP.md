# 🎬 FFMPEG SETUP GUIDE - OUT-OF-THE-BOX WINDOWS SUPPORT

## 📦 **BUNDLED FFMPEG FOR WINDOWS**

This guide shows how to bundle ffmpeg with your Quran Shield project so Windows users **don't need to install ffmpeg system-wide**.

---

## 🚀 **QUICK SETUP (5 minutes)**

### **Step 1: Download FFmpeg for Windows**

**Option A: Direct Download (Recommended)**

1. Go to: https://www.gyan.dev/ffmpeg/builds/
2. Download: **ffmpeg-release-essentials.zip** (~80MB)
3. Or use this direct link: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z

**Option B: Official FFmpeg Site**

1. Go to: https://ffmpeg.org/download.html
2. Click "Windows" → "Windows builds from gyan.dev"
3. Download the "release essentials" build

### **Step 2: Extract and Place Binaries**

1. **Extract the downloaded ZIP file**
2. **Navigate to the bin folder** inside:
   ```
   ffmpeg-7.x-essentials_build/
   └── bin/
       ├── ffmpeg.exe
       ├── ffprobe.exe
       └── ffplay.exe
   ```

3. **Copy only ffmpeg.exe and ffprobe.exe** to your project:
   ```
   C:\Users\omarm\Quran-shield-\bin\ffmpeg\
   ├── ffmpeg.exe     ← Copy this
   └── ffprobe.exe    ← Copy this
   ```

**PowerShell Commands:**
```powershell
# Create bin/ffmpeg directory (already done)
cd C:\Users\omarm\Quran-shield-

# Copy binaries (replace path with your download location)
Copy-Item "C:\Downloads\ffmpeg-7.x-essentials_build\bin\ffmpeg.exe" "bin\ffmpeg\"
Copy-Item "C:\Downloads\ffmpeg-7.x-essentials_build\bin\ffprobe.exe" "bin\ffmpeg\"
```

### **Step 3: Verify Installation**

```powershell
cd C:\Users\omarm\Quran-shield-

# Check if files exist
Get-ChildItem bin\ffmpeg\
```

**Expected output:**
```
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          xx/xx/xxxx   xx:xx      xxxxxxx ffmpeg.exe
-a---          xx/xx/xxxx   xx:xx      xxxxxxx ffprobe.exe
```

---

## ✅ **TESTING**

### **Test 1: Verify FFmpeg is Detected**

```bash
cd C:\Users\omarm\Quran-shield-
python start.py
```

**Look for these logs in the startup output:**
```
INFO:     ✅ Using bundled ffmpeg: C:\Users\omarm\Quran-shield-\bin\ffmpeg\ffmpeg.exe
INFO:     ✅ Using bundled ffprobe: C:\Users\omarm\Quran-shield-\bin\ffmpeg\ffprobe.exe
INFO:     ✅ pydub configured to use detected ffmpeg
INFO:     ✅ YouTubeDownloader initialized with ffmpeg support
```

### **Test 2: Test File Upload**

1. Open: `http://localhost:8000/app`
2. Upload any MP3/WAV file
3. Click "Analyze Audio"
4. Should work! ✅

### **Test 3: Test YouTube Download**

1. Open: `http://localhost:8000/app`
2. Paste YouTube URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
3. Click "Analyze Audio"
4. Wait 10-30 seconds
5. Should see results! ✅

**Server logs should show:**
```
INFO:     Using ffmpeg at: C:\Users\omarm\Quran-shield-\bin\ffmpeg\ffmpeg.exe
INFO:     Converting ...audio.webm to WAV using bundled ffmpeg...
INFO:     ✅ Conversion successful: ...converted_audio.wav
```

---

## 🔍 **HOW IT WORKS**

### **FFmpeg Detection Order**

The app automatically detects ffmpeg in this order:

1. **Bundled in `bin/ffmpeg/`** (for out-of-the-box support) ✅
2. **System PATH** (if user has ffmpeg installed)

### **Auto-Configuration**

When the server starts:

```python
# backend/app/utils/ffmpeg_config.py
class FFmpegConfig:
    def _detect_ffmpeg(self):
        # 1. Check bin/ffmpeg/ for bundled version
        bundled_ffmpeg = project_root / "bin" / "ffmpeg" / "ffmpeg.exe"
        
        if bundled_ffmpeg.exists():
            # Use bundled version! ✅
            self.ffmpeg_path = str(bundled_ffmpeg)
            AudioSegment.ffmpeg = self.ffmpeg_path  # Configure pydub
        else:
            # Fall back to system PATH
            self.ffmpeg_path = find_in_path("ffmpeg.exe")
```

### **YouTube Download Flow**

```
1. User pastes YouTube URL
   ↓
2. yt-dlp downloads audio (webm/m4a/etc)
   ↓
3. pydub uses BUNDLED ffmpeg.exe to convert to WAV
   ↓
4. librosa analyzes WAV
   ↓
5. Results returned to user
   ✅ All automatic! No system ffmpeg needed!
```

---

## 📁 **PROJECT STRUCTURE**

```
Quran-shield-/
├── bin/
│   └── ffmpeg/                    ← Bundled ffmpeg binaries
│       ├── ffmpeg.exe             ← ~80MB
│       └── ffprobe.exe            ← ~80MB
│       └── .gitignore             ← Don't commit binaries!
│
├── backend/
│   └── app/
│       ├── utils/
│       │   └── ffmpeg_config.py   ← Auto-detection logic
│       ├── services/
│       │   └── youtube_downloader.py ← Uses bundled ffmpeg
│       └── ...
│
└── frontend/
    └── ...
```

---

## 🎯 **FOR USERS (DISTRIBUTION)**

### **Option 1: Include Binaries in Repository**

**Pros:**
- ✅ Users just clone and run
- ✅ No setup required
- ✅ Works immediately

**Cons:**
- ❌ Large repository size (~160MB for ffmpeg)
- ❌ GitHub may complain about large files

**Solution:**
Add to `.gitignore`:
```
# Don't commit ffmpeg binaries (too large)
bin/ffmpeg/*.exe
```

Provide download instructions in README.

### **Option 2: Automated Download Script**

Create `setup_ffmpeg.py`:
```python
import urllib.request
import zipfile
import shutil
from pathlib import Path

def download_ffmpeg():
    """Download and extract ffmpeg for Windows"""
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z"
    # Download, extract, copy to bin/ffmpeg/
    # ...
```

Users run:
```bash
python setup_ffmpeg.py
```

### **Option 3: Installer Package**

Use PyInstaller or similar to create .exe that includes ffmpeg:
```bash
pyinstaller --add-binary "bin/ffmpeg/ffmpeg.exe:bin/ffmpeg" main.py
```

---

## 🛠️ **TROUBLESHOOTING**

### **Issue: "ffmpeg not found" on startup**

**Error logs:**
```
⚠️ Bundled ffmpeg not found at C:\Users\...\bin\ffmpeg
❌ ffmpeg not found! The application will not work correctly.
```

**Solution:**
1. Check if `bin\ffmpeg\ffmpeg.exe` exists
2. Download ffmpeg (see Step 1 above)
3. Copy binaries to `bin\ffmpeg\`
4. Restart server

### **Issue: "YouTubeDownloader initialized WITHOUT ffmpeg"**

**Error logs:**
```
⚠️ YouTubeDownloader initialized WITHOUT ffmpeg - downloads may fail!
```

**Solution:**
Same as above - ensure binaries are in `bin\ffmpeg\`

### **Issue: YouTube download fails with conversion error**

**Error message:**
```
Audio conversion failed: ... ffmpeg is not properly configured
```

**Check:**
```powershell
# Verify files exist
dir bin\ffmpeg\

# Check file sizes (should be ~80MB each)
```

**Solution:**
Re-download and copy fresh binaries

### **Issue: File upload works but YouTube doesn't**

**Possible cause:**
ffmpeg works for file conversion but not YouTube download

**Check server logs:**
Look for:
```
INFO:     Using ffmpeg at: C:\Users\...\bin\ffmpeg\ffmpeg.exe
```

If not present, ffmpeg isn't detected.

---

## 📊 **COMPARISON: BUNDLED VS SYSTEM FFMPEG**

| Aspect | Bundled (bin/ffmpeg/) | System-wide |
|--------|------------------------|-------------|
| **Setup** | Copy 2 files | Install + add to PATH |
| **User Experience** | ✅ Works immediately | ❌ Requires setup |
| **Repository Size** | ~160MB larger | No impact |
| **Updates** | Manual | Via system package manager |
| **Portability** | ✅ App is self-contained | ❌ Depends on system |
| **Conflicts** | None | May conflict with other apps |

**Recommendation:** Use bundled ffmpeg for Windows distribution.

---

## 🔐 **SECURITY NOTES**

### **Verify FFmpeg Download**

Only download ffmpeg from trusted sources:
- ✅ https://ffmpeg.org (official)
- ✅ https://www.gyan.dev/ffmpeg/builds/ (official Windows builds)
- ❌ Random websites (may contain malware)

### **Checksum Verification**

For production, verify SHA256 checksums:
```powershell
Get-FileHash bin\ffmpeg\ffmpeg.exe -Algorithm SHA256
```

Compare with official checksums from ffmpeg.org

---

## 📝 **CODE CHANGES SUMMARY**

### **New File: `backend/app/utils/ffmpeg_config.py`**

**Purpose:** Auto-detect and configure ffmpeg

**Key features:**
- Detects bundled ffmpeg in `bin/ffmpeg/`
- Falls back to system PATH
- Configures pydub automatically
- Provides helpful error messages

### **Updated: `backend/app/services/youtube_downloader.py`**

**Changes:**
- Imports `get_ffmpeg_config()`
- Checks ffmpeg availability before download
- Raises `RuntimeError` if ffmpeg missing
- Uses bundled ffmpeg for conversion

### **Updated: `backend/app/services/audio_analyzer.py`**

**Changes:**
- Configures ffmpeg on initialization
- Ensures pydub uses bundled ffmpeg

### **Updated: `backend/app/routes/audio.py`**

**Changes:**
- Catches `RuntimeError` for missing ffmpeg
- Provides helpful setup instructions in error message

---

## ✅ **VERIFICATION CHECKLIST**

After setup, verify:

- [ ] `bin\ffmpeg\ffmpeg.exe` exists (~80MB)
- [ ] `bin\ffmpeg\ffprobe.exe` exists (~80MB)
- [ ] Server starts without errors
- [ ] Startup logs show: "✅ Using bundled ffmpeg"
- [ ] File upload works
- [ ] YouTube URL download works
- [ ] Temp files cleaned up after analysis
- [ ] No error messages about ffmpeg

---

## 🎉 **SUCCESS CRITERIA**

You know it's working when:

1. **Server starts** with logs showing bundled ffmpeg detected
2. **File upload** analysis works
3. **YouTube download** converts and analyzes successfully
4. **No manual ffmpeg installation** required for Windows users
5. **App works out-of-the-box** after cloning repository

---

## 📚 **ADDITIONAL RESOURCES**

**FFmpeg Downloads:**
- Official site: https://ffmpeg.org/download.html
- Windows builds: https://www.gyan.dev/ffmpeg/builds/
- Documentation: https://ffmpeg.org/documentation.html

**pydub Documentation:**
- https://github.com/jiaaro/pydub
- Specifying ffmpeg location: https://github.com/jiaaro/pydub#getting-ffmpeg-set-up

**yt-dlp Documentation:**
- https://github.com/yt-dlp/yt-dlp
- ffmpeg integration: https://github.com/yt-dlp/yt-dlp#embedding-ffmpeg

---

## 🎯 **QUICK REFERENCE**

### **Download FFmpeg:**
https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

### **Copy to:**
```
C:\Users\omarm\Quran-shield-\bin\ffmpeg\
├── ffmpeg.exe
└── ffprobe.exe
```

### **Start Server:**
```bash
cd C:\Users\omarm\Quran-shield-
python start.py
```

### **Verify:**
```
Look for: ✅ Using bundled ffmpeg: ...
```

---

**🎉 Your app now works out-of-the-box on Windows without requiring system ffmpeg installation!**

---

**Created**: April 3, 2026  
**Status**: ✅ READY FOR WINDOWS USERS
