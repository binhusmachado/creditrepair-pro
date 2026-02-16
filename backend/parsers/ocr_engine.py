from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class OCREngine:
    """Advanced OCR engine for extracting text from scanned PDFs and images"""
    
    def __init__(self):
        self.preprocessing_enabled = True
        self.tesseract_config = r'--oem 3 --psm 6'
        
    def process_pdf(self, pdf_path: str, dpi: int = 300) -> str:
        """Convert PDF to images and perform OCR"""
        try:
            logger.info(f"Processing PDF with OCR: {pdf_path}")
            images = convert_from_path(pdf_path, dpi=dpi)
            
            full_text = ""
            for i, image in enumerate(images):
                logger.info(f"Processing page {i+1}/{len(images)}")
                page_text = self._process_image(image)
                full_text += f"\n--- Page {i+1} ---\n" + page_text
            
            return self._post_process_text(full_text)
            
        except Exception as e:
            logger.error(f"PDF OCR error: {str(e)}")
            return f"OCR Error: {str(e)}"
    
    def process_image(self, image_path: str) -> str:
        """Process a single image file"""
        try:
            image = Image.open(image_path)
            text = self._process_image(image)
            return self._post_process_text(text)
        except Exception as e:
            logger.error(f"Image OCR error: {str(e)}")
            return f"OCR Error: {str(e)}"
    
    def _process_image(self, image: Image.Image, strategy: str = "adaptive") -> str:
        """Process image with specified strategy"""
        strategies = {
            "standard": self._preprocess_standard,
            "aggressive": self._preprocess_aggressive,
            "adaptive": self._preprocess_adaptive,
            "morphological": self._preprocess_morphological,
            "deskew": self._preprocess_deskew
        }
        
        preprocessor = strategies.get(strategy, self._preprocess_adaptive)
        processed = preprocessor(image)
        
        text = pytesseract.image_to_string(processed, config=self.tesseract_config)
        return text
    
    def _preprocess_standard(self, image: Image.Image) -> np.ndarray:
        """Standard preprocessing"""
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        return binary
    
    def _preprocess_aggressive(self, image: Image.Image) -> np.ndarray:
        """Aggressive preprocessing for poor quality scans"""
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def _preprocess_adaptive(self, image: Image.Image) -> np.ndarray:
        """Adaptive thresholding preprocessing"""
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return binary
    
    def _preprocess_morphological(self, image: Image.Image) -> np.ndarray:
        """Morphological preprocessing for faded text"""
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        kernel = np.ones((2,2), np.uint8)
        dilated = cv2.dilate(gray, kernel, iterations=1)
        _, binary = cv2.threshold(dilated, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def _preprocess_deskew(self, image: Image.Image) -> np.ndarray:
        """Deskew preprocessing for rotated documents"""
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        
        # Detect skew angle
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Rotate
        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)
        
        _, binary = cv2.threshold(rotated, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def _post_process_text(self, text: str) -> str:
        """Post-process OCR text with corrections"""
        corrections = {
            "Equlfax": "Equifax",
            "Equlfa": "Equifax",
            "Experlan": "Experian",
            "Experian": "Experian",
            "TransUnlon": "TransUnion",
            "TransUnon": "TransUnion",
            "credlt": "credit",
            "sc0re": "score",
            "acc0unt": "account",
            "b4lance": "balance",
            "p4yment": "payment",
            "h1story": "history",
            "negatlve": "negative",
            "posltlve": "positive",
            "inquiry": "inquiry",
            "1nqu1ry": "inquiry",
            "judgment": "judgment",
            "bankruptcy": "bankruptcy",
            "c0llectlon": "collection",
            "charg3-off": "charge-off",
            "ch4rge-off": "charge-off",
            "del1nquent": "delinquent",
            "p4st due": "past due",
            "curr3nt": "current",
            "op3ned": "opened",
            "cl0sed": "closed",
            "1lm1t": "limit",
            "h1gh": "high",
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def extract_credit_report_data(self, text: str) -> Dict:
        """Extract structured data from OCR text"""
        import re
        
        data = {
            "raw_ocr_text": text,
            "pages_processed": text.count("--- Page"),
            "confidence": "medium",
            "extracted_scores": {}
        }
        
        # Try to extract scores
        score_patterns = [
            r"(?:Equifax|EQ)[\s:]*(\d{3})",
            r"(?:Experian|EX)[\s:]*(\d{3})",
            r"(?:TransUnion|TU)[\s:]*(\d{3})"
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bureau = "equifax" if "Equifax" in pattern else "experian" if "Experian" in pattern else "transunion"
                data["extracted_scores"][bureau] = int(match.group(1))
        
        return data