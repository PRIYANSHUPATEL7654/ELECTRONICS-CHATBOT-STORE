# Electronics Chatbot Store

Electronics Chatbot Store is a complete student-friendly full-stack application for live product questions and ordering. Customers chat with a catalog assistant, see matching product cards, and place orders. Store administrators can add, edit, delete, and inspect products and orders.

## Features

- FastAPI REST API with automatic Swagger documentation at `/docs`.
- SQLite database for local development and a simple SQLAlchemy model layer.
- Exactly 50 seeded electronics products across phones, laptops, headphones, earbuds, smartwatches, cameras, and accessories.
- Search and category filters on `GET /products`.
- Keyword-based product chatbot on `POST /chat` that returns an answer, matching products, and suggested questions.
- Order creation with stock validation and automatic stock reduction.
- API-key protected product mutations and order listing.
- Responsive React + Vite + Tailwind frontend.
- Chat bubbles, product cards, and an order form inside the conversation.
- Admin panel at `/admin` with product table and order view.
- Postman collection covering public and protected endpoints.
- Docker Compose for local full-stack execution.
- Render-ready Dockerfiles and `render.yaml`.
- Official MCP SDK server exposing catalog and ordering tools to Claude Desktop, Cursor, or another MCP client.

## Architecture

```text
React/Vite/Tailwind UI  --->  FastAPI REST API  --->  SQLite + SQLAlchemy
       |                            ^
       |                            |
       +---- /chat + /orders        +---- MCP server tools
```

The browser calls the backend directly. The backend owns product, order, stock, validation, and authentication logic. The MCP server is a separate adapter: it calls the same REST API and does not duplicate database logic.

## Folder structure

```text
electronics-chatbot-store/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── seed.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api.js
│   │   ├── index.css
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── mcp-server/
│   ├── claude_desktop_config.json
│   ├── mcp_server.py
│   └── requirements.txt
├── postman/
│   └── Electronics-Chatbot-Store.postman_collection.json
├── docker-compose.yml
├── render.yaml
├── .env.example
├── README.md
└── DETAILED_STEPS.md
```

## API summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | No | Health check |
| GET | `/products` | No | List/search/filter products |
| GET | `/products/{id}` | No | Product details |
| POST | `/products` | `X-Admin-Key` | Add product |
| PUT | `/products/{id}` | `X-Admin-Key` | Update product |
| DELETE | `/products/{id}` | `X-Admin-Key` | Delete product |
| POST | `/orders` | No | Place an order |
| GET | `/orders` | `X-Admin-Key` | View all orders |
| POST | `/chat` | No | Ask the store assistant |

## Admin authentication

The demo panel uses the requested student credentials:

- Username: `admin`
- Password: `admin123`

The frontend then sends the backend API key in `X-Admin-Key`. For local use, the default key is `change-this-admin-key`; change it in the backend `.env` and enter the same key in the panel. For a public deployment, always use a long random key and HTTPS.

## Run locally

The exact copy-paste commands are in [DETAILED_STEPS.md](DETAILED_STEPS.md). The short version is:

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy ..\\.env.example .env  # Windows
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API docs are at `http://localhost:8000/docs`.

## Run with Docker

From the project root:

```bash
docker compose up --build
```

Open `http://localhost:8080`; the API is at `http://localhost:8000`.

## Render deployment

The repository contains separate Docker services for the backend and frontend. Deploy the backend first, set `ADMIN_API_KEY`, copy its public URL, then deploy the frontend with `VITE_API_URL` set to that backend URL. Detailed Render instructions are in [DETAILED_STEPS.md](DETAILED_STEPS.md).

SQLite is suitable for a student demo but is ephemeral on many hosting platforms. For production durability, set `DATABASE_URL` to a managed PostgreSQL connection string and install a PostgreSQL driver such as `psycopg[binary]`. The SQLAlchemy code is designed so the database URL can be changed without changing the API contract.

## MCP server

The MCP adapter provides these tools:

- `list_products(category?)`
- `search_products(search)`
- `get_product(product_id)`
- `create_order(customer_name, customer_email, customer_address, product_id, quantity)`
- `get_orders()`

Start the REST API first. Then run the MCP server from `mcp-server` with `python mcp_server.py`, or configure it in Claude Desktop using the included example. Replace the placeholder absolute path in `claude_desktop_config.json`.

## Security notes

This is a complete educational project, not a payment gateway or enterprise commerce platform. It deliberately does not collect card details. Before a real deployment, add user authentication, HTTPS-only cookies or OAuth, rate limiting, audit logs, CSRF protection for browser sessions, PostgreSQL, migrations, and a real payment provider.
