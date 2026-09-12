import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import Product


TOOLS = [
    {
        "type": "function",
        "name": "search_products",
        "description": "Search and filter the live electronics catalog. Always use this for product recommendations, prices, stock, category, use-case, or budget questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Important product name, feature, or use-case words, such as coding, gaming, ANC, camera, or student."},
                "category": {"type": "string", "description": "Product category, if known: Phones, Laptops, Headphones, Earbuds, Smartwatches, Cameras, or Accessories."},
                "max_price": {"type": "number", "description": "Maximum price in Indian rupees, if the user gives a budget."},
                "min_stock": {"type": "integer", "description": "Minimum stock quantity, usually 1 when the user asks for available products."},
                "sort_by": {"type": "string", "enum": ["relevance", "price_asc", "price_desc", "stock_desc"]},
                "limit": {"type": "integer", "description": "Number of results, from 1 to 6."},
            },
        },
    },
    {
        "type": "function",
        "name": "get_product",
        "description": "Retrieve the complete record for one product when the user asks about a named product or product ID.",
        "parameters": {"type": "object", "properties": {"product_id": {"type": "integer"}, "product_name": {"type": "string"}}},
    },
    {
        "type": "function",
        "name": "compare_products",
        "description": "Retrieve multiple matching product records for a comparison.",
        "parameters": {"type": "object", "properties": {"product_ids": {"type": "array", "items": {"type": "integer"}}}, "required": ["product_ids"]},
    },
]


def product_dict(product: Product) -> dict[str, Any]:
    return {"id": product.id, "name": product.name, "description": product.description, "price": product.price, "category": product.category, "stock": product.stock, "image_url": product.image_url}


def search_products(db: Session, query: str = "", category: str | None = None, max_price: float | None = None, min_stock: int | None = None, sort_by: str = "relevance", limit: int = 6) -> list[dict[str, Any]]:
    query = query or ""
    limit = int(limit or 6)
    products = list(db.scalars(select(Product)).all())
    if category:
        products = [p for p in products if p.category.lower() == category.lower()]
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]
    if min_stock is not None:
        products = [p for p in products if p.stock >= min_stock]
    words = [word for word in query.lower().replace(",", " ").split() if len(word) > 2]

    def score(product: Product) -> int:
        text = f"{product.name} {product.description} {product.category}".lower()
        return sum(1 for word in words if word in text)

    if words:
        products = [p for p in products if score(p) > 0]
    if sort_by == "price_asc":
        products.sort(key=lambda p: p.price)
    elif sort_by == "price_desc":
        products.sort(key=lambda p: p.price, reverse=True)
    elif sort_by == "stock_desc":
        products.sort(key=lambda p: p.stock, reverse=True)
    else:
        products.sort(key=lambda p: (-score(p), p.price))
    return [product_dict(p) for p in products[:max(1, min(limit, 6))]]


def execute_tool(db: Session, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "search_products":
        return {"products": search_products(db, **arguments)}
    if name == "get_product":
        product_id = arguments.get("product_id")
        product = db.get(Product, int(product_id)) if product_id is not None else None
        if not product and arguments.get("product_name"):
            matches = search_products(db, query=str(arguments["product_name"]), limit=1)
            return {"products": matches}
        return {"products": [product_dict(product)] if product else [], "message": "Product not found" if not product else ""}
    if name == "compare_products":
        products = [db.get(Product, product_id) for product_id in arguments.get("product_ids", [])]
        return {"products": [product_dict(product) for product in products if product]}
    return {"error": f"Unknown tool: {name}"}


def collect_product_ids(value: Any, output: list[int]) -> None:
    if isinstance(value, dict):
        if isinstance(value.get("id"), int) and "name" in value:
            output.append(value["id"])
        for child in value.values():
            collect_product_ids(child, output)
    elif isinstance(value, list):
        for child in value:
            collect_product_ids(child, output)


def ask_gemini(db: Session, message: str) -> tuple[str, list[int]]:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    instructions = (
        "You are ElectroChat, a helpful electronics store assistant. "
        "Answer the user's question using only the results returned by your catalog tools. "
        "You must call a tool before answering any question about products, prices, stock, comparisons, recommendations, budgets, features, or categories. "
        "Never invent a product, price, stock count, feature, discount, delivery promise, or order status. "
        "If the catalog has no matching result, say that clearly and suggest a nearby category. "
        "Return a concise answer of at most 3 short sentences. Use a small heading if useful. "
        "Do not write a numbered product list, markdown table, repeated product descriptions, prices, or stock quantities in the text answer; the application renders those records as structured product cards below your message. "
        "Mention the sorting/filter used and recommend products based on the user's stated purpose. "
        "Do not expose database implementation details."
    )
    prompt = f"{instructions}\n\nUser question:\n{message}"
    interaction = client.interactions.create(model=settings.gemini_model, input=prompt, tools=TOOLS)
    ids: list[int] = []
    for _ in range(3):
        calls = [step for step in interaction.steps if step.type == "function_call"]
        if not calls:
            answer = interaction.output_text or "I could not generate an answer."
            if len(answer) > 500 or answer.count("**") >= 4 or answer.count("\n") > 5:
                answer = f"I found {len(dict.fromkeys(ids))} matching products. They are shown below as structured cards in the requested order."
            return answer.strip(), list(dict.fromkeys(ids))
        function_results = []
        for call in calls:
            arguments = call.arguments if isinstance(call.arguments, dict) else json.loads(call.arguments or "{}")
            result = execute_tool(db, call.name, arguments)
            collect_product_ids(result, ids)
            function_results.append({"type": "function_result", "name": call.name, "call_id": call.id, "result": [{"type": "text", "text": json.dumps(result)}]})
        interaction = client.interactions.create(model=settings.gemini_model, previous_interaction_id=interaction.id, tools=TOOLS, input=function_results)
    return "I found the catalog information, but the answer took too many steps. Please ask the question again.", list(dict.fromkeys(ids))


def answer_with_fallback(db: Session, message: str) -> tuple[str, list[int]]:
    """Safe no-key fallback. The AI path above is used whenever GEMINI_API_KEY exists."""
    products = search_products(db, query=message, limit=6)
    if not products:
        products = search_products(db, limit=6)
    return "I am using catalog search because GEMINI_API_KEY is not configured. Add the key to enable natural-language AI answers.", [p["id"] for p in products]


def answer_chat(db: Session, message: str) -> tuple[str, list[int]]:
    if not settings.gemini_api_key:
        return answer_with_fallback(db, message)
    try:
        return ask_gemini(db, message)
    except Exception:
        return answer_with_fallback(db, message)
