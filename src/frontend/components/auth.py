import streamlit as st
from typing import Optional
import hmac
import os
from dotenv import load_dotenv
import hashlib
import base64

load_dotenv()

class Authenticator:
    def __init__(self):
        """Initialize with proper error handling for environment variables"""
        # Initialize secret key with default fallback
        self.secret_key = os.getenv("SECRET_KEY")
        if not self.secret_key:
            st.error("SECRET_KEY not found in environment variables. Using default (unsafe).")
            self.secret_key = "default_secret_key"
        self.secret_key = self.secret_key.encode()

        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'username' not in st.session_state:
            st.session_state.username = ""
        if 'user_role' not in st.session_state:
            st.session_state.user_role = ""

        # Load superadmin credentials with validation
        self.superadmin = {
            "username": os.getenv("SUPERADMIN_USERNAME", "superadmin").strip(),
            "password": os.getenv("SUPERADMIN_PASSWORD", "changeme").strip(),
            "role": "superadmin"
        }
        
        # Regular users credentials with default values
        self.regular_credentials = {
            "admin": {
                "password": self._hash_password("admin123"),
                "role": "admin"
            },
            "manager": {
                "password": self._hash_password("manager123"),
                "role": "manager"
            }
        }

    def _hash_password(self, password: str) -> str:
        """Hash password with proper string handling"""
        if not isinstance(password, str):
            password = str(password)
        return hashlib.sha256(
            password.encode() + self.secret_key
        ).hexdigest()

    def check_password(self, username: str, password: str) -> bool:
        """Verify password with improved error handling"""
        if not username or not password:
            return False
            
        username = username.strip()
        password = password.strip()

        try:
            if username == self.superadmin["username"]:
                return hmac.compare_digest(
                    password.encode(),
                    self.superadmin["password"].encode()
                )
            
            if username in self.regular_credentials:
                hashed_input = self._hash_password(password)
                return hmac.compare_digest(
                    hashed_input.encode(),
                    self.regular_credentials[username]["password"].encode()
                )
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False
            
        return False

    def get_user_role(self, username: str) -> str:
        """Get user role"""
        if username == self.superadmin["username"]:
            return "superadmin"
        return self.regular_credentials.get(username, {}).get("role", "")

    def login(self) -> Optional[str]:
        """Handle login and return username if successful"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None

        if not st.session_state.authenticated:
            st.markdown("## Login")
            
            # Center the login form
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.button("Login", use_container_width=True):
                    if self.check_password(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_role = self.get_user_role(username)
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            return None

        return st.session_state.username

    def check_role_access(self, required_role: str) -> bool:
        """Check if current user has required role access"""
        role_hierarchy = {
            "superadmin": 3,
            "admin": 2,
            "manager": 1
        }
        
        user_role = st.session_state.get("user_role", "")
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level

    def logout(self):
        """Clear session state and log out user"""
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_role = None