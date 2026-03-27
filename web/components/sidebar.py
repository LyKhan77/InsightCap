"""Sidebar component for upload and configuration - Industrial Style."""
from __future__ import annotations

import streamlit as st
from typing import Optional, Tuple


def render_sidebar(api_client) -> Tuple[Optional[bytes], dict]:
    """Render sidebar with upload and configuration."""
    
    st.sidebar.markdown("## UPLOAD_VIDEO")
    
    uploaded_file = st.sidebar.file_uploader(
        "Drop file here or click to browse",
        type=["mp4", "avi", "mov", "mkv", "webm", "mpeg"],
        help="Supported: MP4, AVI, MOV, MKV, WEBM, MPEG"
    )
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("## CONFIGURATION")
    
    
    model = st.sidebar.selectbox(
        "MODEL",
        options=["qwen3.5:0.8b"],
        index=0,
        help="Ollama model for captioning"
    )
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("## SYSTEM_STATUS")
    connected, error = get_api_status_display()
    
    if connected:
        st.sidebar.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #00ff88;">
            [ ONLINE ] API_CONNECTED<br>
            <span style="color: #606066;">Ready for analysis</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #ff3366;">
            [ OFFLINE ] API_DISCONNECTED<br>
            <span style="color: #606066;">{error if error else 'Connection failed'}</span>
        </div>
        """, unsafe_allow_html=True)
    
    if st.sidebar.button("[ REFRESH ]", use_container_width=True):
        st.rerun()
    
    config = {
        "model": model
    }
    
    return uploaded_file, config


def get_api_status_display():
    """Get API status from session state."""
    connected = st.session_state.get("api_connected", False)
    error = st.session_state.get("api_error")
    return connected, error
