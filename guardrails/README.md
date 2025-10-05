# 📂 Guardrails

This folder contains enforced development, security, and design standards for all projects.  
It ensures consistency, professionalism, and compliance across code, AI/LLM usage, and UX/UI design.

---

## 📑 Files Overview

- **bpsbs.md**  
  Backend & DevSecOps standards (Best Practices & Standards by Sami Ben Salah).  
  Covers backend-first workflow, testing, pipelines, compliance, and security.

- **AI_Guardrails.md**  
  Rules for using AI/LLMs safely and productively.  
  Defines prompts, incremental edits, test coverage enforcement, and compliance rules.

- **UX_UI_Guardrails.md**  
  UX/UI consistency & design standards.  
  Prevents cluttered layouts, ambiguous menus, scattered buttons, and accessibility gaps.

- **AI_Failure_Modes.md**  
  Auto-updated log of recurring AI/LLM issues (JWT errors, DI problems, environment mismatches, etc.).  
  Supports audits and team retrospectives.

- **AI_Troubleshooting_Guide.md**  
  Common AI/LLM pain points with example prompts to fix or prevent them.

- **ai_failures.sqlite**  
  SQLite database storing structured records of AI/LLM failures.  
  Used by `log_ai_failures.py` and `analyze_failures.py` to track, classify, and export issues.

---

## 🔧 How to Use
1. Inject **bpsbs.md**, **AI_Guardrails.md**, and **UX_UI_Guardrails.md** into AI sessions (Cursor, Claude, Gemini, etc.) before coding.  
2. Run **log_ai_failures.py** to parse session logs and update `ai_failures.sqlite` + `AI_Failure_Modes.md`.  
3. Run **analyze_failures.py** for quick reports and auto-refresh of Markdown logs.  
4. Use these files as **non-negotiable standards** for all repos.  
5. Update guardloops after retrospectives and audits.

---

## ✅ Benefits
- Ensures **professional, user-friendly, and compliant apps**.  
- Prevents AI from generating **barebones or confusing outputs**.  
- Provides a **living knowledge base** of what fails and how to fix it.  
- Makes audits, onboarding, and team alignment seamless.

---
