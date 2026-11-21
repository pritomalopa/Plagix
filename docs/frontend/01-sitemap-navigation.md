# Sitemap and Navigation

**PLAGIX v1.0**  
**Last updated:** 21 November 2026

---

## Complete Sitemap

```
PLAGIX
│
├── / (Public)
│   ├── /login
│   ├── /register
│   ├── /forgot-password
│   └── /reset-password/:token
│
└── /dashboard (Protected)
    │
    ├── /dashboard (Evaluations List)
    │
    ├── /evaluations
    │   ├── /new (Create Evaluation)
    │   │
    │   └── /:id
    │       ├── /edit (Edit Evaluation)
    │       ├── /upload (Upload Submissions)
    │       ├── /processing (Processing Status)
    │       ├── /results (Results Dashboard)
    │       │   ├── /submissions/:submissionId (Submission Detail)
    │       │   └── /compare/:submissionAId/:submissionBId (Side-by-Side Comparison)
    │       ├── /grading (Grading Review)
    │       └── /reports (Generate & Download Reports)
    │
    ├── /settings
    │   ├── /profile (User Profile)
    │   ├── /account (Account Settings)
    │   └── /preferences (Evaluation Defaults)
    │
    └── /help
        ├── /getting-started
        ├── /faq
        └── /support
```

---

## Navigation Hierarchy

### Top-Level Navigation (Authenticated)

```
┌─────────────────────────────────────────────────────────────┐
│ [PLAGIX Logo]  Evaluations  Help       [User Menu] [Logout] │
└─────────────────────────────────────────────────────────────┘
```

**Primary Navigation Items:**
1. **Evaluations** (Dashboard home)
2. **Help** (Documentation and support)
3. **User Menu** (Dropdown)
   - Profile
   - Account Settings
   - Preferences
   - Logout

---

## Route Definitions

### Public Routes

| Route | Component | Purpose | Auth Required |
|-------|-----------|---------|---------------|
| `/` | Landing/Redirect | Redirect to /login or /dashboard | No |
| `/login` | LoginPage | Teacher authentication | No |
| `/register` | RegisterPage | New teacher account creation | No |
| `/forgot-password` | ForgotPasswordPage | Password reset request | No |
| `/reset-password/:token` | ResetPasswordPage | Password reset with token | No |

### Protected Routes (Require Authentication)

| Route | Component | Purpose | Breadcrumb |
|-------|-----------|---------|------------|
| `/dashboard` | DashboardPage | Evaluation list (home) | Dashboard |
| `/evaluations/new` | CreateEvaluationPage | Create new evaluation | Dashboard > New Evaluation |
| `/evaluations/:id/edit` | EditEvaluationPage | Edit evaluation details | Dashboard > [Eval Name] > Edit |
| `/evaluations/:id/upload` | UploadPage | Upload student submissions | Dashboard > [Eval Name] > Upload |
| `/evaluations/:id/processing` | ProcessingPage | Real-time processing status | Dashboard > [Eval Name] > Processing |
| `/evaluations/:id/results` | ResultsPage | Submission results dashboard | Dashboard > [Eval Name] > Results |
| `/evaluations/:id/results/submissions/:submissionId` | SubmissionDetailPage | Individual submission analysis | Dashboard > [Eval Name] > Results > [Student] |
| `/evaluations/:id/results/compare/:subAId/:subBId` | ComparisonPage | Side-by-side comparison | Dashboard > [Eval Name] > Results > Compare |
| `/evaluations/:id/grading` | GradingPage | Batch grading review | Dashboard > [Eval Name] > Grading |
| `/evaluations/:id/reports` | ReportsPage | Generate and download reports | Dashboard > [Eval Name] > Reports |
| `/settings/profile` | ProfilePage | User profile management | Settings > Profile |
| `/settings/account` | AccountPage | Account and security | Settings > Account |
| `/settings/preferences` | PreferencesPage | Evaluation defaults | Settings > Preferences |
| `/help/*` | HelpPages | Help documentation | Help > ... |

---

## Navigation Patterns

### 1. Dashboard → Create Evaluation Flow
```
Dashboard 
  ↓ [Create New Evaluation]
New Evaluation Form
  ↓ [Save & Continue]
Upload Submissions
  ↓ [Start Processing]
Processing Status
  ↓ [View Results] (auto-redirect when complete)
Results Dashboard
```

### 2. Results → Detail Drill-Down
```
Results Dashboard (Table View)
  ↓ [Click Student Row]
Submission Detail
  ↓ [View Comparison with Student X]
Side-by-Side Comparison
  ↓ [Back] or Breadcrumb
Results Dashboard
```

### 3. Review → Grade → Export Flow
```
Results Dashboard
  ↓ [Review Grades]
Grading Page
  ↓ [Approve & Finalize]
Reports Page
  ↓ [Download PDF/CSV]
File Download
```

---

## Breadcrumb Navigation

### Implementation
```tsx
// Example breadcrumb for: /evaluations/abc123/results/submissions/def456
Dashboard > Midterm Exam > Results > Alice Johnson
```

