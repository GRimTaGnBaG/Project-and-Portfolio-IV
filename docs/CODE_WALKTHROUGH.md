# Code walkthrough

Read modules in this order to follow one document through the application.

1. **`app.py`:** QApplication starts Qt's event loop and retains the main window. This is the launch point, not the scheduling logic.
2. **`core.py`:** PDF extraction preserves page boundaries. A conservative baseline creates a proposal. Pydantic validates the data shape; quotation checks verify source membership. The calendar engine converts approved rules to dates using offset modulo 14. Detailed comments explain why the pre-anchor date maps correctly.
3. **`local_model.py`:** Page-labeled text and a schema go to the loopback model API. Evidence records the exact prompt, settings, response, and timing. Incomplete or invalid responses fail instead of being guessed into a schedule.
4. **`session.py`:** The state boundary owns approval. New source/rule edits invalidate approval and generated rows. Approval reparses the editor contents and checks evidence and unresolved warnings. Generation requires current approval.
5. **`storage.py`:** Parameterized SQL stores reviewed rules and provenance. Transaction handling commits or rolls back and explicitly closes connections. Reload creates a fresh unapproved review session. CSV export defaults to exclusive creation to protect existing files.
6. **`gui.py`:** Buttons delegate to these modules. A QThread performs inference without freezing the main UI. Signals return results to the UI thread. Controls reflect prerequisites, and calendar navigation clears old output. The close guard avoids destroying a running inference thread.
7. **Tests:** Core checks verify known date/source outcomes. Workflow checks verify invalidation, database round trips, and CSV contents/overwrite protection. Live pipeline verification remains separate so a mock or deterministic test is not mistaken for real model evidence.

## Demo sequence

Launch the app, select the generated fictional PDF, inspect source text, run baseline or a loaded local model, inspect the JSON, approve, generate the month, and show overnight rows. Edit the rules to show approval/output invalidation. Approve again, save, reload, review again, generate, and export CSV. Explain the source/schema limitations rather than claiming legal interpretation accuracy.

## Remaining work

The recorded development checkpoint includes longer fictional inputs, six-case held-out metrics, a live Qt-worker check, and a comparison-results tab. Follow-up work includes a fresh untouched evaluation set, structured field editing beyond the JSON editor, broader failure-path checks, report review, and the deferred narrated video. Dedicated-tool Assignment 3 prototype delivery remains separate and unresolved. See EXPANDED_EVALUATION.md and ITERATION1_INCREMENT.md for measured results and limits.
