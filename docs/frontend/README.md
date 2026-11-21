# Frontend Specification Overview

**PLAGIX v1.0**  
**Status:** Phase 0.3 - Frontend Planning  
**Last updated:** 21 November 2026

---

## Purpose

This document provides a comprehensive frontend specification for PLAGIX, a standalone academic answer evaluation and integrity SaaS platform. It defines the complete user interface, user experience, interaction patterns, and technical requirements for the Next.js-based teacher dashboard.

---

## Document Structure

This frontend specification is organized into the following documents:

1. **[Sitemap and Navigation](./01-sitemap-navigation.md)** - Complete site structure, navigation hierarchy, and routing
2. **[Page Specifications](./02-page-specifications.md)** - Detailed requirements for each page/screen
3. **[User Journeys](./03-user-journeys.md)** - End-to-end workflows and interaction flows
4. **[Components and Widgets](./04-components-widgets.md)** - Reusable UI components and dashboard widgets
5. **[File Upload Experience](./05-file-upload.md)** - ZIP, PDF, DOCX upload flows and validation
6. **[Processing and Progress](./06-processing-progress.md)** - Job status, progress indicators, error states
7. **[Results Presentation](./07-results-presentation.md)** - Relevance, similarity, and comparison UI
8. **[Grading and Review](./08-grading-review.md)** - Teacher review, override, and approval workflows
9. **[Reports and Export](./09-reports-export.md)** - Report generation and download UI
10. **[Design System](./10-design-system.md)** - Typography, colors, spacing, component library
11. **[Responsive Design](./11-responsive-design.md)** - Desktop, tablet, mobile layouts
12. **[Accessibility](./12-accessibility.md)** - WCAG 2.1 AA compliance requirements
13. **[API Contract](./13-api-contract.md)** - Frontend-to-backend API requirements

---

## Key Principles

### 1. **Standalone Evaluation Utility**
- PLAGIX is NOT an LMS
- No course management, class rosters, or attendance tracking
- Focus: Question → Upload → Analyze → Review → Export

### 2. **Teacher-Controlled Grading**
- All similarity and AI-writing signals are review aids, not automatic verdicts
- Teacher must approve all final marks
- Override capability with audit trail
- Explainable results with evidence

### 3. **Explainability First**
- Show why a submission was flagged
- Display matched passages with page/offset references
- Separate exact, lexical, and semantic similarity
- Never present AI detection as proof

### 4. **Progressive Disclosure**
- Dashboard shows high-level summary
- Drill-down reveals detailed evidence
- Filtering and search for large batches
- Collapsible sections for complex data

### 5. **Asynchronous Processing**
- Upload returns immediately, processing happens in background
- Real-time progress updates
- Clear status indicators (queued, processing, completed, failed)
- Retry failed operations

---

## Technology Stack

### Core Framework
- **Next.js 14+** with App Router
- **TypeScript** for type safety
- **React Server Components** where appropriate

### Styling
- **Tailwind CSS** for utility-first styling
- **shadcn/ui** for accessible component primitives
- **CSS Modules** for component-specific styles where needed

### State Management
- **React Context** for global state (auth, tenant)
- **TanStack Query (React Query)** for server state and caching
- **Zustand** for complex client state if needed

### Forms and Validation
- **React Hook Form** for form management
- **Zod** for schema validation
- **shadcn/ui Form** components

### Data Visualization
- **Recharts** for charts and analytics
- **React Table (TanStack Table)** for data tables
- **D3.js** for complex similarity matrix visualization

### File Upload
- **react-dropzone** for drag-and-drop
- **tus** protocol for resumable uploads (large files)

### Utilities
- **date-fns** for date formatting
- **clsx** for conditional class names
- **lucide-react** for icons

---

## Browser Support

### Desktop
- Chrome/Edge 100+ ✅ (Primary)
- Firefox 100+ ✅
- Safari 15+ ✅

### Mobile
- iOS Safari 15+ ✅
- Chrome Android 100+ ✅

### Not Supported
- Internet Explorer ❌
- Browsers without ES2020 support ❌

---

## Performance Targets

| Metric | Target | Critical Path |
|--------|--------|---------------|
| First Contentful Paint (FCP) | < 1.5s | All pages |
| Largest Contentful Paint (LCP) | < 2.5s | Dashboard, Results |
| Time to Interactive (TTI) | < 3.5s | All pages |
| Cumulative Layout Shift (CLS) | < 0.1 | All pages |
| Bundle Size (First Load JS) | < 200 KB | Critical pages |

