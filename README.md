# Fantasy Football Draft Optimizer

Senior project for a fantasy football draft optimization system built with Python and Tkinter.

## Features
- Loads player data from a master CSV file
- Calculates Value Over Replacement (VOR)
- Displays ranked players in a GUI
- Supports drafting selected players
- Updates team rosters during the draft
- Tracks snake draft order
- Includes search and position filters
- Displays recent picks and a draft board
- Shows player recommendations during the draft

## Requirements
- Python
- pandas

## How to Run
1. Install Python
2. Install pandas
3. Open the project folder
4. Run `main.py`

## Project Structure
- `main.py` starts the application
- `logic/data_loader.py` loads the player data
- `logic/ranking.py` calculates VOR
- `ui/app_ui.py` runs the graphical interface
