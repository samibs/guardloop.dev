# 🤖 AI/LLM Guardrails & Best Practices (BPSBS)

This document defines how AI/LLMs (Cursor, Claude, Gemini, Kilo, Cline, Codex, ChatGPT) must be used in development.  
It combines a **one-page enforcement checklist** with **best practices and recommendations**.

---

## 📝 One-Page Guardrail Checklist (Feed to AI Before Coding)

### Implementation Rules
- Always implement features in ALL 3 layers: Database, Backend, Frontend.
- Add debug/troubleshoot modules with logging and error handling.
- Authentication must include MFA + Azure AD + local emergency admin.
- RBAC and audit logging required in every request.
- Provide exports (CSV, PDF, XLSX) for data tables with timestamps + watermark.

### Testing Rules
- Generate unit tests with 100% coverage (fail build if <100%).
- Stub/mocks for external dependencies (DB, ApiService, TranslateService).
- Add E2E tests for all features: every button, link, workflow.
- Use incremental edits → never rewrite entire files unless asked.

### Workflow Rules
- Respect existing repo structure and file names. No renaming or rewriting unrelated sections.
- Always confirm compatibility with: Node v18.20.7, Python 3.12, .NET 8, Angular 17.
- Show minimal diffs for changes; preserve existing working logic.
- Include tooltips, dark mode, filters, and export buttons in UIs.

### Compliance & Security
- GDPR/ISO features should be drafted but marked as “manual validation required”.
- Panic button + retention policies (7, 30, 90, 180, 365 days).
- Logs must be auditable and exportable (CSV/PDF).
- Never skip compliance or assume security is implicit.

### Documentation
- Update README and wiki after every feature.
- Add Mermaid/D3.js diagrams for workflows and CI/CD pipelines.
- Document deviations in Decision Logs.

### Enforcement
- `bpsbs.md` is LAW → all code must comply.
- Reject vague prompts → ask for file, path, framework, and expected behavior.
- Always run Implement → Test → Iterate cycle.

---

## 🔎 Best Practices & Recommendations

### 1. Treat AI as Drafting, Not Source of Truth
- AI is good for scaffolding, testing ideas, and generating boilerplate.
- It is weak at maintaining state, compliance, and complete correctness.
- Use AI like a junior dev → you are the senior architect.

### 2. Automate Enforcement
- Use SpecCTRL to enforce guardloops (`bpsbs.md`, `AI_Guardrails.md`).
- Pipelines must fail on <100% coverage or failed scans (SAST/DAST).
- Every repo must include `/health`, `/version`, `/metrics`, and an Admin module.

### 3. Anchor Context Every Session
- Always provide repo tree, exact file path, framework + version.
- Ask for incremental diffs, never full rewrites.

### 4. Security & Compliance Are Mandatory
- MFA + Azure AD + emergency admin = default stack.
- Security modules must be reusable and dropped into all apps.
- GDPR/ISO compliance requires manual validation.

### 5. Engineer Prompts Like Requirements
- Always specify: file path, expected behavior, test coverage, framework.
- Include test and security requirements in every prompt.

### 6. Enforce UX Standards
- Require dark mode toggle, status badges, tooltips, export buttons, collapsible panels.
- Don’t accept “barebones” UIs.

### 7. Use AI Where It Shines
- Boilerplate generation (tests, schemas, pipelines).
- Documentation (README, wikis, diagrams).
- Translating logic across stacks (Python ⇔ .NET ⇔ Angular).
- Rapid prototyping (to refine manually later).

### 8. Adopt AI-First QA Mindset
- Ask AI to find failure paths and edge cases.
- Use AI for test coverage suggestions as much as for coding.

---

## ✅ Final Rule
**AI output is always a draft.  
`bpsbs.md` + `AI_Guardrails.md` = law.  
Implement → Test → Iterate → Document.**

---
