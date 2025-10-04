# 🎨 UX/UI Guardrails

This document defines professional, user-centered design rules to guide AI/LLM-generated UIs.  
Its goal is to prevent cluttered, confusing, or unprofessional designs by enforcing consistent, accessible, and appealing UX standards.

---

## 1. Navigation & Menus
- Use **explicit, descriptive menu names** (no vague “Stuff” or “More” labels).  
- **Max 2 levels** of navigation (primary + secondary).  
- **Consistent placement**: sidebar for modules, topbar for global actions.  
- Avoid too many menus — group related features logically.  
- Highlight **active menu item** clearly.

---

## 2. Layout & Structure
- Apply a **clear visual hierarchy** (titles > subtitles > content > footnotes).  
- Limit primary actions per screen: **1–2 CTAs max**.  
- Place buttons in **predictable locations**:  
  - Primary action → bottom-right or top-right.  
  - Secondary actions → next to or below primary.  
- Avoid overcrowding: **≤7 interactive elements per screen** (reduce cognitive load).  
- Use **grid-based layouts** with consistent spacing (8px scale).

---

## 3. Buttons & Interactive Elements
- Use **action-oriented labels**: e.g., “Save Report” instead of “OK.”  
- Avoid generic icons without text (always label buttons).  
- **Do not scatter buttons** randomly — group them by context.  
- Provide **hover/click feedback** (color change, ripple, etc.).  
- Place destructive actions (Delete, Reset) away from primary CTAs and add confirmation dialogs.

---

## 4. Visual Design
- Maintain **consistent color palette** (max 4 primary colors).  
- Use **WCAG 2.1 AA contrast** for text and UI elements.  
- Ensure adequate **white space** between groups.  
- Keep typography consistent (max 2 fonts, clear hierarchy).  
- Avoid excessive shadows, gradients, or animations.

---

## 5. Accessibility & Responsiveness
- Support **keyboard navigation** and screen readers (ARIA roles).  
- Interactive elements ≥44×44px for touch targets.  
- Ensure proper **contrast ratios** for text and buttons.  
- Design **mobile-first**, then scale up to desktop.  
- Test breakpoints: `sm`, `md`, `lg`, `xl` for layout consistency.

---

## 6. Feedback & States
- Always provide feedback for actions:  
  - Success → green check or toast.  
  - Error → red inline message with details.  
  - Loading → spinner/skeleton, disable duplicate clicks.  
- Preserve user input on error states (don’t clear forms).  
- Add **undo** option for destructive actions.

---

## 7. Information Architecture
- Group related features together — avoid scattering.  
- Keep labels **short, explicit, consistent**.  
- Provide search for large datasets.  
- Use collapsible sections or tabs to reduce clutter.  
- Default view should show the **most common tasks first**.

---

## 8. Export & Utilities
- Exports (CSV, PDF, XLSX) should be **always visible** with labeled buttons + icons.  
- Add tooltips for advanced features.  
- Provide filtering and sorting for lists/grids.  
- Keep utility buttons (refresh, settings) grouped in top-right corners.

---

## 9. Quick Wins to Enforce
- One clear **primary CTA per screen**.  
- Explicit menu names, no ambiguity.  
- Reduce clutter → collapse rarely used options.  
- Buttons grouped logically, never floating without context.  
- Consistent dark/light mode support.  
- Add tooltips and status badges to reduce confusion.

---

## 10. Enforcement Rules
- Reject vague AI output: enforce **explicit menu names + proper hierarchy**.  
- If >7 buttons appear on one screen → redesign.  
- If menus appear in multiple locations inconsistently → consolidate.  
- If buttons have no labels → add descriptive text.  
- If layout feels cluttered → reorganize into tabs/collapsible panels.

---

✅ This file (`UX_UI_Guardrails.md`) must be injected into AI/LLM sessions before generating UIs.  
It ensures output is professional, user-friendly, accessible, and visually consistent.

---
