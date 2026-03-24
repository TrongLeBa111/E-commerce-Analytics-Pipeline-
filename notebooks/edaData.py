import pandas as pd
import os

from pathlib import Path

# Tự động tính đường dẫn tuyệt đối, không phụ thuộc vào chỗ bạn chạy script
DATA_DIR = Path(__file__).parent.parent / "Data" / "raw"
# Load và inspect từng file
files = os.listdir(DATA_DIR)
for f in files:
    df = pd.read_csv(f"{DATA_DIR}/{f}")
    print(f"\n{'='*50}")
    print(f"File: {f}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Null counts:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
    print(f"Sample:\n{df.head(2)}")