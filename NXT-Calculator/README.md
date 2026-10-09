# NXT CALCULATOR — Engineering Calculator

A Flask + HTML/CSS/JavaScript engineering calculator for diploma/college projects.

## Features
- Basic arithmetic calculator
- Scientific calculator
- Electrical engineering
- Electronics
- Mechanical engineering
- Civil engineering
- Computer/IT number conversion
- Unit conversion
- Formula library
- Calculation history
- Dark/light theme
- Responsive layout
- Python/Flask performs the main calculations

## Run on Windows

1. Open terminal in this folder.
2. Create a virtual environment:
   `python -m venv .venv`
3. If PowerShell blocks activation, you can skip activation and use:
   `.venv\Scripts\python.exe -m pip install Flask`
4. Run:
   `.venv\Scripts\python.exe app.py`
5. Open:
   `http://127.0.0.1:5000`

## Important
The scientific expression endpoint uses a restricted AST evaluator rather than Python's unrestricted eval().
