# ML Analysis — Customer Churn Prediction

Mở rộng từ DA project, xây dựng ML model dự đoán khả năng churn của khách hàng Olist dựa trên hành vi mua hàng, delivery experience, và review behavior.

---

## Định nghĩa bài toán

**Churn label:** Khách hàng không có đơn hàng trong **90 ngày** kể từ lần mua cuối tính đến ngày cuối cùng trong dataset → `is_churned = 1`.

**Mục tiêu business:** Xác định nhóm khách hàng có nguy cơ rời đi để ưu tiên chiến dịch win-back, tối ưu ngân sách marketing — không chỉ hỏi *"ai sẽ churn"* mà còn *"nên chi tiền kéo lại ai"*.

---

## Kiến trúc ML Pipeline

```
marts.fct_orders + dim_customers
        │
        ▼
[dbt] mart_churn_labels.sql      ← định nghĩa label (90-day churn)
[dbt] mart_customer_features.sql ← feature engineering
        │
        ▼
notebooks/churn_prediction.py
        │
        ├── Preprocessing (SimpleImputer, LabelEncoder)
        ├── Baseline: Logistic Regression
        ├── Main: LightGBM + class_weight tuning
        ├── Threshold tuning
        └── Score toàn bộ customers
        │
        ▼
marts.churn_scores               ← output: probability + risk segment
```

---

## Dataset

| Chỉ số | Giá trị |
|---|---|
| Tổng customers | 96,478 |
| Churn rate | 90.1% |
| Active rate | 9.9% |
| Train / Test split | 77,182 / 19,296 (80/20, stratified) |

**Class imbalance:** Tỷ lệ 90:10 — xử lý bằng `class_weight={0:5, 1:1}` trên LightGBM (Active được weight 5x để tránh bị model bỏ qua hoàn toàn).

---

## Features (13 features)

| Feature | Nhóm | Mô tả |
|---|---|---|
| `frequency` | RFM | Số đơn hàng đã đặt |
| `monetary` | RFM | Tổng giá trị mua hàng (BRL) |
| `avg_order_value` | RFM | Giá trị trung bình mỗi đơn |
| `avg_delivery_days` | Delivery | Thời gian giao hàng trung bình |
| `max_delivery_days` | Delivery | Thời gian giao hàng tệ nhất |
| `late_delivery_rate` | Delivery | Tỷ lệ đơn giao trễ |
| `avg_review_score` | Review | Điểm đánh giá trung bình |
| `min_review_score` | Review | Điểm đánh giá thấp nhất |
| `bad_review_rate` | Review | Tỷ lệ đánh giá ≤2 sao |
| `credit_card_rate` | Payment | Tỷ lệ dùng thẻ tín dụng |
| `avg_installments` | Payment | Số kỳ trả góp trung bình |
| `avg_items_per_order` | Behavior | Số sản phẩm trung bình mỗi đơn |
| `state_encoded` | Geo | Bang (label encoded, 27 states) |

**Feature bị loại bỏ:** `avg_purchase_gap_days` — toàn NaN với 97% one-time buyers, không có giá trị phân biệt.

**Feature bị phát hiện data leakage:** `recency_days` — tương quan trực tiếp với label (`days_since_last_order > 90 → churned`). Loại bỏ trước khi train để tránh AUC ảo.

---

## Kết quả Model

### So sánh models

| Model | ROC-AUC | Active F1 | Churned F1 | Accuracy |
|---|---|---|---|---|
| Logistic Regression (baseline) | 0.719 | 0.27 | 0.74 | 0.61 |
| LightGBM (no weight) | 0.739 | 0.10 | 0.95 | 0.91 |
| **LightGBM (class_weight={0:5,1:1})** | **0.738** | **0.29** | **0.89** | **0.81** |

**Model được chọn:** LightGBM với `class_weight={0:5, 1:1}`, threshold=0.5.

### Classification Report (Final Model)

```
              precision    recall  f1-score   support
      Active       0.23      0.41      0.29     1,908
     Churned       0.93      0.85      0.89    17,388
    accuracy                           0.81    19,296
   macro avg       0.58      0.63      0.59    19,296
weighted avg       0.86      0.81      0.83    19,296

ROC-AUC: 0.7380
```

### Weight Search Results

