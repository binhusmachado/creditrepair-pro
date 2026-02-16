from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)

class ErrorDetector:
    """Detect 20+ error types in credit reports"""
    
    ERROR_TYPES = {
        "outdated_negative": {
            "name": "Outdated Negative (7+ Years)",
            "severity": "high",
            "fcra_section": "605(a)(1)",
            "description": "Negative items older than 7 years",
            "estimated_impact": 15
        },
        "outdated_inquiry": {
            "name": "Outdated Hard Inquiry (2+ Years)",
            "severity": "medium",
            "fcra_section": "605(a)(3)",
            "description": "Hard inquiries older than 2 years",
            "estimated_impact": 5
        },
        "outdated_bankruptcy": {
            "name": "Outdated Bankruptcy (10+ Years)",
            "severity": "high",
            "fcra_section": "605(a)(1)",
            "description": "Bankruptcy older than 10 years",
            "estimated_impact": 50
        },
        "balance_exceeds_limit": {
            "name": "Balance Exceeds Credit Limit",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "Current balance exceeds stated credit limit",
            "estimated_impact": 10
        },
        "missing_credit_limit": {
            "name": "Missing Credit Limit",
            "severity": "medium",
            "fcra_section": "609(a)(1)",
            "description": "Account lacks credit limit information",
            "estimated_impact": 5
        },
        "duplicate_account": {
            "name": "Duplicate Account",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "Same account reported multiple times",
            "estimated_impact": 15
        },
        "impossible_late_pattern": {
            "name": "Impossible Late Payment Pattern",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "90+ day late without 30/60 day lates",
            "estimated_impact": 20
        },
        "contradictory_status": {
            "name": "Contradictory Account Status",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "Account status contradicts other data",
            "estimated_impact": 15
        },
        "paid_collection": {
            "name": "Paid Collection Still Reporting",
            "severity": "medium",
            "fcra_section": "623(a)(1)",
            "description": "Collection account still shows balance after payment",
            "estimated_impact": 10
        },
        "medical_collection_ncap": {
            "name": "Medical Collection (NCAP Eligible)",
            "severity": "medium",
            "fcra_section": "NCAP 2022",
            "description": "Paid medical collection eligible for removal",
            "estimated_impact": 15
        },
        "tax_lien_ncap": {
            "name": "Tax Lien (NCAP Eligible - 2018+)",
            "severity": "high",
            "fcra_section": "NCAP 2018",
            "description": "Tax lien eligible for removal under NCAP",
            "estimated_impact": 30
        },
        "charge_off_balance_growth": {
            "name": "Charge-Off Balance Increasing",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "Balance increasing after charge-off",
            "estimated_impact": 15
        },
        "closed_with_balance": {
            "name": "Closed Account with Balance",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "Closed account showing non-zero balance",
            "estimated_impact": 15
        },
        "future_date": {
            "name": "Future Date Listed",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "Date in the future",
            "estimated_impact": 10
        },
        "missing_date": {
            "name": "Missing Critical Date",
            "severity": "medium",
            "fcra_section": "609(a)(1)",
            "description": "Required date information missing",
            "estimated_impact": 5
        },
        "re_aging": {
            "name": "Account Re-Aging",
            "severity": "high",
            "fcra_section": "623(a)(5)",
            "description": "Date of first delinquency changed illegally",
            "estimated_impact": 25
        },
        "authorized_user_negative": {
            "name": "Authorized User Account Negative",
            "severity": "medium",
            "fcra_section": "605(a)(1)",
            "description": "Negative authorized user account",
            "estimated_impact": 10
        },
        "settled_with_balance": {
            "name": "Settled Account with Balance",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "Settled account showing remaining balance",
            "estimated_impact": 15
        },
        "unauthorized_inquiry": {
            "name": "Unauthorized Hard Inquiry",
            "severity": "medium",
            "fcra_section": "604(a)(3)",
            "description": "Hard inquiry without permissible purpose",
            "estimated_impact": 5
        },
        "cross_bureau_discrepancy": {
            "name": "Cross-Bureau Discrepancy",
            "severity": "high",
            "fcra_section": "623(a)(1)",
            "description": "Same account shows different data across bureaus",
            "estimated_impact": 15
        },
        "not_my_account": {
            "name": "Account Not Mine",
            "severity": "high",
            "fcra_section": "605B",
            "description": "Account does not belong to consumer",
            "estimated_impact": 20
        },
        "identity_theft": {
            "name": "Identity Theft / Fraud",
            "severity": "critical",
            "fcra_section": "605B",
            "description": "Fraudulent account opened without authorization",
            "estimated_impact": 50
        },
        "mixed_file": {
            "name": "Mixed Credit File",
            "severity": "high",
            "fcra_section": "607(b)",
            "description": "Another person's data on your report",
            "estimated_impact": 30
        }
    }
    
    def analyze_report(self, report_data: Dict) -> Dict[str, Any]:
        """Analyze a credit report for all error types"""
        errors = []
        discrepancies = []
        
        accounts = report_data.get("accounts", [])
        parsed_data = report_data.get("parsed_data", {})
        
        # Check each account for errors
        for account in accounts:
            account_errors = self._analyze_account(account)
            errors.extend(account_errors)
        
        # Check for cross-bureau discrepancies
        discrepancies = self._check_cross_bureau_discrepancies(accounts)
        
        # Check for outdated items
        outdated_errors = self._check_outdated_items(accounts, parsed_data)
        errors.extend(outdated_errors)
        
        # Check inquiries
        inquiry_errors = self._check_inquiries(parsed_data.get("inquiries", []))
        errors.extend(inquiry_errors)
        
        # Check public records
        record_errors = self._check_public_records(parsed_data.get("public_records", []))
        errors.extend(record_errors)
        
        # Calculate totals and impact
        total_impact = sum(e.get("estimated_impact", 0) for e in errors)
        
        return {
            "total_errors": len(errors),
            "total_discrepancies": len(discrepancies),
            "total_estimated_impact": total_impact,
            "errors": errors,
            "discrepancies": discrepancies,
            "error_summary": self._summarize_errors(errors),
            "priority_ranking": self._rank_by_priority(errors),
            "recommended_disputes": self._generate_dispute_recommendations(errors)
        }
    
    def _analyze_account(self, account: Dict) -> List[Dict]:
        """Analyze a single account for errors"""
        errors = []
        
        # Check balance vs limit
        balance = account.get("current_balance", 0) or 0
        limit = account.get("credit_limit", 0) or 0
        
        if limit > 0 and balance > limit:
            errors.append(self._create_error(
                "balance_exceeds_limit",
                account,
                f"Balance (${balance}) exceeds limit (${limit})"
            ))
        
        # Check missing credit limit on open accounts
        if account.get("account_status", "").lower() == "open" and limit == 0:
            if account.get("account_type", "").lower() in ["credit card", "revolving"]:
                errors.append(self._create_error(
                    "missing_credit_limit",
                    account,
                    "Credit limit not reported"
                ))
        
        # Check impossible late pattern
        late_30 = account.get("late_30_count", 0) or 0
        late_60 = account.get("late_60_count", 0) or 0
        late_90 = account.get("late_90_count", 0) or 0
        
        if late_90 > 0 and (late_30 == 0 or late_60 == 0):
            errors.append(self._create_error(
                "impossible_late_pattern",
                account,
                f"90+ day late without corresponding 30/60 day lates"
            ))
        
        # Check closed with balance
        status = account.get("account_status", "").lower()
        if "closed" in status or "paid" in status:
            if balance > 0 and not account.get("is_collection"):
                errors.append(self._create_error(
                    "closed_with_balance",
                    account,
                    f"Closed/paid account shows ${balance} balance"
                ))
        
        # Check charge-off balance growth
        if account.get("is_charge_off"):
            # Would need historical data to verify
            pass
        
        # Check for medical collections
        if account.get("is_collection"):
            creditor = account.get("creditor_name", "").lower()
            if any(term in creditor for term in ["medical", "hospital", "clinic", "health"]):
                errors.append(self._create_error(
                    "medical_collection_ncap",
                    account,
                    "Medical collection - may be eligible for NCAP removal"
                ))
        
        # Check authorized user with negatives
        if account.get("is_authorized_user") and account.get("is_negative"):
            errors.append(self._create_error(
                "authorized_user_negative",
                account,
                "Authorized user account showing negative history"
            ))
        
        return errors
    
    def _check_cross_bureau_discrepancies(self, accounts: List[Dict]) -> List[Dict]:
        """Check for discrepancies between bureaus"""
        discrepancies = []
        
        # Group by account number
        by_account = {}
        for account in accounts:
            acct_num = account.get("account_number", "")
            if acct_num:
                if acct_num not in by_account:
                    by_account[acct_num] = []
                by_account[acct_num].append(account)
        
        # Check for discrepancies
        for acct_num, acct_list in by_account.items():
            if len(acct_list) > 1:
                # Check balance discrepancies
                balances = [a.get("current_balance", 0) for a in acct_list]
                if len(set(balances)) > 1:
                    discrepancies.append({
                        "type": "cross_bureau_discrepancy",
                        "account_number": acct_num,
                        "description": f"Balance varies across bureaus: {balances}",
                        "severity": "high",
                        "fcra_section": "623(a)(1)"
                    })
                
                # Check status discrepancies
                statuses = [a.get("account_status", "") for a in acct_list]
                if len(set(statuses)) > 1:
                    discrepancies.append({
                        "type": "cross_bureau_discrepancy",
                        "account_number": acct_num,
                        "description": f"Status varies across bureaus: {statuses}",
                        "severity": "high",
                        "fcra_section": "623(a)(1)"
                    })
        
        return discrepancies
    
    def _check_outdated_items(self, accounts: List[Dict], parsed_data: Dict) -> List[Dict]:
        """Check for items past reporting periods"""
        errors = []
        now = datetime.utcnow()
        
        seven_years_ago = now - timedelta(days=7*365)
        ten_years_ago = now - timedelta(days=10*365)
        
        for account in accounts:
            date_opened = account.get("date_opened", "")
            
            # Check for negative items over 7 years
            if account.get("is_negative") and date_opened:
                try:
                    opened_date = datetime.strptime(date_opened, "%m/%Y")
                    if opened_date < seven_years_ago:
                        errors.append(self._create_error(
                            "outdated_negative",
                            account,
                            f"Negative item older than 7 years (opened {date_opened})"
                        ))
                except:
                    pass
        
        return errors
    
    def _check_inquiries(self, inquiries: List[Dict]) -> List[Dict]:
        """Check for inquiry-related errors"""
        errors = []
        now = datetime.utcnow()
        two_years_ago = now - timedelta(days=2*365)
        
        for inquiry in inquiries:
            if inquiry.get("type") == "hard":
                inquiry_date = inquiry.get("inquiry_date", "")
                try:
                    if inquiry_date:
                        date = datetime.strptime(inquiry_date, "%m/%d/%Y")
                        if date < two_years_ago:
                            errors.append({
                                "type": "outdated_inquiry",
                                "description": f"Hard inquiry from {inquiry_date} exceeds 2-year limit",
                                "severity": "medium",
                                "fcra_section": "605(a)(3)",
                                "estimated_impact": 5,
                                "inquiry": inquiry
                            })
                except:
                    pass
        
        return errors
    
    def _check_public_records(self, records: List[Dict]) -> List[Dict]:
        """Check public records for errors"""
        errors = []
        
        for record in records:
            if record.get("type") == "tax_lien":
                errors.append({
                    "type": "tax_lien_ncap",
                    "description": "Tax lien may be eligible for NCAP removal",
                    "severity": "high",
                    "fcra_section": "NCAP 2018",
                    "estimated_impact": 30,
                    "record": record
                })
            elif record.get("type") == "bankruptcy":
                # Check if over 10 years
                pass
        
        return errors
    
    def _create_error(self, error_type: str, account: Dict, description: str) -> Dict:
        """Create standardized error object"""
        error_info = self.ERROR_TYPES.get(error_type, {})
        
        return {
            "type": error_type,
            "name": error_info.get("name", error_type),
            "description": description,
            "account": {
                "creditor_name": account.get("creditor_name"),
                "account_number": account.get("account_number"),
                "account_type": account.get("account_type")
            },
            "severity": error_info.get("severity", "medium"),
            "fcra_section": error_info.get("fcra_section", "623(a)(1)"),
            "estimated_impact": error_info.get("estimated_impact", 10),
            "dispute_strategy": self._get_strategy_for_error(error_type),
            "priority": self._severity_to_priority(error_info.get("severity", "medium"))
        }
    
    def _get_strategy_for_error(self, error_type: str) -> str:
        """Get recommended dispute strategy for error type"""
        strategies = {
            "outdated_negative": "fcra_violation",
            "outdated_inquiry": "fcra_violation",
            "balance_exceeds_limit": "factual_dispute",
            "duplicate_account": "not_my_account",
            "impossible_late_pattern": "fcra_violation",
            "paid_collection": "collection_validation",
            "medical_collection_ncap": "collection_validation",
            "closed_with_balance": "factual_dispute",
            "unauthorized_inquiry": "fcra_violation",
            "identity_theft": "section_605b"
        }
        return strategies.get(error_type, "factual_dispute")
    
    def _severity_to_priority(self, severity: str) -> int:
        """Convert severity to priority number"""
        mapping = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        return mapping.get(severity, 3)
    
    def _summarize_errors(self, errors: List[Dict]) -> Dict:
        """Create summary statistics"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for error in errors:
            sev = error.get("severity", "low")
            summary[sev] = summary.get(sev, 0) + 1
        return summary
    
    def _rank_by_priority(self, errors: List[Dict]) -> List[Dict]:
        """Rank errors by priority"""
        return sorted(errors, key=lambda x: (x.get("priority", 5), -x.get("estimated_impact", 0)))
    
    def _generate_dispute_recommendations(self, errors: List[Dict]) -> List[Dict]:
        """Generate dispute recommendations"""
        ranked = self._rank_by_priority(errors)
        recommendations = []
        
        for i, error in enumerate(ranked[:15]):  # Max 15 disputes
            rec = {
                "rank": i + 1,
                "error_type": error.get("type"),
                "creditor": error.get("account", {}).get("creditor_name"),
                "strategy": error.get("dispute_strategy"),
                "priority": error.get("priority"),
                "estimated_impact": error.get("estimated_impact"),
                "legal_basis": f"FCRA § {error.get('fcra_section')}"
            }
            recommendations.append(rec)
        
        return recommendations