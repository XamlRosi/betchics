@echo off
echo Installing Python dependencies for bank-ethics project...
echo.

pip install pandas
pip install numpy
pip install scikit-learn
pip install joblib
pip install fastapi
pip install uvicorn
pip install python-dotenv
pip install openai
pip install sqlalchemy

echo.
echo ✅ Installation complete!
echo.
pause