| class_weight Active | Precision | Recall | F1 | AUC |
|---|---|---|---|---|
| w=3 | 0.46 | 0.10 | 0.163 | 0.739 |
| **w=5** | **0.23** | **0.41** | **0.291** | **0.740** |
| w=8 | 0.18 | 0.69 | 0.290 | 0.739 |
| w=10 | 0.17 | 0.75 | 0.278 | 0.740 |

w=5 cho Active F1 cao nhất (0.291) với AUC tốt nhất — được chọn.

---

## Risk Segmentation Output

Toàn bộ 96,478 customers được score và phân nhóm bằng percentile bins:

| Segment | Customers | Threshold | Action |
|---|---|---|---|
| High Risk | ~32,803 (34%) | prob ≥ 0.833 | Immediate win-back campaign |
| Medium Risk | ~31,837 (33%) | 0.595 ≤ prob < 0.833 | Nurture email sequence |
| Low Risk | ~31,838 (33%) | prob < 0.595 | Standard newsletter |

Output được lưu vào `marts.churn_scores` với columns: `customer_id`, `churn_probability`, `predicted_churned`, `risk_segment`, `recommended_action`.

---

## Lessons Learned — Quan trọng cho phỏng vấn

### 1. Data Leakage Detection
Phát hiện `recency_days` là proxy trực tiếp của churn label → ROC-AUC giả 1.0000 → loại bỏ feature và retrain. AUC giảm về 0.738 — phản ánh đúng độ khó thật sự của bài toán.

> *"ROC-AUC = 1.0 là dấu hiệu cảnh báo, không phải kết quả tốt. Luôn kiểm tra correlation giữa features và label trước khi train."*

### 2. Imbalanced Data — scale_pos_weight sai hướng
`scale_pos_weight` trong LightGBM chỉ có tác dụng khi **positive class là minority**. Dataset này Churned = majority (90%) → dùng `scale_pos_weight` làm model predict Churned nhiều hơn nữa → Active precision = 0.00. Fix bằng `class_weight` dictionary thay thế.

### 3. AUC Ceiling — Data Limitation
ROC-AUC ~0.74 là giới hạn thực tế của dataset này:
- 97% customers chỉ có 1 đơn hàng duy nhất
- Features chỉ đến từ 1 transaction → không đủ thông tin hành vi
- Model không phân biệt được "sẽ churn" vs "chưa bao giờ có ý định quay lại"

Để cải thiện AUC cần dữ liệu phong phú hơn: browse history, wishlist, email engagement, session data.

### 4. Fixed Bins vs Percentile Bins
Dùng fixed bins `[0, 0.3, 0.6, 1.0]` khi probability tập trung vào vùng hẹp → 100% High Risk. Percentile bins đảm bảo phân phối đều 3 nhóm, có giá trị business hơn.

---

## Limitations & Next Steps

**Limitations hiện tại:**
- Active precision thấp (0.23) — cứ 4 lần predict "sẽ quay lại" thì sai 3 lần
- Dataset historical (2016–2018) — pattern có thể đã thay đổi
- Không có A/B test data để đo impact của win-back campaign

**Next Steps đề xuất:**
- **CLV Prediction** — kết hợp churn probability với Customer Lifetime Value để prioritize "ai đáng chi tiền kéo lại"
- **Uplift Modeling** — cần A/B test data để đo tác động thực sự của campaign, tránh tặng ưu đãi cho người đã định quay lại
- **Real-time Scoring** — thay batch Airflow bằng FastAPI endpoint để trigger email ngay khi customer có dấu hiệu churn

---

## Files

| File | Mô tả |
|---|---|
| `ecommerce_pipeline/models/marts/mart_churn_labels.sql` | dbt model tạo churn label |
| `ecommerce_pipeline/models/marts/mart_customer_features.sql` | dbt model feature engineering |
| `notebooks/churn_prediction.py` | Training, evaluation, scoring script |
| `notebooks/results/07_churn_eda.png` | Class imbalance + feature correlation |
| `notebooks/results/08_churn_evaluation.png` | Confusion matrix, ROC, PR curve |
| `notebooks/results/09_shap_importance.png` | SHAP feature importance |
| `ml/models/churn_model.pkl` | Trained model (gitignore nếu file lớn) |

---

*Model trained on Olist Brazilian E-Commerce dataset (2016–2018)*
*Stack: PostgreSQL + dbt → Python + LightGBM + SHAP*
