## 2024-05-23 - Accessibility: Semantic Landmarks and Skip Links
**Learning:** Using semantic landmarks (`<main>`, `<aside>`) and a properly implemented "Skip to main content" link significantly improves navigation for keyboard and screen reader users. The skip link must target an element with `tabindex="-1"` to ensure focus is correctly managed when the link is activated.
**Action:** When auditing pages, always check for the presence of a skip link as the first focusable element and ensure main content regions are semantically marked.
