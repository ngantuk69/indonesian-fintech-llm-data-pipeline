import pandas as pd
import pytest
from scripts.preprocess import (
    remove_duplicates,
    normalize_whitespace,
    normalize_punctuation,
    normalize_text,
    filter_by_length,
    detect_language
)

def test_remove_duplicates():
    df = pd.DataFrame({
        'id': ['1', '2', '3', '4'],
        'text': ['hello', 'world', 'hello', 'test']
    })
    result = remove_duplicates(df)
    assert len(result) == 3
    assert 'hello' in result['text'].values
    assert result['text'].tolist().count('hello') == 1

def test_normalize_whitespace():
    assert normalize_whitespace('hello  world') == 'hello world'
    assert normalize_whitespace('  test  ') == 'test'
    assert normalize_whitespace('a\n\nb') == 'a b'

def test_normalize_punctuation():
    assert normalize_punctuation('wow...') == 'wow...'
    assert normalize_punctuation('wow....') == 'wow...'
    assert normalize_punctuation('no!!!') == 'no!!'
    assert normalize_punctuation('what???') == 'what??'

def test_normalize_text():
    text = 'hello   world!!!  '
    result = normalize_text(text)
    assert result == 'hello world!!'
    assert result.strip() == result

def test_filter_by_length():
    df = pd.DataFrame({
        'id': ['1', '2', '3'],
        'text': ['hi', 'hello world', 'this is a longer msg']
    })
    result = filter_by_length(df, 5, 25)
    assert len(result) == 2
    assert 'hi' not in result['text'].values
    assert result['text'].tolist() == ['hello world', 'this is a longer msg']

def test_detect_language_returns_id_or_en():
    assert detect_language('Halo, apa kabar?') in {'id'}

if __name__ == '__main__':
    pytest.main([__file__, '-v'])