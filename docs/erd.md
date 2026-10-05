# GigForge — Entity Relationship Diagram

> Schema designed before writing SQLAlchemy models. Alembic migrations must match this.

## Diagram

~~~mermaid
erDiagram
    USERS ||--o{ JOBS : "posts (client)"
    USERS ||--o{ BIDS : "places (freelancer)"
    USERS ||--o{ USER_SKILLS : has
    SKILLS ||--o{ USER_SKILLS : tagged
    JOBS ||--o{ JOB_SKILLS : requires
    SKILLS ||--o{ JOB_SKILLS : tagged
    JOBS ||--o{ BIDS : receives
    BIDS ||--o| CONTRACTS : "becomes (accepted)"
    CONTRACTS ||--o{ REVIEWS : has
    USERS ||--o{ REVIEWS : writes
~~~

## Tables

### users

| **Column**    | **Type**                              | **Constraints**           |
| ------------- | ------------------------------------- | ------------------------- |
| id            | UUID                                  | PK, default uuid4         |
| email         | String(255)                           | unique, not null, indexed |
| password_hash | String                                | not null (bcrypt)         |
| role          | Enum(`client`, `freelancer`, `admin`) | not null                  |
| full_name     | String(120)                           | not null                  |
| bio           | Text                                  | nullable                  |
| hourly_rate   | Numeric(10,2)                         | nullable                  |
| avatar_url    | String                                | nullable                  |
| is_active     | Boolean                               | not null, default true    |
| created_at    | DateTime                              | not null                  |

---

### jobs

| **Column**              | **Type**                                           | **Constraints**                      |
| ----------------------- | -------------------------------------------------- | ------------------------------------ |
| id                      | UUID                                               | PK                                   |
| client_id               | UUID                                               | FK → users.id, not null, indexed     |
| title                   | String(140)                                        | not null                             |
| description             | Text                                               | not null                             |
| budget_min              | Numeric(10,2)                                      | not null                             |
| budget_max              | Numeric(10,2)                                      | not null, >= budget_min              |
| deadline                | Date                                               | not null, must be future at creation |
| status                  | Enum(`open`, `in_progress`, `completed`, `closed`) | not null, default `open`, indexed    |
| created_at              | DateTime                                           | not null                             |
| updated_at              | DateTime                                           | not null                             |

**Database constraint:**

- `budget_max >= budget_min`

---

### skills

| **Column** | **Type**   | **Constraints**  |
| ---------- | ---------- | ---------------- |
| id         | Integer    | PK               |
| name       | String(60) | unique, not null |

---

### user_skills

| **Column** | **Type** | **Constraints**                     |
| ---------- | -------- | ----------------------------------- |
| user_id    | UUID     | FK → users.id, part of composite PK |
| skill_id   | Integer  | FK → skills.id, part of composite PK |

**Primary Key:** `(user_id, skill_id)`

---

### job_skills

| **Column** | **Type** | **Constraints**                     |
| ---------- | -------- | ----------------------------------- |
| job_id     | UUID     | FK → jobs.id, part of composite PK |
| skill_id   | Integer  | FK → skills.id, part of composite PK |

**Primary Key:** `(job_id, skill_id)`

---

### bids

| **Column**    | **Type**                                             | **Constraints**                                                     |
| ------------- | ---------------------------------------------------- | ------------------------------------------------------------------- |
| id            | UUID                                                 | PK                                                                  |
| job_id        | UUID                                                 | FK → jobs.id, not null, indexed                                     |
| freelancer_id | UUID                                                 | FK → users.id, not null, indexed                                    |
| amount        | Numeric(10,2)                                        | not null, > 0                                                       |
| cover_letter  | Text                                                 | not null                                                            |
| delivery_days | Integer                                              | not null, > 0                                                       |
| status        | Enum(`pending`, `accepted`, `rejected`, `withdrawn`) | not null, default `pending`                                         |
| created_at    | DateTime                                             | not null                                                            |

**Database constraints:**

- `UNIQUE(job_id, freelancer_id)` — enforces FR-13 at DB level
- `amount > 0`
- `delivery_days > 0`

---

### contracts

| **Column**                | **Type**                                | **Constraints**                              |
| ------------------------- | ---------------------------------------- | -------------------------------------------- |
| id                        | UUID                                     | PK                                           |
| bid_id                    | UUID                                     | FK → bids.id, unique, not null               |
| job_id                    | UUID                                     | FK → jobs.id, unique, not null               |
| client_id                 | UUID                                     | FK → users.id, not null                      |
| freelancer_id             | UUID                                     | FK → users.id, not null                      |
| agreed_amount             | Numeric(10,2)                            | not null, snapshot of bid at acceptance     |
| status                    | Enum(`active`, `completed`, `cancelled`)  | not null, default `active`                  |
| started_at                | DateTime                                 | not null, default now                       |
| completed_at              | DateTime                                 | nullable                                     |

**Database constraints:**

- `UNIQUE(bid_id)` — one contract per accepted bid
- `UNIQUE(job_id)` — one contract per job

> `client_id` and `freelancer_id` are intentionally denormalized for simpler contract queries. The service layer must ensure they remain consistent with the associated job and bid.

---

### reviews

| **Column**  | **Type** | **Constraints**                                  |
| ----------- | -------- | ------------------------------------------------ |
| id          | UUID     | PK                                               |
| contract_id | UUID     | FK → contracts.id, not null                      |
| reviewer_id | UUID     | FK → users.id, not null                          |
| reviewee_id | UUID     | FK → users.id, not null, indexed                 |
| rating      | Integer  | not null, CHECK 1–5                              |
| comment     | Text     | nullable                                         |
| created_at  | DateTime | not null                                         |

**Database constraints:**

- `UNIQUE(contract_id, reviewer_id)` — one review per participant per contract
- `rating >= 1 AND rating <= 5`

---

## Relationship Summary

- `users` 1—∞ `jobs` — a client can post many jobs
- `users` 1—∞ `bids` — a freelancer can place many bids
- `jobs` 1—∞ `bids` — a job can receive many bids
- `jobs` ∞—∞ `skills` via `job_skills`
- `users` ∞—∞ `skills` via `user_skills`
- `bids` 1—0..1 `contracts` — only an accepted bid becomes a contract
- `jobs` 1—0..1 `contracts` — each job can have at most one contract
- `contracts` 1—0..2 `reviews` — maximum one review from each participant
- `users` 1—∞ `reviews` — a user can write many reviews

---

## Business Rules

### Users

- Only `client` and `freelancer` roles can register.
- `admin` accounts are seeded/created administratively.
- Email must be unique.
- Passwords are stored only as bcrypt hashes.
- Deactivated users cannot authenticate or access protected resources.

### Jobs

- Only clients can create jobs.
- `budget_max >= budget_min`.
- Deadline must be in the future when creating a job.
- Only the job owner can update or delete their job.
- Job status follows:

  `open → in_progress → completed`

  or:

  `open → closed`

- Only an open job can receive bids.
- A job can have at most one contract.

### Bids

- Only freelancers can place bids.
- A freelancer can place at most one bid per job.
- Only open jobs accept bids.
- Bid amount must be greater than zero.
- Delivery days must be greater than zero.
- Accepting a bid changes its status to `accepted`.
- All other pending bids for the same job become `rejected`.

### Contracts

- A contract is created only from an accepted bid.
- A job can have at most one contract.
- A bid can create at most one contract.
- The agreed amount is a snapshot of the accepted bid amount.
- Contract creation, bid acceptance, rejection of other bids, and job status update must occur in one database transaction.
- If any operation fails, the entire transaction is rolled back.
- Only contract participants can complete the contract.
- Completing the contract changes the job status to `completed`.

### Reviews

- Reviews are allowed only after a contract is completed.
- Both participants can leave one review for the other participant.
- A participant cannot review themselves.
- A participant cannot review the same contract twice.
- Rating must be between 1 and 5.
- Comments are optional.

---

## Indexing Plan

### users

- `users(email)` — login lookup
- `users(email)` is unique, so PostgreSQL will automatically maintain a unique index

### jobs

- `jobs(status)` — filter open jobs
- `jobs(deadline)` — deadline filtering/sorting
- Composite index `(status, created_at)` — efficient public open-job listing ordered by creation time
- Composite index `(status, deadline)` — useful for open jobs filtered/sorted by deadline

### bids

- `bids(job_id)` — retrieve bids for a job
- `bids(freelancer_id)` — retrieve a freelancer's bids
- `UNIQUE(job_id, freelancer_id)` — prevents duplicate bids and provides a composite index

### contracts

- `contracts(client_id)` — client's contracts
- `contracts(freelancer_id)` — freelancer's contracts
- `UNIQUE(job_id)` — guarantees one contract per job
- `UNIQUE(bid_id)` — guarantees one contract per bid

### reviews

- `reviews(reviewee_id)` — retrieve reviews received by a user
- `UNIQUE(contract_id, reviewer_id)` — guarantees one review per participant per contract

---

## Constraint Enforcement Strategy

| **Rule** | **Application Layer** | **Database Layer** |
| -------- | --------------------- | ------------------ |
| Unique email | Yes | `UNIQUE` |
| Valid user role | Yes | Enum |
| Budget max >= min | Yes | `CHECK` |
| Future deadline | Yes | No |
| Bid amount > 0 | Yes | `CHECK` |
| Delivery days > 0 | Yes | `CHECK` |
| One bid per job/user | Yes | `UNIQUE(job_id, freelancer_id)` |
| One contract per bid | Yes | `UNIQUE(bid_id)` |
| One contract per job | Yes | `UNIQUE(job_id)` |
| Rating 1–5 | Yes | `CHECK` |
| One review per participant | Yes | `UNIQUE(contract_id, reviewer_id)` |
| Role-based authorization | Yes | No |
| Resource ownership | Yes | No |
| Job status transitions | Yes | Partially |
| Contract participants | Yes | No |

> Business rules should be validated at the API/service layer for clear error responses, while critical invariants that the database can enforce should also have database constraints.

---

## Implementation Order

1. Create SQLAlchemy `User` model
2. Create `Skill` model
3. Create `Job` model
4. Create `Bid` model
5. Create `Contract` model
6. Create `Review` model
7. Create `user_skills` association table
8. Create `job_skills` association table
9. Add relationships and foreign keys
10. Add indexes and database constraints
11. Generate the initial Alembic migration
12. Review the generated migration manually
13. Apply migration to PostgreSQL
14. Verify the resulting database schema
15. Begin CRUD implementation
```

## Relationship Summary

- users 1—∞ jobs (as client)
- users 1—∞ bids (as freelancer)
- jobs 1—∞ bids; **unique pair** (job, freelancer)
- bids 1—0..1 contracts (only `accepted` bid becomes a contract)
- contracts 1—0..2 reviews (one per participant)
- users ∞—∞ skills via `user_skills`
- jobs ∞—∞ skills via `job_skills`