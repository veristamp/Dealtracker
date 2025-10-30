# DealTracker Backend API Documentation

## Overview

The DealTracker API is a comprehensive FastAPI-based backend service that provides user authentication, product tracking, and administrative capabilities. The system features JWT-based authentication with refresh tokens, device fingerprinting, rate limiting, and a complete admin panel for user management.

**Base URL:** `http://127.0.0.1:8592`  
**API Version:** 1.0.0  
**Authentication:** JWT Bearer Token with Refresh Token Support

## Authentication System

### Security Features
- **JWT Authentication** with EdDSA algorithm
- **Refresh Token Management** with database storage and revocation
- **Device Fingerprinting** for enhanced security
- **Rate Limiting** to prevent abuse
- **Session-based Admin Authentication** with IP whitelisting

### Token Lifecycle
- **Access Token Expiry:** 1440 minutes (24 hours)
- **Refresh Token Expiry:** 7 days
- **Automatic Cleanup** of expired tokens every hour

## API Endpoints

### 1. User Authentication & Management

#### **POST /users/** - Register New User
Creates a new user account with inactive status by default.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "testuser",
  "is_active": false,
  "tier": "bronze",
  "device_fingerprint": null
}
```

**Error Responses:**
- `400 Bad Request` - Username already exists
- `500 Internal Server Error` - Failed to create user

#### **POST /users/token** - User Login
Authenticates user and returns access and refresh tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "device_fingerprint": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Account inactive or device fingerprint mismatch
- `500 Internal Server Error` - Login processing error

**Security Notes:**
- First login registers the device fingerprint
- Subsequent logins must match the registered fingerprint
- Inactive accounts cannot login

#### **POST /users/refresh** - Refresh Access Token
Generates a new access token using a valid refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired refresh token
- `403 Forbidden` - Account inactive

#### **POST /users/logout** - User Logout
Revokes the specified refresh token.

**Headers:** `Authorization: Bearer `

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### **POST /users/logout-all** - Logout All Devices
Revokes all refresh tokens for the current user.

**Headers:** `Authorization: Bearer `

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out from all devices successfully (3 sessions ended)"
}
```

#### **GET /users/me/** - Get Current User
Returns the current authenticated user's information.

**Headers:** `Authorization: Bearer `

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "testuser",
  "is_active": true,
  "tier": "bronze",
  "device_fingerprint": "python_test_script_abc123"
}
```

#### **GET /users/me/sessions** - Get User Sessions
Returns information about active sessions for the current user.

**Headers:** `Authorization: Bearer `

**Response (200 OK):**
```json
{
  "active_sessions": 2,
  "sessions": [
    {
      "id": 1,
      "created_at": "2025-07-13T10:30:00Z",
      "expires_at": "2025-07-20T10:30:00Z"
    },
    {
      "id": 2,
      "created_at": "2025-07-13T11:15:00Z",
      "expires_at": "2025-07-20T11:15:00Z"
    }
  ]
}
```

### 2. Product Management

#### **POST /products/** - Create Product
Creates a new tracked product for the authenticated user.

**Headers:** `Authorization: Bearer `

**Request Body:**
```json
{
  "url": "https://www.example.com/product/123",
  "price_threshold": 99.99
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "url": "https://www.example.com/product/123",
  "price_threshold": 99.99,
  "owner_id": 1
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `500 Internal Server Error` - Failed to create product

#### **GET /products/** - Get All Products (Admin)
Returns all tracked products across all users (admin function).

**Headers:** `Authorization: Bearer `

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum records to return (default: 100)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "url": "https://www.example.com/product/123",
    "price_threshold": 99.99,
    "owner_id": 1
  },
  {
    "id": 2,
    "url": "https://www.example.com/product/456",
    "price_threshold": 149.99,
    "owner_id": 2
  }
]
```

#### **GET /products/me/** - Get User's Products
Returns all tracked products for the authenticated user.

**Headers:** `Authorization: Bearer `

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "url": "https://www.example.com/product/123",
    "price_threshold": 99.99,
    "owner_id": 1
  }
]
```

#### **GET /products/{product_id}** - Get Specific Product
Returns a specific product if owned by the authenticated user.

**Headers:** `Authorization: Bearer `

**Response (200 OK):**
```json
{
  "id": 1,
  "url": "https://www.example.com/product/123",
  "price_threshold": 99.99,
  "owner_id": 1
}
```

