# 🏷️ DealTracker

**DealTracker** is your personal desktop assistant for catching the best online deals!
Track prices, view analytics, and get instant alerts when your favorite products drop in price — all while keeping your data private and secure.

> 💡 Built as a **three-tier system** — Auth Backend, Local Smart Client, and Frontend Dashboard — DealTracker demonstrates secure authentication, real-time alerts, and a full offline-first architecture.

---

## 🌐 Project Overview

DealTracker consists of **three major components** working together:

| Component                            | Description                                                                                     | Tech Stack                                 |
| ------------------------------------ | ----------------------------------------------------------------------------------------------- | ------------------------------------------ |
| **Auth Backend (`Backend/`)**        | Central authentication and user management system.                                              | FastAPI, PostgreSQL, Ed25519 JWT, Docker   |
| **Local Smart Client (`client/`)**   | Local FastAPI server running on your PC; handles scraping, caching, and frontend serving.       | FastAPI, SQLite, APScheduler, Cryptography |
| **Frontend Dashboard (`Frontend/`)** | React + Vite web interface for managing products, viewing analytics, and receiving live alerts. | React, Vite, TypeScript, shadcn/ui         |

---

## ✨ Key Features

### 🛡️ Secure Authentication

* **EdDSA (Ed25519) JWT** tokens for access and refresh.
* **Per-device fingerprints** (anti-sharing and admin resettable).
* **Revocable refresh tokens** — per device, DB-tracked.
* **bcrypt** password hashing + strict CORS, CSP, and rate limiting.

### ⚙️ Smart Local Server

* Runs on your PC (`127.0.0.1:8001`) and serves the web UI.
* **Encrypted session vault** using Fernet — your tokens never leave your device.
* **Local SQLite cache** for instant UI responses.
* **Automated background scraping** with APScheduler + crawl4ai.
* **Live SSE alerts** for real-time price drops.

### 📊 Modern Frontend

* Sleek, responsive dashboard built with **React + Tailwind + shadcn/ui**.
* Manage tracked products, view price history charts, and control background tasks.
* **Live toasts + dark mode + data tables + filters**.
* Communicates securely with the Local Server via `/api/...`.

### 🔔 Real-Time Alerts

* **Desktop notifications** for price drops.
* (Coming Soon) Telegram, Email, WhatsApp, and push notifications.

---

## 🖥️ Quick Start (No Coding Required) Windows Only

For non-technical users, the setup is automated.(for windows Users Only)

1. **Unzip** the DealTracker.rar folder anywhere on your PC.
2. **Double-click** `setup.bat` — it installs everything automatically.
3. **Launch** `DealTracker.exe` — your local app starts and opens in the browser.

You can now register, log in, and begin tracking products instantly.
No command-line or technical setup required!

> 🪄 *Setup installs dependencies, starts the local FastAPI server,use the prebuilt React app, and launches it automatically. but this still need to host the auth-backend somewhere in vps or locally. Read-Below how to setup the Auth-Backend*
---

## 🧠 Developer Setup (Full Stack)

### Prerequisites

* Python 3.10+
* uv (python)
* Node.js 18+
* Docker (for backend)
* Git

---

### 1️⃣ Backend Setup (`server/`)

```bash
Install uv (python)

curl -LsSf https://astral.sh/uv/install.sh | sh #for mac or linux
or
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" #for windows

cd server
cp .env.example .env
uv run --with cryptography --with python-dotenv server/generate_keys.py
docker-compose up --build
```

