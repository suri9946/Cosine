# Launch COSIN Scientific Drug Research Platform
Write-Host "Starting COSIN — Scientific Drug Research and Evidence Analysis Platform..." -ForegroundColor Cyan
& ".\.venv312\Scripts\streamlit.exe" run cosin_app.py --server.fileWatcherType=none --server.port 8501
