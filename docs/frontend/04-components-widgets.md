# Components and Widgets Specification

**PLAGIX v1.0**  
**Last updated:** 21 November 2026

---

## UI Component Library (shadcn/ui + Tailwind)

PLAGIX uses **shadcn/ui** built on top of Tailwind CSS and Radix UI primitives.

### Core Components
1. **Buttons:** Primary, Secondary, Destructive, Ghost, Outline, Link.
2. **Cards:** Container for content sections with header, title, description, content, and footer.
3. **Badges:** Status indicators (Success, Warning, Destructive, Neutral).
4. **Dialogs & Modals:** For confirmations, overrides, and detail views.
5. **Dropdown Menus:** Context actions for evaluations and submissions.
6. **Tabs:** Switching between views (e.g., Answer vs. Similarity Matches).
7. **Tables:** Data grids with sorting, filtering, and pagination (TanStack Table).
8. **Form Controls:** Input, Textarea, Select, Checkbox, Slider.
9. **Tooltips:** Explanatory text for icons and truncated titles.
10. **Toast Notifications:** Success, warning, and error alerts (Sonner).

---

## Dashboard Widgets

1. **Evaluation Summary Widget:** Total submissions, relevant answers count, high-similarity flag count, average class score.
2. **Processing Progress Widget:** Multi-stage progress bar with live polling status.
3. **Similarity Risk Widget:** Highlighted top 5 highest similarity pairs in the batch.
4. **Relevance Distribution Chart:** Donut chart showing breakdown of Relevant, Partially Relevant, Off-topic, and Uncertain answers (Recharts).

---
