# GigForge — Scope Definition (v1.0)

> This document is the contract against scope creep. Any new feature idea goes here first, or it doesn't get built.

---

## In Scope 

### 🔴 MUST Have — v1 is not done without these

- Registration / login with JWT + bcrypt (US-01, US-02)
- Two user roles: `client`, `freelancer` (+ seeded `admin`)
- Profile view/update (US-03)
- Job CRUD with ownership rules (US-04, US-06)
- Public job browsing with pagination + filters (US-05)
- Bidding with business rules: one bid per job, open jobs only (US-07)
- Accept bid → contract creation + auto-reject other bids (US-10)
- Complete contract flow (US-11)
- Reviews: one per participant per contract (US-12)
- Alembic migrations
- Tests for every MUST feature, coverage ≥ 80%

---

### 🟡 SHOULD Have — planned, may slip if needed

- Avatar upload (image only, ≤ 5 MB)
- Job search: keyword, budget range, skills
- Skills many-to-many (user skills, job skills)
- Admin moderation endpoints (US-13)
- CI pipeline (GitHub Actions: lint + test)

---

### 🟢 COULD Have — only if time remains

- Email notifications via `BackgroundTasks` (bid received, bid accepted)
- Redis caching for hot job listings
- Rate limiting on auth endpoints
- Refresh tokens

---

## Explicitly OUT of Scope for v1

- ❌ Real payment processing (Stripe, etc.) — contracts are records only
- ❌ Real-time chat / WebSocket messaging
- ❌ Frontend UI — API-only project
- ❌ Email verification / password reset (planned v1.1)
- ❌ ML-based freelancer–job matching
- ❌ Multi-tenancy / organizations / teams

---

## Definition of Done — v1.0.0

- Every MUST item implemented, tested, and deployed
- Publicly accessible live URL
- CI green: lint + tests pass on `main`
- README with setup instructions, architecture diagram, and live URL
- Git tag `v1.0.0` + release notes

---

## Assumptions & Constraints

- Single developer, ~8 weeks part-time
- Free-tier hosting (Railway / Render / Fly.io) with managed PostgreSQL
- No real money moves through the system
- English-only content
- Single currency units (plain numbers)