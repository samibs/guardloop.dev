#!/usr/bin/env python3
"""Generate core and specialized guardrail files"""

from pathlib import Path

GUARDRAILS_PATH = Path.home() / ".guardrail" / "guardrails"

def create_core_always():
    """Create core/always.md - Universal rules for ALL code tasks (500 tokens max)"""
    content = """# Core Always Rules

## Universal Requirements (ALL Code Tasks)

### 3-Layer Architecture (Mandatory)
- Every feature: Database → Backend → Frontend
- No partial implementations accepted
- Backend-first approach: Schema + APIs before UI

### Testing Requirements
- 100% test coverage mandatory (fail build if <100%)
- Unit tests for all functions
- E2E tests for all user workflows
- Mocks/stubs for external dependencies

### Security Baseline
- MFA + Azure AD for authentication
- RBAC (role-based access control) required
- Comprehensive audit logging on all actions
- Input validation and sanitization

### Code Quality
- Incremental edits only (no full file rewrites)
- Follow existing repo structure and conventions
- Debug logging at critical points
- Error handling with try/catch blocks

### Documentation
- Update README and wiki after changes
- Include code comments for complex logic
- Mermaid/D3.js diagrams for workflows
- Document deviations in Decision Logs

### Compliance
- GDPR/ISO compliance features included
- Data retention policies (7, 30, 90, 180, 365 days)
- Panic button for data deletion
- Export functionality (CSV, PDF, XLSX) with timestamps

### Workflow
- Implement → Test → Iterate cycle
- Reject vague specifications (demand precision)
- Respect framework versions (Node 18.20.7, Python 3.12, .NET 8)
- Preserve existing working logic

### Enforcement
- bpsbs.md compliance is mandatory
- Features not "done" until: DB + Backend + Frontend + Tests + Docs
- No shortcuts or workarounds allowed
"""

    (GUARDRAILS_PATH / "core" / "always.md").write_text(content)
    print("✅ Created core/always.md")


def create_security_baseline():
    """Create core/security_baseline.md (300 tokens max)"""
    content = """# Security Baseline

## Core Security Requirements

### Authentication
- MFA + Azure Active Directory (primary)
- Local emergency admin account (fallback)
- Session management with secure tokens

### Authorization
- RBAC with defined roles: developer, manager, CISO, admin
- Least privilege principle
- Permission checks on all endpoints

### Audit & Logging
- Log all authentication attempts
- Track all data access and modifications
- Exportable audit trails (CSV/PDF)
- Real-time security alerts

### Data Protection
- Input sanitization on all user data
- SQL injection prevention
- XSS/CSRF protection
- Secrets stored securely (never hardcoded)

### Compliance
- GDPR data handling
- ISO 27001/27002 alignment
- Panic button for data deletion
- Data retention policies enforced
"""

    (GUARDRAILS_PATH / "core" / "security_baseline.md").write_text(content)
    print("✅ Created core/security_baseline.md")


def create_testing_baseline():
    """Create core/testing_baseline.md (300 tokens max)"""
    content = """# Testing Baseline

## Core Testing Requirements

### Unit Tests
- 100% coverage mandatory (fail build if <100%)
- Test all functions and methods
- Mock external dependencies (DB, APIs, services)
- Fast execution (<5 seconds total)

### E2E Tests
- Cover all user workflows
- Test every button, link, form
- Cypress/Playwright (frontend)
- Postman/Newman (backend APIs)

### Test Structure
- Arrange-Act-Assert pattern
- Clear test names describing scenarios
- Edge cases and error paths tested
- Regression tests for bug fixes

### CI/CD Integration
- Unit tests run on every commit
- E2E tests on staging before deploy
- Coverage reports generated
- Fail pipeline on test failures

### Requirements
- Tests documented with examples
- Mock data realistic and comprehensive
- Performance tests for critical paths
- Security tests for auth/authz flows
"""

    (GUARDRAILS_PATH / "core" / "testing_baseline.md").write_text(content)
    print("✅ Created core/testing_baseline.md")


