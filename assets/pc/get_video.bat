@echo off
setlocal
rem Downloads a YouTube video + subtitles into the "inbox" folder next to this
rem file, so Claude (chat) can pick it up through the connected folder.
rem Usage: double-click and paste the link, or:  get_video.bat URL [height]

rem yt-dlp can be a program on PATH (winget) or a Python package (pip).
set "YTDLP="
where yt-dlp >nul 2>nul && set "YTDLP=yt-dlp"
if not defined YTDLP (
  python -m yt_dlp --version >nul 2>nul && set "YTDLP=python -m yt_dlp"
)
if not defined YTDLP (
  py -m yt_dlp --version >nul 2>nul && set "YTDLP=py -m yt_dlp"
)
if not defined YTDLP (
  echo yt-dlp is not installed. Run one of these once, then start again:
  echo     winget install yt-dlp.yt-dlp
  echo     python -m pip install -U yt-dlp
  pause & exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo ffmpeg is not installed. Run this once, then start again:
  echo     winget install Gyan.FFmpeg
  pause & exit /b 1
)

set "URL=%~1"
if "%URL%"=="" set /p "URL=Paste the YouTube link: "
set "H=%~2"
if "%H%"=="" set "H=720"

set "OUT=%~dp0inbox"
if not exist "%OUT%" mkdir "%OUT%"

%YTDLP% --no-playlist --restrict-filenames ^
  -f "bv*[height<=%H%]+ba/b[height<=%H%]/b" -S "vcodec:h264,res,acodec:m4a" ^
  --merge-output-format mp4 ^
  --write-subs --write-auto-subs --sub-langs "en.*,ml.*,-live_chat" ^
  --sub-format "json3/vtt/best" --write-info-json ^
  -o "%OUT%\%%(id)s.%%(ext)s" "%URL%"
if errorlevel 1 (
  echo.
  echo The download reported an error. If a video file is in the inbox it may
  echo still be usable; otherwise update yt-dlp and try again.
)

echo.
echo Done. Files are in: %OUT%
echo Now tell Claude: "the video is in the inbox folder, make the shorts".
pause
