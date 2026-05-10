# Data Insight Team — Session Summary (May 9–10, 2026)

## What We Built

A Streamlit chat application deployed on Databricks Apps that lets users ask plain-English questions about flight data. The app connects to **Databricks Genie** (text-to-SQL AI) backed by the table `slf_srvc.test_db.reporting_flight`, and renders the results as text, interactive tables, bar charts, and downloadable files.

---

## Key Files

| File | Purpose |
|---|---|
| `app.py` | Main Streamlit app — Genie integration, chat UI, chart/download logic |
| `styles.css` | External CSS for dark theme, sidebar, bubbles, download buttons |
| `requirements.txt` | `streamlit~=1.38.0`, `pandas~=2.2.3`, `databricks-sdk~=0.40.0`, `openpyxl~=3.1.5` |

---

## Problems Solved (Chronological)

### 1. `GenieMessage` attribute error
**Problem:** `result.message.attachments` failed — the SDK returns a `GenieMessage` directly, not a nested wrapper.  
**Fix:** Renamed `result` → `message` and accessed `.attachments` and `.content` directly.

### 2. Removed unused import
Dropped `from databricks.sdk.service.dashboards import MessageStatus` which was unused and causing confusion.

### 3. Graph rendering not working
**Root cause (Layer 1):** Genie was responding conversationally (text-only) instead of executing SQL, so no structured query result existed to chart.  
**Root cause (Layer 2):** Even when Genie ran SQL, the rows came back embedded in a markdown bullet list inside the text attachment (`query: null`), not as a separate query-result attachment.  
**Fix (Layer 1):** Added instructions to the Genie space:
- Always query `slf_srvc.test_db.reporting_flight` via SQL
- Never fabricate data; never refuse a graph request
- Added 2 sample SQL questions to train Genie's pattern matching

**Fix (Layer 2):** Added `parse_markdown_data_from_text()` — a regex fallback that extracts `Label: Value` pairs from Genie's bullet-list responses and builds a `pd.DataFrame` from them. This DataFrame then flows through the existing chart/download rendering path.

### 4. LaTeX rendering of dollar signs
**Problem:** Genie responses containing `$81,250` were rendered as LaTeX math, garbling the output.  
**Fix:** `text.replace("$", "\\$")` before `st.markdown(text)`.

### 5. `attachment_id` / `message_id` fetch failures
**Investigation:** Added `safe_dump()` — a best-effort JSON serializer of SDK objects — and logged every attachment's full attribute dict. Confirmed `query` was `None` for the relevant attachment type (explaining why `fetch_query_dataframe()` was never called).

### 6. Button CSS over-scoped
**Problem:** The circular reset button CSS `div[data-testid="column"]:has(button[kind="secondary"])` accidentally matched the three illustration example buttons, squeezing their labels into thin vertical stacks.  
**Fix:** Scoped the selector more tightly to `button[kind="secondary"][data-testid*="reset_btn"]`, then moved CSS to a separate `styles.css` file.

### 7. Reset button placement
**Problem:** `st.button()` placed above `st.chat_input()` in code appears mid-page because Streamlit's chat input anchors to the bottom of the viewport regardless of code order.  
**Final solution:** Moved the reset button into `st.sidebar` as a prominent green "🔄 New chat" button. Sidebar is collapsible by default (Streamlit built-in).

### 8. Git ownership / workflow
**Problem:** Databricks workspace folder was cloned from `databricks/app-templates` (public, no push access). Commits would fail with permission-denied.  
**What was done:**
- Forked `databricks/app-templates` → `JDC-WheelsUp/app-data-insight-agent`
- Installed Git locally (v2.50.1, Mac)
- Cloned fork via GitHub Desktop
- Replaced template files in `streamlit-hello-world-app/` with custom `app.py`, `requirements.txt`, `styles.css`
- Committed and pushed via GitHub Desktop

**Remaining (to do next session):**
1. Go to https://github.com/settings/installations → Databricks app → grant access to `JDC-WheelsUp/app-data-insight-agent`
2. In Databricks: delete the stuck folder (currently in a merge/rebase state after a failed URL-change attempt)
3. Create a fresh Git folder pointing to `https://github.com/JDC-WheelsUp/app-data-insight-agent.git` (sparse checkout: `streamlit-hello-world-app`)
4. Re-deploy app from the new folder

---

## Current App Features (v0.0.7)

