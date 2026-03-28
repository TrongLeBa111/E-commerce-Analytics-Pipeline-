# Olist E-commerce — Data Analysis Project

Phân tích dữ liệu thương mại điện tử Olist (Brazil) dựa trên marts layer được xây dựng từ [E-commerce DE Pipeline](https://github.com/<your-username>/E-commerce-Analytics-Pipeline).

---

## Mối liên hệ với DE Project

```
[DE Pipeline] → marts.fct_orders, dim_customers, dim_products, dim_sellers
                        │
                        ▼
              [DA Analysis — project này]
                        │
                        ├── Customer Analysis (RFM + Cohort)
                        └── Delivery & Operations Analysis
```

DA project này **không đụng vào raw data** — chỉ query từ marts layer đã được transform và tested bởi DE pipeline.

---

## Nội dung phân tích

| # | Phân tích | File | Output |
|---|---|---|---|
| 1 | RFM Segmentation | `notebooks/customer_analysis.py` | `results/01_rfm_segments.png` |
| 2 | Delivery by State | `notebooks/customer_analysis.py` | `results/02_delivery_by_state.png` |
| 3 | Review vs Delivery | `notebooks/customer_analysis.py` | `results/03_review_vs_delivery.png` |
| 4 | Monthly Revenue Trend | `notebooks/customer_analysis.py` | `results/04_monthly_revenue.png` |
| 5 | Top Product Categories | `notebooks/customer_analysis.py` | `results/05_top_categories.png` |
| 6 | Cohort Retention | `notebooks/customer_analysis.py` | `results/06_cohort_retention.png` |

Xem insights chi tiết tại [ANALYSIS.md](./ANALYSIS.md).

---

## Cấu trúc thư mục

```
notebooks/
├── customer_analysis.py     # Script phân tích chính
└── results/
    ├── 01_rfm_segments.png
    ├── 02_delivery_by_state.png
    ├── 03_review_vs_delivery.png
    ├── 04_monthly_revenue.png
    ├── 05_top_categories.png
    └── 06_cohort_retention.png
```

---

## Hướng dẫn chạy

### Yêu cầu
- DE Pipeline đang chạy (Docker Compose up)
- Python 3.11+

### Cài dependencies

```bash
pip install pandas matplotlib seaborn sqlalchemy python-dotenv
```

### Chạy analysis

```bash
# Đảm bảo Docker đang chạy
docker-compose start

# Chạy toàn bộ analysis
python notebooks/customer_analysis.py
```

Kết quả được lưu vào `notebooks/results/`.

---

## Stack

| Tool | Mục đích |
|---|---|
| Python + pandas | Data manipulation |
| matplotlib + seaborn | Visualization |
| SQLAlchemy | Kết nối PostgreSQL |
| PostgreSQL (marts layer) | Data source |

---

## Dataset

**Nguồn:** [Olist Brazilian E-Commerce — Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
**Thời gian:** 2016–2018
**Phạm vi:** ~100,000 đơn hàng, 27 bang tại Brazil
