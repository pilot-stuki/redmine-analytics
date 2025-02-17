import streamlit as st
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

# Import your app
from src.frontend.app import DashboardApp

if __name__ == "__main__":
    # Initialize and run the app
    app = DashboardApp()
    app.run()