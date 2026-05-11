# BuildSummary.md — Data Insight Team App

> **Generated:** 2026-05-10 | **Version:** `beta v0.0.7` | **Status:** ⚠️ BETA

---

## 1. What This App Is

A **Streamlit chat application** deployed on **Databricks Apps** that lets users ask plain-English questions about flight data. The app connects directly to **Databricks Genie** (text-to-SQL AI), which translates questions into SQL queries against a Unity Catalog table and returns results as text, tables, charts, and downloadable files.

---

## 2. Architecture

```
User (browser)
    │
    ▼
Streamlit UI  (app.py)
    │  st.chat_input / st.session_state
    │
    ▼
Databricks SDK  (WorkspaceClient)
    │  w.genie.start_conversation_and_wait()
    │  w.genie.create_message_and_wait()
    │  w.genie.get_message_attachment_query_result()
    │
    ▼
Databricks Genie Space  (Space ID: 01f148039e131b10b43b6f97295e52e7)
    │  text-to-SQL AI — Databricks-managed
    │
    ▼
Unity Catalog Table: slf_srvc.test_db.reporting_flight
```

**The entire "AI brain" is Databricks Genie.** The app contains zero LLM calls — it is a thin UI wrapper.

---

## 3. What Is NOT in the App

| Component | Present? | Notes |
|---|---|---|
| LangChain / LangGraph | ❌ NO | Only in other repo templates — not this app |
| RAG (Retrieval-Augmented Generation) | ❌ NO | Planned Phase 4 |
| Claude / Anthropic SDK | ❌ NO | Planned Phase 2 as orchestrator |
| ChatOpenAI / OpenAI SDK | ❌ NO | Not used |
| Vector DB / embeddings | ❌ NO | Not connected |
| LLM orchestrator | ❌ NO | Genie handles everything internally |
| Agent loop (StateGraph, ReAct, etc.) | ❌ NO | No agent framework |
| MLflow experiment | ❌ NO | Not configured |
| Lakebase / PostgreSQL | ❌ NO | No persistent memory |

> The repo contains many other template directories (`agent-langgraph/`, `agent-openai-advanced/`, `.claude/skills/`) that reference LangChain, RAG, Claude, vector search, etc. Those are **separate templates** with no connection to `streamlit-hello-world-app/`.

---

## 4. Key Files

| File | Purpose |
|---|---|
| `app.py` | Main app — Genie integration, chat UI, chart/download logic (457 lines) |
| `styles.css` | Dark theme CSS — sidebar, chat bubbles, download buttons |
| `requirements.txt` | 4 Python dependencies |
| `app.yaml` | Databricks App startup command |
| `manifest.yaml` | App metadata |
| `SESSION_SUMMARY.md` | Session history and architecture roadmap |

---

## 5. Python Dependencies

```
streamlit~=1.38.0        # Web UI framework
pandas~=2.2.3            # DataFrame manipulation + Excel export
databricks-sdk~=0.40.0   # Genie API + WorkspaceClient
openpyxl~=3.1.5          # Excel file generation
```

No LLM libraries. No vector search libraries. No agent frameworks.

---

## 6. App Features (v0.0.7)

| Feature | Status |
|---|---|
| Chat with Databricks Genie | ✅ Working |
| Multi-turn conversation (session state) | ✅ Working |
| Markdown rendering (bold, bullets) | ✅ Fixed |
| Dollar sign rendering (no LaTeX) | ✅ Fixed |
| Bar chart from Genie text (markdown parser fallback) | ✅ Code in place — chart rendering unverified |
| Structured dataframe from query attachment | ⚠️ Not confirmed — `query` is `null` on current SDK |
| CSV / Excel / JSON download buttons | ✅ Code in place |
| "View SQL query" expander | ✅ Working |
| Collapsible left sidebar with "New chat" button | ✅ Working |
| Session question counter in sidebar | ✅ Working |
| Connected table name displayed | ✅ Working |
| Beta warning + version timestamp | ✅ Visible in sidebar and main header |
| Illustration buttons with mock data + disclaimer | ✅ Working |
| External `styles.css` (dark theme) | ✅ Working |
| Detailed runtime logging to Databricks App logs | ✅ Working |

---

## 7. Genie Space Configuration

**Space ID:** `01f148039e131b10b43b6f97295e52e7`

Instructions added (Text tab in Genie UI):
- Always answer data questions by generating and executing a SQL query
- When users ask for a graph — generate a SQL query with GROUP BY
- NEVER fabricate data values

Sample SQL queries added:
- "Count flights by departure airport"
- "Total revenue by month"

---

## 8. Deployment

| Setting | Value |
|---|---|
| Platform | Databricks Apps |
| Start command | `streamlit run app.py` |
| Connected table | `slf_srvc.test_db.reporting_flight` |
| GitHub fork | `https://github.com/JDC-WheelsUp/app-data-insight-agent` |
| Sparse checkout | `streamlit-hello-world-app/` |

**Pending fix:** Databricks ↔ GitHub connection is stuck (merge/rebase state). Next session: delete stuck folder, create fresh Git folder pointing to fork, re-deploy.

---

## 9. Version History

| Version | Date | Changes |
|---|---|---|
| v0.0.1 | May 9 | Initial fix: GenieMessage attribute error |
| v0.0.2 | May 9 | Added reset button; verbose logging |
| v0.0.3 | May 9 | Markdown parser fallback; fixed `$` LaTeX rendering |
| v0.0.4 | May 9 | Reset button above chat input; `styles.css` introduced |
| v0.0.5 | May 10 | Fixed CSS selector over-scoping |
| v0.0.6 | May 10 | Reset button moved below chat input |
| v0.0.7 | May 10 | Reset button moved to sidebar; layout="wide"; session counter |

---

## 10. Planned Roadmap

```
Phase 1 (Now):   User → Streamlit App → Genie → reporting_flight
Phase 2:         User → Streamlit App → Claude Opus 4.7 (orchestrator) → Genie tool
Phase 3:         + MS Fabric connector as a second tool
Phase 4:         + Vector Search for business glossary / KPI context
Phase 5:         Production (v1.0.0)
```

Phase 2 is where LangChain/LangGraph or Anthropic SDK would be introduced — **it does not exist yet**.

---

## 11. Key IDs

| Item | Value |
|---|---|
| Genie Space ID | `01f148039e131b10b43b6f97295e52e7` |
| Connected table | `slf_srvc.test_db.reporting_flight` |
| GitHub fork | `https://github.com/JDC-WheelsUp/app-data-insight-agent` |
| App URL (approx) | `databricks-data-agent-test-app-1036804910847582.2.azuredatabricks.net` |