def create_specialized_auth_security():
    """Create specialized/auth_security.md (600 tokens max)"""
    content = """# Authentication & Security

## Detailed Security Implementation

### MFA + Azure AD Integration
- Azure Active Directory as primary IdP
- Multi-factor authentication mandatory
- Support TOTP, SMS, authenticator apps
- Device trust and conditional access policies

### Local Emergency Admin
- Fallback admin account with full access
- Secure password storage (bcrypt/Argon2)
- Rate limiting on login attempts
- Account lockout after failed attempts

### RBAC Implementation
**Roles:**
- Developer: code access, limited admin
- Manager: team oversight, reporting
- CISO: security audit, compliance review
- Admin: full system access

**Permission Model:**
- Resource-based permissions
- Hierarchical role inheritance
- Dynamic permission evaluation
- Audit trail for permission changes

### Session Management
- JWT tokens with refresh mechanism
- Session timeout (15 min idle, 8 hr max)
- Concurrent session limits
- Secure cookie settings (HttpOnly, Secure, SameSite)

### Security Headers
- Content-Security-Policy
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security

### Compliance Features
- Panic button: immediate data deletion
- Data retention policies configurable
- Export user data (GDPR right to portability)
- Consent management and tracking

### Monitoring & Alerts
- Failed login attempts tracking
- Suspicious activity detection
- Real-time security event notifications
- Integration with SIEM systems
"""

    (GUARDRAILS_PATH / "specialized" / "auth_security.md").write_text(content)
    print("✅ Created specialized/auth_security.md")


def create_specialized_database_design():
    """Create specialized/database_design.md (600 tokens max)"""
    content = """# Database Design

## Schema Design Standards

### Normalization
- 3NF minimum for transactional data
- Denormalization only for proven performance needs
- Document all denormalization decisions

### Constraints & Integrity
- Primary keys on all tables (UUID or BIGINT)
- Foreign keys with CASCADE/RESTRICT rules
- NOT NULL on required fields
- CHECK constraints for data validation
- UNIQUE constraints where appropriate

### Indexing Strategy
- Index all foreign keys
- Composite indexes for common queries
- Covering indexes for performance-critical queries
- Monitor index usage and remove unused

### Audit Tables
- Created_at, updated_at timestamps
- Created_by, updated_by user tracking
- Soft deletes with deleted_at, deleted_by
- Version history for critical records

### Migration Management
- Versioned migration scripts
- Rollback scripts for all migrations
- Test migrations on staging first
- Seed data for development/testing

### Performance
- Query optimization for <100ms response
- Connection pooling configured
- Read replicas for heavy read loads
- Partitioning for large tables

### Security
- Encrypted sensitive fields (PII, PCI)
- Row-level security policies
- Database user permissions (least privilege)
- SQL injection prevention (parameterized queries)

### Backup & Recovery
- Daily automated backups
- Point-in-time recovery capability
- Backup verification and testing
- Disaster recovery plan documented
"""

    (GUARDRAILS_PATH / "specialized" / "database_design.md").write_text(content)
    print("✅ Created specialized/database_design.md")


def create_specialized_api_patterns():
    """Create specialized/api_patterns.md (600 tokens max)"""
    content = """# API Patterns

## RESTful API Standards

### Endpoint Design
- Nouns for resources (not verbs): `/users`, `/products`
- Consistent naming: kebab-case or snake_case
- Versioning: `/api/v1/resource`
- Hierarchical relationships: `/users/{id}/orders`

### HTTP Methods
- GET: retrieve (idempotent, cacheable)
- POST: create new resource
- PUT: full update (idempotent)
- PATCH: partial update
- DELETE: remove resource

### Request/Response
**Request:**
- JSON body for POST/PUT/PATCH
- Query params for filtering/pagination
- Headers for auth, content-type
- Request validation with schemas

**Response:**
- Consistent structure: `{data, meta, errors}`
- HTTP status codes: 2xx success, 4xx client error, 5xx server error
- Error details: code, message, field
- Pagination: offset/limit or cursor-based

### Authentication & Authorization
- Bearer tokens in Authorization header
- API keys for service-to-service
- OAuth 2.0 for third-party integrations
- Permission checks on every endpoint

### Validation & Error Handling
- Input validation with detailed errors
- Business logic validation
- Rate limiting (per user, per IP)
- Graceful degradation

### Documentation
- OpenAPI/Swagger specs
- Example requests and responses
- Authentication requirements
- Error codes documented

### Performance
- Response time <200ms for GET
- Compression (gzip/brotli)
- Caching headers (ETag, Cache-Control)
- Database query optimization

### Health & Monitoring
- `/health`: liveness check
- `/ready`: readiness check
- `/metrics`: Prometheus metrics
- `/version`: API version info

### Security
- HTTPS only (TLS 1.2+)
- CORS configuration
- Input sanitization
- SQL injection prevention
- Rate limiting and throttling
"""

    (GUARDRAILS_PATH / "specialized" / "api_patterns.md").write_text(content)
    print("✅ Created specialized/api_patterns.md")


