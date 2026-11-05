@echo off
echo Starting COSIN — Scientific Drug Research and Evidence Analysis Platform...
.\.venv312\Scripts\streamlit.exe run cosin_app.py --server.fileWatcherType=none --server.port 8501
pause