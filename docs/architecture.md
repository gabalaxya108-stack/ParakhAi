# Modular Architecture Foundation

## Directory Structure

```
.
├── backend/                  # Python + FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py    # Health check endpoint (GET /api/v1/health)
│   │   │       └── router.py        # Versioned API router
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings & environment parsing
│   │   │   ├── errors.py            # Custom exception hierarchy & standard handlers
│   │   │   └── logging.py           # Structured logging setup
│   │   ├── schemas/
│   │   │   ├── error.py             # Standard error response envelope
│   │   │   └── health.py            # Health check response model
│   │   └── main.py                  # FastAPI factory, CORS, request middleware
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts            # Type-safe generic Fetch API client
│   │   │   └── health.ts            # Health check service
│   │   ├── components/
│   │   │   └── HealthCard.tsx       # System health status display component
│   │   ├── types/
│   │   │   ├── api.ts               # Standard API envelopes & errors
│   │   │   └── health.ts            # Health response interfaces
│   │   ├── App.tsx                  # Foundation landing view
│   │   ├── main.tsx
│   │   └── index.css                # Tailwind CSS styling
│   ├── Dockerfile
│   └── package.json
├── data/                     # Data directory (package images, datasets)
├── rules/                    # Declarative / versioned legal rule definitions
├── tests/                    # Automated test suites
│   ├── conftest.py                  # Pytest fixtures and TestClient
│   └── test_health.py               # Health and root endpoint tests
├── docs/                     # Architecture & API documentation
├── docker-compose.yml        # Multi-container orchestration
└── README.md                 # Project setup and running instructions
```

## Architectural Principles

1. **Strict Decoupling**: Frontend communicates with the backend exclusively through type-safe, versioned endpoints (`/api/v1/`).
2. **Standardized Error Handling**: All API exceptions are caught and wrapped in a consistent error envelope:
   ```json
   {
     "error": {
       "code": "ERROR_CODE",
       "message": "Human readable message",
       "details": null,
       "timestamp": "2026-09-03T13:50:00Z"
     }
   }
   ```
3. **Structured Logging & Telemetry**: Every HTTP request is intercepted, timed, and logged with method, path, status code, and execution time in milliseconds.
4. **Environment-Driven Configuration**: Settings are validated at startup through Pydantic v2 `BaseSettings` reading from `.env` files with strict type-checking.