def create_specialized_ui_accessibility():
    """Create specialized/ui_accessibility.md (600 tokens max)"""
    content = """# UI Accessibility

## WCAG 2.1 AA Compliance

### Semantic HTML
- Use proper HTML elements (`<button>`, `<nav>`, `<main>`)
- Headings hierarchy (h1 → h6)
- Landmarks for page regions
- Lists for grouped content

### ARIA Labels
- `aria-label` for icon buttons
- `aria-describedby` for help text
- `aria-live` for dynamic updates
- `role` attributes when needed

### Keyboard Navigation
- All interactive elements keyboard accessible
- Logical tab order
- Focus indicators visible
- Escape key closes modals/menus

### Screen Reader Support
- Alt text for images
- Form labels associated with inputs
- Error messages announced
- Status updates communicated

### Visual Design
- Color contrast ≥4.5:1 (text)
- Color contrast ≥3:1 (UI components)
- Don't rely on color alone
- Font size ≥16px base

### Responsive Design
- Mobile-first approach
- Touch targets ≥44x44px
- Viewport meta tag configured
- Breakpoints: 320px, 768px, 1024px, 1440px

### Forms & Validation
- Clear labels and instructions
- Error messages specific and helpful
- Success confirmation visible
- Required fields marked clearly

### Interactive Elements
- Clear button labels (no "OK", "Submit" alone)
- Link text descriptive (no "click here")
- Loading states indicated
- Disabled states clear

### Dark Mode
- Color scheme detection
- Manual toggle provided
- Consistent contrast in both themes
- Test all components in both modes

### UX Best Practices
- Max 7 interactive elements per screen
- Tooltips for complex features
- Export buttons for data tables
- Filters and search for long lists
- Collapsible panels for dense content

### Testing
- Automated accessibility scans (axe, Lighthouse)
- Manual keyboard testing
- Screen reader testing (NVDA, JAWS)
- Color contrast validation
"""

    (GUARDRAILS_PATH / "specialized" / "ui_accessibility.md").write_text(content)
    print("✅ Created specialized/ui_accessibility.md")


def create_specialized_compliance_gdpr():
    """Create specialized/compliance_gdpr.md (600 tokens max)"""
    content = """# GDPR Compliance

## Data Protection Requirements

### User Rights
**Right to Access:**
- Users can request their data
- Export in machine-readable format (JSON/CSV)
- Provided within 30 days

**Right to Erasure (Forget):**
- Panic button for immediate deletion
- Complete data removal across systems
- Confirmation and audit trail

**Right to Portability:**
- Export user data in standard format
- Include all personal data
- Transferable to other services

**Right to Rectification:**
- Users can update their information
- Corrections tracked in audit log
- Changes reflected immediately

### Consent Management
- Explicit consent before data collection
- Granular consent options
- Consent withdrawal mechanism
- Consent history tracked

### Data Retention
**Policies:**
- 7 days: temporary/cache data
- 30 days: operational data
- 90 days: analytics data
- 180 days: compliance data
- 365 days: legal/audit data

**Automation:**
- Scheduled deletion jobs
- Retention policy enforcement
- Audit trail of deletions
- Recovery period before final deletion

### Data Processing
- Minimize data collection (necessity principle)
- Encrypt sensitive data at rest
- Encrypt data in transit (TLS 1.2+)
- Pseudonymization where possible

### Security Measures
- Access controls (RBAC)
- Audit logging of all access
- Data breach detection
- Incident response plan

### Documentation
- Privacy policy clear and accessible
- Data processing records maintained
- Impact assessments for high-risk processing
- Third-party processor agreements

### Audit & Compliance
- Regular compliance audits
- Data protection officer (DPO) designated
- Breach notification within 72 hours
- Supervisory authority cooperation

### Technical Implementation
- Data encryption (AES-256)
- Secure key management
- Database-level row security
- Automated retention enforcement
- Comprehensive audit trails
"""

    (GUARDRAILS_PATH / "specialized" / "compliance_gdpr.md").write_text(content)
    print("✅ Created specialized/compliance_gdpr.md")


