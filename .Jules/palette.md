## 2024-05-22 - Accessibility in Text Adventures
**Learning:** Text-based interfaces (like games or CLIs) often neglect `aria-live` regions, making them unusable for screen readers as new content appears without announcement.
**Action:** Always add `aria-live="polite"` and `role="log"` to dynamic text output containers.

## 2024-10-27 - Command History Accessibility
**Learning:** Clickable `div`s for history items exclude keyboard users entirely. Converting them to `button` elements is a simple, high-impact fix. Crucially, explicitly restoring focus to the input field after selection prevents the "focus lost" confusion common in single-page apps.
**Action:** Always use `<button>` for interactive list items and manage focus return on selection.
