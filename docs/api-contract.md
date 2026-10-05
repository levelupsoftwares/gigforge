# GigForge — API Contract (v1)

> Agreement between backend and any client. Design reviewed before implementation.

## Conventions

- **Base URL:** `/api/v1`
- **Auth header:** `Authorization: Bearer <access_token>`
- **Error body:** `{"detail": "human-readable message"}`
- **Pagination:** request `?page=1&size=20` (max 100) → response: `{"items": [...], "total": 137, "page": 1, "size": 20}`
- **Timestamps:** ISO 8601 UTC
- **IDs:** UUID strings
- **Authentication:** Protected endpoints return `401` when authentication is missing or invalid.
- **Authorization:** Protected endpoints return `403` when the authenticated user lacks permission.
- **Validation:** Invalid request data returns `422`.

---

## Health

### `GET /api/v1/health`

Public.

→ `200 {"status": "ok", "environment": "dev"}`

---

## Auth

### `POST /api/v1/auth/register`

Public. Register as client or freelancer.

**Request:**

    {
      "email": "ana@example.com",
      "password": "secret123",
      "role": "freelancer",
      "full_name": "Ana"
    }

| **Status** | **Meaning**                                  |
| ---------- | -------------------------------------------- |
| 201        | Created → `UserRead` without `password_hash` |
| 409        | Email already registered                     |
| 422        | Validation failed                            |

**Validation:**

- Password must be at least 8 characters.
- Role must be `client` or `freelancer`.
- Email must be valid.
- Password must never be returned or logged.

---

### `POST /api/v1/auth/login`

Public.

**Request:**

    {
      "email": "ana@example.com",
      "password": "secret123"
    }

→ `200 {"access_token": "...", "token_type": "bearer"}`

→ `401` invalid credentials.

- Unknown email and incorrect password use the same error message to prevent user enumeration.
- Deactivated users cannot authenticate.

---

## Users

### `GET /api/v1/users/me`

JWT required.

→ `200 UserRead`

Returns the authenticated user's own profile.

---

### `PATCH /api/v1/users/me`

JWT required.

**Request:**

    {
      "full_name": "Ana Smith",
      "bio": "Backend developer",
      "hourly_rate": 25.50,
      "skill_ids": [1, 2, 3]
    }

All fields are optional.

→ `200 UserRead`

---

### `GET /api/v1/users/{user_id}`

Public.

→ `200 UserPublic`

Returns only public/limited profile fields.

→ `404` if user does not exist.

---

### `POST /api/v1/users/me/avatar`

JWT required.

Multipart image upload.

**Constraints:**

- Image files only.
- Maximum size: 5 MB.

→ `200 {"avatar_url": "..."}`

→ `422` wrong file type or size.

---

## Jobs

### `POST /api/v1/jobs`

JWT required. `role=client`.

**Request:**

    {
      "title": "Build a landing page",
      "description": "...",
      "budget_min": 100,
      "budget_max": 500,
      "deadline": "2026-12-01",
      "skill_ids": [1, 2]
    }

| **Status** | **Meaning**                         |
| ---------- | ----------------------------------- |
| 201        | Created → `JobRead`, status `open` |
| 401        | Missing/invalid token               |
| 403        | Authenticated user is not a client |
| 422        | Invalid request data                |

**Validation:**

- `budget_max >= budget_min`
- Deadline must be in the future.
- Required fields must be present.
- Skill IDs must be valid.

---

### `GET /api/v1/jobs`

Public. Returns open jobs only.

**Query parameters:**

- `search` — keyword search against job title/description
- `min_budget` — minimum budget
- `max_budget` — maximum budget
- `skill` — skill name filter
- `page` — page number
- `size` — number of items per page, maximum `100`

Example:

    GET /api/v1/jobs?search=python&min_budget=100&max_budget=500&skill=fastapi&page=1&size=20

→ `200` paginated `JobListItem`

    {
      "items": [],
      "total": 137,
      "page": 1,
      "size": 20
    }

> `skill_ids` are used when creating/updating jobs. `skill` is used as a skill-name filter when searching.

---

