import streamlit as st
import os
from pathlib import Path

# Add the current directory to Python path
import sys
sys.path.insert(0, os.path.dirname(__file__))

try:
    from src.frontend.app import DashboardApp
    
    if __name__ == "__main__":
        st.set_page_config(
            page_title="Redmine Labor Cost Analytics",
            page_icon="💰",
            layout="wide"
        )
        
        app = DashboardApp()
        app.run()
        
except Exception as e:
    st.error(f"Error loading the application: {str(e)}")
    st.write("Detailed error information:")
    st.code(str(e))
    
    # Debug information
    st.write("Current directory:", os.getcwd())
    st.write("Python path:", sys.path)
    st.write("Directory contents:", os.listdir())