**Error Responses:**
- `404 Not Found` - Product not found or not owned by user

#### **DELETE /products/{product_id}** - Delete Product
Deletes a specific product if owned by the authenticated user.

**Headers:** `Authorization: Bearer `

**Response (200 OK):**
```json
{
  "id": 1,
  "url": "https://www.example.com/product/123",
  "price_threshold": 99.99,
  "owner_id": 1
}
```

**Error Responses:**
- `404 Not Found` - Product not found or not owned by user
- `500 Internal Server Error` - Failed to delete product

### 3. System Endpoints

#### **GET /** - Root Endpoint
Returns basic API information.

**Rate Limit:** 10 requests per minute

**Response (200 OK):**
```json
{
  "message": "Welcome to the DealTracker API",
  "version": "1.0.0",
  "status": "operational"
}
```

#### **GET /health** - Health Check
Returns system health status and database connectivity.

**Rate Limit:** 30 requests per minute

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-07-13T15:30:00.000Z"
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Connection timeout"
}
```

#### **GET /info** - API Information
Returns detailed API information and features.

**Rate Limit:** 5 requests per minute

**Response (200 OK):**
```json
{
  "title": "DealTracker API",
  "description": "Backend services for the DealTracker Desktop application",
  "version": "1.0.0",
  "environment": "development",
  "features": [
    "JWT Authentication with Refresh Tokens",
    "Device Fingerprinting",
    "Rate Limiting",
    "Admin Panel",
    "Product Tracking",
    "Price Alerts"
  ]
}
```

### 4. Admin Panel API

**Base URL:** `/admin`  
**Authentication:** Session-based with IP whitelisting

#### **GET /admin/** - Admin Login Page
Returns the admin login form.

**Response:** HTML login page

#### **POST /admin/login** - Admin Login
Authenticates admin user and creates session.

**Request Body (Form Data):**
```
username: admin
password: YourVerySecureAdminPassword123!
```

**Response:** Redirect to `/admin/dashboard`

**Security:**
- IP address must be in allowed list (`127.0.0.1, ::1`)
- Session-based authentication
- Secure session cookies

#### **GET /admin/dashboard** - Admin Dashboard
Returns the main admin dashboard with system statistics.

**Authentication:** Admin session required

**Response:** HTML dashboard with stats

#### **GET /admin/users** - User Management Page
Returns the user management interface.

**Authentication:** Admin session required

**Response:** HTML page with user list and management controls

#### **GET /admin/analytics** - Analytics Page
Returns the analytics dashboard with system metrics.

**Authentication:** Admin session required

**Response:** HTML page with charts and statistics

#### **GET /admin/api/stats** - Dashboard Statistics API
Returns JSON statistics for the admin dashboard.

**Authentication:** Admin session required

**Response (200 OK):**
```json
{
  "total_users": 25,
  "active_users": 18,
  "total_products": 47,
  "pending_users": 7,
  "tier_distribution": {
    "bronze": 20,
    "silver": 4,
    "gold": 1
  }
}
```

#### **GET /admin/api/users** - Paginated Users API
Returns paginated user list with search and filtering.

**Authentication:** Admin session required

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Page size (default: 10)
- `search` (string): Username search filter
- `status` (string): Filter by status ("active" or "inactive")
- `tier` (string): Filter by tier ("bronze", "silver", "gold")

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "testuser",
      "is_active": true,
      "tier": "bronze",
      "device_fingerprint": "registered",
      "product_count": 3
    }
  ],
  "total": 25,
  "page": 1,
  "size": 10,
  "pages": 3
}
```

#### **PUT /admin/api/users/{user_id}/status** - Update User Status
Updates user active/inactive status.

**Authentication:** Admin session required

**Request Body:**
```json
{
  "is_active": true
}
```

**Response (200 OK):**
```json
{
  "message": "User status updated successfully"
}
```

#### **PUT /admin/api/users/{user_id}/tier** - Update User Tier
Updates user tier level.

**Authentication:** Admin session required

**Request Body:**
```json
{
  "tier": "silver"
}
```

**Valid Tiers:** `bronze`, `silver`, `gold`

**Response (200 OK):**
```json
{
  "message": "User tier updated successfully"
}
```

#### **DELETE /admin/api/users/{user_id}** - Delete User
Permanently deletes a user and all associated data.

**Authentication:** Admin session required

**Response (200 OK):**
```json
{
  "message": "User testuser deleted successfully"
}
```