### Rules
1. Always show full path from Dashboard
2. Clickable ancestors for easy navigation
3. Current page is not clickable (plain text)
4. Truncate long evaluation titles (e.g., "Advanced Calculus Midte..." → tooltip on hover)
5. Use student labels, not IDs where possible

---

## Mobile Navigation

### Collapsed Menu (< 768px)
```
┌─────────────────────────────────┐
│ [☰]  PLAGIX      [User] [•••]  │
└─────────────────────────────────┘

[Tap ☰] → Slide-out drawer:
  - Dashboard
  - Help
  ───────────
  - Profile
  - Settings
  - Logout
```

### Tab Bar (Optional for mobile)
```
┌───────────────────────────────────┐
│ [Home] [Activity] [Profile] [+]  │
└───────────────────────────────────┘
```
**Decision:** Use hamburger menu only (simpler, consistent with desktop)

---

## Context-Sensitive Navigation

### Evaluation Context Bar
When inside an evaluation (`/evaluations/:id/*`), show persistent context bar:

```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Dashboard                                        │
│                                                            │
│ Midterm Exam - Calculus 101                              │
│ [Edit] [Upload] [Results] [Grading] [Reports]            │
└────────────────────────────────────────────────────────────┘
```

**Active tab styling:**
- Bold text
- Bottom border (primary color)
- Background tint

---

## Route Guards and Redirects

### Authentication Guard
```typescript
// Middleware: Check auth on protected routes
if (!isAuthenticated && route.startsWith('/dashboard')) {
  redirect('/login?redirect=' + encodeURIComponent(route))
}
```

### Post-Login Redirect
```typescript
// After successful login:
const redirectUrl = searchParams.get('redirect') || '/dashboard'
router.push(redirectUrl)
```

### Evaluation Status Guard
```typescript
// /evaluations/:id/results requires status: 'ready_for_review' or 'completed'
if (evaluation.status === 'created' || evaluation.status === 'uploading') {
  redirect(`/evaluations/${id}/upload`)
}

if (evaluation.status === 'processing') {
  redirect(`/evaluations/${id}/processing`)
}
```

### 404 Handling
```typescript
// Invalid evaluation ID or unauthorized access
if (!evaluation || evaluation.tenant_id !== user.tenant_id) {
  return <NotFoundPage />
}
```

---

## Deep Linking Support

### Shareable URLs
Teachers should be able to bookmark and share these URLs (within their tenant):

✅ **Shareable:**
- `/dashboard` - Dashboard home
- `/evaluations/:id/results` - Results for specific evaluation
- `/evaluations/:id/results/submissions/:submissionId` - Specific student

❌ **Not shareable (temporary state):**
- `/evaluations/:id/upload` - Upload is session-based
- `/evaluations/:id/processing` - Processing is transient

### Email Link Integration (Future)
```
Subject: PLAGIX - "Midterm Exam" processing complete

Your evaluation "Midterm Exam" has finished processing.

[View Results] → https://plagix.app/evaluations/abc123/results
```

---

## Navigation State Management

### Active Route Tracking
```typescript
// Use Next.js usePathname() hook
const pathname = usePathname()
const isActive = (path: string) => pathname.startsWith(path)

// Apply active styles
<Link className={isActive('/dashboard') ? 'active' : ''}>
  Dashboard
</Link>
```

### Unsaved Changes Warning
```typescript
// Warn before navigation if form has unsaved changes
useEffect(() => {
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (hasUnsavedChanges) {
      e.preventDefault()
      e.returnValue = ''
    }
  }
  window.addEventListener('beforeunload', handleBeforeUnload)
  return () => window.removeEventListener('beforeunload', handleBeforeUnload)
}, [hasUnsavedChanges])
```

---

## Keyboard Navigation

### Shortcuts (Future Enhancement)
| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Global search / command palette |
| `Ctrl/Cmd + N` | New evaluation |
| `Esc` | Close modal / drawer |
| `Tab` | Navigate focusable elements |
| `Shift + ?` | Show keyboard shortcuts |

---

## URL Query Parameters

### Common Patterns

**Pagination:**
```
/evaluations/:id/results?page=2&per_page=25
```

**Filtering:**
```
/evaluations/:id/results?status=high_similarity&relevance=off_topic
```

**Sorting:**
```
/evaluations/:id/results?sort=similarity_desc
```

**Search:**
```
/evaluations/:id/results?search=john
```

---

## Navigation Analytics

### Track Navigation Events
```typescript
// Track page views
trackPageView(pathname)

// Track navigation patterns
trackEvent('navigation', {
  from: previousPath,
  to: currentPath,
  method: 'click' | 'breadcrumb' | 'back_button'
})
```

### Useful Metrics
- Time spent per page
- Most common navigation paths
- Drop-off points in evaluation creation flow
- Back button usage (indicates confusion)

---

## References

- [Next.js App Router](https://nextjs.org/docs/app)
- [Next.js Middleware](https://nextjs.org/docs/app/building-your-application/routing/middleware)
- [React Router Patterns](https://reactrouter.com/en/main/start/overview)
