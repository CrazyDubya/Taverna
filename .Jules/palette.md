## 2024-05-23 - Focus Management in Text Adventures
**Learning:** In text-heavy interfaces like RPGs, users expect immediate keyboard readiness. Failing to autofocus the main input creates friction on every page load.
**Action:** Always verify `autofocus` on the primary input for command-driven interfaces.

## 2024-12-22 - Modal Focus Management Patterns
**Learning:** Proper modal dialogs require careful focus management to ensure keyboard users and screen reader users can navigate effectively. Key requirements include:
- Save the previously focused element before opening the modal
- Move focus to the first interactive element (usually first input field) when modal opens
- Restore focus to the previously focused element when modal closes
- Support Escape key to close modal
- Add semantic ARIA attributes: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
**Action:** Implement comprehensive focus management for all modal dialogs. Test with keyboard-only navigation and screen readers.

## 2024-12-22 - Command History Keyboard Accessibility
**Learning:** Interactive lists using clickable `<div>` elements are not keyboard accessible. Screen readers don't recognize them as interactive elements, and keyboard users cannot tab to or activate them.
**Solution:** Convert interactive list items to semantic `<button>` elements with proper attributes:
- Use `<button type="button">` for interactive list items
- Add `aria-label` to provide context for screen readers
- Include `focus:ring` styles for visual focus indicators
- Return focus to the command input after selection for smooth workflow
- Maintain `aria-expanded` state on toggle buttons
**Action:** Always use semantic HTML elements (`<button>`, `<a>`, etc.) for interactive elements, never plain `<div>` with click handlers.

## 2024-12-22 - Interactive List Item Best Practices
**Learning:** For lists of selectable items (like command history), proper accessibility requires:
1. Semantic HTML: Use `<button>` elements, not `<div>` with click handlers
2. Focus management: Return focus to the primary interaction point after selection
3. ARIA attributes: Use `aria-expanded` and `aria-controls` on toggles
4. Visual feedback: Provide clear focus rings and hover states
5. Keyboard navigation: Support both mouse and keyboard interaction patterns
**Action:** Audit all interactive lists and dropdowns to ensure they follow these patterns. Test with keyboard-only navigation.

## 2024-05-24 - Async Button Loading Patterns
**Learning:** Using `disabled` state alone for async actions provides insufficient feedback. Users need visual confirmation that their action is being processed.
**Action:** Implement a dual-state button pattern:
1. Save original content on loading start
2. Inject accessible spinner (SVG + `aria-hidden`)
3. Add `aria-busy="true"`
4. Restore content on completion

## 2024-05-25 - Responsive Content Duplication
**Learning:** When creating mobile-specific views by duplicating content (like a sidebar), simply cloning HTML nodes creates duplicate IDs, breaking JavaScript logic that relies on `getElementById`.
**Action:** When creating responsive duplicates, ensure unique IDs for the mobile versions (e.g., prefixing with `mobile-`) and update state management logic to target both the desktop and mobile elements.

## 2024-05-25 - Skip Links in Application Shells
**Learning:** In application-like interfaces with persistent headers/sidebars, a "Skip to Main Content" link is critical because the "main content" (e.g., the narrative feed) isn't just the first heading, but often buried inside a layout.
**Action:** Always include a Skip Link that targets the dynamic content container, ensuring it is the very first focusable element for keyboard users.

## 2024-05-25 - Autocomplete Accessibility Patterns
**Learning:** Autocomplete suggestions should be interactive elements (buttons/options) not static divs, to support keyboard navigation and screen readers. When implementing a simple dropdown, ensure items are focusable.
**Action:** Use `<button>` elements for simple suggestion lists, or `role="option"` inside `role="listbox"` for complex ones.

## 2026-01-28 - Autocomplete Keyboard Navigation Patterns
**Learning:** Autocomplete components often break keyboard flow if they don't explicitly handle focus transfer. Users expect `ArrowDown` to move from the input to the suggestions list, and `Escape` to dismiss it without losing focus.
**Action:** When implementing custom autocomplete, explicitly handle `ArrowDown` (input -> first item), `ArrowUp` (first item -> input), and `Escape` (close + focus input).
