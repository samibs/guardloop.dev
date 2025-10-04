# 🤖 AI/LLM Troubleshooting & Guardrail Guide

This document captures the **pain points** detected when using AI/LLMs (Cursor, Kilo, Cline, Codex, Gemini, Claude, ChatGPT) and provides **prompts** to mitigate them.  
Based on real troubleshooting and lessons learned.

---

## 1. Code generation fragility
**Pain Point**: AI produces incomplete or inconsistent code (missing mocks, half-done endpoints, duplicates).

**Mitigation**: Enforce 3-layer rule, auto-add debug/test modules, never trust raw AI output.

**Prompt**:  
```
Implement this feature fully across Database, Backend, and Frontend. 
Add debug/troubleshoot modules and generate unit tests with 100% coverage. 
Do not skip validation or leave placeholders.
```

---

## 2. Context reset & forgetfulness
**Pain Point**: AI forgets scaffolding, changes file names, rewrites blocks.

**Mitigation**: Use memory bank, re-anchor context, enforce compliance with SpecCTRL.

**Prompt**:  
```
Here is my current repo structure and the file I am editing. 
Apply changes incrementally without renaming folders/files. 
Never rewrite unrelated sections.
```

---

## 3. Environment mismatch
**Pain Point**: AI suggests incompatible libraries/versions.

**Mitigation**: Check versions first, validate runtimes, use lockfiles.

**Prompt**:  
```
Before writing code, confirm compatibility with my current stack:
Node v18.20.7, Python 3.12, .NET 8, Angular 17. 
Only suggest libraries that work with these versions.
```

---

## 4. Pipeline & CI/CD blind spots
**Pain Point**: AI ignores test coverage thresholds, scans, or enforcement.

**Mitigation**: Add SonarQube/SAST/DAST hooks, enforce 100% coverage in YAML.

**Prompt**:  
```
Update my Azure DevOps pipeline to enforce:
- Unit test coverage at 100% (fail otherwise)
- SAST/DAST scans
- E2E tests before deployment
```

---

## 5. Security overlook
**Pain Point**: AI skips RBAC, MFA, audit logs.

**Mitigation**: Treat MFA + Azure AD + emergency admin as default.

**Prompt**:  
```
Add authentication with MFA + Azure AD as primary and a local emergency admin account as fallback. 
Include RBAC roles and audit logging in every request.
```

---

## 6. Ambiguity in prompts
**Pain Point**: Vague prompts lead to wrong stack or missing logic.

**Mitigation**: Always specify file path, behavior, framework, tests.

**Prompt**:  
```
Modify `frontend/app/components/Login.tsx` to add a login form 
with Azure AD + MFA. 
Include frontend validation, backend endpoint `/auth/login`, 
DB schema updates, and unit/E2E tests.
```

---

## 7. Dependency injection & mocking
**Pain Point**: AI doesn’t inject services correctly in tests.

**Mitigation**: Standardize mock templates, always stub DI.

**Prompt**:  
```
Generate unit tests for `UserService` in Angular. 
Stub TranslateService and ApiService using TestBed. 
Ensure no duplicate variable declarations and 100% coverage.
```

---

## 8. Overwriting good code
**Pain Point**: AI overwrites working logic with noise.

**Mitigation**: Never accept full replacements, request diffs.

**Prompt**:  
```
Show only the minimal diff for changes in `main.py`. 
Do not rewrite the full file. 
Preserve all existing working logic unless explicitly marked for change.
```

---

## 9. UX/UI superficiality
**Pain Point**: AI produces barebones UIs.

**Mitigation**: Define acceptance criteria (badges, filters, exports, dark mode).

**Prompt**:  
```
Enhance the dashboard UI with:
- Dark mode toggle
- Status badges (✅ OK, ⚠️ Warning, ❌ Error)
- Export buttons (CSV, PDF, XLSX)
- Collapsible panels with tooltips
```

---

## 10. Over-reliance on AI for compliance
**Pain Point**: AI suggests GDPR/ISO features but doesn’t enforce.

**Mitigation**: Keep compliance checklists manual, never outsource legal completeness.

**Prompt**:  
```
Draft GDPR/ISO 27001 features for this module. 
List mandatory items but mark them as "to be validated manually." 
Do not assume compliance without human confirmation.
```

---

# ✅ Summary Guardrails
1. Never trust AI blindly → test & verify.  
2. Always re-anchor context.  
3. Implement in 3 layers.  
4. Enforce 100% coverage + E2E tests.  
5. Security by default (MFA + Azure AD + local admin).  
6. Prompt clarity = output quality.  
7. Incremental edits only.  
8. UI must meet UX acceptance criteria.  
9. Compliance = manual confirmation.  
10. `bpsbs.md` is law.  

---
