# Follow-up Tasks

## Typo Fix
- **Issue:** The item form instructions show `" |primary"` with an unintended leading space before the pipe, which misleads users about the exact flag they should type.
- **Task:** Update the helper text in `app/templates/item_form.html` to display `"|primary"` without the leading space.
- **References:** `app/templates/item_form.html` line 28.

## Bug Fix
- **Issue:** The `_sync_characters` helper only splits character names on commas, so semicolon-delimited values promised in the README are ignored when editing or creating items through the UI.
- **Task:** Extend `_sync_characters` in `app/main.py` to normalize both comma- and semicolon-separated character lists before processing.
- **References:** `app/main.py` lines 42-67; `README.md` line 31.

## Documentation Update
- **Issue:** The form label says "Characters (comma-separated…)" even though the application (and README) support semicolons, so the UI copy contradicts the documented behavior.
- **Task:** Revise the label text in `app/templates/item_form.html` to mention both commas and semicolons, matching the README guidance.
- **References:** `app/templates/item_form.html` line 28; `README.md` line 31.

## Test Improvement
- **Issue:** The CSV importer’s `split_characters` helper silently handles both commas and semicolons, but there are no automated tests to ensure future changes preserve this normalization.
- **Task:** Add a unit test around `split_characters` (e.g., under a new `tests/` module) that covers comma/semicolon mixtures and the `|primary` marker trimming.
- **References:** `app/importers/import_csv.py` lines 89-95.
