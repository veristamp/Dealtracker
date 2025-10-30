# DealTracker Auth Backend

> **🚧 An Open-Source personal project for secure authentication experiments and backend architecture. 🚧**

---

## 🦾 Purpose

This backend powers authentication and user security for **DealTracker**, a desktop product-tracking app. It’s a playground for best practices, security experiments, and modern backend design — not a starter template, but a showcase of how to build a robust authentication system.

---

## 🚀 Features

- **EdDSA (Ed25519) JWT Authentication**
- **Refresh Tokens** (revocable, DB-backed, per-device)
- **Device Fingerprinting** per user (anti-sharing, anti-bot, admin-resettable)
- **Session-based Admin Panel** (IP whitelist, session cookies)
- **User Approval & Tiers:** Inactive by default, admin can approve and tier (bronze/silver/gold)
- **Secure password storage** (bcrypt)
- **Rate Limiting** (per endpoint, configurable)
- **Admin Panel:** User management, analytics, and audit logs
- **CORS, CSP, and secure headers**
- **Docker-ready, production deployment with Gunicorn/Uvicorn**
- **Background tasks** for token cleanup
- **Audit logs with structlog (JSON, timestamped, no secrets in logs)**

---

## 🗝️ Authentication Architecture

### 🔑 JWT Token Model

- **Access Token**  
  - EdDSA (Ed25519) signed  
  - 24h expiry (configurable)  
  - Contains only user identifier (no sensitive claims)
- **Refresh Token**  
  - EdDSA signed  
  - 7d expiry (configurable)  
  - Stored in DB, can be revoked for single-session logout  
  - Only usable by the device it was issued to

### 🛰 Device Fingerprinting

- On first login, device fingerprint is saved to the user account
- Further logins *require* same device fingerprint
- Device cannot be registered to more than one user (409 Conflict on attempt)
- Admin panel allows device reset (e.g., lost device, support case)

### 👑 Admin Security

- Session-based, not JWT
- IP whitelisting (`127.0.0.1`, `::1` or as configured)
- Secure cookies, no session exposure to JS
- All admin actions logged
- User management, tier changes, device reset, and user deletion via HTML admin panel

### 🕵️‍♂️ Rate Limiting

| Endpoint           | Limit        | Window    |
|--------------------|-------------|-----------|
| `/`                | 10          | 1 minute  |
| `/health`          | 30          | 1 minute  |
| `/info`            | 5           | 1 minute  |
| `/users/token`     | 5           | 1 minute  |
| (default)          | 60          | 1 minute  |

- Strict, per-route
- JSON error on excess: includes `retry_after`

### 🔒 Security Model

- **bcrypt** + salt for all user passwords
- **SQLAlchemy ORM** for all DB access (no raw SQL injection risk)
- **Pydantic** for all validation (no arbitrary payloads)
- **CORS** locked to dev hosts, **CSP** applied to all responses
- **Error handling:** All errors have standard format, no stacktraces exposed

---

## 🧩 API Reference

<details>
<summary><b>Full endpoint list with sample requests/responses (click to expand)</b></summary>

### **User Authentication & Management**

#### `POST /users/` – Register New User  
Creates a new user (inactive by default; admin must activate).

