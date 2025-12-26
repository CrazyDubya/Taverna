## 2024-03-21 - Skip to Main Content Implementation
**Learning:** When implementing "Skip to Main Content" links in a single-page app or dynamic interface, simply adding the anchor isn't enough. You must ensure the target element (e.g., `<main>`) has `tabindex="-1"` and `outline-none`. This allows the element to receive programmatic focus (so the next Tab press starts inside the content) without showing an ugly focus ring on the container itself.
**Action:** Always pair Skip Links with `tabindex="-1"` on the target container and `outline-none` for visual polish.

## 2024-03-21 - Semantic Landmarks
**Learning:** Replacing generic wrapper `<div>`s with semantic landmarks like `<main>` and `<aside>` is a "free" accessibility win that doesn't require CSS changes if classes are preserved, but significantly improves screen reader navigation modes.
**Action:** Default to using `<main>`, `<aside>`, `<nav>`, and `<header>` instead of `div` wrappers for major layout sections.
