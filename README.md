# E-commerce Analytics Pipeline

End-to-end data pipeline xây dựng trên dataset thương mại điện tử Olist (Brazil), bao gồm ingestion, transformation, data quality testing và orchestration tự động.

---

## Kiến trúc tổng quan

```
CSV (Kaggle)
    │
    ▼
[Airflow DAG — chạy mỗi 6am]
    │
    ├── Task 1: ingest_raw_data
    │       Python + pandas → PostgreSQL schema: raw
    │
    ├── Task 2: dbt_run
    │       staging layer (6 views) + marts layer (4 tables)
    │
    └── Task 3: dbt_test
            16 data quality tests
```

**Stack công nghệ:**

| Layer | Công nghệ | Phiên bản |
|---|---|---|
| Ingestion | Python, pandas, SQLAlchemy | Python 3.12 |
| Storage | PostgreSQL | 15 |
| Transform | dbt Core | 1.11 |
| Orchestration | Apache Airflow | 2.9.0 |
| Infrastructure | Docker, Docker Compose | - |

---

## Cấu trúc thư mục

```
E-commerce-Analytics-Pipeline/
├── docker-compose.yml
├── init_schemas.sql          # Tạo schema raw, staging, marts
├── init_airflow_db.sql       # Tạo database airflow
├── .env                      # Không commit — xem .env.sample
├── .env.sample
├── .gitignore
├── requirements.txt
├── README.md
│
├── Data/
│   └── raw/                  # CSV gốc từ Kaggle (gitignore)
│
├── ingestion/
│   ├── load_raw.py           # Load CSV → schema raw
│   └── validate.py           # Kiểm tra data quality
│
├── notebooks/
│   └── edaData.py            # Exploratory Data Analysis
│
├── ecommerce_pipeline/       # dbt project
│   ├── dbt_project.yml
│   ├── macros/
│   │   └── generate_schema_name.sql
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml
│   │   │   ├── schema.yml
│   │   │   ├── stg_orders.sql
│   │   │   ├── stg_order_items.sql
│   │   │   ├── stg_order_payments.sql
│   │   │   ├── stg_customers.sql
│   │   │   ├── stg_products.sql
│   │   │   └── stg_sellers.sql
│   │   └── marts/
│   │       ├── schema.yml
│   │       ├── fct_orders.sql
│   │       ├── dim_customers.sql
│   │       ├── dim_products.sql
│   │       └── dim_sellers.sql
│   └── tests/
│
└── airflow/
    └── dags/
        └── ecommerce_pipeline_dag.py
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

**Lưu ý quan trọng:**
- `order_delivered_customer_date` null = đơn chưa giao, không phải data lỗi
- `order_payments` có thể có nhiều dòng trên 1 đơn — khi tính revenue phải `SUM GROUP BY order_id`
- `geolocation` không có primary key tự nhiên

---

## Hướng dẫn chạy

### Yêu cầu
- Docker Desktop (đang chạy)
- Python 3.11+

### 1. Clone repo

```bash
git clone https://github.com/<your-username>/E-commerce-Analytics-Pipeline.git
cd E-commerce-Analytics-Pipeline
pip install -r requirements.txt
```

### 2. Tạo file `.env`

Tạo file `.env` ở thư mục gốc — dùng PyCharm hoặc VS Code (tránh PowerShell vì sinh ra UTF-8 BOM):

```
POSTGRES_USER=de_admin
POSTGRES_PASSWORD=de_password_local
POSTGRES_DB=ecommerce_db
```

> Kiểm tra encoding: mở file `.env` trong PyCharm, góc dưới phải phải hiện `UTF-8` (không phải `UTF-8 BOM`).

### 3. Download dataset

Tải dataset từ Kaggle và giải nén vào `Data/raw/`. Cần có đủ 9 file CSV.

### 4. Khởi động toàn bộ hệ thống

```bash
docker-compose up -d
```

Lần đầu mất 3–5 phút (pull Airflow image ~500MB). Kiểm tra:

```bash
docker-compose ps
# Mong đợi: postgres (healthy), airflow-webserver (healthy), airflow-scheduler (up)
```

### 5. Tạo Airflow admin user (lần đầu)

```bash
docker exec -it airflow_webserver airflow db migrate
docker exec -it airflow_webserver airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname User \
  --role Admin --email admin@example.com
