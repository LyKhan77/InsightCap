"""LIVE_STREAM panel component.

Architecture note:
  st.video() is rendered OUTSIDE stream_placeholder in app.py so it stays
  stable (not re-rendered on every frame event). These functions only render
  the dynamic content that lives inside stream_placeholder.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


# ── JS helpers ────────────────────────────────────────────────────────────────

def _js_autoplay_and_lock() -> str:
    """JS: start video from beginning and disable controls."""
    return """<script>
    (function() {
        var apply = function() {
            var v = window.parent.document.querySelector('video');
            if (v) {
                v.controls = false;
                v.currentTime = 0;
                v.play();
            }
        };
        setTimeout(apply, 100);
    })();
    </script>"""


def _js_restore_controls() -> str:
    """JS: re-enable video controls after analysis completes."""
    return """<script>
    (function() {
        var apply = function() {
            var v = window.parent.document.querySelector('video');
            if (v) {
                v.controls = true;
            }
        };
        setTimeout(apply, 60);
    })();
    </script>"""


def _inject_js(js_html: str):
    """Render invisible iframe that runs the JS snippet."""
    components.html(js_html, height=0, scrolling=False)


# ── Dynamic content functions (rendered inside stream_placeholder) ────────────

def render_stream_initializing():
    """Shown while backend reads video metadata before analysis begins."""
    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem;
                color:#606066; margin-top:0.5rem; letter-spacing:0.12em;">
        ◈ INITIALIZING...
    </div>
    """, unsafe_allow_html=True)


def render_stream_empty():
    """Full empty state — no video uploaded. Renders header + placeholder."""
    st.markdown('<div class="panel-header">◈ LIVE_STREAM</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background:#08080a; border:2px dashed #2a2a32;
        padding:5rem 2rem; text-align:center;
        font-family:'JetBrains Mono',monospace;
    ">
        <div style="font-size:2rem; color:#2a2a32; margin-bottom:1rem;">◈</div>
        <div style="font-size:0.78rem; color:#606066; text-transform:uppercase;
                    letter-spacing:0.1em;">
            UPLOAD_VIDEO_TO_BEGIN
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stream_idle(filename: str):
    """Idle label below the stable video player."""
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem;
                color:#606066; margin-top:0.4rem; letter-spacing:0.06em;">
        ■ {filename} &nbsp;·&nbsp; READY
    </div>
    """, unsafe_allow_html=True)
    _inject_js(_js_restore_controls())


def render_stream_analyzing_start():
    """Called once at analysis start: autoplay video + lock controls."""
    _inject_js(_js_autoplay_and_lock())


def render_stream_analyzing():
    """Simple status shown during analysis — no frame counter."""
    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem;
                color:#ffaa00; margin-top:0.5rem; letter-spacing:0.1em;">
        ● ANALYZING...
    </div>
    """, unsafe_allow_html=True)


def render_stream_complete(frame_count: int, total: int):
    """Post-analysis: complete status + restore video controls."""
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace; display:flex; align-items:center;
                justify-content:space-between; padding:0.6rem 0.75rem; margin:0.5rem 0;
                background:#0a0a0d; border:1px solid #1e1e24;">
        <div>
            <div style="font-size:0.55rem; color:#606066; letter-spacing:0.15em;
                        margin-bottom:0.2rem;">FRAME</div>
            <div style="font-size:1.4rem; color:#606066; font-weight:600; line-height:1;">
                {frame_count:02d}
                <span style="color:#2a2a32; font-size:0.9rem;"> / </span>
                <span style="color:#606066; font-size:0.9rem;">{total:02d}</span>
            </div>
        </div>
        <div style="font-size:0.75rem; color:#00ff88; letter-spacing:0.08em;">
            ✓ COMPLETE
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(1.0)

    # Restore controls so user can play the video normally after analysis
    _inject_js(_js_restore_controls())
