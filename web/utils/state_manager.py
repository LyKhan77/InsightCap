"""Session state manager for UI state."""
from __future__ import annotations

from typing import Optional
import streamlit as st


class StateManager:
    """Manages session state."""

    @staticmethod
    def init_session_state():
        """Initialize session state variables."""
        if "app_mode" not in st.session_state:
            st.session_state.app_mode = None
        if "current_analysis" not in st.session_state:
            st.session_state.current_analysis = None
        if "current_rtsp_session" not in st.session_state:
            st.session_state.current_rtsp_session = None
        if "is_analyzing" not in st.session_state:
            st.session_state.is_analyzing = False
        if "api_connected" not in st.session_state:
            st.session_state.api_connected = False
        if "api_error" not in st.session_state:
            st.session_state.api_error = None

    @staticmethod
    def set_mode(mode: Optional[str]):
        st.session_state.app_mode = mode

    @staticmethod
    def get_mode() -> Optional[str]:
        return st.session_state.get("app_mode")

    @staticmethod
    def set_analyzing(value: bool):
        st.session_state.is_analyzing = value

    @staticmethod
    def is_analyzing() -> bool:
        return st.session_state.get("is_analyzing", False)

    @staticmethod
    def set_api_status(connected: bool, error: Optional[str] = None):
        st.session_state.api_connected = connected
        st.session_state.api_error = error

    @staticmethod
    def set_rtsp_session(session: Optional[dict]):
        st.session_state.current_rtsp_session = session

    @staticmethod
    def get_rtsp_session() -> Optional[dict]:
        return st.session_state.get("current_rtsp_session")
