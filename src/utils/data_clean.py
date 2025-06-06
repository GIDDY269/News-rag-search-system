from unstructured.cleaners.core import (
    clean,
    clean_non_ascii_chars,
    replace_unicode_quotes,
    remove_punctuation,
    clean_ordered_bullets

)

import html
from bs4 import BeautifulSoup

import re





def standardize_dates(text, placeholder="[DATE]"):
    date_pattern = (
        r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{2,4}[-/]\d{1,2}[-/]\d{1,2})\b"
    )
    return re.sub(date_pattern, placeholder, text)

def standardize_times(text, placeholder="[TIME]"):
    time_pattern = r"\b(?:\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?)\b"
    return re.sub(time_pattern, placeholder, text)

#def remove_html_tags(text):
  #  html_tag_pattern = r"<[^>]+>"
 #   return re.sub(html_tag_pattern, "", text)

#def normalize_whitespace(text):
  #  return re.sub(r"\s+", " ", text).strip()

def remove_html_tags(text: str) -> str:
    if not text: return ""
    soup = BeautifulSoup(text, 'html.parser')
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text()
    return text

def normalize_whitespace(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def clean_full(text: str) -> str:
    if not text: return ""
    text = remove_html_tags(text)
    text = html.unescape(text)
    text = normalize_whitespace(text)
    return text


