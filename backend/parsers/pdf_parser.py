import pdfplumber
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PDFParser:
    """Parse credit report PDFs from all three bureaus and formats"""
    
    def __init__(self):
        self.parsed_data = {}
        
    def parse_report(self, file_path: str, bureau: str = None) -> Dict[str, Any]:
        """Parse a credit report PDF and extract structured data"""
        try:
            full_text = ""
            tables = []
            
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                    # Extract tables for account data
                    page_tables = page.extract_tables()
                    tables.extend(page_tables)
            
            # Detect bureau and format
            detected_bureau = bureau or self._detect_bureau(full_text)
            report_format = self._detect_format(full_text)
            
            # Parse based on format
            if report_format == "SmartCredit":
                return self._parse_smartcredit(full_text, tables, file_path)
            elif report_format == "IdentityIQ":
                return self._parse_identityiq(full_text, tables, file_path)
            elif detected_bureau == "equifax":
                return self._parse_equifax(full_text, tables, file_path)
            elif detected_bureau == "experian":
                return self._parse_experian(full_text, tables, file_path)
            elif detected_bureau == "transunion":
                return self._parse_transunion(full_text, tables, file_path)
            else:
                return self._parse_generic(full_text, tables, file_path)
                    
        except Exception as e:
            logger.error(f"PDF parsing error: {str(e)}")
            return {"error": str(e), "file_path": file_path}
    
    def _detect_bureau(self, text: str) -> str:
        """Detect which bureau the report is from"""
        text_lower = text.lower()
        scores = {
            "equifax": text_lower.count("equifax"),
            "experian": text_lower.count("experian"),
            "transunion": text_lower.count("transunion")
        }
        max_bureau = max(scores, key=scores.get)
        return max_bureau if scores[max_bureau] > 0 else "unknown"
    
    def _detect_format(self, text: str) -> str:
        """Detect the credit report format"""
        text_lower = text.lower()
        if "smartcredit" in text_lower or "smart credit" in text_lower:
            return "SmartCredit"
        elif "identityiq" in text_lower or "identity iq" in text_lower:
            return "IdentityIQ"
        elif "myfico" in text_lower:
            return "MyFICO"
        elif "annualcreditreport" in text_lower:
            return "AnnualCreditReport"
        return "Unknown"
    
    def _extract_score(self, text: str, bureau: str = None) -> Optional[int]:
        """Extract credit score from text"""
        patterns = [
            rf"{bureau}.*?score[:\s]*(\d{{3}})" if bureau else r"credit\s*score[:\s]*(\d{3})",
            r"score[:\s]*(\d{3})",
            r"(\d{3})\s*(?:credit\s*)?score",
            r"fico\s*score[:\s]*(\d{3})",
            r"vantage\s*score[:\s]*(\d{3})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                score = int(match.group(1))
                if 300 <= score <= 850:
                    return score
        return None
    
    def _extract_personal_info(self, text: str) -> Dict:
        """Extract personal information from report"""
        info = {}
        
        # Name
        name_match = re.search(r"(?:name|consumer)[:\s]+([A-Za-z\s]+)", text, re.IGNORECASE)
        if name_match:
            info["name"] = name_match.group(1).strip()
        
        # Address
        address_match = re.search(r"(?:current\s*)?address[:\s]+([^\n]+(?:\n[^\n]+)?)", text, re.IGNORECASE)
        if address_match:
            info["address"] = address_match.group(1).strip()
        
        # SSN
        ssn_match = re.search(r"(?:ssn|social)[:\s]+(\d{3}-?\d{2}-?\d{4}|XXX-XX-(\d{4}))", text, re.IGNORECASE)
        if ssn_match:
            ssn = ssn_match.group(1)
            if "X" in ssn:
                info["ssn_last_four"] = ssn_match.group(2)
            else:
                info["ssn_last_four"] = ssn[-4:]
        
        # DOB
        dob_match = re.search(r"(?:dob|date\s*of\s*birth)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text, re.IGNORECASE)
        if dob_match:
            info["date_of_birth"] = dob_match.group(1)
        
        return info
    
    def _extract_accounts(self, text: str, tables: List) -> List[Dict]:
        """Extract account information from report"""
        accounts = []
        
        # Look for account sections
        account_patterns = [
            r"(?:revolving|installment|mortgage|open|closed)\s*accounts",
            r"(?:creditor|account)\s*name",
            r"tradelines"
        ]
        
        # Try to extract from tables first
        for table in tables:
            if table and len(table) > 1:
                for row in table[1:]:  # Skip header
                    if row and len(row) >= 3:
                        account = {
                            "creditor_name": row[0] if row[0] else "",
                            "account_number": self._mask_account_number(row[1]) if len(row) > 1 else "",
                            "account_type": "",
                            "current_balance": self._parse_amount(row[2]) if len(row) > 2 else 0,
                            "status": ""
                        }
                        if account["creditor_name"]:
                            accounts.append(account)
        
        # Extract from text if tables didn't work
        if not accounts:
            # Find account blocks
            account_blocks = re.findall(
                r"([A-Z][A-Za-z\s&.,]+)\s+([X\d-]+)\s+([A-Za-z]+)\s+([\d,]+\.?\d*)",
                text
            )
            for block in account_blocks:
                accounts.append({
                    "creditor_name": block[0].strip(),
                    "account_number": self._mask_account_number(block[1]),
                    "account_type": block[2],
                    "current_balance": self._parse_amount(block[3]),
                    "status": ""
                })
        
        return accounts
    
    def _extract_inquiries(self, text: str) -> List[Dict]:
        """Extract hard and soft inquiries"""
        inquiries = []
        
        # Hard inquiries
        hard_pattern = r"(?:hard\s*)?inquiries?[\s:]*([^\n]*(?:\n(?![A-Z]{2,})[^\n]*)*)"
        hard_match = re.search(hard_pattern, text, re.IGNORECASE)
        if hard_match:
            inquiry_text = hard_match.group(1)
            creditor_matches = re.findall(r"([A-Z][A-Za-z\s]+)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", inquiry_text)
            for match in creditor_matches:
                inquiries.append({
                    "creditor_name": match[0].strip(),
                    "inquiry_date": match[1],
                    "type": "hard"
                })
        
        return inquiries
    
    def _extract_public_records(self, text: str) -> List[Dict]:
        """Extract public records (bankruptcy, judgments, tax liens)"""
        records = []
        
        patterns = {
            "bankruptcy": r"(?:chapter\s*(7|11|13)|bankruptcy)\s*[\s:]*([^\n]+)",
            "judgment": r"(?:civil\s*)?judgment[\s:]*([^\n]+)",
            "tax_lien": r"tax\s*lien[\s:]*([^\n]+)"
        }
        
        for record_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                records.append({
                    "type": record_type,
                    "details": match if isinstance(match, str) else match[-1],
                    "status": "active"
                })
        
        return records
    
    def _mask_account_number(self, account_num: str) -> str:
        """Mask account number for security"""
        if not account_num:
            return ""
        account_num = str(account_num).strip()
        if len(account_num) > 4:
            return "X" * (len(account_num) - 4) + account_num[-4:]
        return account_num
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str:
            return 0.0
        try:
            return float(str(amount_str).replace(",", "").replace("$", "").strip())
        except:
            return 0.0
    
    def _parse_smartcredit(self, text: str, tables: List, file_path: str) -> Dict:
        """Parse SmartCredit report format"""
        return {
            "format": "SmartCredit",
            "bureau": self._detect_bureau(text),
            "personal_info": self._extract_personal_info(text),
            "scores": {
                "equifax": self._extract_score(text, "equifax"),
                "experian": self._extract_score(text, "experian"),
                "transunion": self._extract_score(text, "transunion")
            },
            "accounts": self._extract_accounts(text, tables),
            "inquiries": self._extract_inquiries(text),
            "public_records": self._extract_public_records(text),
            "raw_text": text[:50000],  # Limit raw text size
            "file_path": file_path,
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _parse_identityiq(self, text: str, tables: List, file_path: str) -> Dict:
        """Parse IdentityIQ report format"""
        return {
            "format": "IdentityIQ",
            "bureau": self._detect_bureau(text),
            "personal_info": self._extract_personal_info(text),
            "scores": {
                "equifax": self._extract_score(text, "equifax"),
                "experian": self._extract_score(text, "experian"),
                "transunion": self._extract_score(text, "transunion")
            },
            "accounts": self._extract_accounts(text, tables),
            "inquiries": self._extract_inquiries(text),
            "public_records": self._extract_public_records(text),
            "raw_text": text[:50000],
            "file_path": file_path,
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _parse_equifax(self, text: str, tables: List, file_path: str) -> Dict:
        """Parse Equifax report format"""
        return {
            "format": "Equifax",
            "bureau": "equifax",
            "personal_info": self._extract_personal_info(text),
            "scores": {"equifax": self._extract_score(text, "equifax")},
            "accounts": self._extract_accounts(text, tables),
            "inquiries": self._extract_inquiries(text),
            "public_records": self._extract_public_records(text),
            "raw_text": text[:50000],
            "file_path": file_path,
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _parse_experian(self, text: str, tables: List, file_path: str) -> Dict:
        """Parse Experian report format"""
        return {
            "format": "Experian",
            "bureau": "experian",
            "personal_info": self._extract_personal_info(text),
            "scores": {"experian": self._extract_score(text, "experian")},
            "accounts": self._extract_accounts(text, tables),
            "inquiries": self._extract_inquiries(text),
            "public_records": self._extract_public_records(text),
            "raw_text": text[:50000],
            "file_path": file_path,
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _parse_transunion(self, text: str, tables: List, file_path: str) -> Dict:
        """Parse TransUnion report format"""
        return {
            "format": "TransUnion",
            "bureau": "transunion",
            "personal_info": self._extract_personal_info(text),
            "scores": {"transunion": self._extract_score(text, "transunion")},
            "accounts": self._extract_accounts(text, tables),
            "inquiries": self._extract_inquiries(text),
            "public_records": self._extract_public_records(text),
            "raw_text": text[:50000],
            "file_path": file_path,
            "parsed_at": datetime.utcnow().isoformat()
        }
    
    def _parse_generic(self, text: str, tables: List, file_path: str) -> Dict:
        """Generic parser for unknown formats"""
        return {
            "format": "Unknown",
            "bureau": "unknown",
            "personal_info": self._extract_personal_info(text),
            "scores": {
                "equifax": self._extract_score(text, "equifax"),
                "experian": self._extract_score(text, "experian"),
                "transunion": self._extract_score(text, "transunion")
            },
            "accounts": self._extract_accounts(text, tables),
            "inquiries": self._extract_inquiries(text),
            "public_records": self._extract_public_records(text),
            "raw_text": text[:50000],
            "file_path": file_path,
            "parsed_at": datetime.utcnow().isoformat()
        }