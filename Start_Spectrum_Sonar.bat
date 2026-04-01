@echo off
echo ===================================================
echo        Spectrum Sonar - Initialization Script       
echo ===================================================
echo.
echo Starting the AI Backend Server...
start "" /B python app.py

echo Waiting for the server to load...
timeout /t 4 /nobreak > NUL

echo Opening Spectrum Sonar in your default web browser...
start http://127.0.0.1:5001/
echo.
echo Please leave the black terminal window open while using the website!
echo You can close this window now.
pause
