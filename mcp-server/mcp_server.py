import os
import httpx
from mcp.server.fastmcp import FastMCP

API_URL = os.getenv("STORE_API_URL", "http://localhost:8000").rstrip("/")
ADMIN_API_KEY = os.getenv("STORE_ADMIN_API_KEY", "change-this-admin-key")
mcp = FastMCP("Electronics Chatbot Store")

async def call(path: str, method: str = "GET", payload: dict | None = None, admin: bool = False):
    headers = {"X-Admin-Key": ADMIN_API_KEY} if admin else {}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.request(method, f"{API_URL}{path}", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def list_products(category: str | None = None) -> list[dict]:
    """List products, optionally filtered by category."""
    query = f"?category={category}" if category else ""
    return await call(f"/products{query}")

@mcp.tool()
async def search_products(search: str) -> list[dict]:
    """Search the live product catalog by name, description, or category."""
    return await call(f"/products?{httpx.QueryParams({'search': search})}")

@mcp.tool()
async def get_product(product_id: int) -> dict:
    """Get one product by its numeric ID."""
    return await call(f"/products/{product_id}")

@mcp.tool()
async def create_order(customer_name: str, customer_email: str, customer_address: str, product_id: int, quantity: int = 1) -> dict:
    """Place an order for one product and quantity."""
    return await call("/orders", "POST", {"customer_name": customer_name, "customer_email": customer_email, "customer_address": customer_address, "items": [{"product_id": product_id, "quantity": quantity}]})

@mcp.tool()
async def get_orders() -> list[dict]:
    """Retrieve store orders; requires the configured admin key."""
    return await call("/orders", admin=True)

if __name__ == "__main__":
    mcp.run()
