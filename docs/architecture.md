# GigForge — Architecture Document

|             |                                                |
| ----------- | ---------------------------------------------- |
| **Version** | 1.0                                            |
| **Status**  | Draft (Phase 2)                                |
| **Related** | `requirements.md`, `user-stories.md`, `scope.md`, `erd.md`, `api-contract.md` |

---

## 1. Tech Stack

| **Layer** | **Choice** | **Why** |
| --------- | ---------- | ------- |
| Language | Python 3.14 | Stable, typed, strong backend ecosystem |
| Framework | FastAPI | High-performance ASGI framework with async support and automatic OpenAPI documentation |
| Database | PostgreSQL 16 | Strong relational integrity for jobs, bids, contracts, and reviews |
| ORM | SQLAlchemy 2.0 (async) | Mature ORM with typed models and async support |
| Migrations | Alembic | Versioned and reviewable database schema changes |
| Validation | Pydantic v2 + pydantic-settings | Request/response validation and environment-based configuration |
| Authentication | JWT | Stateless authentication for the API |
| Password Hashing | `pwdlib` + bcrypt | Maintained password-hashing interface while satisfying the bcrypt requirement |
| Testing | pytest + pytest-cov + httpx | API testing, async support, and coverage measurement |
| Linting | Ruff | Fast linting and formatting |
| Type Checking | mypy | Static type checking |
| Caching (COULD) | Redis | Optional caching and future rate-limiting support |
| Deployment | Docker + Railway/Render | Reproducible deployment with simple hosting |
| CI | GitHub Actions | Automated linting, type checking, testing, and image builds |

### Password Hashing

GigForge shall never store plaintext passwords.

Passwords are hashed before persistence using `pwdlib` with bcrypt.

The password hashing implementation must remain isolated inside the security/core layer.

Example responsibility:

~~~text
Client password
      ↓
Security utility
      ↓
pwdlib + bcrypt
      ↓
password_hash
      ↓
PostgreSQL
~~~

The API, service, and CRUD layers must never directly implement password hashing.

---

## 2. High-Level Architecture

GigForge uses a layered architecture with a single deployable FastAPI service.

~~~mermaid
flowchart TD
    C[Client] -->|HTTP| R["API Layer<br/>Routers + Validation + Dependencies"]
    R --> S["Service Layer<br/>Business Rules + Orchestration"]
    S --> CR["CRUD Layer<br/>Database Operations"]
    CR --> M["SQLAlchemy Models"]
    M --> DB[(PostgreSQL)]

    S -.->|Optional BackgroundTasks| N[Email / Notifications]
    S -.->|Optional| CACHE[(Redis)]
~~~

### Golden Chain

~~~text
endpoint
    ↓
service
    ↓
crud
    ↓
model
    ↓
database
~~~

The service layer is the central business-logic boundary.

---

## 3. Architecture Principles

GigForge follows these principles:

1. **Thin API layer**
2. **Business logic belongs in services**
3. **CRUD performs database operations only**
4. **Database constraints protect critical invariants**
5. **Pydantic validates external input**
6. **Transactions are controlled by the service layer**
7. **API responses use Pydantic response schemas**
8. **Sensitive database fields must never leak into API responses**
9. **Configuration and secrets come from environment variables**
10. **Every important business rule must be testable independently**

---

## 4. Layer Responsibilities

| **Layer** | **Directory** | **Responsibility** | **Must NOT** |
| --------- | ------------- | ------------------ | ------------ |
| API | `app/api/` | HTTP parsing, routing, dependencies, authentication, status codes | contain business rules or direct SQL |
| Services | `app/services/` | Business rules, authorization, orchestration, transactions | depend on `HTTPException` or request objects |
| CRUD | `app/crud/` | Database queries and persistence operations | enforce business rules |
| Models | `app/models/` | SQLAlchemy tables, relationships, database constraints | contain HTTP/API logic |
| Schemas | `app/schemas/` | Pydantic request and response models | expose `password_hash` |
| Core | `app/core/` | Configuration, security, exceptions, logging | contain feature-specific business logic |
| DB | `app/db/` | Engine, session factory, declarative base | contain business rules |

