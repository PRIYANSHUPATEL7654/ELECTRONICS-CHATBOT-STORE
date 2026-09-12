# Detailed setup and usage steps

These steps are written for Windows first, with macOS/Linux alternatives where commands differ. Run commands from the folder shown in each step.

## 1. Local setup: backend

1. Open PowerShell or Command Prompt and enter the project folder:

```powershell
cd "C:\path\to\electronics-chatbot-store"
cd backend
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install backend packages:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Create the environment file:

```powershell
copy ..\.env.example .env
```

Open `backend/.env` and set a private key, for example:

```env
DATABASE_URL=sqlite:///./electronics_store.db
ADMIN_API_KEY=change-this-admin-key
```

5. Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

The first startup creates the SQLite tables and inserts exactly 50 products. Keep this terminal running. Visit `http://localhost:8000/docs` to inspect and execute endpoints interactively.

## 2. Local setup: frontend

1. Open a second terminal and enter the frontend folder:

```powershell
cd "C:\path\to\electronics-chatbot-store\frontend"
```

2. Install JavaScript packages and start Vite:

```powershell
npm install
npm run dev
```

3. Open the URL printed by Vite, normally `http://localhost:5173`.

If the backend is not running on port 8000, create `frontend/.env` with:

```env
VITE_API_URL=http://localhost:8000
```

Restart Vite after changing an environment file.

## 3. Run and use the chatbot

1. Open `http://localhost:5173`.
2. Try these questions:

```text
Show me phones
Find budget laptops in stock
What is the price of Pulse Buds Pro?
Recommend premium headphones
I want to buy a smartwatch
```

3. The assistant sends each question to `POST /chat`.
4. Product cards are rendered from the database response.
5. Click `Order now` on an in-stock product.
6. Enter a name, email, address, and quantity.
7. Submit the order. The backend validates stock, reduces the stock count, saves the order, and returns the order number and total.

## 4. Use the admin panel

1. Open `http://localhost:5173/admin`.
2. The requested demo credentials are:

```text
Username: admin
Password: admin123
```

3. Enter the value of `ADMIN_API_KEY` from `backend/.env`. The local default is `change-this-admin-key`.
4. Use the Products tab to add, edit, or delete products.
5. Use the Orders tab to see customers, addresses, ordered items, totals, and statuses.
6. The UI sends the API key as `X-Admin-Key`; the backend rejects protected requests with a 401 response if the key is missing or wrong.

## 5. Test with Postman

1. Open Postman.
2. Select Import.
3. Choose `postman/Electronics-Chatbot-Store.postman_collection.json`.
4. Open collection variables and set:

```text
baseUrl = http://localhost:8000
adminKey = change-this-admin-key
```

5. Run `Health`, then `List products`. The list should contain 50 seeded products on a fresh database.
6. Run `Chat` with the sample body.
7. Run `Create order` with product ID 1. Use a unique email if desired.
8. Run `Admin list orders` with the admin key.
9. Run the protected create, update, and delete product requests when you want to test administration.

## 6. Run the complete app with Docker

From the project root:

```powershell
docker compose up --build
```

Open:

```text
Frontend: http://localhost:8080
Backend:  http://localhost:8000
Swagger:  http://localhost:8000/docs
```

Stop containers with:

```powershell
docker compose down
```

To remove the local Docker volume and reseed from zero:

```powershell
docker compose down -v
```

## 7. Deploy the backend to Render

1. Push the project to a GitHub repository.
2. In Render, choose New > Web Service and connect the repository.
3. Select Docker as the environment.
4. Set Dockerfile path to `backend/Dockerfile` and Docker context to `backend`.
5. Set the health check path to `/health` if Render shows that option.
6. Add environment variables:

```text
ADMIN_API_KEY = a-long-random-secret
DATABASE_URL = sqlite:///./electronics_store.db
```

7. Deploy and wait for the service to become live.
8. Test `https://YOUR-BACKEND.onrender.com/health` and open `/docs`.

For a student demo, SQLite is acceptable. Hosted container disks can be reset during redeploys or restarts, so use a managed PostgreSQL database if order persistence matters.

## 8. Deploy the frontend to Render

1. Create a second Render Web Service from the same repository.
2. Select Docker.
3. Set Dockerfile path to `frontend/Dockerfile` and Docker context to `frontend`.
4. Add:

```text
VITE_API_URL = https://YOUR-BACKEND.onrender.com
```

5. Deploy the frontend.
6. Open the frontend URL and test a chat question and an order.

Important: Vite environment variables are embedded during the Docker build. If you change `VITE_API_URL`, trigger a new deploy.

The included `render.yaml` can also be used as a starting point for a Blueprint deployment. Review the generated service settings before applying it.

## 9. Set up and connect the MCP server

1. Start the FastAPI backend first.
2. Open a third terminal:

```powershell
cd "C:\path\to\electronics-chatbot-store\mcp-server"
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

3. Set environment variables in the same terminal:

```powershell
$env:STORE_API_URL="http://localhost:8000"
$env:STORE_ADMIN_API_KEY="change-this-admin-key"
```

4. Run the MCP server:

```powershell
python mcp_server.py
```

The process uses stdio, so it normally appears to wait silently. That is expected: an MCP client launches it and communicates through its standard input/output.

5. For Claude Desktop, copy `mcp-server/claude_desktop_config.json` into Claude’s configuration file, replace the absolute Windows path, restart Claude Desktop, and verify that the `electronics-store` tools appear.
6. For Cursor, add the same server configuration in Cursor’s MCP settings and use the absolute path to `mcp_server.py`.
7. Test `list_products` and `get_product` first. Then test `create_order`. Use `get_orders` only when the admin key is configured.

Example Windows configuration shape:

```json
{
  "mcpServers": {
    "electronics-store": {
      "command": "C:\\Users\\YourName\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": ["C:\\Projects\\electronics-chatbot-store\\mcp-server\\mcp_server.py"],
      "env": {
        "STORE_API_URL": "http://localhost:8000",
        "STORE_ADMIN_API_KEY": "change-this-admin-key"
      }
    }
  }
}
```

## 10. Troubleshooting

- `Connection refused`: confirm the backend terminal is running on port 8000.
- Browser CORS error: verify the browser is calling the same backend URL in `VITE_API_URL`, then restart Vite.
- 401 in admin: copy the exact `ADMIN_API_KEY` value from `backend/.env`.
- Empty catalog: delete the local SQLite file only when the API is stopped, then restart it so the seed runs again.
- Docker frontend calls the wrong backend: rebuild with `docker compose up --build` after changing frontend environment values.
- MCP server seems frozen: stdio MCP servers wait for their client; launch them from Claude Desktop or Cursor rather than expecting a browser page.

