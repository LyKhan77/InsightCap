"""RTSP LIVE_STREAM and LIVE_CAPTIONS components."""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components


def render_rtsp_stream_empty():
    """Empty state for RTSP mode before a session is started."""
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
            START_RTSP_SESSION_TO_BEGIN
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_rtsp_live_stream(preview_url: str, session_name: str, source: str):
    """Render the MJPEG bridge stream for RTSP monitoring."""
    st.markdown('<div class="panel-header">◈ LIVE_STREAM</div>', unsafe_allow_html=True)
    html = f"""
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            background: #08080a;
            font-family: 'JetBrains Mono', monospace;
            color: #f0f0f5;
        }}
        .shell {{
            border: 1px solid #1e1e24;
            background: #0a0a0d;
        }}
        .stream {{
            position: relative;
            width: 100%;
            height: 320px;
            background: #050508;
            overflow: hidden;
        }}
        .stream img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .overlay {{
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #606066;
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            background: rgba(8, 8, 10, 0.25);
            text-transform: uppercase;
        }}
        .meta {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.7rem 0.8rem;
            border-top: 1px solid #1e1e24;
            font-size: 0.62rem;
            color: #909099;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .meta strong {{
            display: block;
            color: #00f0ff;
            font-size: 0.68rem;
            margin-bottom: 0.18rem;
        }}
        .source {{
            max-width: 50%;
            text-align: right;
            word-break: break-word;
        }}
    </style>
    <div class="shell">
        <div class="stream">
            <img src="{preview_url}" alt="RTSP preview"
                 onload="document.getElementById('rtsp-overlay').style.display='none';"
                 onerror="document.getElementById('rtsp-overlay').style.display='flex';">
            <div class="overlay" id="rtsp-overlay">Connecting preview bridge...</div>
        </div>
        <div class="meta">
            <div>
                <strong>{session_name}</strong>
                LIVE CAMERA
            </div>
            <div class="source">{source}</div>
        </div>
    </div>
    """
    components.html(html, height=390, scrolling=False)


