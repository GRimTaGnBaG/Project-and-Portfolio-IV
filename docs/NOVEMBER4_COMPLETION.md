# November 4 desktop completion

The desktop MVP now runs a fresh baseline/local-model comparison, reports measured method runtimes and retains failures. Accuracy is scored only against explicitly approved current rules and is labeled as a reviewed reference, not independent ground truth. Historical results remain available. This workflow never grants approval or modifies the reviewed document.

The Document page now opens the bundled fictional sample directly and probes the local LM Studio server without blocking the interface. Source assets and writable records are separated. Saved records default to the user's local application-data folder, so replacing the application folder does not overwrite them. Loading an old plan returns the calendar to that plan's anchor month and invalidates approval.

The Windows launcher supports the configured environment and a fresh per-folder setup. The user guide covers baseline use, model setup, records, export and supported boundaries. Interactive inference no longer creates raw request/response archives automatically; deliberate research runners retain their existing evidence mechanism.

## Verification

- 38 automated checks pass, including the real five-page fictional PDF, native preview, proposal review, 30 November dates, SQLite reload, comparison rendering, and failure preservation.
- A separate live Qt/local-model test uses the installed `parentvault-research` alias. It passes extraction, explicit review, 30 overnight assignments, CSV export, SQLite save, fresh comparison and unapproved reload.
- All eight baseline/model comparison field checks match the reviewed fictional sample. These are four fields for each of two methods, not eight independent documents. They do not replace the earlier held-out evaluation or establish general accuracy.
- The event loop processed 2,381 iterations across the two inference operations; no integration errors were reported.

The supported result is a bounded 14-day recurring-schedule MVP. OCR, holiday interpretation and unsupported provisions remain excluded. Historical course report findings are preserved as their original research checkpoint.