### `GET /api/v1/jobs/{job_id}`

Public.

→ `200 JobDetail`

Includes:

- Job information
- Required skills
- Bid count
- Other relevant public counts

→ `404` if job does not exist.

---

### `PATCH /api/v1/jobs/{job_id}`

JWT required. Job owner only.

→ `200 JobRead`

| **Status** | **Meaning**                  |
| ---------- | ---------------------------- |
| 200        | Job updated                  |
| 401        | Missing/invalid token        |
| 403        | Authenticated user not owner |
| 404        | Job not found                |
| 422        | Invalid request body         |

---

### `DELETE /api/v1/jobs/{job_id}`

JWT required. Job owner only.

→ `204`

| **Status** | **Meaning**                  |
| ---------- | ---------------------------- |
| 204        | Job deleted                  |
| 401        | Missing/invalid token        |
| 403        | Authenticated user not owner |
| 404        | Job not found                |

---

### `PATCH /api/v1/jobs/{job_id}/close`

JWT required. Job owner or admin.

→ `200` with job status `closed`.

| **Status** | **Meaning**                      |
| ---------- | -------------------------------- |
| 200        | Job closed                       |
| 401        | Missing/invalid token            |
| 403        | User is not owner or admin      |
| 404        | Job not found                    |
| 409        | Job cannot be closed in its state |

---

## Bids

### `POST /api/v1/jobs/{job_id}/bids`

JWT required. `role=freelancer`.

**Request:**

    {
      "amount": 450,
      "cover_letter": "I can deliver in 10 days",
      "delivery_days": 10
    }

| **Status** | **Meaning**                              |
| ---------- | ---------------------------------------- |
| 201        | Created → `BidRead`, status `pending`    |
| 401        | Missing/invalid token                    |
| 403        | Authenticated user is not a freelancer  |
| 404        | Job not found                            |
| 409        | Already bid on this job / job not `open` |
| 422        | `amount <= 0` or invalid body             |

---

### `GET /api/v1/jobs/{job_id}/bids`

JWT required. Job owner only.

→ `200` paginated bids.

| **Status** | **Meaning**                  |
| ---------- | ---------------------------- |
| 200        | Bids returned                |
| 401        | Missing/invalid token        |
| 403        | Authenticated user not owner |
| 404        | Job not found                |

---

### `GET /api/v1/bids/me`

JWT required. Freelancer only.

→ `200` paginated list of the authenticated freelancer's own bids with statuses.

- User only receives their own bids.
- `401` missing/invalid token.
- `403` authenticated user is not a freelancer.

---

## Contracts

### `POST /api/v1/bids/{bid_id}/accept`

JWT required. Job owner only. Job must be `open`.

→ `201 ContractRead`

On successful acceptance:

1. Selected bid becomes `accepted`.
2. Contract is created.
3. All other `pending` bids for the job become `rejected`.
4. Job status becomes `in_progress`.

**Atomic transaction requirement:**

All four operations must occur in a single database transaction.

If any operation fails, the entire transaction must be rolled back.

| **Status** | **Meaning**                  |
| ---------- | ---------------------------- |
| 201        | Contract created             |
| 401        | Missing/invalid token        |
| 403        | User is not the job owner    |
| 404        | Bid/job not found            |
| 409        | Bid already accepted / job not open |

---

### `GET /api/v1/contracts`

JWT required.

Returns contracts where the authenticated user is either:

- `client_id`
- `freelancer_id`

→ `200` paginated contracts.

Users must never receive another user's contracts.

---

### `GET /api/v1/contracts/{contract_id}`

JWT required. Contract participant only.

→ `200 ContractRead`

| **Status** | **Meaning**                    |
| ---------- | ------------------------------ |
| 200        | Contract returned              |
| 401        | Missing/invalid token          |
| 403        | User is not a participant      |
| 404        | Contract not found             |

---

### `PATCH /api/v1/contracts/{contract_id}/complete`

JWT required. Contract participant.

Contract must have status `active`.

→ `200` with status `completed`.

On completion:

- Contract status → `completed`
- Job status → `completed`
- `completed_at` is set