The Auth Backend will start at **[http://localhost:8592](http://localhost:8592)**

---

### 2️⃣ Local Client Setup (`client/`)

```bash
#create Virtual Environment
python -m venv .venv
or 
uv venv .venv

#Activate Virtual Environment
#For Linux/Mac
source .venv/bin/activate    
#For Windows
.venv\Scripts\activate

#install requirements
uv pip install -r requirements.txt
or
pip install -r requirements.txt
```

Configure `.env`:

```bash
cp .env.example .env
```

Run the local FastAPI server:

```bash
python main.py
```

Runs at **[http://127.0.0.1:8001](http://127.0.0.1:8001)**
This server serves the frontend and manages scraping, local cache, and notifications.

---

### 3️⃣ Frontend Setup (`Frontend/`)
There is already a dist folder so you dont have to run the build. but if you wanna add your customization in Frontend follow the below steps

```bash
cd Frontend
npm install
npm run dev
```

Frontend runs on **[http://localhost:5173](http://localhost:5173)** (Vite dev mode).
In production, the built assets are copied into `client/dist/`.

---

## 🔑 Authentication Architecture (Simplified)

| Token         | Lifetime      | Usage        | Storage                  |
| ------------- | ------------- | ------------ | ------------------------ |
| Access Token  | 24h           | API auth     | Memory                   |
| Refresh Token | 7d            | Renew access | Encrypted vault (Fernet) |
| Admin Session | Session-based | Admin panel  | Secure cookie            |

* Device fingerprints ensure one device per account.
* Admins can reset fingerprints or revoke tokens.
* All admin actions and logins are logged.

---

## 📈 Core Workflow

1. **User registers** → Backend stores inactive user → Admin approves.
2. **User logs in** → Device fingerprint bound → JWTs issued.
3. **Local Client stores tokens** in an encrypted vault.
4. **Frontend interacts only with Local Client** via `/api`.
5. **Local Client scrapes and syncs** product data, pushing live alerts.

---

## 🧩 Example Endpoints

| Route                 | Description                  |
| --------------------- | ---------------------------- |
| `POST /users/`        | Register new user            |
| `POST /users/token`   | Login and receive JWTs       |
| `POST /users/refresh` | Refresh access token         |
| `GET /users/me/`      | Get own user info            |
| `POST /products/`     | Add tracked product          |
| `GET /products/me/`   | List user’s tracked products |
| `/admin/...`          | HTML-based admin interface   |

---

## 💾 Environment Variables (server)

```bash
DATABASE_URL="postgresql://postgres:postgres@postgres:5432/mykb"
PRIVATE_KEY_PATH="./private.pem"
PUBLIC_KEY_PATH="./public.pem"
ALGORITHM="EdDSA"
ACCESS_TOKEN_EXPIRE_MINUTES="1440"
REFRESH_TOKEN_EXPIRE_DAYS="7"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="StrongAdminPassword123!"
ALLOWED_ADMIN_IPS="127.0.0.1,::1"
SESSION_SECRET_KEY="your_64_character_hex_string"
ENVIRONMENT="production"
```

---

## 📦 Deployment

* **Dockerized backend** with Gunicorn + Uvicorn workers
* **Client server** runs locally or can be bundled into an executable
* **Frontend** served as static assets from the Local Client
* **Health check endpoint** `/health` for readiness probes

---

## 📚 References

* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [Ed25519 / EdDSA JWT RFC](https://datatracker.ietf.org/doc/html/rfc8032)
* [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

---

## 💬 Feedback

Got an idea or found a bug?
Open an [issue](https://github.com/veristamp/DealTracker/issues) or share suggestions!

---

## 🧭 Roadmap
```
✅ Secure authentication & local client
✅ Live frontend alerts
🚧 Telegram & Email notifications
🚧 Flipkart support
🚧 Mobile companion app
```
---

## ⚖️ License

**MIT License** — feel free to fork, modify, and build upon it.
Just remember to credit the original author.

---

> **Track smarter. Shop better. Save more — with DealTracker.**

---

> ⚠️ **Note from the Developer**
>
> This project was never meant to be “just a scraper.”  
> **DealTracker** started as my experiment to build a **complete SaaS-style environment** —  
> from secure backend auth to frontend UI and local orchestration — while I was learning full-stack development.  
>
> The small scraper included here (about 100 lines) was only a demo component.  
> The real goal was to understand **how a real SaaS system is structured** — with authentication, background jobs,  
> Dockerized infrastructure, and a frontend.  
>
> So if you’re here expecting a simple scraper — it’s much more than that 😄.  
> This is the full-stack learning playground that got me started on my dev journey.

