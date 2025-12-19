import re
import pandas as pd
from typing import Dict, List, Tuple

def remove_duplicates(df: pd.DataFrame, text_col: str = 'text') -> pd.DataFrame:
    import hashlib
    df['text_hash'] = df[text_col].apply(lambda x: hashlib.md5(x.encode()).hexdigest())
    df_clean = df.drop_duplicates(subset='text_hash', keep='first').copy()
    df_clean = df_clean.drop(columns=['text_hash'])
    return df_clean

def normalize_whitespace(text: str) -> str:
    # Remove leading/trailing whitespace
    text = text.strip()
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text

def normalize_punctuation(text: str) -> str:
    # Normalize multiple dots (keep max 5 for emphasis)
    text = re.sub(r'\.{6,}', '.....', text)
    # Normalize multiple exclamations (keep max 5)
    text = re.sub(r'!{6,}', '!!!!!', text)
    # Normalize multiple questions (keep max 3)
    text = re.sub(r'\?{4,}', '???', text)
    return text

def normalize_text(text: str) -> str:
    text = normalize_whitespace(text)
    text = normalize_punctuation(text)
    return text

def filter_by_length(df: pd.DataFrame, min_len: int, max_len: int, text_col: str = 'text') -> pd.DataFrame:
    df['text_length'] = df[text_col].str.len()
    mask = (df['text_length'] >= min_len) & (df['text_length'] <= max_len)
    return df[mask].copy()

def detect_language(text: str) -> str:
    from langdetect import detect, LangDetectException
    try:
        lang = detect(text)
        # Treat Malay and Tagalog as Indonesian due to similarity
        if lang in {'ms', 'tl'}:
            return 'id'
        return lang
    except LangDetectException:
        return 'unknown'

def filter_by_language(df: pd.DataFrame, target_lang: str = 'id', text_col: str = 'text') -> pd.DataFrame:
    df['detected_lang'] = df[text_col].apply(detect_language)
    return df[df['detected_lang'] == target_lang].copy()

def clean_pipeline(df: pd.DataFrame, config: Dict) -> Tuple[pd.DataFrame, Dict]:
    stats = {
        'initial_count': len(df),
        'after_dedup': 0,
        'after_length_filter': 0,
        'after_lang_filter': 0,
        'duplicates_removed': 0,
        'length_filtered': 0,
        'lang_filtered': 0
    }
    
    # Step 1: Remove duplicates
    df_clean = remove_duplicates(df)
    stats['after_dedup'] = len(df_clean)
    stats['duplicates_removed'] = stats['initial_count'] - stats['after_dedup']
    
    # Step 2: Normalize text
    df_clean['text'] = df_clean['text'].apply(normalize_text)
    
    # Step 3: Filter by length
    min_len = config['cleaning']['min_length']
    max_len = config['cleaning']['max_length']
    df_clean = filter_by_length(df_clean, min_len, max_len)
    stats['after_length_filter'] = len(df_clean)
    stats['length_filtered'] = stats['after_dedup'] - stats['after_length_filter']
    
    # Step 4: Filter by language
    if config['cleaning']['target_language']:
        df_clean = filter_by_language(df_clean, config['cleaning']['target_language'])
        stats['after_lang_filter'] = len(df_clean)
        stats['lang_filtered'] = stats['after_length_filter'] - stats['after_lang_filter']
    else:
        stats['after_lang_filter'] = stats['after_length_filter']
    
    stats['final_count'] = len(df_clean)
    stats['total_removed'] = stats['initial_count'] - stats['final_count']
    
    return df_clean, stats