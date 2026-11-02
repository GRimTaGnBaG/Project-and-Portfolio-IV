# Desktop design checkpoint

## Five-page workflow

My desktop interface now follows the supplied Figma screenshots with separate Document, Review Rules, Calendar, Saved Records, and Research Comparison pages. The presentation uses a consistent sidebar, light panels, blue/gold ownership labels, and the existing validated backend.

The redesign was committed locally on November 1 and held for later integration. Its original commit metadata is preserved. Publication on November 2 is an integration of that existing work, not a claim that it was all developed on the upload date.

## Implemented behavior

- Native PDF preview alongside extracted source text.
- Editable anchor, 14-day ownership controls, and exchange metadata.
- Explicit review acknowledgment; edits clear approval and calendar rows.
- Parent labels inside calendar cells as well as dated ownership rows.
- Searchable local saved records and a separate historical-results view.
- Saving/loading/export continue to use the tested backend operations.

## November 2 correction

Filtering saved records previously hid table rows without necessarily changing the record targeted by Load or Delete. A second visible selector could also disagree with the filtered table. The table now owns visible selection, the redundant selector is hidden, and no-match searches clear the action target and disable those actions.

The regression check verifies that a search targets the visible November record rather than a hidden December record; an empty result cannot load the previous selection; clearing the query restores an actionable visible selection. All 35 development checks passed after the correction.

## Remaining limits

This checkpoint does not establish broad document interpretation accuracy or complete Assignment 3 prototype playback. Scanned input and comprehensive holiday rules remain outside the supported scope. Historical research metrics and earlier report test counts retain their original checkpoint meaning.
