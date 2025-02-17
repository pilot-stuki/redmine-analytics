import streamlit as st
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

# Import your app
from src.frontend.app import DashboardApp

if __name__ == "__main__":
    st.set_page_config(
        page_title="Redmine Labor Cost Analytics",
        page_icon="💰",
        layout="wide"
    )
    
    app = DashboardApp()
    app.run()