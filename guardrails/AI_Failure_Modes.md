# 🤖 AI Failure Modes Log

This document tracks recurring issues when using AI/LLMs (Cursor, Claude, Gemini, Kilo, Cline, Codex, ChatGPT).  
Entries are automatically appended from logs and stored in SQLite (`ai_failures.sqlite`).

---

| Timestamp | Tool   | Category       | Issue                          | Context                  | Log File |
|-----------|--------|----------------|--------------------------------|--------------------------|----------|
| 2025-09-29 07:50 | Cursor | JWT/Auth       | Token refresh missing          | eSalary authentication   | ai_session_20250929_072833.log |
| 2025-09-29 07:51 | Claude | .NET Code      | Broke DI in UserService.cs     | Smart Stub Generator      | ai_session_20250929_072833.log |
| 2025-09-29 07:52 | Gemini | Angular DI     | Missing TranslateService mock  | Angular unit tests        | ai_session_20250929_072833.log |
| 2025-09-29 07:53 | Cursor | File Overwrite | Random )))))))) characters     | File overwrite detected   | ai_session_20250929_072833.log |
| 2025-09-29 07:54 | Claude | Environment    | Suggested Node.js 20 instead of 18 | npm install troubleshooting | ai_session_20250929_072833.log |
