import streamlit as st
from db import db

def login_form():
    with st.form("Login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if db.authenticate_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.session_state['role'] = db.get_user_role(username)
                st.rerun()
            else:
                st.error("Invalid credentials")

def logout():
    st.session_state.pop('authenticated', None)
    st.session_state.pop('username', None)
    st.session_state.pop('role', None)

def auth_guard():
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        st.title("Stock Analyst Portal")
        login_form()
        st.stop()