| **Status** | **Meaning**                    |
| ---------- | ------------------------------ |
| 200        | Contract completed             |
| 401        | Missing/invalid token          |
| 403        | User is not a participant      |
| 404        | Contract not found             |
| 409        | Contract already completed     |
| 422        | Contract is not active         |

---

## Reviews

### `POST /api/v1/contracts/{contract_id}/reviews`

JWT required. Contract participant. Contract must be `completed`.

**Request:**

    {
      "rating": 5,
      "comment": "Great work, delivered early"
    }

The server determines the `reviewee_id` automatically.

- If reviewer is the client → reviewee is the freelancer.
- If reviewer is the freelancer → reviewee is the client.
- `reviewee_id` must not be supplied by the client.
- A user cannot review themselves.
- A user must be a participant of the contract.

| **Status** | **Meaning**                                |
| ---------- | ------------------------------------------ |
| 201        | Created → `ReviewRead`                     |
| 401        | Missing/invalid token                      |
| 403        | Not a participant                          |
| 404        | Contract not found                         |
| 409        | Already reviewed this contract (this side) |
| 422        | Contract not completed / rating outside 1–5 |

---

### `GET /api/v1/contracts/{contract_id}/reviews`

JWT required. Contract participant only.

→ `200` reviews for the contract.

| **Status** | **Meaning**               |
| ---------- | ------------------------- |
| 200        | Reviews returned          |
| 401        | Missing/invalid token     |
| 403        | Not a participant         |
| 404        | Contract not found        |

---

### `GET /api/v1/users/{user_id}/reviews`

Public.

→ `200` received reviews + average rating.

Example:

    {
      "items": [],
      "average_rating": 4.7,
      "total": 12
    }

→ `404` if user does not exist.

---

## Admin

> All admin endpoints require `role=admin`. Authenticated non-admin users receive `403`.

### `GET /api/v1/admin/users`

JWT required. Admin only.

→ `200` paginated list of all users.

| **Status** | **Meaning**             |
| ---------- | ----------------------- |
| 200        | Users returned          |
| 401        | Missing/invalid token   |
| 403        | User is not an admin    |

---

### `PATCH /api/v1/admin/users/{user_id}/deactivate`

JWT required. Admin only.

→ `200 UserRead` with `is_active=false`.

| **Status** | **Meaning**             |
| ---------- | ----------------------- |
| 200        | User deactivated        |
| 401        | Missing/invalid token   |
| 403        | User is not an admin    |
| 404        | User not found          |

---

### `PATCH /api/v1/admin/jobs/{job_id}/close`

JWT required. Admin only.

→ `200 JobRead` with status `closed`.

| **Status** | **Meaning**             |
| ---------- | ----------------------- |
| 200        | Job closed              |
| 401        | Missing/invalid token   |
| 403        | User is not an admin    |
| 404        | Job not found           |
| 409        | Job cannot be closed in its current state |

---

# Response Schemas

## UserRead

    {
      "id": "uuid",
      "email": "ana@example.com",
      "role": "freelancer",
      "full_name": "Ana Smith",
      "bio": "Backend developer",
      "hourly_rate": 25.50,
      "avatar_url": "...",
      "is_active": true,
      "created_at": "2026-10-05T12:00:00Z",
      "skills": []
    }

> `password_hash` must never be included.

---

## UserPublic

    {
      "id": "uuid",
      "role": "freelancer",
      "full_name": "Ana Smith",
      "bio": "Backend developer",
      "hourly_rate": 25.50,
      "avatar_url": "...",
      "skills": []
    }

---

## JobRead

    {
      "id": "uuid",
      "client_id": "uuid",
      "title": "Build a landing page",
      "description": "...",
      "budget_min": 100,
      "budget_max": 500,
      "deadline": "2026-12-01",
      "status": "open",
      "skills": [],
      "created_at": "2026-10-05T12:00:00Z",
      "updated_at": "2026-10-05T12:00:00Z"
    }

---

## JobListItem

    {
      "id": "uuid",
      "title": "Build a landing page",
      "budget_min": 100,
      "budget_max": 500,
      "deadline": "2026-12-01",
      "status": "open",
      "skills": [],
      "created_at": "2026-10-05T12:00:00Z"
    }