#### **GET /admin/api/products** - All Products API
Returns paginated list of all tracked products.

**Authentication:** Admin session required

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Page size (default: 10)

**Response (200 OK):**
```json
{
  "products": [
    {
      "id": 1,
      "url": "https://www.example.com/product/123",
      "price_threshold": 99.99,
      "owner_id": 1,
      "owner_username": "testuser"
    }
  ],
  "total": 47,
  "page": 1,
  "size": 10,
  "pages": 5
}
```

## Data Models

### User Model
```json
{
  "id": "integer",
  "username": "string (unique)",
  "hashed_password": "string",
  "is_active": "boolean",
  "tier": "string (bronze|silver|gold)",
  "device_fingerprint": "string (unique, nullable)"
}
```

### TrackedProduct Model
```json
{
  "id": "integer",
  "url": "string",
  "price_threshold": "float",
  "owner_id": "integer (foreign key to User)"
}
```

### RefreshToken Model
```json
{
  "id": "integer",
  "token": "string (unique)",
  "user_id": "integer (foreign key to User)",
  "expires_at": "datetime",
  "created_at": "datetime"
}
```

## Error Handling

### Standard HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 405 | Method Not Allowed | HTTP method not supported |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service temporarily unavailable |


### Error Response Format
```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

### Rate Limiting
When rate limits are exceeded, the API returns:
```json
{
  "error": "Rate limit exceeded",
  "detail": "Rate limit exceeded: 10 per 1 minute",
  "retry_after": 60
}
```

## Security Considerations

### Authentication Security
- **JWT Tokens** use EdDSA algorithm with asymmetric keys
- **Refresh Tokens** are stored in database for revocation capability
- **Device Fingerprinting** prevents unauthorized device access
- **Password Hashing** uses bcrypt with salt

### API Security
- **Rate Limiting** prevents abuse and brute force attacks
- **CORS Configuration** restricts cross-origin requests
- **Input Validation** using Pydantic models
- **SQL Injection Protection** via SQLAlchemy ORM

### Admin Security
- **IP Whitelisting** restricts admin access to specific IPs
- **Session-based Authentication** for admin panel
- **Secure Session Cookies** with proper expiration
- **Audit Logging** for all admin actions

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/` | 10 requests | 1 minute |
| `/health` | 30 requests | 1 minute |
| `/info` | 5 requests | 1 minute |
| `/users/token` | 5 requests | 1 minute |
| All other endpoints | 60 requests | 1 minute |

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL="postgresql://user:password@host:port/database"

# JWT Configuration
PRIVATE_KEY_PATH="./private.pem"
PUBLIC_KEY_PATH="./public.pem"
ALGORITHM="EdDSA"
ACCESS_TOKEN_EXPIRE_MINUTES="1440"
REFRESH_TOKEN_EXPIRE_DAYS="7"

# Admin Configuration
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="YourVerySecureAdminPassword123!"
ALLOWED_ADMIN_IPS="127.0.0.1,::1"
SESSION_SECRET_KEY="your_64_character_hex_string"

# Application
ENVIRONMENT="development"
```
### Device Fingerprint Conflict Handling

**Error Response (409 Conflict):**
{
"detail": "This device is already registered to another user. Please contact support if this is your device."
}

text

**When this occurs:**
- Another user has already registered this device fingerprint
- System prevents device sharing between accounts
- Contact admin for device fingerprint reset if needed
## Production Deployment

### Deployment Readiness
This API is **production-ready** with:
- ✅ Comprehensive error handling and validation
- ✅ Security measures properly implemented
- ✅ Multi-tenant user isolation working correctly
- ✅ Database operations with proper constraint handling
- ✅ Rate limiting and authentication protection

### Performance Considerations
- Database connection pooling recommended for high load
- Consider Redis for session storage in multi-instance deployments
- Monitor rate limiting thresholds based on actual usage patterns
## Testing

### API Testing
The API includes a comprehensive test suite that validates:
- User registration and authentication
- Token refresh and logout functionality
- Product CRUD operations
- Rate limiting behavior
- Admin panel functionality
- Database connectivity

### Test Results
All endpoints have been tested and verified to work correctly with proper error handling, security measures, and data validation.

This documentation covers the complete DealTracker backend API with all endpoints, authentication mechanisms, security features, and usage examples. The API is production-ready with comprehensive error handling, rate limiting, and security measures in place.