import time
import csv
import logging
from collections import deque, Counter
from datetime import datetime
from pathlib import Path
import importlib.util
import sys
import os

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def test_reader(repeat: bool = True):
    """Simulate streaming from Data Collection/rawData.csv for testing.

    Yields rows in the same shape as `datacollection.stream_readings()`.
    """
    test_path = ROOT / 'Data Collection' / 'rawData.csv'
    if not test_path.exists():
        logging.error('Test file not found: %s', test_path)
        return

    # each line in rawData.csv has some pressure values; pad to 28 values with zeros
    rows = []
    with open(test_path, 'r') as f:
        for line in f:
            parts = [p.strip() for p in line.strip().split(',') if p.strip()]
            # pad or truncate to 28 values
            vals = parts[:28]
            if len(vals) < 28:
                vals = vals + ['0'] * (28 - len(vals))
            rows.append(vals)

    sample = 0
    while True:
        for vals in rows:
            timestamp = format(sample * 0.01, '.2f')
            row = [timestamp] + vals + ['test']
            yield row
            sample += 1
        if not repeat:
            break


def main(batch_size: int = 2400):
    setup_logging()

    # load data collection module (path contains space)
    dc_path = ROOT / 'Data Collection' / 'datacollection.py'
    datacollection = load_module_from_path('datacollection', dc_path)

    # load preprocessing and prediction modules from src
    fe_path = Path(__file__).resolve().parent / 'src' / 'feature_engineering.py'
    predict_path = Path(__file__).resolve().parent / 'src' / 'predict.py'

    feature_mod = load_module_from_path('feature_engineering', fe_path)
    predict_mod = load_module_from_path('predict', predict_path)

    # output predictions CSV
    out_path = Path(__file__).resolve().parent / 'predictions.csv'
    if not out_path.exists():
        with open(out_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['batch_index', 'timestamp', 'prediction'])

    buffer = []
    batch_index = 0

    logging.info('Starting pipeline: waiting for readings...')

    # stream_readings yields rows matching datacollection.header
    if os.environ.get('RUN_PIPELINE_TEST') == '1':
        reader = test_reader()
        logging.info('Running in TEST streaming mode (Data Collection/rawData.csv)')
    else:
        reader = datacollection.stream_readings()

    # small progress logging
    rows_seen = 0

    try:
        for row in reader:
            buffer.append(row)
            rows_seen += 1

            if rows_seen % 100 == 0:
                logging.info(f'Reader supplied {rows_seen} rows; current buffer {len(buffer)}')

            if len(buffer) >= batch_size:
                batch_index += 1
                ts = datetime.utcnow().isoformat() + 'Z'
                logging.info(f'Batch {batch_index} received ({batch_size} rows)')

                # convert to DataFrame with proper columns
                try:
                    df = pd.DataFrame(buffer, columns=datacollection.header)
                except Exception as e:
                    logging.exception('Failed to build DataFrame from raw buffer: %s', e)
                    buffer.clear()
                    continue

                # convert sensor columns to numeric (timestamp and mood excluded)
                try:
                    numeric_cols = [c for c in datacollection.header if c not in ('timestamp', 'mood')]
                    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
                except Exception:
                    logging.exception('Failed to convert raw values to numeric; continuing with NaNs')

                # Preprocessing
                try:
                    logging.info(f'Batch {batch_index}: preprocessing started')
                    preprocessed = feature_mod.process_raw_data(df)
                    logging.info(f'Batch {batch_index}: preprocessing done')
                except Exception as e:
                    logging.exception('Batch %s preprocessing failed: %s', batch_index, e)
                    buffer.clear()
                    continue

                # Prediction
                try:
                    logging.info(f'Batch {batch_index}: prediction started')

                    # preprocessed is list of feature-rows; build DataFrame with expected columns
                    feat_df = pd.DataFrame(preprocessed, columns=predict_mod.columns)
                    preds = predict_mod.model.predict(feat_df)

                    # choose majority label for the batch
                    pred_label = Counter(preds).most_common(1)[0][0]

                    logging.info(f'Batch {batch_index}: prediction done -> %s', pred_label)

                    # persist prediction
                    with open(out_path, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([batch_index, ts, pred_label])

                except Exception as e:
                    logging.exception('Batch %s prediction failed: %s', batch_index, e)

                # reset buffer for next non-overlapping batch
                buffer.clear()
                logging.info(f'Batch {batch_index}: buffer cleared, continuing to next batch')

    except KeyboardInterrupt:
        logging.info('Interrupted by user, shutting down pipeline')
    except Exception as e:
        logging.exception('Unhandled exception in pipeline: %s', e)


if __name__ == '__main__':
    # allow optional batch size arg
    bs = 2400
    if len(sys.argv) > 1:
        try:
            bs = int(sys.argv[1])
        except Exception:
            pass

    main(batch_size=bs)