| Feature | Status |
|---|---|
| Chat with Databricks Genie | ✅ Working |
| Multi-turn conversation (session state) | ✅ Working |
| Markdown rendering (bold, bullets) | ✅ Fixed |
| Dollar sign rendering (no LaTeX) | ✅ Fixed |
| Bar chart from Genie text (markdown parser) | ✅ Code in place — confirmed Genie now runs SQL; chart rendering **unverified** |
| Structured dataframe from query attachment | ⚠️ Not yet confirmed — `query` is `null` on current SDK version |
| CSV / Excel / JSON download buttons | ✅ Code in place |
| "View SQL query" expander | ✅ Working |
| Collapsible left sidebar with "New chat" button | ✅ Working |
| Session question counter in sidebar | ✅ Working |
| Connected table name displayed | ✅ Working |
| Beta warning + version timestamp | ✅ Visible in sidebar and main header |
| Illustration buttons with mock data + disclaimer | ✅ Working |
| External `styles.css` (dark theme) | ✅ Working |
| Detailed runtime logging to Databricks App logs | ✅ Working (Source: APP) |

---

## Genie Space Configuration Applied

Genie Space ID: `01f148039e131b10b43b6f97295e52e7`

**Instructions added (Text tab):**
```
You are a SQL data agent connected to slf_srvc.test_db.reporting_flight.

CRITICAL RULES:
1. Always answer data questions by generating and executing a SQL query.
2. When users ask for a graph — generate a SQL query with GROUP BY. Never respond "I cannot create graphs."
3. When users ask for downloads — run a SQL query and return rows.
4. If a question cannot be answered from this table, say "I cannot answer this from the available data."
5. NEVER fabricate data values.
6. When in doubt, RUN THE QUERY.
```

**Sample SQL queries added:**
- "Count flights by departure airport" → `SELECT FROMAIRPORT, COUNT(*) GROUP BY ... ORDER BY flight_count DESC LIMIT 20`
- "Total revenue by month" → `SELECT DATE_TRUNC('month', FLIGHTDATE) AS month, SUM(REVENUE) GROUP BY 1 ORDER BY 1`

---

## Architecture Context

The current app is **Phase 1** of a planned multi-source AI analytics platform:

```
Phase 1 (Now):  User → Streamlit App → Genie (Databricks) → reporting_flight
Phase 2:        User → Streamlit App → Claude Opus 4.7 (orchestrator) → Genie tool
Phase 3:        + MS Fabric connector as a second tool
Phase 4:        + Vector Search for business glossary / KPI context
Phase 5:        Production (remove BETA warning, v1.0.0)
```

---

## Version History

| Version | Date | Changes |
|---|---|---|
| v0.0.1 | May 9 | Initial fix: GenieMessage attribute error |
| v0.0.2 | May 9 | Added "🔄 Start new conversation" centered button; verbose question logging |
| v0.0.3 | May 9 | Added `parse_markdown_data_from_text()` fallback; fixed `$` LaTeX rendering; bumped logging detail |
| v0.0.4 | May 9 | Moved reset button above chat input (right-aligned icon); `styles.css` introduced |
| v0.0.5 | May 10 | Fixed CSS selector over-scoping (example buttons no longer squished) |
| v0.0.6 | May 10 | Reset button moved below chat input area (centered pill) |
| v0.0.7 | May 10 | Reset button moved to collapsible left sidebar; sidebar with session counter, table info, version footer; layout="wide" |

---

## Next Session Priorities

1. **Fix Databricks ↔ GitHub fork connection** (15 min, clean reset approach — see section above)
2. **Confirm graph rendering** — ask `count flights by departure airport` in fresh conversation, verify table + bar chart + downloads appear
3. **Set up Claude Code** on local Mac for "Claude writes directly to repo" workflow
4. **Plan Phase 2** — Claude Opus 4.7 as orchestrator, routing questions to Genie as a tool

---

## Credentials / IDs to Remember

- **Genie Space ID:** `01f148039e131b10b43b6f97295e52e7`
- **Connected table:** `slf_srvc.test_db.reporting_flight`
- **Fork:** `https://github.com/JDC-WheelsUp/app-data-insight-agent`
- **App URL:** `databricks-data-agent-test-app-1036804910847582.2.azuredatabricks.net` (approx)
- **Databricks workspace source path:** `streamlit-hello-world-app/` (sparse checkout)
