# scripts/init_db.py
"""生成模拟商城数据库 data/shop.db"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"已删除旧数据库：{DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ============ 建表 ============
    cur.executescript("""
    CREATE TABLE customers (
        customer_id   INTEGER PRIMARY KEY,
        name          TEXT NOT NULL,
        phone         TEXT NOT NULL,
        city          TEXT
    );

    CREATE TABLE products (
        product_id    INTEGER PRIMARY KEY,
        name          TEXT NOT NULL,
        price         REAL NOT NULL,
        stock         INTEGER NOT NULL
    );

    CREATE TABLE orders (
        order_id      INTEGER PRIMARY KEY,
        customer_id   INTEGER NOT NULL,
        status        TEXT NOT NULL,      -- 待发货/已发货/已签收/已取消
        total_amount  REAL NOT NULL,
        created_at    TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE order_items (
        item_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id      INTEGER NOT NULL,
        product_id    INTEGER NOT NULL,
        quantity      INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );

    CREATE TABLE logistics (
        log_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id      INTEGER NOT NULL,
        status        TEXT NOT NULL,      -- 已揽收/运输中/派送中/已签收
        location      TEXT,
        updated_at    TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );

    CREATE TABLE after_sales (
        ticket_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id      INTEGER NOT NULL,
        type          TEXT NOT NULL,      -- 退款/换货/咨询
        status        TEXT NOT NULL,      -- 处理中/已完成/已拒绝
        created_at    TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );
    """)

    # ============ 客户 ============
    customers = [
        (1, "张三", "13800138001", "北京"),
        (2, "李四", "13800138002", "上海"),
        (3, "王五", "13800138003", "广州"),
        (4, "赵六", "13800138004", "深圳"),
        (5, "钱七", "13800138005", "杭州"),
    ]
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)

    # ============ 商品 ============
    products = [
        (1, "无线蓝牙耳机", 299.00, 50),
        (2, "机械键盘", 499.00, 30),
        (3, "人体工学椅", 1299.00, 10),
        (4, "27寸显示器", 1899.00, 15),
        (5, "手机支架", 39.00, 200),
    ]
    cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

    # ============ 订单 ============
    orders = [
        (1001, 1, "已签收", 299.00, "2026-09-10 10:23:00"),
        (1002, 1, "已发货", 499.00, "2026-09-14 15:40:00"),
        (1003, 2, "待发货", 1899.00, "2026-09-15 09:12:00"),
        (1004, 3, "已签收", 39.00, "2026-09-08 20:05:00"),
        (1005, 4, "已取消", 1299.00, "2026-09-11 11:30:00"),
        (1006, 5, "已发货", 299.00, "2026-09-13 18:20:00"),
    ]
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)

    # ============ 订单明细 ============
    order_items = [
        (1001, 1, 1),
        (1002, 1, 1),
        (1003, 2, 1),
        (1004, 5, 1),
        (1005, 3, 1),
        (1006, 1, 1),
    ]
    cur.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
        order_items,
    )

    # ============ 物流轨迹 ============
    logistics = [
        (1001, "已签收", "北京市朝阳区", "2026-09-12 14:20:00"),
        (1002, "运输中", "上海市浦东转运中心", "2026-09-15 08:30:00"),
        (1002, "已揽收", "北京市海淀区", "2026-09-14 18:00:00"),
        (1004, "已签收", "广州市天河区", "2026-09-10 16:45:00"),
        (1006, "派送中", "杭州市西湖区", "2026-09-16 09:00:00"),
        (1006, "运输中", "杭州转运中心", "2026-09-15 20:10:00"),
    ]
    cur.executemany(
        "INSERT INTO logistics (order_id, status, location, updated_at) VALUES (?, ?, ?, ?)",
        logistics,
    )

    # ============ 售后工单 ============
    after_sales = [
        (1004, "退款", "已完成", "2026-09-11 10:00:00"),
        (1005, "退款", "处理中", "2026-09-12 09:30:00"),
    ]
    cur.executemany(
        "INSERT INTO after_sales (order_id, type, status, created_at) VALUES (?, ?, ?, ?)",
        after_sales,
    )

    conn.commit()

    # ============ 验证 ============
    print(f"数据库已生成：{DB_PATH}")
    for table in ["customers", "products", "orders", "order_items", "logistics", "after_sales"]:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} 条")

    conn.close()


if __name__ == "__main__":
    init_db()