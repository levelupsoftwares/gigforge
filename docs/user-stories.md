# GigForge — User Stories

## Sprint 1 — Authentication & Users

### US-01: Register an Account

**As a** visitor, **I want** to register with email, password, and role, **so that** I can start using the platform.

**Acceptance Criteria:**

- Valid data → `201` with user object without `password_hash`
- Duplicate email → `409` (FR-02)
- Password < 8 characters → `422`
- Role not in (`client`, `freelancer`) → `422`

**Maps to:** FR-01, FR-02  
**Tests:** `test_auth.py`

---

### US-02: Log In

**As a** registered user, **I want** to log in with email and password, **so that** I can receive a JWT token.

**Acceptance Criteria:**

- Correct credentials → `200` with `access_token` + `token_type`
- Wrong password → `401`
- Unknown email → `401` with the same message as wrong password to prevent user enumeration
- Token expires after the configured lifetime

**Maps to:** FR-03, FR-04  
**Tests:** `test_auth.py`

---

### US-03: Manage My Profile

**As a** logged-in user, **I want** to view and update my profile (full name, bio, hourly rate, skills), **so that** others know who I am.

**Acceptance Criteria:**

- `GET /api/v1/users/me` → `200` with my profile
- `PATCH /api/v1/users/me` updates fields → `200`
- Without token → `401`

**Maps to:** FR-05  
**Tests:** `test_users.py`

---

## Sprint 2 — Jobs

### US-04: Post a Job

**As a** client, **I want** to create a job posting with title, description, budget range, deadline, and required skills, **so that** freelancers can bid on it.

**Acceptance Criteria:**

- Valid data + JWT (`role=client`) → `201` with created job
- Missing/invalid token → `401`
- Freelancer tries to post → `403`
- `budget_max < budget_min` → `422` (FR-08)
- `deadline` in the past → `422` (FR-09)

**Maps to:** FR-07, FR-08, FR-09  
**Tests:** `test_jobs.py`

---

### US-05: Browse and Search Jobs

**As a** freelancer (or visitor), **I want** to browse open jobs filtered by keyword, budget range, and skills, **so that** I can find relevant work.

**Acceptance Criteria:**

- `GET /api/v1/jobs` without token → `200` (public browsing, FR-10)
- Only jobs with status `open` are returned
- `?search=python&min_budget=100&max_budget=500&skill=fastapi` filters correctly
- Pagination: `?page=1&size=20`
- Response includes `items`, `total`, `page`, and `size`
- `size > 100` → `422`

**Maps to:** FR-10  
**Tests:** `test_jobs.py`

---

### US-06: Update or Delete My Job

**As a** client, **I want** to edit or delete my own job posting, **so that** I can keep it accurate.

**Acceptance Criteria:**

- Owner updates → `200`
- Owner deletes → `204`
- Non-owner (even authenticated) → `403` (FR-11)
- Job not found → `404`

**Maps to:** FR-11  
**Tests:** `test_jobs.py`

---

## Sprint 3 — Bids & Contracts

### US-07: Place a Bid

**As a** freelancer, **I want** to bid on an open job with amount, cover letter, and delivery days, **so that** I can win the work.

**Acceptance Criteria:**

- Valid bid → `201`
- Second bid on the same job by the same user → `409` (FR-13)
- Bid on non-`open` job → `409` (FR-14)
- `amount <= 0` → `422` (FR-15)
- Client tries to bid → `403`

**Maps to:** FR-13, FR-14, FR-15  
**Tests:** `test_bids.py`

---

### US-08: Review Bids on My Job

**As a** client, **I want** to see all bids on my job, **so that** I can choose the best freelancer.

**Acceptance Criteria:**

- Owner requests bids → `200` paginated list
- Non-owner → `403` (FR-16)
- Job not found → `404`

**Maps to:** FR-16  
**Tests:** `test_bids.py`

---

### US-09: Track My Bids

**As a** freelancer, **I want** to see all my bids and their statuses, **so that** I know where I stand.

**Acceptance Criteria:**

- `GET /api/v1/bids/me` → `200` with my bids + statuses (FR-17)
- Without token → `401`
- User only receives their own bids

**Maps to:** FR-17  
**Tests:** `test_bids.py`

---

### US-10: Accept a Bid → Create Contract

**As a** client, **I want** to accept one bid on my job, **so that** a contract is created with that freelancer.

**Acceptance Criteria:**

- Owner accepts a pending bid on an open job → `201` + contract created (FR-18)
- All other pending bids on that job automatically become `rejected` (FR-19)
- Job status becomes `in_progress` (FR-12)
- Non-owner tries to accept → `403`
- Accepting a second bid on the same job → `409` (FR-20)
- Bid acceptance, contract creation, rejection of other bids, and job status update occur atomically
- If any part of the operation fails, the entire transaction is rolled back

**Maps to:** FR-12, FR-18, FR-19, FR-20  
**Tests:** `test_contracts.py`

---

## Sprint 4 — Completion, Reviews & Admin

### US-11: Complete a Contract

**As a** contract participant, **I want** to mark an active contract as completed, **so that** we can both leave reviews.

**Acceptance Criteria:**

- Participant marks `active` contract → `200`, status = `completed`
- Job status becomes `completed` (FR-12)
- Non-participant → `403`
- Completing an already completed contract → `409`

**Maps to:** FR-12, FR-21  
**Tests:** `test_contracts.py`

---

### US-12: Leave a Review

**As a** contract participant, **I want** to rate the other party (1–5) with an optional comment, **so that** the marketplace builds trust.

**Acceptance Criteria:**

- Participant on `completed` contract → `201` (FR-22)
- Client can review the freelancer
- Freelancer can review the client
- Second review by the same person on the same contract → `409`
- Review on non-`completed` contract → `422` (FR-23)
- Rating outside `1–5` → `422`
- `GET /api/v1/users/{id}/reviews` → list of their received reviews
- A user cannot review themselves
- A user must be a participant of the contract

**Maps to:** FR-22, FR-23  
**Tests:** `test_reviews.py`

---

### US-13: Admin Moderates Users & Jobs

**As an** admin, **I want** to list users, deactivate accounts, and close rule-violating jobs, **so that** the platform stays safe.

**Acceptance Criteria:**

- Admin: `GET /api/v1/admin/users` → `200`
- Admin: `PATCH /api/v1/admin/users/{id}/deactivate` → `200`
- Admin: `PATCH /api/v1/admin/jobs/{id}/close` → `200`
- Non-admin on any admin route → `403` (FR-24, FR-25)
- Unauthenticated request → `401`
- Deactivated users cannot authenticate or access protected resources

**Maps to:** FR-24, FR-25  
**Tests:** `test_admin.py`

---

## Definition of Done

A User Story is considered complete when:

- [ ] Implementation is complete
- [ ] All acceptance criteria are satisfied
- [ ] Authentication and authorization rules are enforced
- [ ] Business rules are implemented in the service layer
- [ ] Database operations are implemented in the CRUD layer
- [ ] Appropriate HTTP status codes are returned
- [ ] Tests are written
- [ ] All tests pass
- [ ] Test coverage remains ≥ 80%
- [ ] No N+1 queries are introduced
- [ ] Full type hints are implemented
- [ ] API documentation is updated
- [ ] README is updated where necessary