"""Session state manager for UI state."""
from __future__ import annotations

from typing import Optional
import streamlit as st


class StateManager:
    """Manages session state."""

    @staticmethod
    def init_session_state():
        """Initialize session state variables."""
        if "current_analysis" not in st.session_state:
            st.session_state.current_analysis = None
        if "is_analyzing" not in st.session_state:
            st.session_state.is_analyzing = False
        if "api_connected" not in st.session_state:
            st.session_state.api_connected = False
        if "api_error" not in st.session_state:
            st.session_state.api_error = None

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
