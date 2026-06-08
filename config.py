import os

# 优先使用 Streamlit Secrets（云端部署），fallback 到 .env（本地开发）
try:
    import streamlit as st
    LLM_API_KEY = st.secrets.get("LLM_API_KEY", os.getenv("LLM_API_KEY", ""))
    LLM_BASE_URL = st.secrets.get("LLM_BASE_URL", os.getenv("LLM_BASE_URL", "https://api.deepseek.com"))
    LLM_MODEL = st.secrets.get("LLM_MODEL", os.getenv("LLM_MODEL", "deepseek-chat"))
except (ImportError, FileNotFoundError):
    from dotenv import load_dotenv
    load_dotenv()
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
