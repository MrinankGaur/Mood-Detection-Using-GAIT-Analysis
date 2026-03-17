from src.predict import predict_from_raw
import pandas as pd

# Example: load raw sensor CSV
raw_df = pd.read_csv("sample_raw_data.csv")

result = predict_from_raw(raw_df)

print("Final Mood:", result)