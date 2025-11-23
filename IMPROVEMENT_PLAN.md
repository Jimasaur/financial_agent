# Financial Research Agent - Improvement Plan

## 1. 💾 Database Upgrade
The goal is to make the application runnable "out of the box" without requiring a PostgreSQL server installation, while maintaining support for Postgres in production environments.

- [x] **Modify `database.py`**:
    - Check for `DATABASE_URL` environment variable.
    - If present, use `psycopg2` (existing logic).
    - If absent, fallback to `sqlite3` (standard library) to create a local file-based database (e.g., `research.db`).
    - Ensure all SQL queries are compatible with both dialects or abstract the differences.

## 2. 👀 Agent Transparency
The user wants to see the "actual words" exchanged between the system and the agents.

- [x] **Modify `manager.py`**:
    - Enhance `_log` calls to capture full input prompts and output responses.
    - Wrap `Runner.run` calls for Planner, Search, and Verifier to log the input `text` and output `final_output`.
    - For `Writer` (which uses streaming), inspect the stream events to capture generated text or tool calls and log them to the callback.
- [x] **Update Frontend Display**:
    - Ensure these detailed logs are clearly formatted in the Activity Log (e.g., distinct "Input" vs "Output" blocks).

## 3. 🎨 UI Polish & Features
Enhance the visual appeal and usability of the web interface.

- [x] **Markdown Rendering**:
    - Switch from simple regex-based replacement to `marked.js` (via CDN) in `index.html`.
    - Update `script.js` to use `marked.parse()` for rendering the report.
- [x] **Styling (`style.css`)**:
    - Add pulse animations to active steps in the progress stepper.
    - Improve print styles (`@media print`) so the report looks good on paper/PDF.
    - Add gradient fills to the Chart.js configuration.
    - Improve mobile responsiveness.
- [x] **New Features (`index.html` & `script.js`)**:
    - **Download PDF**: Add a button to trigger `window.print()` (styled for PDF export).
    - **Copy Report**: Add a button to copy the markdown content to clipboard.
    - **Clear History**: Add a button to clear the search history (backend endpoint + frontend button).

## 4. 🛠️ Code Robustness
- [x] **Error Handling**: Ensure graceful failure if stock data fetching fails.
- [x] **Feedback**: Visual cues for "Thinking..." states.
- [x] **Turn Limits**: Hard cap the number of turns for the Verifier Agent (and others) to prevent infinite loops/excessive costs.

## Execution Steps
1.  Update `database.py` to support SQLite.
2.  Update `manager.py` for transparency logging.
3.  Update `index.html` to include `marked.js` and new UI elements.
4.  Update `style.css` for polish.
5.  Update `script.js` to wire up new features and improved rendering.