def render_rtsp_live_captions(events_ws_url: str):
    """Render a browser-side WebSocket captions panel for RTSP events."""
    st.markdown('<div class="panel-header">◈ LIVE_CAPTIONS</div>', unsafe_allow_html=True)
    ws_url = json.dumps(events_ws_url)
    html = f"""
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: transparent;
            color: #f0f0f5;
            font-family: 'JetBrains Mono', monospace;
            overflow: hidden;
        }}
        #shell {{
            height: 388px;
            border: 1px solid #1e1e24;
            background: #0a0a0d;
            display: flex;
            flex-direction: column;
        }}
        #status {{
            padding: 0.75rem 0.85rem;
            border-bottom: 1px solid #1e1e24;
            color: #ffaa00;
            font-size: 0.66rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}
        #events {{
            flex: 1;
            overflow-y: auto;
            padding: 0.35rem 0.5rem;
        }}
        #events::-webkit-scrollbar {{ width: 3px; }}
        #events::-webkit-scrollbar-track {{ background: transparent; }}
        #events::-webkit-scrollbar-thumb {{ background: #2a2a32; border-radius: 2px; }}
        .row {{
            display: flex;
            align-items: flex-start;
            gap: 0.6rem;
            padding: 0.35rem 0.45rem;
            border-left: 2px solid #2a2a32;
            margin: 0.18rem 0;
        }}
        .row.caption {{ border-left-color: #00f0ff; }}
        .row.warning {{ border-left-color: #ff3366; }}
        .row.system {{ border-left-color: #ffaa00; }}
        .label {{
            color: #ffaa00;
            font-size: 0.62rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            flex-shrink: 0;
            padding-top: 1px;
        }}
        .text {{
            color: #c0c0c8;
            font-size: 0.8rem;
            line-height: 1.45;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .muted {{
            color: #606066;
            font-size: 0.64rem;
            letter-spacing: 0.06em;
        }}
        .empty {{
            padding: 1rem;
            color: #3a3a42;
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
    </style>
    <div id="shell">
        <div id="status">CONNECTING_WEBSOCKET...</div>
        <div id="events">
            <div class="empty" id="empty">Waiting for live RTSP events...</div>
        </div>
    </div>
    <script>
        const wsUrl = {ws_url};
        const statusEl = document.getElementById("status");
        const eventsEl = document.getElementById("events");
        const emptyEl = document.getElementById("empty");
        let socket = null;
        let stopped = false;
        let reconnectTimer = null;

        function setStatus(text, color) {{
            statusEl.textContent = text;
            statusEl.style.color = color;
        }}

        function removeEmpty() {{
            if (emptyEl) {{
                emptyEl.remove();
            }}
        }}

        function appendRow(kind, label, text, meta) {{
            removeEmpty();
            const row = document.createElement("div");
            row.className = `row ${{kind}}`;

            const labelEl = document.createElement("div");
            labelEl.className = "label";
            labelEl.textContent = label;

            const body = document.createElement("div");

            const textEl = document.createElement("div");
            textEl.className = "text";
            textEl.textContent = text;
            body.appendChild(textEl);

            if (meta) {{
                const metaEl = document.createElement("div");
                metaEl.className = "muted";
                metaEl.textContent = meta;
                body.appendChild(metaEl);
            }}

            row.appendChild(labelEl);
            row.appendChild(body);
            eventsEl.appendChild(row);

            while (eventsEl.children.length > 40) {{
                eventsEl.removeChild(eventsEl.firstChild);
            }}
            eventsEl.scrollTop = eventsEl.scrollHeight;
        }}

        function scheduleReconnect() {{
            if (stopped || reconnectTimer) return;
            reconnectTimer = window.setTimeout(() => {{
                reconnectTimer = null;
                connect();
            }}, 1200);
        }}

        function connect() {{
            setStatus("CONNECTING_RTSP_FEED...", "#ffaa00");
            socket = new WebSocket(wsUrl);

            socket.onopen = () => {{
                setStatus("LISTENING_RTSP_EVENTS", "#00ff88");
            }};

            socket.onmessage = (event) => {{
                const payload = JSON.parse(event.data);
                const eventType = payload.event;
                const data = payload.data || {{}};

                if (eventType === "connected") {{
                    setStatus("CAMERA_ONLINE", "#00ff88");
                    appendRow("system", "SYS", "Camera connected", `${{data.width || "?"}}x${{data.height || "?"}} · ${{data.fps || "?"}} FPS`);
                    return;
                }}

                if (eventType === "caption") {{
                    const seq = String(data.seq || 0).padStart(2, "0");
                    const lag = data.lag_ms != null ? `LAG ${{data.lag_ms}} ms` : "";
                    appendRow("caption", `F${{seq}}`, data.caption || "", lag);
                    return;
                }}

                if (eventType === "warning") {{
                    setStatus("STREAM_WARNING", "#ff3366");
                    appendRow("warning", "WARN", data.message || "Warning", `RECONNECTS ${{data.reconnect_count || 0}}`);
                    return;
                }}

                if (eventType === "heartbeat") {{
                    const lag = data.lag_ms != null ? ` · LAG ${{data.lag_ms}} ms` : "";
                    setStatus(`STATUS_${{String(data.status || "UNKNOWN").toUpperCase()}}${{lag}}`, "#ffaa00");
                    return;
                }}

                if (eventType === "stopped") {{
                    stopped = true;
                    setStatus("SESSION_STOPPED", "#606066");
                    appendRow("system", "SYS", "RTSP session stopped", null);
                    try {{ socket.close(); }} catch (err) {{}}
                }}
            }};

            socket.onerror = () => {{
                if (!stopped) {{
                    setStatus("WEBSOCKET_ERROR", "#ff3366");
                }}
            }};

            socket.onclose = () => {{
                if (!stopped) {{
                    setStatus("RECONNECTING_WEBSOCKET...", "#ffaa00");
                    scheduleReconnect();
                }}
            }};
        }}

        connect();
    </script>
    """
    components.html(html, height=410, scrolling=False)
