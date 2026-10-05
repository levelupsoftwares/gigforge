# GigForge — Freelance Marketplace REST API

## 1. Overview

GigForge is a production-grade freelance marketplace REST API. Clients post jobs, freelancers place bids on them, and accepting a bid creates a contract. After a contract is completed, both parties exchange reviews and ratings.

The system enforces role-based access control, JWT authentication, and strict business rules around bidding and contracting.

---

## 2. System Roles

| Role | Description |
|---|---|
| `client` | Posts jobs, reviews bids, accepts bids, marks contracts complete |
| `freelancer` | Browses jobs, places bids, delivers work, leaves reviews |
| `admin` | Moderates users and job postings |

---

## 3. Functional Requirements

### 3.1 Authentication & Users

- **FR-01:** The system shall allow visitors to register with email, password, and role (`client` or `freelancer`).
- **FR-02:** The system shall reject registration with a duplicate email (`HTTP 409`).
- **FR-03:** The system shall authenticate users via email + password and issue a JWT access token with configurable expiry.
- **FR-04:** Passwords shall be hashed with bcrypt. Plain passwords shall never be stored, logged, or returned in any response.
- **FR-05:** Authenticated users shall view and update their own profile (full name, bio, hourly rate, skills).
- **FR-06:** Authenticated users shall upload a profile avatar (image files only, size limit 5 MB).

### 3.2 Jobs

- **FR-07:** Authenticated users with role `client` shall create job postings containing:
  - `title`
  - `description`
  - `budget_min`
  - `budget_max`
  - `deadline`
  - `required_skills`

- **FR-08:** `budget_max` shall be greater than or equal to `budget_min` (`HTTP 422` otherwise).
- **FR-09:** `deadline` shall be a future date (`HTTP 422` otherwise).
- **FR-10:** Anyone — including unauthenticated visitors — shall browse and search open jobs with pagination and filters:
  - keyword
  - budget range
  - skills

- **FR-11:** Only the job owner shall update or delete their own job (`HTTP 403` otherwise).
- **FR-12:** A job's status shall transition through the following states:

```text
open → in_progress → completed
  │
  └──────────────→ closed
  ```

### 3.3 Bids

- **FR-13**: Authenticated users with role `freelancer` shall place at most one bid per job, containing: amount, cover letter, and delivery days (HTTP 409 on duplicate).
- **FR-14**: Bids shall only be placed on jobs with status `open` (HTTP 409 otherwise).
- **FR-15**: Bid `amount` shall be a positive number (HTTP 422 otherwise).
- **FR-16**: Only the job owner shall view all bids on their own job (HTTP 403 otherwise).
- **FR-17**: A freelancer shall view a list of all their own bids and their statuses.

### 3.4 Contracts

- **FR-18**: Only the job owner shall accept a bid, and only while the job is `open`.
- **FR-19**: Accepting a bid shall create exactly one contract and automatically reject all other pending bids on that job.
- **FR-20**: Each job shall have at most one accepted bid / one contract.
- **FR-21**: The client or freelancer shall mark an `active` contract as `completed`.

### 3.5 Reviews

- **FR-22**: Both parties of a `completed` contract shall leave exactly one review (rating 1–5 and optional comment) for the other party (HTTP 409 on duplicate).
- **FR-23**: Reviews shall only be allowed on contracts with status `completed` (HTTP 422 otherwise).

### 3.6 Administration

- **FR-24**: Only role `admin` shall list all users and deactivate accounts.
- **FR-25**: Only role `admin` shall close any job posting.

## 4. Non-Functional Requirements

| **ID** | **Category**    | **Requirement**                                                                |
| ------ | --------------- | ------------------------------------------------------------------------------ |
| NFR-01 | Security        | All endpoints except `/api/v1/auth/*` and `/api/v1/health` require a valid JWT |
| NFR-02 | Security        | Users shall only access or modify their own resources (HTTP 403 otherwise)     |
| NFR-03 | Security        | All inputs validated via Pydantic; no raw SQL string interpolation             |
| NFR-04 | Performance     | List endpoints respond in < 300 ms with 10,000 records; no N+1 queries         |
| NFR-05 | Reliability     | Test coverage ≥ 80%; every FR has at least one test                            |
| NFR-06 | Maintainability | Layered architecture (endpoint → service → crud); full type hints              |
| NFR-07 | Configurability | All secrets and settings via environment variables; no hardcoded values        |
| NFR-08 | Documentation  | Auto-generated OpenAPI docs at `/docs`; complete README   