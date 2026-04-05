# Finance Data Processing & Access Control Dashboard

A production-quality backend API for managing financial records with role-based access control and dashboard analytics.

Built with **Python 3.12 / FastAPI / SQLAlchemy (async) / PostgreSQL / JWT**.

---

## 🏗️ Architecture

```
src/
├── main.py                    # App entry point (middleware, error handlers, routers)
├── config.py                  # Environment settings (Pydantic BaseSettings)
├── database.py                # Async SQLAlchemy engine + session dependency
│
├── models/                    # SQLAlchemy ORM models (database tables)
│   ├── user.py                # User model (id, name, email, password, role, status)
│   └── record.py              # FinancialRecord model (amount, type, category, date)
│
├── schemas/                   # Pydantic schemas (request/response validation)
│   ├── auth.py                # RegisterRequest, LoginRequest, TokenResponse
│   ├── user.py                # UserResponse, UserUpdate, UserListResponse
│   ├── record.py              # RecordCreate, RecordUpdate, RecordResponse
│   └── dashboard.py           # SummaryResponse, TrendsResponse, etc.
│
├── routers/                   # API route definitions (thin controllers)
│   ├── auth.py                # POST /register, POST /login
│   ├── users.py               # GET/PUT/DELETE /users (Admin only)
│   ├── records.py             # CRUD /records (role-based)
│   └── dashboard.py           # GET /dashboard/* (Analyst + Admin)
│
├── services/                  # Business logic layer
│   ├── auth_service.py        # Registration, authentication
│   ├── user_service.py        # User CRUD, role management
│   ├── record_service.py      # Record CRUD, filtering, search
│   └── dashboard_service.py   # Aggregation queries, trends
│
├── dependencies/              # FastAPI Depends() functions
│   └── auth.py                # get_current_user (JWT), require_role (RBAC)
│
└── utils/
    ├── errors.py              # AppError custom exception
    └── security.py            # JWT encode/decode, bcrypt hashing
```

### Layered Architecture

| Layer | Responsibility |
|---|---|
| **Routers** | HTTP endpoint definitions, wire dependencies to services |
| **Dependencies** | Authentication (JWT verify), Authorization (role check), DB session |
| **Schemas** | Request validation (Pydantic) + response serialization |
| **Services** | Business logic, orchestration, data access |
| **Models** | Database table definitions (SQLAlchemy ORM) |

Each layer only knows about the layer below it. Services are testable without HTTP.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- pip

### Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd zoryvn

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env — set your PostgreSQL password in DATABASE_URL

# 4. Create the PostgreSQL database
psql -U postgres -c "CREATE DATABASE finance_db;"

# 5. Start the server (auto-creates tables + seeds sample data on first run)
uvicorn src.main:app --reload
```

> **Note:** You do NOT need to run `seed.py` manually. The server automatically creates tables and seeds sample data on first startup if the database is empty.

### Access
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Test Credentials (auto-seeded)
| Role | Email | Password |
|---|---|---|
| Admin | admin@finance.com | password123 |
| Analyst | analyst@finance.com | password123 |
| Viewer | viewer@finance.com | password123 |

---

## 🔐 Access Control

### Roles

| Role | View Records | CRUD Records | Analytics | Manage Users |
|---|---|---|---|---|
| **Viewer** | ✅ own | ❌ | ❌ | ❌ |
| **Analyst** | ✅ own | ❌ | ✅ | ❌ |
| **Admin** | ✅ all | ✅ | ✅ | ✅ |

### Implementation

Access control is implemented via **FastAPI dependency injection**, not traditional middleware:

```python
# Authentication: JWT → User object
async def get_current_user(token = Depends(oauth2_scheme), db = Depends(get_db)) -> User

# Authorization: Role check factory
def require_role(*allowed_roles: str) → Depends(get_current_user) + role check

# Usage in routes:
@router.get("/records")
async def list_records(user = Depends(require_role("viewer", "analyst", "admin"))):

@router.post("/records")
async def create_record(user = Depends(require_role("admin"))):
```

### Middleware Stack

| Layer | Type | Purpose |
|---|---|---|
| CORS | Middleware (global) | Cross-origin request handling |
| Rate Limiter | Middleware (global) | 100 requests/minute per IP |
| Request Logger | Middleware (global) | Log method, path, status, duration |
| Authentication | Dependency (per-route) | JWT verification → User object |
| Authorization | Dependency (per-route) | Role-based access check |
| Validation | Pydantic (automatic) | Request body/query validation |

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register (default role: viewer) |
| POST | `/api/auth/login` | Public | Login → JWT token |

### Users (Admin only)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/users` | List users (paginated) |
| GET | `/api/users/{id}` | Get user details |
| PUT | `/api/users/{id}` | Update user (name/role/status) |
| DELETE | `/api/users/{id}` | Deactivate user |

