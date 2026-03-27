[README.md](https://github.com/user-attachments/files/26198553/README.md)
# E-commerce Analytics Pipeline

Một end-to-end data pipeline xây dựng trên dataset thương mại điện tử Olist (Brazil), bao gồm các bước ingestion, transformation, và analytics theo kiến trúc 3-layer tiêu chuẩn.

---

## Kiến trúc tổng quan

```
CSV (Kaggle)
    │
    ▼
[Ingestion — Python + pandas]
    │
    ▼
PostgreSQL · schema: raw          ← dữ liệu gốc, không transform
    │
    ▼
[Transform — dbt]
    │
    ├── schema: staging            ← cleaned, cast type, rename
    │
    └── schema: marts              ← fact & dimension tables
```

**Stack công nghệ:**

| Layer | Công nghệ |
|---|---|
| Ingestion | Python, pandas, SQLAlchemy |
| Storage | PostgreSQL 15 (Docker) |
| Transform | dbt Core |
| Orchestration | Apache Airflow |
| Infrastructure | Docker, Docker Compose |

---

## Cấu trúc thư mục

```
E-commerce-Analytics-Pipeline/
├── docker-compose.yml
├── init_schemas.sql
├── .env.sample
├── .gitignore
├── requirements.txt
├── README.md
│
├── Data/
│   └── raw/                    # Chứa CSV gốc từ Kaggle (gitignore)
│
├── ingestion/
│   ├── load_raw.py             # Load CSV → schema raw
│   └── validate.py             # Kiểm tra data quality sau khi load
│
├── notebooks/
│   └── edaData.py              # Exploratory Data Analysis
│
├── dbt_project/                # (Session 2)
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   └── tests/
│
└── airflow/                    # (Session 3)
    └── dags/
```

---

## Dataset

**Nguồn:** [Olist Brazilian E-Commerce — Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

9 bảng, ~650,000 rows tổng cộng:

| Bảng | Rows | Granularity |
|---|---|---|
| orders | 99,441 | 1 row = 1 đơn hàng |
| order_items | 112,650 | 1 row = 1 sản phẩm trong 1 đơn |
| order_payments | 103,886 | 1 row = 1 lần thanh toán |
| order_reviews | 99,224 | 1 row = 1 đánh giá |
| customers | 99,441 | 1 row = 1 tài khoản khách hàng |
| products | 32,951 | 1 row = 1 sản phẩm |
| sellers | 3,095 | 1 row = 1 seller |
| geolocation | 1,000,163 | 1 row = 1 tọa độ của 1 zip code |
| product_category_translation | 71 | 1 row = 1 tên category (PT → EN) |

**Lưu ý quan trọng về data:**
- `order_delivered_customer_date` null = đơn chưa giao, không phải data lỗi
- `order_payments` có thể có nhiều dòng trên 1 đơn — khi tính revenue phải `SUM GROUP BY order_id`
- `geolocation` không có primary key tự nhiên — 1 zip code có nhiều tọa độ

---

## Hướng dẫn chạy

### 1. Yêu cầu
- Docker Desktop (đang chạy)
- Python 3.11+
- PyCharm hoặc VS Code

### 2. Clone repo và cài dependencies

```bash
git clone https://github.com/<your-username>/E-commerce-Analytics-Pipeline.git
cd E-commerce-Analytics-Pipeline
pip install -r requirements.txt
```

### 3. Tạo file `.env`

Tạo file `.env` ở thư mục gốc dựa theo `.env.sample`:

```
POSTGRES_USER=de_admin
POSTGRES_PASSWORD=de_password_local
POSTGRES_DB=ecommerce_db
```

> **Lưu ý:** Dùng PyCharm hoặc VS Code để tạo file — tránh PowerShell vì sẽ sinh ra UTF-8 BOM khiến `python-dotenv` không đọc được.

### 4. Khởi động PostgreSQL

```bash
docker-compose up -d

# Kiểm tra đã chạy chưa
docker-compose ps
# Kết quả mong đợi: de_postgres — Up (healthy)

# Verify 3 schema được tạo
docker exec -it de_postgres psql -U de_admin -d ecommerce_db -c "\dn"
```

### 5. Download dataset

Tải dataset từ Kaggle và giải nén vào thư mục `Data/raw/`. Cần có 9 file CSV.

### 6. Chạy ingestion

```bash
python ingestion/load_raw.py
```

Output mong đợi:
```
INFO — Loading olist_orders_dataset.csv → raw.orders
INFO — Loaded 99,441 rows into raw.orders
...
INFO — Done. Total rows loaded: 650,904
```

### 7. Validate data

```bash
python ingestion/validate.py
```

Kết quả mong đợi:
```
CHECK: row_counts       → 9 bảng
CHECK: orders_null_check → total_rows: 99441
CHECK: orders_duplicate_check → không có row nào (không có duplicate)
```

---

## Thiết kế 3-layer schema

### Layer 1 — `raw`
Dữ liệu gốc từ CSV, load nguyên vẹn dưới dạng `VARCHAR`. Không transform, không clean.

**Nguyên tắc:** Raw layer là source of truth. Nếu pipeline bị lỗi, có thể reprocess lại từ đây mà không cần download lại data.

### Layer 2 — `staging` *(đang xây dựng — Session 2)*
- Cast đúng kiểu dữ liệu (timestamp, numeric)
- Đổi tên cột theo convention thống nhất
- Xử lý null theo business logic
- 1 staging model = 1 source table

### Layer 3 — `marts` *(đang xây dựng — Session 2)*
Star schema theo Kimball methodology:
- `dim_customers`, `dim_products`, `dim_sellers`, `dim_date`
- `fct_orders`, `fct_order_items`

---

## Tiến độ

- [x] Session 1 — Project setup, Docker, raw ingestion, EDA, validation
- [ ] Session 2 — Data modeling với dbt (staging + marts)
- [ ] Session 3 — Orchestration với Airflow
- [ ] Session 4 — Analytics queries & visualization

---

## Lessons learned

Tổng kết Session 2 — Data Modeling với dbtNhững gì đã làm được1. Kiến trúc 3-layer hoàn chỉnhraw schema          staging schema           marts schema
──────────          ──────────────           ────────────
orders         →    stg_orders          →    fct_orders
order_items    →    stg_order_items     →    dim_customers
customers      →    stg_customers       →    dim_products
products       →    stg_products        →    dim_sellers
sellers        →    stg_sellers
order_payments →    stg_order_payments2. Staging layer (6 views)ModelNhiệm vụ chínhstg_ordersCast 5 timestamp columnsstg_order_itemsCast price, freight thành numericstg_customersRename bỏ prefix customer_stg_productsCast dimensions, qty thành đúng typestg_sellersRename bỏ prefix seller_stg_order_paymentsCast payment_value, installments3. Marts layer (4 tables — Star Schema)fct_orders là fact table trung tâm, tính sẵn các metrics:

item_count, total_price, total_freight_value
total_order_value, delivery_days
3 dimension tables: dim_customers, dim_products, dim_sellers4. dbt Tests — 16 tests passLoại testModels được testuniqueorder_id, customer_id, product_idnot_nullTất cả primary keys + foreign keys quan trọngConcepts quan trọng đã họcMaterialization: Staging dùng view (không tốn storage), Marts dùng table (performance tốt hơn cho query phức tạp).{{ ref() }} — dbt tự động hiểu dependency graph và chạy đúng thứ tự. Không cần hardcode schema name.{{ source() }} — khai báo raw tables trong sources.yml, dbt track lineage từ raw → staging → marts.Custom macro generate_schema_name — override behavior mặc định của dbt để schema name không bị ghép đôi.Bài học thực tế
dbt init wizard không hoạt động tốt trong PowerShell → tạo profiles.yml thủ công
dbt ghép schema mặc định + custom schema → cần custom macro để override
Xóa example models ngay sau khi init, không để lẫn vào project thật

- File `.env` phải là UTF-8 **không có BOM** — kiểm tra ở góc dưới phải PyCharm
- Docker Desktop phải mở trước khi dùng `docker-compose`
- Dùng `Path(__file__).parent.parent` thay vì hardcode path — hoạt động đúng từ mọi thư mục
- Load raw data bằng `dtype=str` — không cast type ở ingestion layer
- Luôn validate sau khi load, không assume data đúng chỉ vì không có error