**Body:**
```json
{
  "username": "string",
  "password": "string"
}
````

**Response:**

```json
{
  "id": 1,
  "username": "testuser",
  "is_active": false,
  "tier": "bronze",
  "device_fingerprint": null
}
```

#### `POST /users/token` – User Login

Returns JWT access and refresh tokens. Requires device fingerprint.

**Body:**

```json
{
  "username": "string",
  "password": "string",
  "device_fingerprint": "string"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> 🛡️ **First login binds device fingerprint; subsequent logins require a match.**
> 🔒 **If fingerprint already registered to another user:**
>
> ```json
> {
>   "detail": "This device is already registered to another user. Please contact support if this is your device."
> }
> ```

#### `POST /users/refresh` – Refresh Access Token

Exchanges valid refresh token for new access token.
**Body:**

```json
{
  "refresh_token": "string"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### `POST /users/logout` – Revoke Refresh Token

Logs out current session by revoking a refresh token.

#### `POST /users/logout-all` – Revoke All Sessions

Logs out user from all devices (revokes all refresh tokens).

#### `GET /users/me/` – Get Own User Info

**JWT required.**
**Response:**

```json
{
  "id": 1,
  "username": "testuser",
  "is_active": true,
  "tier": "bronze",
  "device_fingerprint": "python_test_script_abc123"
}
```

#### `GET /users/me/sessions` – List Active Sessions

Lists active refresh tokens (i.e., all devices logged in).

---

### **Product Management**

#### `POST /products/` – Create Product

**JWT required.**
**Body:**

```json
{
  "url": "https://www.example.com/product/123",
  "price_threshold": 99.99
}
```

**Response:**

```json
{
  "id": 1,
  "url": "https://www.example.com/product/123",
  "price_threshold": 99.99,
  "owner_id": 1
}
```

#### `GET /products/me/` – List My Products

#### `GET /products/{product_id}` – Get Product (own)

#### `DELETE /products/{product_id}` – Delete Product (own)

---

### **Admin Panel (Session/IP only, HTML responses)**

* `/admin/` – Login form
* `/admin/login` – Login, creates session cookie
* `/admin/dashboard` – Dashboard/stats
* `/admin/users` – User management (activate, deactivate, tier, reset device, delete)
* `/admin/analytics` – Analytics and metrics

</details>

---

## 🗄️ Data Models

**User**

```json
{
  "id": "integer",
  "username": "string (unique)",
  "hashed_password": "string",
  "is_active": "boolean",
  "tier": "bronze|silver|gold",
  "device_fingerprint": "string (unique, nullable)"
}
```

**TrackedProduct**

```json
{
  "id": "integer",
  "url": "string",
  "price_threshold": "float",
  "owner_id": "integer"
}
```

**RefreshToken**

```json
{
  "id": "integer",
  "token": "string (unique)",
  "user_id": "integer",
  "expires_at": "datetime",
  "created_at": "datetime"
}
```

---

## ⚠️ Error Handling

All errors use this format:

```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

* `401 Unauthorized`: Invalid credentials or token
* `403 Forbidden`: Account inactive, device mismatch, or permission denied
* `404 Not Found`: Resource doesn’t exist or unauthorized access
* `409 Conflict`: Device fingerprint conflict
* `429 Too Many Requests`: Rate limiting (see `retry_after`)
* `500/503`: Internal or database error

---

## 🛡️ Environment Configuration

```bash
DATABASE_URL="postgresql://user:password@host:port/database"
PRIVATE_KEY_PATH="./private.pem"
PUBLIC_KEY_PATH="./public.pem"
ALGORITHM="EdDSA"
ACCESS_TOKEN_EXPIRE_MINUTES="1440"
REFRESH_TOKEN_EXPIRE_DAYS="7"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="YourVerySecureAdminPassword123!"
ALLOWED_ADMIN_IPS="127.0.0.1,::1"
SESSION_SECRET_KEY="your_64_character_hex_string"
ENVIRONMENT="development"
```

* **Keys:** Run `uv run --with cryptography --with python-dotenv generate_keys.py` to generate Ed25519 keypair

---

## 🐳 Deployment & Operations

* **Dockerfile** and **docker-compose.yml** included
* **Gunicorn** (with Uvicorn workers) for production
* Mount private/public keys as Docker secrets/volumes
* `/health` endpoint for container readiness/liveness

**Production notes:**

* DB connection pooling enabled
* Token cleanup is async, hourly
* CORS and session cookie config vary by `ENVIRONMENT`
* Consider Redis-backed session for admin if scaling horizontally

---

## 🧑‍💻 Philosophy

> Security by default. No implicit magic. Explicit configs. All management auditable.

* No silent failures — all errors explicit, helpful, never ambiguous
* Multi-tenant isolation enforced everywhere
* Admin is king — all user actions require admin approval
* Structured, timestamped logs, no secrets ever written

---

## 📚 References

* [FastAPI Docs](https://fastapi.tiangolo.com/)
* [Ed25519/EdDSA JWT](https://datatracker.ietf.org/doc/html/rfc8032)
* [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

---

> *This repo is a public playground . Fork ideas, code whatever You want.*

---

## ✨ This is it. ✨