### Financial Records
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/records` | Admin | Create record |
| GET | `/api/records` | All roles | List (filtered, paginated) |
| GET | `/api/records/{id}` | All roles | Get single record |
| PUT | `/api/records/{id}` | Admin | Update record |
| DELETE | `/api/records/{id}` | Admin | Soft-delete record |

**Filters**: `?type=income&category=salary&start_date=2026-01-01&end_date=2026-03-31&search=bonus&page=1&limit=20`

### Dashboard Analytics (Analyst + Admin)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard/summary` | Total income, expenses, net balance |
| GET | `/api/dashboard/category-totals` | Grouped by category |
| GET | `/api/dashboard/trends?interval=monthly` | Weekly/monthly trends |
| GET | `/api/dashboard/recent?limit=10` | Recent transactions |

---

## 🗄️ Database

### PostgreSQL Setup

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE finance_db;"

# Connection string format (set in .env)
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/finance_db
```

### Schema

#### Users Table
| Column | Type | Constraints |
|---|---|---|
| id | UUID (string) | Primary key |
| name | VARCHAR(100) | Not null |
| email | VARCHAR(255) | Unique, not null, indexed |
| password | VARCHAR(255) | Not null (bcrypt hash) |
| role | VARCHAR(20) | Default: "viewer" |
| status | VARCHAR(20) | Default: "active" |
| created_at | TIMESTAMP | Auto-set |
| updated_at | TIMESTAMP | Auto-updated |

#### Financial Records Table
| Column | Type | Constraints |
|---|---|---|
| id | UUID (string) | Primary key |
| user_id | UUID (string) | Foreign key → users, indexed |
| amount | NUMERIC(12,2) | Not null, positive |
| type | VARCHAR(10) | "income" or "expense", indexed |
| category | VARCHAR(50) | Not null, indexed |
| date | DATE | Not null, indexed |
| description | TEXT | Optional |
| is_deleted | BOOLEAN | Default: false (soft delete) |
| created_at | TIMESTAMP | Auto-set |
| updated_at | TIMESTAMP | Auto-updated |

### Design Decisions
- **UUID** over auto-increment: prevents enumeration attacks
- **NUMERIC(12,2)** for money: exact arithmetic (no float rounding)
- **Soft delete**: financial records are never physically removed (audit trail)
- **Indexes**: on date, category, type, user_id for fast dashboard queries

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_rbac.py -v
python -m pytest tests/test_records.py -v
python -m pytest tests/test_dashboard.py -v
```

### Test Coverage
- **Auth tests**: Registration, login, validation, duplicates
- **RBAC tests**: Role enforcement for all 3 roles + unauthenticated
- **Record tests**: CRUD, pagination, filtering, soft delete
- **Dashboard tests**: Summary, category totals, trends, empty state

---

## ⚙️ Technology Choices & Tradeoffs

| Choice | Why | Alternative considered |
|---|---|---|
| **FastAPI** | Auto docs, Pydantic validation, async, DI | Express (no built-in validation/docs) |
| **SQLAlchemy async** | Pythonic ORM, session-per-request DI | Raw SQL (more verbose) |
| **PostgreSQL** | Production-grade, ACID, scalable | SQLite (not production-ready) |
| **asyncpg** | Fastest async PostgreSQL driver | psycopg (less performant async) |
| **JWT** | Stateless auth, role in payload | Sessions (needs server-side store) |
| **bcrypt** | Industry standard, slow by design | argon2 (newer but less adoption) |
| **Pydantic** | Built into FastAPI, type-safe | Marshmallow (extra dependency) |
| **Depends() over middleware** | Per-route, composable, self-documenting | Global middleware (too broad for RBAC) |

---

## 📝 Assumptions

1. **Single-tenant**: One organization, admins see all data
2. **No refresh tokens**: JWT with 24h expiry (sufficient for this scope)
3. **Categories are free-text**: Not a fixed enum — allows flexibility
4. **Soft delete only**: No physical delete (financial data integrity)
5. **Default role = viewer**: Least privilege principle on registration
6. **Admin creates records**: Assignment specifies Admin has CRUD access
7. **No file uploads**: Records are text/numeric only

---

## 📄 Sample Requests

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com", "password": "secure123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@finance.com", "password": "password123"}'
```

### Create Record (Admin)
```bash
curl -X POST http://localhost:8000/api/records \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "type": "income", "category": "salary", "date": "2026-04-01"}'
```

### Get Dashboard Summary (Analyst/Admin)
```bash
curl http://localhost:8000/api/dashboard/summary \
  -H "Authorization: Bearer <token>"
```
