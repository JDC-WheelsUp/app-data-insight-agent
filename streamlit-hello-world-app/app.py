# =============================================================================
# Data Insight Team - Streamlit Chat App for Databricks Genie
# Status: BETA - DO NOT USE IN PRODUCTION
# =============================================================================

APP_VERSION = "DO NOT USE IN PRODUCTION — beta v0.0.7 [2026-05-10 00:40 EDT]"
SPACE_ID = "01f148039e131b10b43b6f97295e52e7"
CONNECTED_TABLE = "slf_srvc.test_db.reporting_flight"

import streamlit as st
import pandas as pd
import io
import json
import sys
import re
import traceback
from pathlib import Path
from databricks.sdk import WorkspaceClient

st.set_page_config(
    page_title="Data Insight Team",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEME_LIGHT = {
    "--bg-app":         "#f5f6fa",
    "--bg-sidebar":     "#ffffff",
    "--bg-card":        "#ffffff",
    "--bg-input":       "#ffffff",
    "--bg-btn-dl":      "#f0f2f8",
    "--border-color":   "#dde1ea",
    "--accent":         "#FF3621",
    "--accent-hover":   "#d42c1a",
    "--text-primary":   "#1a1a2e",
    "--text-secondary": "#5a5f7a",
    "--text-muted":     "#9095ae",
    "--text-on-accent": "#ffffff",
    "--text-version":   "#e05a00",
    "--shadow-card":    "0 1px 4px rgba(0,0,0,0.08)",
}

THEME_DARK = {
    "--bg-app":         "#1a1a2e",
    "--bg-sidebar":     "#16213e",
    "--bg-card":        "#0f3460",
    "--bg-input":       "#2a2a4a",
    "--bg-btn-dl":      "#2a2a4a",
    "--border-color":   "#3a3a5c",
    "--accent":         "#FF3621",
    "--accent-hover":   "#ff5a47",
    "--text-primary":   "#e8eaf0",
    "--text-secondary": "#a0a8c8",
    "--text-muted":     "#6a7090",
    "--text-on-accent": "#ffffff",
    "--text-version":   "#ffb84d",
    "--shadow-card":    "0 1px 6px rgba(0,0,0,0.4)",
}


def inject_theme(dark: bool) -> None:
    """Inject CSS variable values into :root so every var() in styles.css resolves correctly.
    Called on every rerun — Streamlit re-renders the full page so the new values take effect
    immediately without any JavaScript."""
    tokens = THEME_DARK if dark else THEME_LIGHT
    vars_css = "\n".join(f"  {k}: {v};" for k, v in tokens.items())
    st.markdown(f"<style>:root {{\n{vars_css}\n}}</style>", unsafe_allow_html=True)


def log(msg):
    """Print to stdout so it shows up in Databricks App logs (Source: APP)."""
    print(f"[APP LOG] {msg}", flush=True)
    sys.stdout.flush()


def load_css(file_name):
    """Load external CSS file and inject into the page."""
    css_path = Path(__file__).parent / file_name
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        log(f"Loaded CSS from {file_name}")
    else:
        log(f"WARNING: CSS file not found: {css_path}")


def safe_dump(obj, max_len=2000):
    try:
        if obj is None:
            return "None"
        if hasattr(obj, "__dict__"):
            d = {}
            for k, v in vars(obj).items():
                try:
                    if v is None:
                        d[k] = None
                    elif isinstance(v, (str, int, float, bool)):
                        d[k] = v
                    elif hasattr(v, "__dict__"):
                        d[k] = f"<{type(v).__name__}>"
                    else:
                        d[k] = str(v)[:200]
                except Exception:
                    d[k] = "<unreadable>"
            s = json.dumps(d, default=str, indent=2)
            return s[:max_len]
        return str(obj)[:max_len]
    except Exception as e:
        return f"<dump failed: {e}>"


def parse_markdown_data_from_text(text):
    if not text:
        return None
    pattern = r"[-*]\s*\*?\*?([A-Za-z0-9_\-→() ]+?)\*?\*?\s*[:\-]\s*\$?([\d,]+\.?\d*)"
    matches = re.findall(pattern, text)
    if len(matches) < 2:
        return None
    try:
        labels = [m[0].strip() for m in matches]
        values = [float(m[1].replace(",", "")) for m in matches]
        return pd.DataFrame({"Label": labels, "Value": values})
    except Exception:
        return None


log("=" * 60)
log(f"APP SCRIPT EXECUTING - version: {APP_VERSION}")
log(f"Connected table: {CONNECTED_TABLE}")
log("=" * 60)


# ---------- Load styles ----------
load_css("styles.css")


# ---------- Session state ----------

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_example" not in st.session_state:
    st.session_state.show_example = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ---------- Theme injection ----------
# Writes the correct CSS variable values into :root on every rerun.
# No JavaScript needed — Streamlit strips <script> tags; this pure-CSS
# approach works because Streamlit does a full page re-render on rerun.
inject_theme(st.session_state.dark_mode)


# ---------- Sidebar ----------

with st.sidebar:
    st.markdown('<div class="sidebar-brand">✈️ Data Insight Team</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">AI-powered flight data Q&A</div>', unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🔄 New chat", key="reset_btn", use_container_width=True,
                 help="Start a new conversation"):
        log("USER CLICKED RESET")
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.show_example = None
        st.rerun()

    _theme_label = "🌙 Dark mode" if not st.session_state.dark_mode else "☀️ Light mode"
    if st.button(_theme_label, key="theme_toggle_btn", use_container_width=True,
                 help="Toggle between light and dark theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown("---")

    st.markdown('<div class="sidebar-section-label">CONNECTED TO</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sidebar-table-pill">📊 {CONNECTED_TABLE}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown('<div class="sidebar-section-label">SESSION</div>', unsafe_allow_html=True)
    msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    if msg_count == 0:
        st.markdown('<div class="sidebar-meta">No questions asked yet</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="sidebar-meta">{msg_count} question{"s" if msg_count != 1 else ""} this session</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="flex: 1; min-height: 2rem;"></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f'<div class="sidebar-version">{APP_VERSION}</div>',
        unsafe_allow_html=True,
    )


# ---------- Main area header ----------

st.markdown('<div class="chat-title">✈️ Data Insight Team</div>', unsafe_allow_html=True)
st.markdown('<div class="chat-subtitle">Ask anything about your flight data in plain English</div>', unsafe_allow_html=True)
st.markdown(f'<div class="chat-version">{APP_VERSION}</div>', unsafe_allow_html=True)


# ---------- Helpers ----------

def fetch_query_dataframe(w, space_id, conversation_id, message_id, attachment_id):
    log(f"fetch_query_dataframe: conv={conversation_id}, msg={message_id}, att={attachment_id}")
    result = None
    try:
        result = w.genie.get_message_attachment_query_result(
            space_id=space_id, conversation_id=conversation_id,
            message_id=message_id, attachment_id=attachment_id,
        )
    except AttributeError:
        result = w.genie.get_message_query_result(
            space_id=space_id, conversation_id=conversation_id, message_id=message_id,
        )
    except Exception as e:
        log(f"Fetch error: {e}")
        raise

    if not result:
        return None

    sr = getattr(result, "statement_response", None)
    if not sr or not sr.result or not sr.manifest:
        return None

    rows = sr.result.data_array or []
    cols = [c.name for c in sr.manifest.schema.columns]
    log(f"Got {len(rows)} rows, cols: {cols}")

    df = pd.DataFrame(rows, columns=cols)
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass
    return df


def df_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return output.getvalue()


def render_assistant_response(payload, msg_index):
    text = payload.get("text")
    df_records = payload.get("dataframe")
    sql = payload.get("sql")

    if text:
        safe_text = text.replace("$", "\\$")
        st.markdown(safe_text)

        if not df_records:
            extracted_df = parse_markdown_data_from_text(text)
            if extracted_df is not None and len(extracted_df) >= 2:
                log(f"Extracted DataFrame from markdown text: {len(extracted_df)} rows")
                df_records = extracted_df.to_dict(orient="records")
                payload["dataframe"] = df_records

    if df_records:
        df = pd.DataFrame(df_records)
        st.dataframe(df, use_container_width=True, hide_index=True)

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        non_numeric_cols = [c for c in df.columns if c not in numeric_cols]
        if len(numeric_cols) >= 1 and len(non_numeric_cols) >= 1 and len(df) <= 50:
            try:
                chart_df = df.set_index(non_numeric_cols[0])[numeric_cols]
                st.bar_chart(chart_df)
            except Exception as e:
                log(f"Chart render failed: {e}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "⬇ CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"genie_result_{msg_index}.csv",
                mime="text/csv",
                key=f"csv_{msg_index}",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "⬇ Excel",
                data=df_to_excel_bytes(df),
                file_name=f"genie_result_{msg_index}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"xlsx_{msg_index}",
                use_container_width=True,
            )
        with col3:
            st.download_button(
                "⬇ JSON",
                data=json.dumps(df_records, indent=2, default=str).encode("utf-8"),
                file_name=f"genie_result_{msg_index}.json",
                mime="application/json",
                key=f"json_{msg_index}",
                use_container_width=True,
            )

    if sql:
        with st.expander("View SQL query"):
            st.code(sql, language="sql")


# ---------- Render chat history ----------

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(
            f'<div class="msg-user"><div class="bubble">{msg["content"]}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        col_avatar, col_content = st.columns([1, 20])
        with col_avatar:
            st.markdown(
                '<div style="width:32px;height:32px;border-radius:50%;background:#10a37f;'
                'color:white;font-size:0.75rem;font-weight:bold;display:flex;'
                'align-items:center;justify-content:center;margin-top:4px;">G</div>',
                unsafe_allow_html=True,
            )
        with col_content:
            render_assistant_response(msg["payload"], i)


# ---------- Chat input ----------

if question := st.chat_input("Ask a question about your data..."):
    log("#" * 70)
    log(f"### USER QUESTION: {question}")
    log("#" * 70)

    st.session_state.messages.append({"role": "user", "content": question})
    st.markdown(
        f'<div class="msg-user"><div class="bubble">{question}</div></div>',
        unsafe_allow_html=True,
    )

    payload = {"text": None, "dataframe": None, "sql": None}
    with st.spinner("Thinking..."):
        try:
            w = WorkspaceClient()

            if st.session_state.conversation_id is None:
                message = w.genie.start_conversation_and_wait(SPACE_ID, question)
            else:
                message = w.genie.create_message_and_wait(
                    SPACE_ID, st.session_state.conversation_id, question
                )

            log(f"Message: {safe_dump(message, max_len=2000)}")

            if hasattr(message, "conversation_id") and message.conversation_id:
                st.session_state.conversation_id = message.conversation_id

            message_id = getattr(message, "message_id", None) or getattr(message, "id", None)
            attachments = getattr(message, "attachments", None)

            if attachments:
                for idx, att in enumerate(attachments):
                    log(f"==== Attachment {idx} ====")
                    log(safe_dump(att, max_len=1500))

                    text_obj = getattr(att, "text", None)
                    if text_obj and getattr(text_obj, "content", None):
                        payload["text"] = text_obj.content

                    query_obj = getattr(att, "query", None)
                    if query_obj is not None:
                        sql_str = (
                            getattr(query_obj, "query", None)
                            or getattr(query_obj, "statement", None)
                            or getattr(query_obj, "sql", None)
                            or getattr(query_obj, "query_text", None)
                        )
                        if sql_str:
                            payload["sql"] = sql_str

                        attachment_id = (
                            getattr(att, "attachment_id", None)
                            or getattr(att, "id", None)
                        )
                        if attachment_id and message_id and st.session_state.conversation_id:
                            try:
                                df = fetch_query_dataframe(
                                    w, SPACE_ID, st.session_state.conversation_id,
                                    message_id, attachment_id,
                                )
                                if df is not None and not df.empty:
                                    payload["dataframe"] = df.to_dict(orient="records")
                                    log(f"DataFrame captured: {len(df)} rows")
                            except Exception as fe:
                                log(f"FETCH FAILED: {fe}")

            if not payload["text"] and getattr(message, "content", None):
                payload["text"] = message.content
            if not payload["text"] and not payload["dataframe"]:
                payload["text"] = "I wasn't able to generate an answer. Please try rephrasing your question."

            log(f"FINAL: text:{bool(payload['text'])} df:{bool(payload['dataframe'])} sql:{bool(payload['sql'])}")
            if payload['sql']:
                log(f"SQL: {payload['sql']}")

        except Exception as e:
            log(f"TOP-LEVEL ERROR: {e}")
            log(traceback.format_exc())
            payload["text"] = f"Error connecting to Genie: {str(e)}"

    msg_index = len(st.session_state.messages)
    col_avatar, col_content = st.columns([1, 20])
    with col_avatar:
        st.markdown(
            '<div style="width:32px;height:32px;border-radius:50%;background:#10a37f;'
            'color:white;font-size:0.75rem;font-weight:bold;display:flex;'
            'align-items:center;justify-content:center;margin-top:4px;">G</div>',
            unsafe_allow_html=True,
        )
    with col_content:
        render_assistant_response(payload, msg_index)

    st.session_state.messages.append({"role": "assistant", "payload": payload})


# ---------- Empty state suggestions ----------

if not st.session_state.messages:
    st.markdown(
        '<p style="text-align:center; color:#8e8ea0; font-size:0.85rem; margin-top:1.5rem;">'
        'Try one of these examples (illustrations only — type your real question in the chat below):'
        '</p>',
        unsafe_allow_html=True,
    )

    EXAMPLES = {
        "📊 Flights per month": {
            "description": "How total flight count trends month over month.",
            "data": {
                "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "Flights": [142, 168, 195, 178, 210, 232],
            },
            "chart_x": "Month",
            "chart_y": "Flights",
        },
        "✈️ Top 10 departure airports": {
            "description": "Which airports we fly out of most often.",
            "data": {
                "Airport": ["KTEB", "KAPA", "KPDK", "KHPN", "KSRQ",
                            "KBNA", "KAUS", "KDAL", "KEUG", "KCEU"],
                "Flight Count": [487, 412, 398, 356, 312, 298, 274, 251, 198, 187],
            },
            "chart_x": "Airport",
            "chart_y": "Flight Count",
        },
        "💰 Avg revenue by route": {
            "description": "Average member price for the most common routes.",
            "data": {
                "Route": ["KTEB→KPBI", "KAPA→KEGE", "KHPN→KSRQ",
                          "KPDK→KMYY", "KAUS→KDAL", "KBNA→KMHL"],
                "Avg Price (USD)": [28450, 19800, 22300, 15600, 12400, 9850],
            },
            "chart_x": "Route",
            "chart_y": "Avg Price (USD)",
        },
    }

    cols = st.columns(len(EXAMPLES))
    for col, (label, info) in zip(cols, EXAMPLES.items()):
        with col:
            if st.button(label, key=f"example_{label}", use_container_width=True):
                st.session_state["show_example"] = label

    selected = st.session_state.get("show_example")
    if selected and selected in EXAMPLES:
        info = EXAMPLES[selected]
        st.markdown("---")

        st.warning(
            f"⚠️ **This is just an illustration with mock data.** "
            f"It is NOT a real query against your data — the numbers shown are fabricated examples.\n\n"
            f"💡 **Want live data?** Use the chat box at the bottom of the page to ask your own question. "
            f"This chatbot is currently connected to the **`{CONNECTED_TABLE}`** table."
        )

        st.markdown(f"### {selected}")
        st.markdown(f"_{info['description']}_")

        sample_df = pd.DataFrame(info["data"])
        st.dataframe(sample_df, use_container_width=True, hide_index=True)

        chart_df = sample_df.set_index(info["chart_x"])[[info["chart_y"]]]
        st.bar_chart(chart_df)

        st.caption(f"📌 Mock data shown above. Real queries hit `{CONNECTED_TABLE}`.")

        if st.button("Close illustration", key="close_example"):
            st.session_state["show_example"] = None
            st.rerun()