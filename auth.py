"""
auth.py
Authentication module for Fake Website Detection System
Provides login, registration, and session management functions
"""

import sqlite3
import bcrypt
import re
import streamlit as st
import os

# Database setup
DB_PATH = "users.db"

def init_db():
    """Initialize the SQLite database for users"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def register_user(email, password):
    """
    Register a new user
    Returns: (success: bool, message: str)
    """
    if not validate_email(email):
        return False, "Invalid email format"

    if len(password) < 6:
        return False, "Password must be at least 6 characters long"

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Check if user already exists
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return False, "Email already registered"

        # Hash password and insert user
        password_hash = hash_password(password)
        c.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)",
                 (email, password_hash))
        conn.commit()
        conn.close()

        return True, "Registration successful!"

    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"

def authenticate_user(email, password):
    """
    Authenticate a user
    Returns: (success: bool, message: str)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        result = c.fetchone()
        conn.close()

        if not result:
            return False, "User not found"

        stored_hash = result[0]
        if verify_password(password, stored_hash):
            return True, "Login successful!"
        else:
            return False, "Incorrect password"

    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"

def login_with_google():
    """
    Placeholder for Google OAuth login
    In a real implementation, this would handle OAuth flow
    For now, returns a mock successful login
    """
    # This is a simplified placeholder
    # Real Google OAuth would require:
    # 1. Google Cloud Console setup
    # 2. OAuth client credentials
    # 3. Proper redirect handling
    # 4. Token validation

    st.warning("Google OAuth not fully implemented yet. This is a placeholder.")
    return False, "Google login not available"

def logout():
    """Clear session state to logout user"""
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
    if 'user_email' in st.session_state:
        del st.session_state['user_email']

def show_login_register_ui():
    """
    Display the login/registration UI
    Returns True if user successfully logs in
    """
    LOGIN_CSS = """
    <style>
    /* Main Background */
    .stApp {
        background-color: #EEE4DA;
    }

    /* Login/Register Container */
    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #29281E !important;
        border-radius: 12px !important;
        padding: 30px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
        border: none !important;
    }

    /* Labels (Email & Password text) */
    [data-testid="stForm"] [data-testid="stWidgetLabel"] p {
        color: #EEE4DA !important;
        font-size: 1rem;
        font-weight: 500;
    }

    /* Input Fields */
    [data-baseweb="input"] {
        background-color: #EEE4DA !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.2rem 0.5rem !important;
    }
    [data-baseweb="input"] input {
        color: #29281E !important;
        font-weight: bold;
    }
    [data-baseweb="input"] input::placeholder {
        color: #29281E !important;
        opacity: 0.6;
    }

    /* Buttons (Sign In / Sign Up) */
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {
        background-color: #857861 !important;
        color: #29281E !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold;
        transition: 0.3s;
        width: 100%;
    }
    [data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover {
        background-color: #6C5F4D !important;
        color: #EEE4DA !important;
    }
    
    /* Radio Labels for Register/Login Tab Text */
    [data-testid="stRadio"] * {
        color: #4D0E13 !important;
        font-weight: 600;
    }
    </style>
    """
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #4D0E13;">Welcome to PhishGuard</h1>
        <h4 style="color: #4D0E13; font-weight: normal;">Please login or register to access the Fake Website Detection System</h4>
    </div>
    """, unsafe_allow_html=True)

    # Initialize database
    init_db()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Mode selection
        mode = st.radio("Choose action:", ["Login", "Register"], horizontal=True, label_visibility="collapsed")
        
        with st.form(key=f"{mode.lower()}_form"):
            email = st.text_input("Email", key="email_input")
            password = st.text_input("Password", type="password", key="password_input")

            submitted = st.form_submit_button(f"{mode}")

            if submitted:
                if mode == "Register":
                    success, message = register_user(email, password)
                    if success:
                        st.success(message)
                        st.info("You can now login with your credentials.")
                    else:
                        st.error(message)
                else:  # Login
                    success, message = authenticate_user(email, password)
                    if success:
                        st.session_state['logged_in'] = True
                        st.session_state['user_email'] = email
                        st.success(message)
                        st.rerun()  # Refresh to show main app
                    else:
                        st.error(message)

        # Google login button (placeholder)
        st.markdown("---")
        if st.button("🔵 Sign in with Google", use_container_width=True):
            success, message = login_with_google()
            if success:
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = "google_user@example.com"  # Mock email
                st.success("Logged in with Google!")
                st.rerun()
            else:
                st.error(message)

        # Link to switch modes
        if mode == "Login":
            st.markdown('<p style="text-align: center; color: #4D0E13;">New user? Select "Register" above</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="text-align: center; color: #4D0E13;">Already have an account? Select "Login" above</p>', unsafe_allow_html=True)

def is_logged_in():
    """Check if user is currently logged in"""
    return st.session_state.get('logged_in', False)

def get_current_user():
    """Get the current logged-in user's email"""
    return st.session_state.get('user_email', None)

def require_login():
    """
    Main function to handle authentication flow
    Call this at the start of your main app
    Returns True if user is logged in and can proceed
    """
    if is_logged_in():
        # Show logout button in sidebar
        with st.sidebar:
            st.markdown("---")
            user_email = get_current_user()
            st.markdown(f"**Logged in as:** {user_email}")
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()
        return True
    else:
        show_login_register_ui()
        return False