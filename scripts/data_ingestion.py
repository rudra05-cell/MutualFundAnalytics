import pandas as pd
from pathlib import Path

data_path = Path("../data/raw")

csv_files = list(data_path.glob("*.csv"))

print(f"Found {len(csv_files)} CSV files")

for file in csv_files:

    print("\n" + "="*70)
    print(f"DATASET : {file.name}")
    print("="*70)

    df = pd.read_csv(file)

    print("\nShape:")
    print(df.shape)

    print("\nData Types:")
    print(df.dtypes)

    print("\nFirst 5 Rows:")
    print(df.head())

    print("\nMissing Values:")
    print(df.isnull().sum())