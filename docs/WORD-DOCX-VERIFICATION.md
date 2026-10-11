# Read-only Word DOCX verification gate

The executable verifier reads the saved DOCX file as an OOXML ZIP and inspects word/document.xml. It never controls the desktop or edits the document.

From SmartAutomation project root, AFTER UFO finishes and you independently know the saved file path:

```powershell
py -3.11 -m smartautomation.docx_verification --file "$env:USERPROFILE\Desktop\SmartAutomation-Word-Test.docx" --expected "SMARTAUTOMATION WORD TEST" --output "$env:USERPROFILE\Desktop\SmartAutomation-DOCX-Verification.json"
```

The report verifies file existence, ZIP readability and that the exact expected string appears in Word paragraph text. It does NOT check formatting, images, fields, tracked revisions, layout, visual rendering, or whether the content was produced by UFO. A `verified` result is limited to these checks.

Do not claim a process exit code or an agent-written evaluation independently verifies the saved artifact. Do not rerun Word automatically when a check fails.