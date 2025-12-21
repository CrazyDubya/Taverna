## 2024-05-22 - Accessibility in Text Adventures
**Learning:** Text-based interfaces (like games or CLIs) often neglect `aria-live` regions, making them unusable for screen readers as new content appears without announcement.
**Action:** Always add `aria-live="polite"` and `role="log"` to dynamic text output containers.