---

## Security Considerations

### Authentication
- JWT tokens stored in httpOnly cookies
- CSRF protection on all state-changing operations
- Automatic token refresh
- Secure session timeout (30 minutes idle)

### Authorization
- All API calls include tenant context
- Client-side route guards
- Server-side authorization checks
- No sensitive data in URL parameters

### Data Protection
- No student answers logged to console
- Sanitize file names and user input
- Content Security Policy (CSP) headers
- XSS protection via React's escaping

---

## Localization (Future)

### MVP Language
- English (US) only

### Post-MVP
- Bengali (Bangladesh) - High priority
- Support for RTL languages in design system

---

## Analytics and Monitoring

### User Analytics
- Google Analytics 4 or Plausible (privacy-focused)
- Page views and navigation paths
- Evaluation creation funnel
- Upload success/failure rates

### Error Monitoring
- Sentry for client-side error tracking
- Source maps for production debugging
- User session replay for critical errors

### Performance Monitoring
- Core Web Vitals tracking
- API response time monitoring
- Client-side performance metrics

---

## Development Workflow

### Local Development
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

### Code Quality
- ESLint for linting
- Prettier for formatting
- TypeScript strict mode
- Husky pre-commit hooks

### Testing Strategy
- **Unit Tests:** Jest + React Testing Library
- **Integration Tests:** Playwright or Cypress
- **Accessibility Tests:** axe-core, WAVE
- **Visual Regression:** Chromatic or Percy

---

## Deployment

### Build Command
```bash
npm run build
```

### Deployment Targets
- **Development:** Vercel preview deployments
- **Staging:** Vercel staging environment
- **Production:** Vercel, Cloudflare Pages, or Netlify

### Environment-Specific Configuration
- API URL per environment
- Feature flags for gradual rollout
- Different analytics/monitoring keys

---

## Open Questions

### Resolved
1. ~~Use Next.js App Router or Pages Router?~~ → **App Router** (modern, RSC support)
2. ~~Client-side or server-side rendering?~~ → **Hybrid** (SSR for initial load, CSR for interactions)
3. ~~Global state management library?~~ → **React Query + Context** (minimal state library)

### Pending Review
1. **Real-time updates:** WebSockets vs. polling for processing progress?
   - **Recommendation:** Polling (simpler, more reliable, works with serverless)
2. **File upload approach:** Direct S3 upload vs. proxy through API?
   - **Recommendation:** API proxy for MVP (simpler auth, easier validation)
3. **Similarity matrix visualization:** Which library for N×N heatmap?
   - **Recommendation:** Recharts for small batches (<50), D3 for larger
4. **Offline support:** Should the app work offline?
   - **Recommendation:** No offline support in MVP (requires sync complexity)

---

## Success Criteria

### Phase 0.3 Exit Criteria
- [ ] All frontend specification documents completed
- [ ] Sitemap covers all MVP workflows
- [ ] Page wireframes and requirements defined
- [ ] Component inventory documented
- [ ] API contract defined with request/response schemas
- [ ] Design system documented
- [ ] Accessibility requirements specified
- [ ] Missing backend endpoints identified

### Phase 1 Frontend Implementation Ready
- [ ] Next.js project initialized
- [ ] shadcn/ui components configured
- [ ] Authentication flow designed
- [ ] Dashboard layout prototyped
- [ ] File upload flow designed
- [ ] Results presentation UI designed

---

## Next Steps

1. **Review Specification** - Validate against SRS and backend capabilities
2. **Identify API Gaps** - Document missing endpoints needed by frontend
3. **Create Wireframes** - Low-fidelity mockups for key screens
4. **Build Component Library** - Set up shadcn/ui and custom components
5. **Implement Authentication** - Login, registration, session management
6. **Build Dashboard** - Evaluation list and creation flow

---

## References

- [PLAGIX SRS v1.0](../PLAGIX_SRS_v1.0.pdf)
- [System Overview](../architecture/system-overview.md)
- [Data Model](../architecture/data-model.md)
- [Processing Pipeline](../architecture/processing-pipeline.md)
- [Phase Plan](../roadmap/phase-plan.md)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Next.js 14 Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
