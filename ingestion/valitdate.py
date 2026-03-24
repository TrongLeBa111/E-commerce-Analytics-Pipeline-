from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def get_engine():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    return create_engine(f"postgresql://{user}:{password}@localhost:5432/{db}")


VALIDATION_QUERIES = {
    "row_counts": """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'raw'
        ORDER BY table_name;
    """,

    "orders_null_check": """
        SELECT 
            COUNT(*) AS total_rows,
            COUNT(order_id) AS non_null_order_id,
            COUNT(customer_id) AS non_null_customer_id,
            COUNT(order_status) AS non_null_status,
            COUNT(order_purchase_timestamp) AS non_null_purchase_ts
        FROM raw.orders;
    """,

    "orders_duplicate_check": """
        SELECT order_id, COUNT(*) AS cnt
        FROM raw.orders
        GROUP BY order_id
        HAVING COUNT(*) > 1
        LIMIT 10;
    """,
    "geolocation_duplicate_check": """
        SELECT geolocation_zip_code_prefix, COUNT(*) AS cnt
        FROM raw.geolocation
        GROUP BY geolocation_zip_code_prefix
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 5;
    """,
    "orphan_order_items": """
        SELECT COUNT(*) AS orphan_count
        FROM raw.order_items oi
        LEFT JOIN raw.orders o ON oi.order_id = o.order_id
        WHERE o.order_id IS NULL;
    """,
}


def run_validations(engine):
    with engine.connect() as conn:
        for check_name, query in VALIDATION_QUERIES.items():
            print(f"\n{'=' * 50}")
            print(f"CHECK: {check_name}")
            result = conn.execute(text(query))
            rows = result.fetchall()
            for row in rows:
                print(dict(row._mapping))


if __name__ == "__main__":
    engine = get_engine()
    run_validations(engine)