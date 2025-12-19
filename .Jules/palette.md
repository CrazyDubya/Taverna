## 2024-05-22 - Accessibility in Text Adventures
**Learning:** Text-based interfaces (like games or CLIs) often neglect `aria-live` regions, making them unusable for screen readers as new content appears without announcement.
**Action:** Always add `aria-live="polite"` and `role="log"` to dynamic text output containers.

## 2024-05-23 - Modal Accessibility
**Learning:** Modals often break keyboard navigation if focus is not trapped or managed. Users can get lost tabbing behind the modal.
**Action:** Always implement `open()` and `close()` methods that handle focus management (save active element, move focus to modal, restore focus) and Escape key support.
