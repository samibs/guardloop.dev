# BPSBS Developer Workflow & Standards

This document merges **Best Practices & Standards by (BPSBS)** and the **DevWorkflow playbook** into a single enforced guide for all projects.

---

## 1. Core principles
- Backend first: start with DB schema + APIs before UI.  
- Implement → Test → Iterate: no partial features; ship in full.  
- Cold-blooded logic: refuse vague specs, enforce precision.  
- Documentation as code: README, diagrams, test cases are mandatory.  
- Compliance-first: ISO 27001/27002, GDPR, audit logs, RBAC.  
- Security baked-in: MFA, Azure AD, local emergency admin.  
- All features implemented in 3 layers: Database → Backend → Frontend.  

---

## 2. Project structure
Every repo must include:

```
backend/
frontend/
modules/
scripts/
memory_bank/
docs/
logs/
```

Mandatory files:
- `.env.example`  
- `README.md`  
- `requirements.txt` / `package.json` / `.csproj`  
- `bpsbs.md` (this file)  

---

## 3. Feature implementation rule
Every new feature must include:
- Database schema updates (migration scripts, constraints, seed data).  
- Backend endpoints (FastAPI/.NET controllers with validation & logging).  
- Frontend UI (components, forms, grids, dashboards).  

❗ Features without all 3 layers are considered **incomplete**.  

---

## 4. Authentication & security
- **Primary**: MFA with Azure Active Directory integration.  
- **Fallback**: local emergency admin account with full access.  
- **Role-based access control (RBAC)**: developer, manager, CISO, admin, etc.  
- **Panic button**: full user data deletion on demand.  
- **Retention policies**: 7, 30, 90, 180, 365 days.  

---

## 5. Testing policy
- **Unit tests**  
  - 100% coverage (backend + frontend).  
  - Mocks for external services (DB, API, TranslateService, etc.).  
  - Fail build if coverage <100%.  

- **E2E tests**  
  - Cover every button, link, form, workflow.  
  - Cypress/Playwright (frontend) + Postman/Newman (backend).  
  - Simulate full workflows (login, data entry, export, error paths).  

- **CI/CD integration**  
  - Unit tests → coverage reports.  
  - E2E tests → run on staging before deploy.  
  - Vulnerability scans (SAST/DAST).  

---

## 6. Mandatory features in all apps
### Admin module
- API & infra health monitoring (`/health`, `/status`, `/metrics`, `/logs/recent`).  
- Config management (DB, SMTP, SFTP, AD, API keys).  
- Debug console (tooltips + toast notifications).  
- Audit logs & real-time alerts.  
- Real-time logs streaming.  

### Export & reporting
- PDF, CSV, XLSX for every data view.  
- Timestamp + watermark in all exports.  

### Documentation
- `README.md` quick start guide.  
- Mermaid/D3.js diagrams for workflows.  
- Azure DevOps Wiki integration.  

---

## 7. CI/CD pipelines
Pipelines must include:
1. Orchestrator (entry point).  
2. Scan/Analyze (SonarQube, lint, dependency checks).  
3. Unit Tests (fail under 100% coverage).  
4. Build/Publish.  
5. Deploy (staging → prod).  
6. Audit & Logs (append to SQLite/Elastic).  

---

## 8. Developer workflow
1. Scaffold project → use templates with health/version/log endpoints.  
2. Implement feature in all 3 layers (DB → API → UI).  
3. Write unit tests → ensure 100% coverage.  
4. Write E2E tests → validate user flows.  
5. Push code → pipeline enforces scans, tests, build, deploy.  
6. Update docs → diagrams, wikis, release notes.  

---

## 9. Enforced rules
- No feature is “done” until:  
  - Implemented in DB + Backend + Frontend.  
  - Covered by unit tests (100%).  
  - Covered by E2E tests.  
  - Documented in README + Wiki.  

- All apps must include:  
  - MFA + Azure AD auth.  
  - Local emergency admin.  
  - Admin module.  
  - Panic button.  

---

## 10. Governance & memory bank
- `bpsbs.md` is **law** → enforced by SpecCTRL/VS Code extension.  
- Any deviation must be documented in Decision Logs.  
- Project retrospectives update `bpsbs.md` with lessons learned.  

---
