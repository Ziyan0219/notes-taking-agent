"""
PDF parsing service for extracting content from PDF files
"""

import re
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from PIL import Image
import io
import base64

from app.models.schemas import PDFContent

logger = logging.getLogger(__name__)


class PDFParser:
    """PDF parsing service with multiple extraction methods"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def parse_pdf(self, file_path: Path) -> PDFContent:
        """
        Parse PDF file and extract all content
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            PDFContent object with extracted content
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if file_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        logger.info(f"Starting PDF parsing for: {file_path}")
        
        try:
            # Use PyMuPDF for comprehensive extraction
            pdf_content = self._extract_with_pymupdf(file_path)
            
            # Enhance with pdfplumber for better table extraction
            tables = self._extract_tables_with_pdfplumber(file_path)
            pdf_content.tables = tables
            
            logger.info(f"PDF parsing completed. Pages: {pdf_content.pages}, "
                       f"Text length: {len(pdf_content.text)}, "
                       f"Images: {len(pdf_content.images)}, "
                       f"Tables: {len(pdf_content.tables)}")
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise
    
    def _extract_with_pymupdf(self, file_path: Path) -> PDFContent:
        """Extract content using PyMuPDF"""
        
        doc = fitz.open(str(file_path))
        
        text_content = []
        images = []
        metadata = {}
        
        try:
            # Extract metadata
            metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', ''),
                'page_count': doc.page_count
            }
            
            # Extract text and images from each page
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Extract text
                page_text = page.get_text()
                if page_text.strip():
                    text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
                # Extract images
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            img_name = f"page_{page_num + 1}_img_{img_index + 1}.png"
                            
                            # Convert to base64 for storage
                            img_base64 = base64.b64encode(img_data).decode()
                            images.append({
                                'name': img_name,
                                'page': page_num + 1,
                                'data': img_base64,
                                'format': 'png'
                            })
                        
                        pix = None
                        
                    except Exception as e:
                        logger.warning(f"Error extracting image {img_index} from page {page_num + 1}: {e}")
                        continue
            
        finally:
            doc.close()
        
        # Combine all text
        full_text = "\n\n".join(text_content)
        
        return PDFContent(
            text=full_text,
            pages=metadata.get('page_count', 0),
            metadata=metadata,
            images=[img['name'] for img in images],  # Store image names
            tables=[]  # Will be filled by pdfplumber
        )
    
    def _extract_tables_with_pdfplumber(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract tables using pdfplumber"""
        
        tables = []
        
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for table_index, table in enumerate(page_tables):
                        if table and len(table) > 1:  # Ensure table has content
                            tables.append({
                                'page': page_num + 1,
                                'table_index': table_index + 1,
                                'data': table,
                                'rows': len(table),
                                'columns': len(table[0]) if table else 0
                            })
                            
        except Exception as e:
            logger.warning(f"Error extracting tables with pdfplumber: {e}")
        
        return tables
    
    def extract_formulas(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract mathematical formulas from text
        
        Args:
            text: Input text content
            
        Returns:
            List of formula dictionaries
        """
        formulas = []
        
        # Pattern for LaTeX-style formulas
        latex_patterns = [
            r'\$\$([^$]+)\$\$',  # Display math
            r'\$([^$]+)\$',      # Inline math
            r'\\begin\{equation\}(.*?)\\end\{equation\}',  # Equation environment
            r'\\begin\{align\}(.*?)\\end\{align\}',        # Align environment
            r'\\begin\{gather\}(.*?)\\end\{gather\}',      # Gather environment
        ]
        
        # Pattern for common mathematical expressions
        math_patterns = [
            r'([a-zA-Z]\s*=\s*[^,\.\n]+)',  # Simple equations like "x = ..."
            r'([∫∑∏][^,\.\n]+)',            # Integrals, sums, products
            r'([a-zA-Z]+\([^)]+\)\s*=\s*[^,\.\n]+)',  # Functions
        ]
        
        formula_id = 1
        
        # Extract LaTeX formulas
        for pattern in latex_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                formula_text = match.group(1).strip()
                if len(formula_text) > 2:  # Filter out very short matches
                    formulas.append({
                        'id': f"formula_{formula_id}",
                        'latex': formula_text,
                        'raw_text': match.group(0),
                        'start_pos': match.start(),
                        'end_pos': match.end(),
                        'type': 'latex'
                    })
                    formula_id += 1
        
        # Extract mathematical expressions
        for pattern in math_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                formula_text = match.group(1).strip()
                if len(formula_text) > 3 and '=' in formula_text:
                    formulas.append({
                        'id': f"formula_{formula_id}",
                        'latex': formula_text,
                        'raw_text': match.group(0),
                        'start_pos': match.start(),
                        'end_pos': match.end(),
                        'type': 'expression'
                    })
                    formula_id += 1
        
        # Remove duplicates and sort by position
        unique_formulas = []
        seen_formulas = set()
        
        for formula in sorted(formulas, key=lambda x: x['start_pos']):
            formula_key = formula['latex'].replace(' ', '').lower()
            if formula_key not in seen_formulas:
                seen_formulas.add(formula_key)
                unique_formulas.append(formula)
        
        logger.info(f"Extracted {len(unique_formulas)} unique formulas")
        return unique_formulas
    
    def identify_topics(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify topics and sections from text structure
        
        Args:
            text: Input text content
            
        Returns:
            List of topic dictionaries
        """
        topics = []
        
        # Patterns for different heading levels
        heading_patterns = [
            (r'^#{1}\s+(.+)$', 1, 'chapter'),      # # Chapter
            (r'^#{2}\s+(.+)$', 2, 'section'),     # ## Section
            (r'^#{3}\s+(.+)$', 3, 'subsection'),  # ### Subsection
            (r'^Chapter\s+\d+[:\.]?\s*(.+)$', 1, 'chapter'),
            (r'^Section\s+\d+[:\.]?\s*(.+)$', 2, 'section'),
            (r'^\d+\.\s+(.+)$', 2, 'section'),    # 1. Section
            (r'^\d+\.\d+\s+(.+)$', 3, 'subsection'),  # 1.1 Subsection
        ]
        
        lines = text.split('\n')
        topic_id = 1
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern, level, topic_type in heading_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 2:  # Filter out very short titles
                        topics.append({
                            'id': f"topic_{topic_id}",
                            'title': title,
                            'type': topic_type,
                            'level': level,
                            'line_number': line_num + 1,
                            'raw_text': line
                        })
                        topic_id += 1
                    break
        
        logger.info(f"Identified {len(topics)} topics")
        return topics
    
    def extract_page_content(self, file_path: Path, page_number: int) -> str:
        """
        Extract content from a specific page
        
        Args:
            file_path: Path to the PDF file
            page_number: Page number (1-based)
            
        Returns:
            Page content as string
        """
        try:
            doc = fitz.open(str(file_path))
            
            if page_number < 1 or page_number > doc.page_count:
                raise ValueError(f"Page number {page_number} out of range (1-{doc.page_count})")
            
            page = doc[page_number - 1]  # Convert to 0-based
            content = page.get_text()
            
            doc.close()
            return content
            
        except Exception as e:
            logger.error(f"Error extracting page {page_number} from {file_path}: {e}")
            raise
    
    def get_pdf_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get basic information about the PDF
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF information
        """
        try:
            doc = fitz.open(str(file_path))
            
            info = {
                'page_count': doc.page_count,
                'metadata': doc.metadata,
                'file_size': file_path.stat().st_size,
                'is_encrypted': doc.is_encrypted,
                'is_pdf': doc.is_pdf
            }
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"Error getting PDF info for {file_path}: {e}")
            raise

