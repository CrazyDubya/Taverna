## 2024-03-21 - [Implementing Loading States in Vanilla JS]
**Learning:** When implementing complex loading states (saving/restoring content) in vanilla JS, rely on instance variables to cache the original state. Crucially, check if the cache exists before overwriting to prevent race conditions or repeated calls destroying the original content. Also, always ensure SVG spinners are `aria-hidden="true"` and paired with `sr-only` text.
**Action:** Use the pattern `if (!this.cache) this.cache = el.innerHTML` for all future toggle-based UI states in this project.
