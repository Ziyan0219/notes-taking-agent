"""
Utility functions and helpers for the Notes Taking Agent
"""

import os
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import json
import re

logger = logging.getLogger(__name__)


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique identifier
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique identifier string
    """
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if prefix:
        return f"{prefix}_{timestamp}_{unique_id}"
    return f"{timestamp}_{unique_id}"


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate MD5 hash of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return ""


def ensure_directory_exists(directory: Path) -> bool:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        directory: Directory path
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing underscores and dots
    cleaned = cleaned.strip('_.')
    
    # Ensure it's not empty
    if not cleaned:
        cleaned = "unnamed_file"
    
    return cleaned


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_text_between_markers(text: str, start_marker: str, end_marker: str) -> List[str]:
    """
    Extract text between start and end markers
    
    Args:
        text: Source text
        start_marker: Start marker
        end_marker: End marker
        
    Returns:
        List of extracted text segments
    """
    pattern = re.escape(start_marker) + r'(.*?)' + re.escape(end_marker)
    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def split_text_by_sentences(text: str, max_sentences: int = 5) -> List[str]:
    """
    Split text into chunks by sentences
    
    Args:
        text: Input text
        max_sentences: Maximum sentences per chunk
        
    Returns:
        List of text chunks
    """
    # Simple sentence splitting (can be improved with NLTK)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    
    for sentence in sentences:
        current_chunk.append(sentence)
        
        if len(current_chunk) >= max_sentences:
            chunks.append('. '.join(current_chunk) + '.')
            current_chunk = []
    
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks


def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extract numbers from text
    
    Args:
        text: Input text
        
    Returns:
        List of extracted numbers
    """
    # Pattern for numbers (including decimals and scientific notation)
    pattern = r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    
    return numbers


def create_safe_dict(data: Any) -> Dict[str, Any]:
    """
    Create a safe dictionary from any data structure
    
    Args:
        data: Input data
        
    Returns:
        Safe dictionary representation
    """
    if isinstance(data, dict):
        return {str(k): create_safe_dict(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [create_safe_dict(item) for item in data]
    elif hasattr(data, '__dict__'):
        return create_safe_dict(data.__dict__)
    else:
        return str(data) if data is not None else None


def validate_file_type(file_path: Path, allowed_extensions: List[str]) -> bool:
    """
    Validate file type based on extension
    
    Args:
        file_path: Path to the file
        allowed_extensions: List of allowed extensions (with dots)
        
    Returns:
        True if file type is allowed
    """
    file_extension = file_path.suffix.lower()
    return file_extension in [ext.lower() for ext in allowed_extensions]


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.now().isoformat()


def parse_page_range(page_range_str: str) -> tuple[int, int]:
    """
    Parse page range string like "1-5" or "3"
    
    Args:
        page_range_str: Page range string
        
    Returns:
        Tuple of (start_page, end_page)
    """
    try:
        if '-' in page_range_str:
            start, end = page_range_str.split('-', 1)
            return (int(start.strip()), int(end.strip()))
        else:
            page = int(page_range_str.strip())
            return (page, page)
    except ValueError:
        return (1, 1)


def merge_overlapping_ranges(ranges: List[tuple[int, int]]) -> List[tuple[int, int]]:
    """
    Merge overlapping page ranges
    
    Args:
        ranges: List of (start, end) tuples
        
    Returns:
        List of merged ranges
    """
    if not ranges:
        return []
    
    # Sort ranges by start position
    sorted_ranges = sorted(ranges)
    merged = [sorted_ranges[0]]
    
    for current in sorted_ranges[1:]:
        last = merged[-1]
        
        # Check if ranges overlap or are adjacent
        if current[0] <= last[1] + 1:
            # Merge ranges
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            # Add new range
            merged.append(current)
    
    return merged


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estimate reading time for text
    
    Args:
        text: Input text
        words_per_minute: Average reading speed
        
    Returns:
        Estimated reading time in minutes
    """
    word_count = len(text.split())
    reading_time = max(1, word_count // words_per_minute)
    return reading_time


def create_progress_callback(total_steps: int, callback_func=None):
    """
    Create a progress tracking callback
    
    Args:
        total_steps: Total number of steps
        callback_func: Optional callback function
        
    Returns:
        Progress callback function
    """
    current_step = 0
    
    def update_progress(step_name: str = ""):
        nonlocal current_step
        current_step += 1
        progress = min(100, (current_step / total_steps) * 100)
        
        if callback_func:
            callback_func(progress, step_name)
        else:
            logger.info(f"Progress: {progress:.1f}% - {step_name}")
        
        return progress
    
    return update_progress


def sanitize_json_string(text: str) -> str:
    """
    Sanitize string for JSON serialization
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    # Replace problematic characters
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    text = text.replace('\t', '\\t')
    text = text.replace('"', '\\"')
    text = text.replace('\\', '\\\\')
    
    return text


def load_config_file(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from JSON file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config file {config_path}: {e}")
        return {}


def save_config_file(config: Dict[str, Any], config_path: Path) -> bool:
    """
    Save configuration to JSON file
    
    Args:
        config: Configuration dictionary
        config_path: Path to save config file
        
    Returns:
        True if saved successfully
    """
    try:
        ensure_directory_exists(config_path.parent)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        logger.error(f"Error saving config file {config_path}: {e}")
        return False

