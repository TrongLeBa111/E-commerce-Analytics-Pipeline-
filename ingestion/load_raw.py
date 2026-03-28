import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# DEBUG: xóa sau khi fix xong
print(f"ENV_PATH: {ENV_PATH}")
print(f"File exists: {ENV_PATH.exists()}")
print(f"Raw content: {ENV_PATH.read_bytes()[:80]}")  # Đọc raw bytes để thấy encoding

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


def get_engine():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    # Nếu chạy trong Docker thì dùng service name, local thì dùng localhost
    host = os.getenv("POSTGRES_HOST", "localhost")
    return create_engine(f"postgresql://{user}:{password}@{host}:5432/{db}")


def load_csv_to_raw(file_path: Path, table_name: str, engine) -> int:
    logger.info(f"Loading {file_path.name} → raw.{table_name}")

    df = pd.read_csv(file_path, dtype=str)
    row_count = len(df)

    with engine.begin() as conn:
        # Truncate thay vì DROP — giữ nguyên bảng và dependencies
        conn.execute(text(f"TRUNCATE TABLE raw.{table_name}"))
        logger.info(f"Truncated raw.{table_name}")

    df.to_sql(
        name=table_name,
        con=engine,
        schema="raw",
        if_exists="append",  # Append vào bảng đã truncate
        index=False,
        chunksize=10_000
    )

    logger.info(f"Loaded {row_count:,} rows into raw.{table_name}")
    return row_count

def main():
    DATA_DIR = Path(__file__).parent.parent / "Data" / "raw"
    engine = get_engine()

    # Map tên file → tên bảng
    file_table_map = {
        "olist_orders_dataset.csv": "orders",
        "olist_order_items_dataset.csv": "order_items",
        "olist_customers_dataset.csv": "customers",
        "olist_products_dataset.csv": "products",
        "olist_sellers_dataset.csv": "sellers",
        "olist_order_payments_dataset.csv": "order_payments",
        "olist_order_reviews_dataset.csv": "order_reviews",
        "olist_geolocation_dataset.csv": "geolocation",
        "product_category_name_translation.csv": "product_category_translation",
    }

    total_loaded = 0
    for filename, table_name in file_table_map.items():
        file_path = DATA_DIR / filename
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}, skipping.")
            continue
        rows = load_csv_to_raw(file_path, table_name, engine)
        total_loaded += rows

    logger.info(f"Done. Total rows loaded: {total_loaded:,}")


if __name__ == "__main__":
    main()
