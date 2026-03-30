"""Sidebar component for upload and configuration - Industrial Style."""
from __future__ import annotations

import streamlit as st
from typing import Optional, Tuple


def _render_system_status():
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


def render_video_sidebar(api_client) -> Tuple[Optional[bytes], dict]:
    """Render sidebar with upload-video configuration."""

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

    _render_system_status()

    config = {
        "model": model
    }

    return uploaded_file, config


def render_rtsp_sidebar(api_client) -> dict:
    """Render sidebar with RTSP monitoring configuration."""
    st.sidebar.markdown("## RTSP_SOURCE")

    rtsp_url = st.sidebar.text_input(
        "RTSP_URL",
        value=st.session_state.get("rtsp_url_input", ""),
        placeholder="rtsp://user:password@camera-host/stream",
        help="Full RTSP URL for the camera stream",
    )
    st.session_state.rtsp_url_input = rtsp_url

    session_name = st.sidebar.text_input(
        "SESSION_NAME",
        value=st.session_state.get("rtsp_session_name_input", ""),
        placeholder="front-gate",
        help="Optional label shown in the live monitoring UI",
    )
    st.session_state.rtsp_session_name_input = session_name

    st.sidebar.markdown("---")

    st.sidebar.markdown("## CONFIGURATION")

    model = st.sidebar.selectbox(
        "MODEL",
        options=["qwen3.5:0.8b"],
        index=0,
        help="Ollama model for captioning",
        key="rtsp_model_select",
    )

    sample_every_seconds = st.sidebar.number_input(
        "SAMPLE_SECONDS",
        min_value=0.2,
        max_value=60.0,
        value=float(st.session_state.get("rtsp_sample_seconds", 1.0)),
        step=0.2,
        help="Minimum interval between caption requests for the live camera stream",
    )
    st.session_state.rtsp_sample_seconds = sample_every_seconds

    st.sidebar.markdown("---")

    _render_system_status()

    return {
        "rtsp_url": rtsp_url.strip(),
        "session_name": session_name.strip(),
        "model": model,
        "sample_every_seconds": float(sample_every_seconds),
    }


def render_sidebar(api_client) -> Tuple[Optional[bytes], dict]:
    """Backward-compatible alias for the upload-video sidebar."""
    return render_video_sidebar(api_client)


def get_api_status_display():
    """Get API status from session state."""
    connected = st.session_state.get("api_connected", False)
    error = st.session_state.get("api_error")
    return connected, error
