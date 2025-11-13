# STATISTIKA - Data Detective

This package contains a small Flask app created as "Week 1: Foundation" deliverable.

## Files
- `app.py` : single-file Flask application (input data up to 10 entries, stats, charts, mini-games)
- `schema.json` : JSON Schema for dataset + example dataset
- `ui_mockup.png` : visual mockup (pastel theme)
- `README.md` : this file

## Setup (quick)
1. Create virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate:
   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
3. Install:
   ```bash
   pip install Flask Pillow
   ```
4. Run:
   ```bash
   python app.py
   ```
5. Open browser: http://127.0.0.1:5000

## Notes
- The app stores the dataset in server-side session (non-persistent). Use `/export_schema` to see schema + example export.
- To persist data across restarts, replace session storage with a JSON file or SQLite (next steps).
- The UI uses Chart.js (CDN) for charts.

## Author
Created by Data Detective generator (assistant).
