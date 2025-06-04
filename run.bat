@echo off
set FLASK_APP=wsgi.py
set FLASK_ENV=development
set FLASK_DEBUG=1

set MAX_RETRIES=5
set RETRY_DELAY=5
set RETRY_COUNT=1

:start
echo Starting Flask app (attempt %RETRY_COUNT% of %MAX_RETRIES%)...
flask run --host=0.0.0.0 --port=5000

if %ERRORLEVEL% EQU 0 goto end

set /a RETRY_COUNT+=1
if %RETRY_COUNT% GTR %MAX_RETRIES% goto end

echo Flask app crashed. Restarting in %RETRY_DELAY% seconds...
timeout /t %RETRY_DELAY% /nobreak > nul
goto start

:end
echo Flask server stopped.