---

## 5. API Layer

Directory:

~~~text
app/api/
└── v1/
    ├── auth.py
    ├── users.py
    ├── jobs.py
    ├── bids.py
    ├── contracts.py
    ├── reviews.py
    ├── admin.py
    └── health.py
~~~

The API layer is responsible for:

- Defining routes
- Parsing HTTP requests
- Pydantic request validation
- Authentication dependencies
- Role/permission dependencies
- Calling service functions
- Returning response schemas
- Mapping service results to HTTP status codes

### Example flow

~~~python
@router.post("/jobs", response_model=JobRead, status_code=201)
async def create_job(
    data: JobCreate,
    current_user: CurrentUser,
    service: JobService = Depends(get_job_service),
):
    return await service.create_job(current_user, data)
~~~

The endpoint should remain thin.

It should not contain:

- SQL queries
- Database transactions
- Complex ownership checks
- Bid acceptance logic
- Contract creation logic
- Business-state transitions

---

## 6. Service Layer

Directory:

~~~text
app/services/
├── auth_service.py
├── user_service.py
├── job_service.py
├── bid_service.py
├── contract_service.py
├── review_service.py
└── admin_service.py
~~~

The service layer contains GigForge's business logic.

### Responsibilities

- Role authorization
- Resource ownership checks
- Status transition rules
- Cross-entity operations
- Transaction orchestration
- Calling multiple CRUD operations
- Domain validation that cannot be expressed by Pydantic
- Business-rule enforcement

### Example

Accepting a bid requires multiple operations:

~~~text
Accept Bid Service
        │
        ├── verify job exists
        ├── verify current user owns job
        ├── verify job is open
        ├── verify bid exists
        ├── verify bid belongs to job
        ├── verify bid is pending
        ├── accept selected bid
        ├── reject other pending bids
        ├── create contract
        └── change job → in_progress
~~~

These operations belong in the service layer rather than the router.

---

## 7. CRUD Layer

Directory:

~~~text
app/crud/
├── user.py
├── job.py
├── skill.py
├── bid.py
├── contract.py
└── review.py
~~~

CRUD functions are responsible only for database operations.

Examples:

~~~text
get_user_by_email()
get_user_by_id()

create_job()
get_job_by_id()
update_job()
delete_job()

create_bid()
get_bid_by_id()
get_bids_for_job()

create_contract()
get_contract_by_id()

create_review()
get_reviews_for_user()
~~~

CRUD functions should not decide whether an operation is allowed.

For example:

**Incorrect:**

~~~python
def accept_bid(db, bid, user):
    if user.id != bid.job.client_id:
        raise PermissionDenied()
~~~

The ownership rule belongs in the service layer.

CRUD should focus on persistence/query operations.

---

## 8. Database Layer

Directory:

~~~text
app/db/
├── base.py
├── session.py
└── dependencies.py
~~~

### Responsibilities

- SQLAlchemy declarative base
- Async engine
- Async session factory
- Database dependency
- Database connection lifecycle

### Session

GigForge uses SQLAlchemy 2.0 async sessions.

The application should use:

~~~text
AsyncEngine
    ↓
async_sessionmaker
    ↓
AsyncSession
~~~

Database sessions are injected into services through the application dependency system.

---

## 9. Transaction Management

Transactions are controlled by the service layer.

This is important because several GigForge operations modify multiple entities atomically.

### Accept Bid Transaction

The following operations must happen in a single transaction:

~~~text
1. Accept selected bid
2. Reject other pending bids
3. Create contract
4. Change job status → in_progress
~~~

If any operation fails:

~~~text
ROLLBACK
    ↓
No changes are persisted
~~~

If all operations succeed:

~~~text
COMMIT