---

## JobDetail

    {
      "id": "uuid",
      "client": {},
      "title": "Build a landing page",
      "description": "...",
      "budget_min": 100,
      "budget_max": 500,
      "deadline": "2026-12-01",
      "status": "open",
      "skills": [],
      "bid_count": 12,
      "created_at": "2026-10-05T12:00:00Z",
      "updated_at": "2026-10-05T12:00:00Z"
    }

---

## BidRead

    {
      "id": "uuid",
      "job_id": "uuid",
      "freelancer_id": "uuid",
      "amount": 450,
      "cover_letter": "I can deliver in 10 days",
      "delivery_days": 10,
      "status": "pending",
      "created_at": "2026-10-05T12:00:00Z"
    }

---

## ContractRead

    {
      "id": "uuid",
      "bid_id": "uuid",
      "job_id": "uuid",
      "client_id": "uuid",
      "freelancer_id": "uuid",
      "agreed_amount": 450,
      "status": "active",
      "started_at": "2026-10-05T12:00:00Z",
      "completed_at": null
    }

---

## ReviewRead

    {
      "id": "uuid",
      "contract_id": "uuid",
      "reviewer_id": "uuid",
      "reviewee_id": "uuid",
      "rating": 5,
      "comment": "Great work, delivered early",
      "created_at": "2026-10-05T12:00:00Z"
    }

---

# Status Code Summary

| **Code** | **Used for**                                                                                  |
| -------- | ---------------------------------------------------------------------------------------------- |
| 200      | Successful read/update                                                                         |
| 201      | Resource created                                                                               |
| 204      | Successful delete                                                                              |
| 401      | Missing/expired/invalid token, bad login                                                       |
| 403      | Authenticated but not allowed (role/ownership/participation)                                   |
| 404      | Resource not found                                                                              |
| 409      | Business conflict (duplicate email/bid/review, wrong resource state)                           |
| 422      | Request validation failure                                                                      |
| 500      | Unhandled server error; error is logged and a generic body is returned                         |

---

# Transaction Requirements

The following operations must be transactional:

## Accept Bid

The following must succeed or fail together:

1. Verify job ownership.
2. Verify job is `open`.
3. Verify bid belongs to the job.
4. Verify bid is `pending`.
5. Set selected bid → `accepted`.
6. Create contract.
7. Reject all other pending bids for the job.
8. Set job → `in_progress`.

If any operation fails:

- Roll back the transaction.
- No partial state may remain.

## Complete Contract

The following must succeed or fail together:

1. Verify user is a contract participant.
2. Verify contract is `active`.
3. Set contract → `completed`.
4. Set `completed_at`.
5. Set job → `completed`.

---

# API Design Rules

- All API routes use the `/api/v1` prefix.
- Protected routes require JWT authentication.
- Role checks are enforced in the service/authorization layer.
- Ownership checks are enforced before modifying resources.
- Business rules are enforced in the service layer.
- Critical database invariants are also enforced at the database layer where possible.
- Pydantic schemas validate all incoming request data.
- Response schemas must never expose `password_hash`.
- Passwords must never be logged.
- Pagination is used for collection endpoints.
- `size` must not exceed `100`.
- All timestamps are returned as ISO 8601 UTC.
- IDs are represented as UUID strings.
- The API must return consistent error bodies using `{"detail": "human-readable message"}`.

---

# API Contract Checklist

- [ ] Authentication endpoints defined
- [ ] User endpoints defined
- [ ] Job endpoints defined
- [ ] Bid endpoints defined
- [ ] Contract endpoints defined
- [ ] Review endpoints defined
- [ ] Admin endpoints defined
- [ ] Request schemas defined
- [ ] Response schemas defined
- [ ] HTTP status codes defined
- [ ] Authentication rules defined
- [ ] Authorization rules defined
- [ ] Ownership rules defined
- [ ] Business conflicts defined
- [ ] Pagination defined
- [ ] Transaction boundaries defined
- [ ] Error format defined
- [ ] API versioning defined