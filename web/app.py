"""InsightCap Web App - Real-Time Dual Panel Interface."""
from __future__ import annotations

import os
import sys
import tempfile
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import APIClient, InsightCapAPIError
from utils.state_manager import StateManager
from components import (
    render_video_sidebar,
    render_rtsp_sidebar,
    render_stream_empty,
    render_stream_idle,
    render_stream_initializing,
    render_stream_analyzing_start,
    render_stream_analyzing,
    render_stream_complete,
    render_live_captions_streaming,
    render_live_captions_complete,
    render_live_captions_empty,
    render_rtsp_stream_empty,
    render_rtsp_live_stream,
    render_rtsp_live_captions,
)

st.set_page_config(
    page_title="INSIGHTCAP // VIDEO_CAPTIONING",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #08080a;
        --bg-secondary: #0f0f12;
        --bg-tertiary: #16161a;
        --border-subtle: #1e1e24;
        --border-strong: #2a2a32;
        --text-primary: #f0f0f5;
        --text-secondary: #909099;
        --text-muted: #606066;
        --accent-cyan: #00f0ff;
        --accent-amber: #ffaa00;
        --accent-red: #ff3366;
        --accent-green: #00ff88;
    }

    * { font-family: 'JetBrains Mono', monospace; }

    .stApp {
        background: var(--bg-primary);
        background-image:
            linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        text-transform: uppercase;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-subtle);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 0.75rem !important;
        letter-spacing: 0.1em;
        color: var(--text-secondary) !important;
        border-bottom: 1px solid var(--border-subtle);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }

    /* Sidebar input labels - prevent wrapping */
    [data-testid="stSidebar"] [data-testid="stNumberInput"] label p,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label p {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.65rem !important;
        letter-spacing: 0.06em;
    }

    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {
        font-size: 0.72rem !important;
        padding: 0.5rem 0.75rem !important;
        letter-spacing: 0.06em;
        white-space: nowrap;
    }

    /* Primary Button */
    .stButton > button {
        background: transparent !important;
        color: var(--accent-cyan) !important;
        border: 1px solid var(--accent-cyan) !important;
        border-radius: 0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 0.75rem 1.5rem !important;
        position: relative;
        overflow: hidden;
        transition: all 0.2s ease;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }

    .stButton > button:hover::before { left: 100%; }
    .stButton > button:hover {
        background: rgba(0, 240, 255, 0.1) !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
    }

    .stButton > button:disabled {
        border-color: var(--text-muted) !important;
        color: var(--text-muted) !important;
        cursor: not-allowed;
    }
    .stButton > button:disabled::before { display: none; }

    /* Secondary Button */
    button[kind="secondary"] {
        background: var(--bg-tertiary) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    button[kind="secondary"]:hover {
        border-color: var(--accent-amber) !important;
        color: var(--accent-amber) !important;
    }

    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: var(--bg-tertiary);
        border: 2px dashed var(--border-strong);
        border-radius: 0 !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent-cyan);
        background: rgba(0, 240, 255, 0.05);
    }

    /* Inputs */
    .stNumberInput input,
    .stSelectbox select,
    .stTextInput input {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 0 !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stNumberInput input:focus,
    .stSelectbox select:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 1px var(--accent-cyan);
    }

    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--accent-cyan) 0%, var(--accent-amber) 100%);
        border-radius: 0 !important;
    }

    /* Live panel containers — override st.container(border=True) defaults */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--accent-cyan) !important;
        box-shadow: 0 0 24px rgba(0, 240, 255, 0.12) !important;
        background: var(--bg-tertiary) !important;
        border-radius: 0 !important;
    }

    .panel-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        color: var(--accent-cyan);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(0, 240, 255, 0.2);
    }

    /* Blinking cursor during streaming */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    .cursor-blink {
        animation: blink 1s infinite;
        color: var(--accent-cyan);
    }

    /* Download button */
    .stDownloadButton > button {
        background: var(--bg-tertiary) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        white-space: nowrap;
        letter-spacing: 0.04em;
    }
    .stDownloadButton > button:hover {
        border-color: var(--accent-cyan) !important;
        color: var(--accent-cyan) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0 !important;
        color: var(--text-muted) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .streamlit-expanderHeader:hover {
        color: var(--text-secondary) !important;
        border-color: var(--border-strong) !important;
    }

    /* Alerts */
    .stAlert { border-radius: 0 !important; border-left: 3px solid; }
</style>
""", unsafe_allow_html=True)


def check_api_connection(api_client: APIClient):
    try:
        health = api_client.health_check()
        StateManager.set_api_status(True, None)
        return health
    except InsightCapAPIError as e:
        StateManager.set_api_status(False, str(e))
        return None


def render_metadata_compact(metadata: dict):
    """Render analysis metadata — small, de-emphasized, below panels."""
    st.markdown("""
    <div style="border-top: 1px solid #1e1e24; margin: 1.25rem 0 0.75rem; padding-top: 0.75rem;
                font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#3a3a42;
                letter-spacing:0.08em; text-transform:uppercase;">
        ANALYSIS_METADATA
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("FRAMES", metadata.get("frame_count", 0))
    with col2:
        duration = metadata.get("duration_seconds", 0)
        st.metric("DURATION", f"{duration:.1f}s")
    with col3:
        device = metadata.get("device_used", "?")
        st.metric("DEVICE", device.upper())
    with col4:
        model = metadata.get("model_id", "?")
        st.metric("MODEL", model)

    # Override metric styling to be muted
    st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background: transparent !important;
        border: 1px solid #1e1e24;
        padding: 0.5rem 0.75rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 0.9rem !important;
        color: #606066 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.6rem !important;
        color: #3a3a42 !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_rtsp_metadata(metadata: dict):
    """Render RTSP session metadata below the panels."""
    st.markdown("""
    <div style="border-top: 1px solid #1e1e24; margin: 1.25rem 0 0.75rem; padding-top: 0.75rem;
                font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#3a3a42;
                letter-spacing:0.08em; text-transform:uppercase;">
        RTSP_SESSION_METADATA
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("STATUS", str(metadata.get("status", "?")).upper())
    with col2:
        st.metric("CAPTIONS", metadata.get("captions_emitted", 0))
    with col3:
        lag_ms = metadata.get("lag_ms")
        st.metric("LAG", f"{lag_ms:.0f}ms" if isinstance(lag_ms, (int, float)) else "--")
    with col4:
        st.metric("MODEL", metadata.get("model_id", "?"))

    st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background: transparent !important;
        border: 1px solid #1e1e24;
        padding: 0.5rem 0.75rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 0.9rem !important;
        color: #606066 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.6rem !important;
        color: #3a3a42 !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_app_header(mode: str):
    """Render the shared application header with the active mode."""
    mode_label = "VIDEO_MODE" if mode == "video" else "RTSP_MODE"
    system_label = "VIDEO_CAPTIONING_SYSTEM" if mode == "video" else "RTSP_MONITORING_SYSTEM"
    st.markdown(f"""
    <div style="padding: 1rem 0 1.25rem; border-bottom: 1px solid #1e1e24; margin-bottom: 1.5rem;">
        <div style="display:flex; align-items:baseline; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
            <div style="display:flex; align-items:baseline; gap:0.5rem;">
                <span style="font-family:'Space Grotesk',sans-serif; font-size:1.6rem; font-weight:700;
                             color:#00f0ff; letter-spacing:-0.02em;">INSIGHTCAP</span>
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#606066;
                             text-transform:uppercase; letter-spacing:0.15em;">// {system_label}</span>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#00f0ff;
                        border:1px solid rgba(0, 240, 255, 0.35); padding:0.35rem 0.55rem;
                        letter-spacing:0.12em; text-transform:uppercase;">
                {mode_label}
            </div>
        </div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#3a3a42;
                    margin-top:0.2rem;">
            v2.0.0 // QWEN3.5_0.8B // VLLM_BACKEND
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_mode_selector():
    """Render the landing page for choosing Video or RTSP mode."""
    st.markdown("""
    <div style="padding: 2rem 0 1.25rem; border-bottom: 1px solid #1e1e24; margin-bottom: 2rem;">
        <div style="display:flex; align-items:baseline; gap:0.5rem;">
            <span style="font-family:'Space Grotesk',sans-serif; font-size:2rem; font-weight:700;
                         color:#00f0ff; letter-spacing:-0.02em;">INSIGHTCAP</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#606066;
                         text-transform:uppercase; letter-spacing:0.15em;">// SELECT_MODE_PAGE</span>
        </div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#909099;
                    margin-top:0.9rem; max-width:50rem; line-height:1.7;">
            Choose the monitoring mode first, then continue into the main dual-panel interface.
            Video mode keeps the existing upload-analysis flow. RTSP mode opens live camera monitoring.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        <div style="border:1px solid #00f0ff; background:#0f0f12; padding:1.2rem 1.25rem; min-height:13rem;">
            <div style="font-family:'Space Grotesk',sans-serif; font-size:1.25rem; font-weight:700; color:#00f0ff;">
                VIDEO
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#909099;
                        margin-top:0.85rem; line-height:1.8; text-transform:uppercase; letter-spacing:0.08em;">
                Upload a local clip, run batch analysis, then review frame captions and the final summary.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("[ VIDEO_MODE ]", use_container_width=True, type="primary", key="mode-video"):
            StateManager.set_mode("video")
            st.rerun()

    with col2:
        st.markdown("""
        <div style="border:1px solid #ffaa00; background:#0f0f12; padding:1.2rem 1.25rem; min-height:13rem;">
            <div style="font-family:'Space Grotesk',sans-serif; font-size:1.25rem; font-weight:700; color:#ffaa00;">
                RTSP
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#909099;
                        margin-top:0.85rem; line-height:1.8; text-transform:uppercase; letter-spacing:0.08em;">
                Monitor a live camera source through RTSP with the same two-panel layout, but fed by a live preview bridge.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("[ RTSP_MODE ]", use_container_width=True, type="secondary", key="mode-rtsp"):
            StateManager.set_mode("rtsp")
            st.rerun()


def render_mode_controls():
    """Render shared sidebar controls for returning to mode selection."""
    st.sidebar.markdown("---")
    if st.sidebar.button("[ SELECT_MODE_PAGE ]", use_container_width=True):
        StateManager.set_mode(None)
        st.rerun()


def sync_rtsp_session(api_client: APIClient):
    """Refresh the current RTSP session snapshot from the API."""
    session = StateManager.get_rtsp_session()
    if not session:
        return None

    session_id = session.get("session_id")
    if not session_id:
        StateManager.set_rtsp_session(None)
        return None

    try:
        latest = api_client.get_rtsp_session(session_id)
        StateManager.set_rtsp_session(latest)
        return latest
    except InsightCapAPIError as exc:
        if "404" in str(exc):
            StateManager.set_rtsp_session(None)
            return None
        st.error(f"RTSP_STATUS_FAILED: {exc}")
        return session


def render_video_mode(api_client: APIClient):
    """Render the existing upload-video experience."""
    uploaded_file, config = render_video_sidebar(api_client)
    render_mode_controls()
    render_app_header("video")

    analyze_clicked = False
    if uploaded_file is not None:
        analyze_clicked = st.button(
            "[ INITIATE_ANALYSIS ]",
            use_container_width=True,
            disabled=not st.session_state.api_connected or StateManager.is_analyzing(),
            type="primary"
        )
    else:
        st.button(
            "[ INITIATE_ANALYSIS ]",
            use_container_width=True,
            disabled=True,
            type="primary"
        )

    st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)

    file_bytes = uploaded_file.getvalue() if uploaded_file else None
    filename = uploaded_file.name if uploaded_file else None

    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        with st.container(border=True):
            if file_bytes:
                st.markdown('<div class="panel-header">◈ LIVE_STREAM</div>',
                            unsafe_allow_html=True)
                st.video(file_bytes)
            stream_placeholder = st.empty()

    with col_right:
        with st.container(border=True):
            captions_placeholder = st.empty()

    if analyze_clicked and file_bytes is not None:
        StateManager.set_analyzing(True)

        file_ext = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(file_bytes)
            temp_path = tmp.name

        frame_captions = []
        final_caption = None
        metadata = None

        with stream_placeholder.container():
            render_stream_initializing()

        try:
            for event in api_client.analyze_stream(
                video_path=temp_path,
                model=config["model"]
            ):
                if "total_frames" in event:
                    render_stream_analyzing_start()
                    with stream_placeholder.container():
                        render_stream_analyzing()

                elif "index" in event and "caption" in event:
                    frame_captions.append(event)
                    with captions_placeholder.container():
                        render_live_captions_streaming(frame_captions)

                elif "caption" in event and len(event) == 1:
                    final_caption = event["caption"]

                elif "frame_count" in event:
                    metadata = event

        except InsightCapAPIError as e:
            st.error(f"ANALYSIS_FAILED: {e}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            StateManager.set_analyzing(False)

        if final_caption and metadata:
            st.session_state.current_analysis = {
                "final_caption": final_caption,
                "frame_captions": frame_captions,
                "metadata": metadata,
                "filename": filename,
                "params": config
            }
        st.rerun()

    else:
        current = st.session_state.get("current_analysis")

        with stream_placeholder.container():
            if file_bytes:
                if current:
                    total = current.get("metadata", {}).get("frame_count", 0)
                    render_stream_complete(total, total)
                else:
                    render_stream_idle(filename)
            else:
                render_stream_empty()

        with captions_placeholder.container():
            if current:
                render_live_captions_complete(
                    frame_captions=current.get("frame_captions", []),
                    final_caption=current.get("final_caption"),
                    metadata=current.get("metadata")
                )
            else:
                render_live_captions_empty()

    current = st.session_state.get("current_analysis")
    if current and current.get("metadata"):
        render_metadata_compact(current["metadata"])


def render_rtsp_mode(api_client: APIClient):
    """Render the RTSP live monitoring experience."""
    current_session = sync_rtsp_session(api_client)
    config = render_rtsp_sidebar(api_client)
    render_mode_controls()
    render_app_header("rtsp")

    button_label = "[ STOP_MONITORING ]" if current_session else "[ START_MONITORING ]"
    button_disabled = not st.session_state.api_connected or (
        not current_session and not config["rtsp_url"]
    )

    action_clicked = st.button(
        button_label,
        use_container_width=True,
        disabled=button_disabled,
        type="primary" if not current_session else "secondary",
    )

    st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)

    if action_clicked:
        if current_session:
            try:
                api_client.delete_rtsp_session(current_session["session_id"])
                StateManager.set_rtsp_session(None)
                st.rerun()
            except InsightCapAPIError as exc:
                st.error(f"RTSP_STOP_FAILED: {exc}")
        else:
            try:
                created = api_client.create_rtsp_session(
                    rtsp_url=config["rtsp_url"],
                    model=config["model"],
                    sample_every_seconds=config["sample_every_seconds"],
                    session_name=config["session_name"] or None,
                )
                StateManager.set_rtsp_session(created)
                st.rerun()
            except InsightCapAPIError as exc:
                st.error(f"RTSP_START_FAILED: {exc}")

    current_session = StateManager.get_rtsp_session()

    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        with st.container(border=True):
            if current_session:
                render_rtsp_live_stream(
                    preview_url=api_client.rtsp_preview_stream_url(current_session["session_id"]),
                    session_name=current_session.get("session_name", "rtsp-camera"),
                    source=current_session.get("source", "RTSP_SOURCE"),
                )
            else:
                render_rtsp_stream_empty()

    with col_right:
        with st.container(border=True):
            if current_session:
                render_rtsp_live_captions(
                    api_client.rtsp_events_ws_url(current_session["session_id"])
                )
            else:
                render_live_captions_empty()

    if current_session:
        render_rtsp_metadata(current_session)


def main():
    StateManager.init_session_state()
    api_client = APIClient()
    check_api_connection(api_client)
    mode = StateManager.get_mode()
    if not mode:
        render_mode_selector()
        return

    if mode == "rtsp":
        render_rtsp_mode(api_client)
        return

    render_video_mode(api_client)


if __name__ == "__main__":
    main()
