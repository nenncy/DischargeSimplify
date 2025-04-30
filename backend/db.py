from sqlalchemy import create_engine
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

CONNECTION_URL = os.getenv("CONNECTION_URL")
@st.cache_resource
def get_engine():
    connection_url = (CONNECTION_URL)
    engine = create_engine(connection_url)
    return engine