def create_specialized_deployment_ops():
    """Create specialized/deployment_ops.md (600 tokens max)"""
    content = """# Deployment & Operations

## CI/CD Pipeline Standards

### Pipeline Stages
1. **Orchestrator**: Entry point, branch detection
2. **Scan/Analyze**: SonarQube, linting, dependency checks
3. **Unit Tests**: 100% coverage requirement
4. **Build**: Compile, package, containerize
5. **E2E Tests**: Staging environment validation
6. **Deploy**: Staging → Production
7. **Audit**: Log deployment events

### Environment Configuration
**Staging:**
- Mirror production config
- Test data seeded
- E2E tests run here
- Blue-green deployment

**Production:**
- Zero-downtime deployment
- Health checks before traffic
- Automatic rollback on failure
- Canary releases for high-risk changes

### Health Monitoring
**Endpoints:**
- `/health`: Liveness probe
- `/ready`: Readiness probe
- `/metrics`: Prometheus metrics
- `/version`: Build and version info

**Metrics:**
- Response time (p50, p95, p99)
- Error rate and status codes
- Request throughput
- Resource usage (CPU, memory, disk)

### Logging
- Structured logging (JSON)
- Centralized aggregation (ELK, Splunk)
- Log levels: DEBUG, INFO, WARN, ERROR
- Request tracing (correlation IDs)
- PII redaction in logs

### Alerting
- Critical: Page on-call immediately
- High: Notify team channel
- Medium: Daily digest
- Low: Weekly report

**Alert Conditions:**
- Error rate >1%
- Response time >500ms (p95)
- Service down or unhealthy
- Resource usage >80%

### Disaster Recovery
- Automated backups (daily, weekly, monthly)
- Backup verification and testing
- Point-in-time recovery capability
- DR runbook documented
- RTO: <4 hours, RPO: <1 hour

### Scaling
- Horizontal auto-scaling rules
- Load balancer health checks
- Connection pooling
- Cache layer (Redis/Memcached)
- CDN for static assets

### Security Operations
- Vulnerability scanning (SAST/DAST)
- Dependency updates automated
- Secrets management (Vault, Azure Key Vault)
- Network policies and firewalls
- TLS/SSL certificate management

### Infrastructure as Code
- Terraform/CloudFormation templates
- Version controlled configs
- Environment parity
- Reproducible deployments
"""

    (GUARDRAILS_PATH / "specialized" / "deployment_ops.md").write_text(content)
    print("✅ Created specialized/deployment_ops.md")


def main():
    print("🎯 Task 1.2: Creating Core and Specialized Guardrails\n")

    print("Creating core guardrails...")
    create_core_always()
    create_security_baseline()
    create_testing_baseline()

    print("\nCreating specialized modules...")
    create_specialized_auth_security()
    create_specialized_database_design()
    create_specialized_api_patterns()
    create_specialized_ui_accessibility()
    create_specialized_compliance_gdpr()
    create_specialized_deployment_ops()

    print("\n✅ Task 1.2 Complete!")
    print(f"📁 Core files: {GUARDRAILS_PATH / 'core'}")
    print(f"📁 Specialized files: {GUARDRAILS_PATH / 'specialized'}")


if __name__ == "__main__":
    main()
