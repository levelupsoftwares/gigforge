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