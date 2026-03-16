@echo off
echo ===================================================
echo        Autism Prediction - Initialization Script       
echo ===================================================
echo.
echo Starting the AI Backend Server in the background...
start "" pythonw app.py

echo Waiting for the server to load...
timeout /t 4 /nobreak > NUL

echo Opening Autism Prediction in your default web browser...
start http://127.0.0.1:5001/
echo.
echo The server is now running silently in the background!
echo You can safely close this terminal window without interrupting the website.
echo To stop the server later, simply run Stop_Spectrum_Sonar.bat
pause
