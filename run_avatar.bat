@echo off
REM Run the real-time avatar with Gemini AI

REM Set your Google API key here
set GOOGLE_API_KEY=AIzaSyBohBueeFz2SwJrdJVFAjjfapF3OHzZA48

REM Activate conda and run
call conda activate ditto
python realtime_avatar.py --image "./example/image.png" %*

pause

