# Analysis Results — Olist E-commerce (Brazil)

Tổng hợp insights chiến lược từ phân tích ~100,000 đơn hàng trên nền tảng Olist giai đoạn 2016–2018.

---

## 1. RFM Customer Segmentation
![RFM Segments](notebooks/results/01_rfm_segments.png)

### Phân khúc khách hàng
| Segment | Đặc điểm | Chiến lược đề xuất |
|---|---|---|
| **Champions** | Mua gần đây, tần suất cao, chi tiêu lớn | Đặc quyền VIP, tri ân khách hàng thân thiết |
| **Loyal** | Khách hàng trung thành, mua đều đặn | Chương trình tích điểm, ưu tiên trải nghiệm |
| **New** | Khách hàng mới phát sinh giao dịch | Quy trình Onboarding, coupon cho đơn thứ 2 |
| **Potential** | Khách hàng tiềm năng, cần thúc đẩy | Gợi ý sản phẩm liên quan (Cross-sell) |
| **At Risk** | Khách hàng cũ có dấu hiệu rời bỏ | Win-back campaign, giảm giá sâu để kéo lại |
| **Lost** | Đã ngừng tương tác rất lâu | Tối ưu chi phí, chỉ re-marketing vào dịp lớn |

### Key Insights
* **Acquisition vs Retention:** Phần lớn khách hàng dừng lại ở nhóm **New** hoặc **Potential**. Olist đang làm rất tốt việc thu hút khách hàng mới nhưng cực kỳ yếu trong việc giữ chân họ.
* **Sức mạnh nhóm tinh hoa:** Nhóm **Champions** chiếm tỷ trọng nhỏ về số lượng nhưng đóng góp giá trị đơn hàng trung bình (AOV) cao nhất.
* **Cảnh báo:** Tỷ lệ khách hàng chuyển dịch sang nhóm **At Risk** và **Lost** tăng nhanh theo thời gian.

---

## 2. Delivery Performance by State
![Delivery by State](notebooks/results/02_delivery_by_state.png)

### Key Insights
* **Phân hóa địa lý:** Các bang vùng **Bắc và Đông Bắc** (RR, AP, AM) có thời gian giao hàng dài nhất (trung bình >20 ngày) do hạ tầng logistics gặp trở ngại địa lý.
* **Trung tâm Logistics:** Khu vực **São Paulo (SP)** và miền Nam có tốc độ giao hàng nhanh vượt trội nhờ tập trung mật độ seller và kho bãi cao.
* **Tỷ lệ trễ hạn:** Có sự tương quan thuận giữa khoảng cách địa lý và tỷ lệ đơn hàng bị trễ (Late Delivery).

---

## 3. Review Score vs Delivery Time
![Review vs Delivery](notebooks/results/03_review_vs_delivery.png)

### Key Insights
* **Ngưỡng kiên nhẫn:** Review score giữ mức cao (~4.2+) nếu hàng đến trong **≤7 ngày**.
* **Điểm rơi hài lòng:** Khi thời gian giao hàng vượt quá **21 ngày**, điểm đánh giá sụt giảm nghiêm trọng xuống dưới 3.0.
* **Kết luận:** Tốc độ giao hàng là yếu tố tiên quyết ảnh hưởng đến uy tín của sàn và khả năng quay lại của khách hàng.

---

## 4. Monthly Revenue Trend
![Monthly Revenue](notebooks/results/04_monthly_revenue.png)

### Key Insights
* **Đà tăng trưởng:** Doanh thu tăng trưởng phi mã từ cuối 2017 đến giữa 2018.
* **Điểm bùng nổ:** **Tháng 11/2017** ghi nhận doanh thu kỷ lục nhờ sự kiện **Black Friday**.
* **Lưu ý dữ liệu:** Sự sụt giảm ở tháng cuối cùng là do tập dữ liệu bị cắt ngang (Data Cutoff), không phải do kinh doanh sa sút.

---

## 5. Top Product Categories
![Top Categories](notebooks/results/05_top_categories.png)

### Key Insights
* **Ngành hàng chủ lực:** **Health & Beauty** (Sức khỏe & Sắc đẹp) là "con gà đẻ trứng vàng" khi dẫn đầu cả về doanh thu lẫn số lượng đơn hàng.
* **Giá trị cao:** **Watches & Gifts** có số đơn hàng ít hơn nhưng doanh thu rất lớn, cho thấy AOV của ngành hàng này rất cao.
* **Thiết yếu:** Các nhóm ngành Home Decor (Bed/Bath/Table) duy trì sức mua ổn định xuyên suốt.

---

## 6. Repeat Purchase Behavior (The Retention Challenge)
![Repeat Purchase](notebooks/results/06_repeat_purchase.png)

### Key Insights
* **Thực trạng báo động:** **~97% khách hàng chỉ mua 1 lần duy nhất.** Đây là vấn đề cốt lõi của mô hình Olist trong giai đoạn này.
* **Tỷ lệ quay lại:** Chỉ có khoảng **3%** khách hàng phát sinh đơn hàng thứ 2 trở đi.
* **Giải thích phương pháp:** Thay vì dùng Cohort Heatmap (vốn sẽ bị trống sau tháng 12), biểu đồ Repeat Purchase phản ánh trực diện sự đứt gãy trong vòng đời khách hàng.

---

## Tổng kết & Kiến nghị chiến lược

1.  **Chiến lược Retention (Ưu tiên số 1):** Triển khai hệ thống CRM và Email Marketing tự động để chăm sóc khách hàng sau mua. Cần tập trung chuyển đổi nhóm "New" thành "Loyal".
2.  **Tối ưu Logistics vùng xa:** Cân nhắc thiết lập các trạm trung chuyển (Hub) tại khu vực Đông Bắc để giảm thời gian giao hàng và cứu vãn Review Score.
3.  **Khai thác nhóm Champions:** Tạo chương trình khách hàng thân thiết (Loyalty Program) dành riêng cho nhóm $3\%$ khách hàng quay lại để biến họ thành đại sứ thương hiệu.

---
*Phân tích thực hiện trên tập dữ liệu Olist Brazilian E-Commerce (2016–2018)*
