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

## 2024-12-24 - Async Button State Management
**Learning:** When adding loading states to buttons, always guard against other event listeners (like 'input' events) resetting the button's disabled state while the async operation is still in progress.
**Action:** Use a central `isLoading` flag to coordinate state changes between async operations and UI event listeners.
