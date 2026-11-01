# Technical source notes

I am using primary documentation to connect the implementation choices with observed results. These notes are source material for the technical report, not a completed report or complete prompt log.

## PDF extraction and scanned inputs

Artifex Software. (n.d.). *FAQ*. PyMuPDF documentation. https://pymupdf.readthedocs.io/en/latest/faq/index.html

I use page-indexed text extraction and preserve page references. Image-only documents require a separate OCR path; my current app rejects them. The generated scanned fixture verifies that boundary without using private documents. The documentation also notes that extraction order depends on the PDF's construction, which matters when interpreting multipart forms.

## Structured local-model output

LM Studio. (n.d.). *Structured output*. https://lmstudio.ai/docs/developer/openai-compat/structured-output

I pass a JSON schema through the chat-completions response format. The documentation describes schema-directed outputs, but my experiments show why I still need application-level checks: one model produced reasoning text, and another returned schema-valid but incorrect rotations on longer examples. I treat API formatting support and semantic correctness as separate properties.

## Validation and semantic checks

Pydantic. (n.d.). *Models*. Pydantic documentation. https://docs.pydantic.dev/latest/concepts/models/

I use model validation to constrain dates, cycle length, owner labels, and evidence fields. I added deterministic checks against recognizable source rules after a longer example returned an incorrect cycle with a genuine quotation. A valid model object does not establish that the document was interpreted correctly.

## Desktop responsiveness

The Qt Company. (n.d.). *Threads and QObjects*. Qt for Python documentation. https://doc.qt.io/qtforpython-6.10/overviews/qtdoc-threads-qobject.html

I run blocking inference in a worker and return results through signals to the main GUI thread. My automated live GUI check observed 314 event-loop timer ticks while inference ran, then verified approval and 30 generated rows. This checks event-loop progress in that run; it is not a complete usability study or manual file-dialog test.
