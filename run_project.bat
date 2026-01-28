@echo off
echo ===========================================
echo      AI Study Buddy - Automatic Setup
echo ===========================================

echo [1/2] Checking and installing required modules...
:: This uses the pip inside your virtual environment
call .venv\Scripts\activate
python -m pip install -r requirements.txt

echo.
echo [2/2] Launching the App...
echo.
:: This runs streamlit through the virtual environment
python -m streamlit run app1.py

pause