# Analysis Results — Olist E-commerce

Tổng hợp insights từ phân tích ~100,000 đơn hàng thương mại điện tử Olist (Brazil) giai đoạn 2016–2018.

---

## 1. RFM Customer Segmentation

![RFM Segments](notebooks/results/01_rfm_segments.png)

### Phân khúc khách hàng

| Segment | Đặc điểm | Chiến lược đề xuất |
|---|---|---|
| **Champions** | Mua gần đây, thường xuyên, giá trị cao | Reward, upsell, VIP program |
| **Loyal** | Mua đều đặn, gắn bó lâu dài | Loyalty program, early access |
| **New** | Mới mua lần đầu | Onboarding email, nurture campaign |
| **Potential** | Có tiềm năng nhưng chưa convert | Targeted promotions |
| **At Risk** | Từng mua nhiều nhưng đang rời đi | Win-back campaigns |
| **Lost** | Không mua trong thời gian dài | Re-engagement hoặc bỏ qua |

### Key Insights
- Phần lớn khách hàng thuộc nhóm **New** — Olist đang tăng trưởng mạnh về acquisition nhưng yếu về retention
- Nhóm **Champions** tuy ít về số lượng nhưng đóng góp revenue không cân xứng — cần được chăm sóc đặc biệt
- Tỷ lệ **Lost** cao → retention là vấn đề ưu tiên số 1

---

## 2. Delivery Performance by State

![Delivery by State](notebooks/results/02_delivery_by_state.png)

### Key Insights
- Các bang vùng **Bắc và Đông Bắc** (RR, AP, AM) có delivery time dài nhất — do địa lý xa xôi và hạ tầng logistics kém
- Khu vực **São Paulo (SP)** và các bang miền Nam có delivery time tốt nhất — tập trung nhiều seller và warehouse
- Late delivery rate tương quan rõ với khoảng cách địa lý: bang xa = trễ nhiều hơn

---

## 3. Review Score vs Delivery Time

![Review vs Delivery](notebooks/results/03_review_vs_delivery.png)

### Key Insights
- Delivery time có **tương quan nghịch rõ ràng** với review score
- Đơn giao trong **≤7 ngày**: review score cao nhất
- Đơn giao **>21 ngày**: review score giảm đáng kể
- **Implication:** Cải thiện delivery time là đòn bẩy trực tiếp để tăng customer satisfaction

---

## 4. Monthly Revenue Trend

![Monthly Revenue](notebooks/results/04_monthly_revenue.png)

### Key Insights
- Revenue tăng trưởng ổn định từ **2016 đến 2018**
- Đỉnh điểm vào **tháng 11** — trùng với Black Friday Brazil
- Sụt giảm đột ngột cuối dataset — do data bị cắt, không phản ánh thực tế kinh doanh

---

## 5. Top Product Categories

![Top Categories](notebooks/results/05_top_categories.png)

### Key Insights
- **Health & Beauty**, **Watches & Gifts**, **Bed/Bath/Table** là top 3 về revenue
- **Health & Beauty** dẫn đầu cả revenue lẫn order count → category chiến lược
- Một số category có average order value cao dù order count thấp → sản phẩm giá trị cao (Electronics, Furniture)

---

## 6. Customer Purchase Behavior — Repeat vs One-time

![Repeat Purchase](notebooks/results/06_repeat_purchase.png)

### Key Insights
- **~97% khách hàng chỉ mua đúng 1 lần** và không bao giờ quay lại — đây là vấn đề nghiêm trọng nhất của Olist
- Số lượng repeat buyers cực kỳ nhỏ, hầu hết chỉ mua 1–2 lần
- Đây là đặc điểm đã được nhiều nghiên cứu về dataset Olist xác nhận

> **Ghi chú phương pháp:** Ban đầu thực hiện cohort retention analysis nhưng phát hiện ra rằng do tỷ lệ one-time buyers quá cao (~97%), cohort heatmap không có ý nghĩa thống kê (toàn bộ retention rate về 0 sau tháng đầu). Chuyển sang phân tích repeat purchase behavior để truyền tải insight trực tiếp và rõ ràng hơn.

---

## Tổng kết — Business Recommendations

### Vấn đề 1: Retention cực thấp ⚠️ Nghiêm trọng nhất
- ~97% khách hàng chỉ mua 1 lần, không quay lại
- **Giải pháp:** Loyalty program, personalized email follow-up, subscription model

### Vấn đề 2: Delivery chậm ở vùng xa
- Các bang phía Bắc có delivery time gấp 2–3 lần so với São Paulo
- **Giải pháp:** Mở rộng warehouse network, partnership với carrier địa phương

### Vấn đề 3: Review score giảm theo delivery time
- Mỗi tuần giao hàng thêm → review score giảm rõ rệt
- **Giải pháp:** SLA rõ ràng theo vùng, thông báo proactive khi có delay

### Cơ hội: Champions segment
- Nhóm Champions đóng góp revenue không cân xứng với số lượng
- **Giải pháp:** VIP program, early access, exclusive offers

---

*Analysis performed on Olist Brazilian E-Commerce dataset (2016–2018)*
*Pipeline: PostgreSQL + dbt → Python + matplotlib/seaborn*
*Source code: `notebooks/customer_analysis.py`*
