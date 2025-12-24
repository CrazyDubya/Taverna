## 2024-12-24 - Semantic Structure & Skip Links
**Learning:** For keyboard-heavy interfaces like text adventures, a "Skip to Main Content" link is critical to bypass repetitive header navigation.
**Action:**
1. Add a skip link at the top of `<body>`.
2. Ensure the target uses `<main>` or `<aside>` with `tabindex="-1"` to guarantee focus moves correctly.
3. Use `sr-only` coupled with `focus:not-sr-only` to keep the UI clean but accessible.
