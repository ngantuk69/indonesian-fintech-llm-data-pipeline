#!/usr/bin/env python3

import sys
from pathlib import Path
import pandas as pd
import yaml
import jsonlines
from datetime import datetime

# Add parent dir to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.preprocess import clean_pipeline
from scripts.validate import run_validation

def main():
    print("="*60)
    print("Indonesian Fintech Customer Messages - Cleaning Pipeline")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load config
    config_path = Path(__file__).parents[1] / 'configs' / 'pipeline_config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print(f"Config loaded: {config_path.name}")
    
    # Load raw data
    raw_path = Path(config['data_sources']['synthetic'])
    if not raw_path.is_absolute():
        raw_path = Path(__file__).parents[1] / raw_path
    
    print(f"Loading raw data: {raw_path}")
    df_raw = pd.read_csv(raw_path, header=None, names=['id', 'text'])
    print(f"  Loaded {len(df_raw)} rows\n")
    
    # Run cleaning
    print("Running cleaning pipeline...")
    df_clean, stats = clean_pipeline(df_raw, config)
    
    print("\n--- Cleaning Statistics ---")
    print(f"Initial:          {stats['initial_count']}")
    print(f"Duplicates:      -{stats['duplicates_removed']}")
    print(f"Length filtered: -{stats['length_filtered']}")
    print(f"Lang filtered:   -{stats['lang_filtered']}")
    print(f"Final:           {stats['final_count']}")
    print(f"Removal rate:    {stats['total_removed']/stats['initial_count']*100:.1f}%\n")
    
    # Validate
    validation_path = Path(__file__).parents[1] / config['processed_dir'] / 'validation_report.json'
    print(f"Running validation...")
    try:
        report = run_validation(df_clean, config, validation_path)
        print(f"  Status: {report['status']}")
        print(f"  Report saved: {validation_path}\n")
    except Exception as e:
        print(f"  FAILED: {e}\n")
        return 1
    
    # Export cleaned data
    output_dir = Path(__file__).parents[1] / config['processed_dir']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_jsonl = output_dir / 'cleaned_data.jsonl'
    print(f"Exporting cleaned data...")
    with jsonlines.open(output_jsonl, 'w') as writer:
        for _, row in df_clean.iterrows():
            writer.write({
                'id': row['id'],
                'text': row['text'],
                'text_length': int(row['text_length']),
                'detected_lang': row['detected_lang']
            })
    print(f"  Saved {len(df_clean)} records to {output_jsonl}")
    
    # Save log
    log_df = pd.DataFrame([stats])
    log_df['timestamp'] = datetime.now()
    log_path = output_dir / 'cleaning_log.csv'
    log_df.to_csv(log_path, index=False)
    print(f"  Log saved to {log_path}\n")
    
    print("="*60)
    print("Pipeline completed successfully!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())