import json
import re
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
                "query": {"type": "string"},
                "category": {"type": "string"},
                "max_price": {"type": "number"},
                "min_stock": {"type": "integer"},
                "sort_by": {"type": "string", "enum": ["relevance", "price_asc", "price_desc", "stock_desc"]},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "type": "function",
        "name": "get_product",
        "description": "Retrieve the complete record for one named product or product ID.",
        "parameters": {"type": "object", "properties": {"product_id": {"type": "integer"}, "product_name": {"type": "string"}}},
    },
    {
        "type": "function",
        "name": "compare_products",
        "description": "Retrieve multiple matching product records for a comparison.",
        "parameters": {"type": "object", "properties": {"product_ids": {"type": "array", "items": {"type": "integer"}}}, "required": ["product_ids"]},
    },
]


CATEGORY_ALIASES = {
    "phone": "Phones", "phones": "Phones", "mobile": "Phones", "mobiles": "Phones",
    "smartphone": "Phones", "smartphones": "Phones", "laptop": "Laptops", "laptops": "Laptops",
    "headphone": "Headphones", "headphones": "Headphones", "earbud": "Earbuds", "earbuds": "Earbuds",
    "smartwatch": "Smartwatches", "smartwatches": "Smartwatches", "smart watch": "Smartwatches",
    "smart watches": "Smartwatches", "camera": "Cameras", "cameras": "Cameras",
    "accessory": "Accessories", "accessories": "Accessories",
}


def detect_category(message: str) -> str | None:
    normalized = message.lower()
    for alias, category in sorted(CATEGORY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", normalized):
            return category
    return None


def product_dict(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "stock": product.stock,
        "image_url": product.image_url,
    }


def search_products(
    db: Session,
    query: str = "",
    category: str | None = None,
    max_price: float | None = None,
    min_stock: int | None = None,
    sort_by: str = "relevance",
    limit: int = 6,
) -> list[dict[str, Any]]:
    products = list(db.scalars(select(Product)).all())
    if category:
        products = [product for product in products if product.category.lower() == category.lower()]
    if max_price is not None:
        products = [product for product in products if product.price <= max_price]
    if min_stock is not None:
        products = [product for product in products if product.stock >= min_stock]

    words = [word for word in (query or "").lower().replace(",", " ").split() if len(word) > 2]

    def score(product: Product) -> int:
        text = f"{product.name} {product.description} {product.category}".lower()
        return sum(1 for word in words if word in text)

    if words:
        products = [product for product in products if score(product) > 0]
    if sort_by == "price_asc":
        products.sort(key=lambda product: product.price)
    elif sort_by == "price_desc":
        products.sort(key=lambda product: product.price, reverse=True)
    elif sort_by == "stock_desc":
        products.sort(key=lambda product: product.stock, reverse=True)
    else:
        products.sort(key=lambda product: (-score(product), product.price))

    return [product_dict(product) for product in products[:max(1, min(int(limit or 6), 6))]]


def execute_tool(db: Session, name: str, arguments: dict[str, Any], user_message: str = "") -> dict[str, Any]:
    if name == "search_products":
        # The user's explicit category always wins over a model guess.
        search_arguments = dict(arguments)
        category_hint = detect_category(user_message)
        if category_hint:
            search_arguments["category"] = category_hint
            search_arguments["query"] = ""
        return {"products": search_products(db, **search_arguments)}

    if name == "get_product":
        product_id = arguments.get("product_id")
        product = db.get(Product, int(product_id)) if product_id is not None else None
        if not product and arguments.get("product_name"):
            return {"products": search_products(db, query=str(arguments["product_name"]), limit=1)}
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
        "Answer using only results returned by catalog tools. Always call a tool for product questions. "
        "Never invent product facts. Keep the answer concise; the application renders products as cards. "
        "Do not expose database or API-key configuration details."
    )
    interaction = client.interactions.create(
        model=settings.gemini_model,
        input=f"{instructions}\n\nUser question:\n{message}",
        tools=TOOLS,
    )
    ids: list[int] = []
    for _ in range(3):
        calls = [step for step in interaction.steps if step.type == "function_call"]
        if not calls:
            answer = interaction.output_text or "I could not generate an answer."
            if len(answer) > 500 or answer.count("\n") > 5:
                answer = f"I found {len(dict.fromkeys(ids))} matching products. They are shown below as structured cards."
            return answer.strip(), list(dict.fromkeys(ids))

        function_results = []
        for call in calls:
            arguments = call.arguments if isinstance(call.arguments, dict) else json.loads(call.arguments or "{}")
            result = execute_tool(db, call.name, arguments, message)
            collect_product_ids(result, ids)
            function_results.append({"type": "function_result", "name": call.name, "call_id": call.id, "result": [{"type": "text", "text": json.dumps(result)}]})
        interaction = client.interactions.create(
            model=settings.gemini_model,
            previous_interaction_id=interaction.id,
            tools=TOOLS,
            input=function_results,
        )

    return "I found the catalog information, but the answer took too many steps. Please ask again.", list(dict.fromkeys(ids))


def answer_with_fallback(db: Session, message: str) -> tuple[str, list[int]]:
    """Answer from the database without exposing Gemini configuration details."""
    category = detect_category(message)
    normalized = message.lower()
    sort_by = "price_desc" if any(term in normalized for term in ("decreasing", "highest price", "most expensive", "expensive first")) else "price_asc" if any(term in normalized for term in ("increasing", "lowest price", "cheapest", "affordable first")) else "relevance"
    budget_match = re.search(r"(?:under|below|less than|up to|upto|budget of|within)\s*(?:â‚¹|rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(k)?", normalized)
    max_price = None
    if budget_match:
        max_price = float(budget_match.group(1).replace(",", ""))
        if budget_match.group(2):
            max_price *= 1000
    requires_stock = any(term in normalized for term in ("in stock", "available", "availability"))
    products = search_products(db, query="" if category else message, category=category, max_price=max_price, min_stock=1 if requires_stock else None, sort_by=sort_by, limit=6)

    if not products:
        answer = f"I could not find {category.lower() if category else 'products'} matching that request in the current catalog. Try another category, price range, or feature."
    else:
        scope = category.lower() if category else "matching products"
        details = []
        if max_price is not None:
            details.append(f"within â‚¹{max_price:,.0f}")
        if sort_by == "price_desc":
            details.append("highest price first")
        elif sort_by == "price_asc":
            details.append("lowest price first")
        if requires_stock:
            details.append("currently in stock")
        qualifier = f" ({', '.join(details)})" if details else ""
        answer = f"Here are {scope} from the live catalog{qualifier}. The product cards below contain the exact price, stock, and features."

    return answer, [product["id"] for product in products]


def answer_chat(db: Session, message: str) -> tuple[str, list[int]]:
    if not settings.gemini_api_key:
        return answer_with_fallback(db, message)
    try:
        return ask_gemini(db, message)
    except Exception:
        return answer_with_fallback(db, message)