```

### 6. Cài dbt trong Airflow container (lần đầu)

```bash
docker exec -it --user airflow airflow_scheduler python -m pip install dbt-postgres
```

### 7. Chạy pipeline

Mở Airflow UI tại [http://localhost:8080](http://localhost:8080) (admin/admin):
- Bật toggle DAG `ecommerce_pipeline`
- Bấm **▶ Trigger DAG** để chạy thủ công

Hoặc chờ schedule tự động chạy lúc 6:00 AM UTC mỗi ngày.

### 8. Verify kết quả

```bash
docker exec -it de_postgres psql -U de_admin -d ecommerce_db -c "\dt marts.*"
docker exec -it de_postgres psql -U de_admin -d ecommerce_db -c "SELECT COUNT(*) FROM marts.fct_orders;"
```

---

## Data Model — Star Schema

```
                 dim_date (TODO)
                     │
dim_customers ── fct_orders ── dim_products
                     │
                dim_sellers
```

**`fct_orders`** — fact table trung tâm, metrics đã được tính sẵn:

| Cột | Mô tả |
|---|---|
| `item_count` | Số sản phẩm trong đơn |
| `total_price` | Tổng giá sản phẩm |
| `total_freight_value` | Tổng phí vận chuyển |
| `total_order_value` | Tổng giá trị đơn hàng |
| `delivery_days` | Số ngày giao hàng thực tế |

---

## Data Quality Tests

16 tests chạy tự động sau mỗi lần transform:

| Test | Models |
|---|---|
| `unique` + `not_null` | `order_id` trong `stg_orders`, `fct_orders` |
| `unique` + `not_null` | `customer_id` trong `stg_customers`, `dim_customers` |
| `unique` + `not_null` | `product_id` trong `dim_products` |
| `not_null` | Foreign keys trong `stg_order_items`, `stg_order_payments` |

---

## Airflow DAG

**DAG ID:** `ecommerce_pipeline`
**Schedule:** `0 6 * * *` (6:00 AM UTC hàng ngày)

```
ingest_raw_data ──→ dbt_run ──→ dbt_test
  PythonOperator   BashOperator  BashOperator
```

---

## Workflow hàng ngày

```bash
# Mở máy lên → mở Docker Desktop → chạy:
docker-compose start

# Xong việc:
docker-compose stop
```

---

## Lessons Learned

**Docker & Networking:**
- Các container giao tiếp qua tên service (`postgres`), không phải `localhost`
- Biến môi trường phải khai báo trong `docker-compose.yml`, cần `down` + `up` để apply
- Dependencies cài bằng pip trong container bị mất khi `docker-compose down -v` → production dùng custom Dockerfile

**dbt:**
- Schema bị ghép đôi (`staging_staging`) → cần custom macro `generate_schema_name`
- `profiles.yml` không commit lên Git (chứa password)
- Xóa example models (`models/example/`) ngay sau khi `dbt init`

**Windows:**
- File `.env` phải là UTF-8 không BOM — tạo bằng PyCharm/VS Code
- PowerShell không có `grep`, dùng `Select-String` thay thế
- Dùng `Path(__file__).parent` thay vì hardcode đường dẫn

---

## Tiến độ

- [x] Session 1 — Project setup, Docker, raw ingestion, EDA, validation
- [x] Session 2 — Data modeling với dbt (staging + marts + 16 tests)
- [x] Session 3 — Orchestration với Airflow (DAG 3 tasks, schedule daily)
- [ ] Session 4 — Analytics queries & Metabase visualization

---

## Tài liệu tham khảo

- [dbt Documentation](https://docs.getdbt.com)
- [Apache Airflow Documentation](https://airflow.apache.org/docs)
- [Fundamentals of Data Engineering — Reis & Housley](https://www.oreilly.com/library/view/fundamentals-of-data/9781098108298/)
