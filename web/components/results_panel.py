"""LIVE_CAPTIONS panel component - scrollable chat-style."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Dict, Any, Optional

_CAPTION_FONTS = "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap"

_CAPTIONS_CSS = """
<style>
    @import url('{fonts}');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: transparent; overflow: hidden; }}
    @keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0}} }}
    @keyframes typing-bounce {{
        0%, 60%, 100% {{ transform: translateY(0); opacity: 0.3; }}
        30% {{ transform: translateY(-5px); opacity: 1; }}
    }}
    .cursor {{ animation: blink 1s infinite; color: #00f0ff; }}
    #scroll-box {{
        height: {height}px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        padding: 4px 0;
    }}
    #scroll-box::-webkit-scrollbar {{ width: 3px; }}
    #scroll-box::-webkit-scrollbar-track {{ background: transparent; }}
    #scroll-box::-webkit-scrollbar-thumb {{ background: #2a2a32; border-radius: 2px; }}
    .frame-row {{
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 0.35rem 0.5rem;
        border-left: 2px solid #2a2a32;
        margin: 0.2rem 0;
        font-family: 'JetBrains Mono', monospace;
        transition: border-color 0.2s;
    }}
    .frame-row.latest {{
        border-left-color: #00f0ff;
        background: rgba(0, 240, 255, 0.04);
    }}
    .frame-num {{
        color: #ffaa00;
        font-size: 0.62rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        flex-shrink: 0;
        padding-top: 1px;
    }}
    .frame-caption {{
        color: #606066;
        font-size: 0.8rem;
        line-height: 1.5;
    }}
    .frame-row.latest .frame-caption {{ color: #c0c0c8; }}
    .typing-indicator {{
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 0.5rem 0.75rem;
        margin: 0.3rem 0;
        border-left: 2px solid #1e1e24;
    }}
    .typing-indicator span {{
        display: inline-block;
        width: 5px;
        height: 5px;
        background: #00f0ff;
        border-radius: 50%;
        animation: typing-bounce 1.4s infinite;
    }}
    .typing-indicator span:nth-child(2) {{ animation-delay: 0.2s; }}
    .typing-indicator span:nth-child(3) {{ animation-delay: 0.4s; }}
    .typing-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.58rem;
        color: #3a3a42;
        letter-spacing: 0.08em;
        margin-left: 6px;
    }}
</style>
"""

_SCROLL_SCRIPT = """
<script>
    var box = document.getElementById('scroll-box');
    if (box) box.scrollTop = box.scrollHeight;
</script>
"""


def _build_captions_html(frame_captions: List[Dict[str, Any]], height: int, streaming: bool) -> str:
    rows = []
    for i, frame in enumerate(frame_captions):
        frame_num = frame.get("index", i) + 1
        caption = frame.get("caption", "")
        is_last = i == len(frame_captions) - 1
        css_class = "frame-row latest" if (is_last and streaming) else "frame-row"
        cursor = '<span class="cursor">▋</span>' if (is_last and streaming) else ""
        rows.append(
            f'<div class="{css_class}">'
            f'<span class="frame-num">F{frame_num:02d}</span>'
            f'<span class="frame-caption">{caption}{cursor}</span>'
            f'</div>'
        )

    typing = ""
    if streaming:
        typing = (
            '<div class="typing-indicator">'
            '<span></span><span></span><span></span>'
            '<span class="typing-label">PROCESSING NEXT FRAME...</span>'
            '</div>'
        )

    css = _CAPTIONS_CSS.format(fonts=_CAPTION_FONTS, height=height)
    scroll = _SCROLL_SCRIPT if streaming else ""
    return f"{css}<div id='scroll-box'>{''.join(rows)}{typing}</div>{scroll}"


def render_live_captions_streaming(frame_captions: List[Dict[str, Any]]):
    """Real-time update: captions append at bottom, auto-scroll down."""
    st.markdown('<div class="panel-header">◈ LIVE_CAPTIONS</div>', unsafe_allow_html=True)

    if not frame_captions:
        st.markdown("""
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.78rem;
                    color:#3a3a42; padding:0.5rem 0;">
            Waiting for first frame...
        </div>
        """, unsafe_allow_html=True)
        return

    html = _build_captions_html(frame_captions, height=360, streaming=True)
    components.html(html, height=380, scrolling=False)


def render_live_captions_complete(
    frame_captions: List[Dict[str, Any]],
    final_caption: Optional[str],
    metadata: Optional[Dict[str, Any]] = None
):
    """Post-analysis view: all frame captions + final caption + export button."""
    st.markdown('<div class="panel-header">◈ LIVE_CAPTIONS</div>', unsafe_allow_html=True)

    if frame_captions:
        html = _build_captions_html(frame_captions, height=220, streaming=False)
        components.html(html, height=240, scrolling=False)

    if final_caption:
        st.markdown("""
        <div style="border-top: 1px solid #2a2a32; margin: 0.75rem 0 0.6rem;
                    font-family:'JetBrains Mono',monospace; font-size:0.62rem;
                    color:#00f0ff; letter-spacing:0.1em;">
            FINAL_CAPTION
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#0f0f12; border:1px solid #00f0ff; padding:0.9rem 1rem;
                    font-family:'JetBrains Mono',monospace; font-size:0.85rem;
                    color:#f0f0f5; line-height:1.7;">
            {final_caption}
        </div>
        """, unsafe_allow_html=True)

        if metadata:
            export_data = {
                "caption": final_caption,
                "frame_captions": [f.get("caption", "") for f in frame_captions],
                "frame_count": metadata.get("frame_count", len(frame_captions)),
                "duration_seconds": metadata.get("duration_seconds", 0),
                "device_used": metadata.get("device_used", "unknown"),
                "model_id": metadata.get("model_id", "unknown")
            }
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            col1, col2 = st.columns([2.5, 1.5])
            with col2:
                st.download_button(
                    label="[ JSON ]",
                    data=json_str,
                    file_name=f"analysis_{metadata.get('frame_count', 'result')}.json",
                    mime="application/json",
                    use_container_width=True
                )


def render_live_captions_empty():
    """Empty state placeholder."""
    st.markdown('<div class="panel-header">◈ LIVE_CAPTIONS</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace; color:#2a2a32;
                font-size:0.78rem; line-height:2.2; padding:0.5rem 0.25rem;">
        <div>F01 &nbsp; ──────────────────────</div>
        <div>F02 &nbsp; ───────────────</div>
        <div>F03 &nbsp; ─────────────────────</div>
        <div>F04 &nbsp; ────────────</div>
        <br>
        <span style="color:#3a3a42; font-size:0.65rem; letter-spacing:0.1em;">
            CAPTIONS_WILL_APPEAR_HERE
        </span>
    </div>
    """, unsafe_allow_html=True)
