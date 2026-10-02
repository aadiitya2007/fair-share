# Fair Share UI/UX Principles Guide

This document outlines the design psychology and laws used to rebuild the Fair Share application. Use this reference during your viva to explain *why* the UI was built this way.

## 1. Gestalt Principles
* **Proximity:** In the group and dashboard pages, related elements (e.g., a member's name, avatar, and what they owe) are tightly grouped into a single "Balance Row." The space between rows is larger than the space between elements inside a row.
* **Similarity:** All primary actions (Login, Add Expense, Settle Up) share the same `btn-primary-custom` gradient and pill shape, signalling to the user that they perform comparable major actions.
* **Common Region:** We use the `.surface-card` class to encapsulate distinct functional areas (e.g., "Money to Collect" vs. "Money to Pay"). Borders and shadows create a distinct container.
* **Figure/Ground:** When modals open, the `backdrop-filter: blur(4px)` dims and blurs the background. In Dark Mode, raised surfaces (modals) use `--bg-raised`, a lighter shade of indigo to appear "closer" to the user than the `--bg-app`.
* **Continuity & Alignment:** The layout follows a strict Bootstrap 12-column grid. All financial numbers utilize `font-variant-numeric: tabular-nums` (tabular lining) and are right-aligned to allow the eye to easily scan down columns.

## 2. Interaction Laws
* **Fitts's Law:** Target sizes must be large and easy to click. All primary buttons are large pills (`px-5 py-3`), and mobile users get a massive 56x56px Floating Action Button (FAB) in the bottom-right corner for their thumb.
* **Hick's Law:** The number of choices minimizes cognitive load. On the dashboard, we limit choices to two primary actions (Add Member, Add Expense) instead of burying the user in settings.
* **Miller's Law:** Humans can keep ~7 items in working memory. We chunked the interface into logical blocks (Header, My Debts, Chart, History).
* **Jakob's Law:** Users expect your app to work like other apps. We copied the mental model of *Splitwise*—red for owe, green for get, a central dashboard, and a similar exact/percentage split modal.
* **Aesthetic-Usability Effect:** Users perceive aesthetically pleasing designs as more usable. The new fluid animations, deep indigo/soft gradients, and staggered fade-ups create a polished, forgiving feel.

## 3. Nielsen's Heuristics
* **Visibility of System Status:** Added a top loading progress bar when clicking links, and all buttons change to a disabled spinner state instantly upon form submission.
* **Error Prevention:** Forms use HTML5 validation. On error, the form physically shakes (using CSS `@keyframes shakeX`) to catch the user's attention before a bad request is sent. Buttons disable after one click to prevent double-charging.
* **Recognition rather than Recall:** The Chart.js widget visually breaks down expenses so users don't have to mental-math their category spending. Avatars use the first letter of names to instantly identify group members.
