# E-commerce-Analytics-Pipeline-
Dữ liệu được lấy từ Kaggle, mục tiêu xây dựng pipeline để hiểu thêm về e-commerce cũng như tương tác giữa các luồng dữ liệu trong hệ thống.

# SESSION 1: Project Setup & Raw Data Ingestion
Những gì đã làm được: 
1 - Xây dựng cấu trúc dự án 
E-commerce-Analytics-Pipeline/
├── docker-compose.yml
├── init_schemas.sql
├── .env                  (gitignore)
├── .env.sample
├── .gitignore
├── requirements.txt
├── Data/raw/             (gitignore)
├── ingestion/
│   ├── load_raw.py
│   └── validate.py
├── notebooks/
│   └── edaData.py
├── dbt_project/
└── airflow/
2 - Tạo môi trường PostgresSQL - Docker 
raw --> Chứa data gốc từ CSV, không transform
staging --> Cleaned, cast đúng kiểu dữ liệu, đổi tên cột
marts --> Fact & Dimension tables — dùng để query analytics
3 - EDA:  Dùng Python inspect 9 bảng của dataset Olist trước khi viết bất kỳ pipeline nào
4 - Ingestion pipeline — load_raw.py
Load 9 file CSV vào schema raw với các nguyên tắc:

  Load toàn bộ cột dưới dạng dtype=str — không cast type ở bước này, đó là việc của staging layer
  Dùng chunksize=10_000 để tránh OOM với file lớn
  Dùng Path(__file__) thay vì hardcode đường dẫn → chạy được từ mọi thư mục
  Load .env bằng đường dẫn tuyệt đối → không bị lỗi khi Airflow gọi script

5. Validation — validate.py --> Sau khi load, kiểm tra

6. Kết quả học được:
Về engineering:

  Không bao giờ commit .env lên GitHub
  Luôn validate data sau khi load — chạy không lỗi không có nghĩa là data đúng
  Đọc hiểu data trước khi code bất cứ thứ gì
  Dùng Path(__file__) thay vì hardcode path

Về môi trường Windows:

  File .env phải là UTF-8 không BOM — kiểm tra ở góc dưới phải PyCharm
  Docker Desktop phải mở trước khi dùng docker-compose
  Tạo file config bằng Python hoặc VS Code/PyCharm, tránh dùng PowerShell echo
7 - Công nghệ đã dùng
Công nghệ                           Mục đích                                Ghi chú
Docker + Docker Compose             Chạy PostgreSQL không cần cài           Cần mở Docker Desktop trước
PostgreSQL 15                       Database lưu raw data                   Chạy trong container
Python + pandas                     Đọc CSV, load vào DB                    dtype=str để giữ nguyên raw
SQLAlchemy                          Kết nối Python ↔ PostgreSQL             Dùng connection string
python-dotenv                       Đọc biến từ .env                        Chú ý encoding UTF-8 no BOM
