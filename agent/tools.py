# agent/tools.py
"""Agent 可调用的工具函数"""
import sqlite3
from pathlib import Path

from langchain_core.tools import tool

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop.db"


def _query(sql, params=()):
    """执行 SQL 查询，返回字典列表"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@tool
def query_order(order_id: int) -> str:
    """根据订单号查询订单详情，包括客户、状态、金额、下单时间、商品明细。

    Args:
        order_id: 订单号，例如 1001
    """
    orders = _query("""
        SELECT o.order_id, c.name AS customer_name, c.phone,
               o.status, o.total_amount, o.created_at
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_id = ?
    """, (order_id,))

    if not orders:
        return f"未找到订单 {order_id}。"

    order = orders[0]
    items = _query("""
        SELECT p.name AS product_name, oi.quantity, p.price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """, (order_id,))

    item_lines = "\n".join(
        f"  - {it['product_name']} × {it['quantity']}（单价 {it['price']} 元）"
        for it in items
    ) or "  （无商品明细）"

    return (
        f"订单 {order['order_id']}\n"
        f"客户：{order['customer_name']}（{order['phone']}）\n"
        f"状态：{order['status']}\n"
        f"金额：{order['total_amount']} 元\n"
        f"下单时间：{order['created_at']}\n"
        f"商品明细：\n{item_lines}"
    )


@tool
def query_logistics(order_id: int) -> str:
    """根据订单号查询物流轨迹，返回按时间倒序的物流状态列表。

    Args:
        order_id: 订单号，例如 1002
    """
    rows = _query("""
        SELECT status, location, updated_at
        FROM logistics
        WHERE order_id = ?
        ORDER BY updated_at DESC
    """, (order_id,))

    if not rows:
        return f"订单 {order_id} 暂无物流信息，可能尚未发货。"

    lines = "\n".join(
        f"  [{r['updated_at']}] {r['status']} - {r['location']}"
        for r in rows
    )
    return f"订单 {order_id} 的物流轨迹：\n{lines}"


@tool
def query_product(product_name: str) -> str:
    """根据商品名称查询价格和库存。

    Args:
        product_name: 商品名称关键词，例如 "耳机"
    """
    rows = _query(
        "SELECT name, price, stock FROM products WHERE name LIKE ?",
        (f"%{product_name}%",),
    )
    if not rows:
        return f"未找到包含「{product_name}」的商品。"

    lines = "\n".join(
        f"  - {r['name']}：{r['price']} 元，库存 {r['stock']} 件"
        for r in rows
    )
    return f"找到以下商品：\n{lines}"


@tool
def query_after_sales(order_id: int) -> str:
    """根据订单号查询售后工单状态。

    Args:
        order_id: 订单号，例如 1004
    """
    rows = _query("""
        SELECT ticket_id, type, status, created_at
        FROM after_sales
        WHERE order_id = ?
    """, (order_id,))

    if not rows:
        return f"订单 {order_id} 没有售后工单记录。"

    lines = "\n".join(
        f"  - 工单 {r['ticket_id']}：{r['type']}，状态 {r['status']}，创建于 {r['created_at']}"
        for r in rows
    )
    return f"订单 {order_id} 的售后记录：\n{lines}"


@tool
def query_customer_orders(phone: str) -> str:
    """根据客户手机号查询该客户的所有订单。

    Args:
        phone: 手机号，例如 "13800138001"
    """
    rows = _query("""
        SELECT o.order_id, o.status, o.total_amount, o.created_at
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE c.phone = ?
        ORDER BY o.created_at DESC
    """, (phone,))

    if not rows:
        return f"未找到手机号 {phone} 对应的订单。"

    lines = "\n".join(
        f"  - 订单 {r['order_id']}：{r['status']}，{r['total_amount']} 元，{r['created_at']}"
        for r in rows
    )
    return f"手机号 {phone} 的订单列表：\n{lines}"


# 所有工具，供 Agent 绑定
ALL_TOOLS = [
    query_order,
    query_logistics,
    query_product,
    query_after_sales,
    query_customer_orders,
]