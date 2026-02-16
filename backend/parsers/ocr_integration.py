from parsers.pdf_parser import PDFParser
from parsers.ocr_engine import OCREngine
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class OCRIntegration:
    """Integration layer for PDF and OCR processing"""
    
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.ocr_engine = OCREngine()
    
    def process_credit_report(self, file_path: str, bureau: str = None) -> Dict[str, Any]:
        """
        Process a credit report file using both PDF parsing and OCR
        Returns structured data with error handling
        """
        result = {
            "file_path": file_path,
            "bureau": bureau or "unknown",
            "success": False,
            "data": {},
            "errors": [],
            "method_used": None
        }
        
        try:
            # First try direct PDF text extraction
            logger.info("Attempting direct PDF text extraction...")
            pdf_data = self.pdf_parser.parse_report(file_path, bureau)
            
            # Check if we got good data
            has_meaningful_data = (
                pdf_data.get("personal_info") or
                any(pdf_data.get("scores", {}).values()) or
                len(pdf_data.get("accounts", [])) > 0
            )
            
            if has_meaningful_data and "error" not in pdf_data:
                logger.info("Direct PDF extraction successful")
                result["success"] = True
                result["data"] = pdf_data
                result["method_used"] = "pdf_parser"
                return result
            
            # If direct extraction fails or returns minimal data, try OCR
            logger.info("Direct extraction insufficient, trying OCR...")
            ocr_text = self.ocr_engine.process_pdf(file_path)
            
            if not ocr_text.startswith("OCR Error"):
                # Parse OCR text
                bureau_detected = self.pdf_parser._detect_bureau(ocr_text)
                personal_info = self.pdf_parser._extract_personal_info(ocr_text)
                accounts = self.pdf_parser._extract_accounts(ocr_text, [])
                inquiries = self.pdf_parser._extract_inquiries(ocr_text)
                records = self.pdf_parser._extract_public_records(ocr_text)
                
                # Extract scores from OCR
                scores = {
                    "equifax": self.pdf_parser._extract_score(ocr_text, "equifax"),
                    "experian": self.pdf_parser._extract_score(ocr_text, "experian"),
                    "transunion": self.pdf_parser._extract_score(ocr_text, "transunion")
                }
                
                result["success"] = True
                result["data"] = {
                    "format": "OCR_Extracted",
                    "bureau": bureau_detected,
                    "personal_info": personal_info,
                    "scores": scores,
                    "accounts": accounts,
                    "inquiries": inquiries,
                    "public_records": records,
                    "raw_text": ocr_text[:50000],
                    "ocr_processed": True,
                    "file_path": file_path
                }
                result["method_used"] = "ocr"
                return result
            
            result["errors"].append("Both PDF parsing and OCR failed")
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            result["errors"].append(str(e))
        
        return result
    
    def process_upload(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """Handle uploaded file processing"""
        if file_type and file_type.startswith('image/'):
            logger.info("Processing image file...")
            ocr_text = self.ocr_engine.process_image(file_path)
            
            # Extract data from OCR text
            accounts = self.pdf_parser._extract_accounts(ocr_text, [])
            personal_info = self.pdf_parser._extract_personal_info(ocr_text)
            
            return {
                "success": True,
                "method_used": "ocr_image",
                "data": {
                    "format": "Image_OCR",
                    "raw_text": ocr_text,
                    "personal_info": personal_info,
                    "accounts": accounts,
                    "scores": {
                        "equifax": self.pdf_parser._extract_score(ocr_text, "equifax"),
                        "experian": self.pdf_parser._extract_score(ocr_text, "experian"),
                        "transunion": self.pdf_parser._extract_score(ocr_text, "transunion")
                    }
                }
            }
        else:
            return self.process_credit_report(file_path)