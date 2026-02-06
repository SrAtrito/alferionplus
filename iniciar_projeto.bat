@echo off
cd /d "D:\Python Salvos\alferion-app - multiplos e DCs"

call .venv\Scripts\activate

echo Iniciando o aplicativo Streamlit...

streamlit run app_alferionplus.py

pause
