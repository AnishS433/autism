@echo off
echo ===================================================
echo         Autism Prediction - Shutdown Script       
echo ===================================================
echo.
echo Stopping the Autism Prediction Server...
echo.

FOR /F "tokens=5" %%T IN ('netstat -aon ^| find ":5001" ^| find "LISTENING"') DO (
    echo Found server process with PID: %%T
    taskkill /F /PID %%T
)

echo.
echo Server stopped successfully!
pause
