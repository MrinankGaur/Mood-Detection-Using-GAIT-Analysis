import pandas as pd
import joblib
from collections import Counter
from src.feature_engineering import process_raw_data

model = joblib.load("model/mood_model.pkl")
columns = joblib.load("model/feature_columns.pkl")

def predict_from_raw(raw_data):

    features = process_raw_data(raw_data)

    df = pd.DataFrame(features, columns=columns)

    preds = model.predict(df)

    return Counter(preds).most_common(1)[0][0]