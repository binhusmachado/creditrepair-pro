from typing import Dict, Any, List
from datetime import datetime
from config import settings
import logging

logger = logging.getLogger(__name__)

class LetterGenerator:
    """Generate professional dispute letters"""
    
    def generate_letter(self, letter_type: str, dispute_data: Dict, client_data: Dict) -> str:
        """Generate a dispute letter based on type"""
        generators = {
            "bureau_dispute": self._generate_bureau_dispute,
            "debt_validation": self._generate_debt_validation,
            "goodwill": self._generate_goodwill,
            "direct_creditor": self._generate_direct_creditor,
            "cfpb_warning": self._generate_cfpb_warning,
            "method_of_verification": self._generate_mov_request,
            "cease_desist": self._generate_cease_desist,
            "section_605b": self._generate_section_605b
        }
        
        generator = generators.get(letter_type, self._generate_bureau_dispute)
        return generator(dispute_data, client_data)
    
    def _generate_bureau_dispute(self, dispute: Dict, client: Dict) -> str:
        """Generate bureau dispute letter"""
        bureau = dispute.get("bureau", "")
        bureau_info = settings.BUREAU_INFO.get(bureau, {})
        
        letter = f"""{datetime.utcnow().strftime("%B %d, %Y")}

{bureau_info.get('name', bureau.upper())}
{bureau_info.get('address', '')}
{bureau_info.get('city_state_zip', '')}

Re: Formal Dispute of Inaccurate Credit Information
Report #: [REPORT NUMBER]

To Whom It May Concern:

I am writing pursuant to the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681 et seq., to formally dispute the following inaccurate and/or incomplete information appearing in my credit file.

CONSUMER INFORMATION:
Name: {client.get('full_name', '')}
Address: {client.get('address', '')}
City, State ZIP: {client.get('city', '')}, {client.get('state', '')} {client.get('zip_code', '')}
SSN: XXX-XX-{client.get('ssn_last_four', 'XXXX')}
Date of Birth: {client.get('date_of_birth', '')}

DISPUTED ITEM(S):

{self._format_disputed_items(dispute.get('disputed_items', []))}

REASON FOR DISPUTE:
{dispute.get('dispute_reason', 'The information is inaccurate and/or incomplete.')}

LEGAL BASIS:
Under 15 U.S.C. § 1681i(a)(1)(A), you are required to conduct a reasonable investigation of this dispute within thirty (30) days of receipt. Pursuant to 15 U.S.C. § 1681e(b), you must follow reasonable procedures to assure maximum possible accuracy.

{self._get_specific_legal_citation(dispute.get('error_type', ''))}

REQUESTED ACTION:
I respectfully request that you:
1. Conduct an immediate investigation of the disputed item(s)
2. Delete or correct all inaccurate/incomplete information
3. Provide written confirmation of your actions
4. Notify all recipients of my credit report of any corrections

ATTACHMENTS:
□ Copy of government-issued photo ID
□ Copy of utility bill showing current address
□ Copy of relevant supporting documentation

Please be advised that this dispute is submitted in good faith. I request that this letter and all related correspondence be retained in my file.

Thank you for your prompt attention to this matter.

Sincerely,

_____________________________
{client.get('full_name', '')}
Date: {datetime.utcnow().strftime("%B %d, %Y")}

---
SEND VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED
"""
        return letter
    
    def _generate_debt_validation(self, dispute: Dict, client: Dict) -> str:
        """Generate debt validation letter"""
        return f"""{datetime.utcnow().strftime("%B %d, %Y")}

{dispute.get('creditor_name', '[CREDITOR NAME]')}
[COLLECTION AGENCY ADDRESS]

Re: Debt Validation Request
Account #: {dispute.get('account_number', '[ACCOUNT NUMBER]')}

To Whom It May Concern:

I am writing pursuant to the Fair Debt Collection Practices Act (FDCPA), 15 U.S.C. § 1692g, to request validation of the alleged debt referenced above.

CONSUMER INFORMATION:
Name: {client.get('full_name', '')}
Address: {client.get('full_address', '')}

DEBT INFORMATION:
Alleged Creditor: {dispute.get('creditor_name', '')}
Account Number: {dispute.get('account_number', '')}
Alleged Amount: [AMOUNT]

VALIDATION REQUESTED:
Please provide the following pursuant to 15 U.S.C. § 1692g(b):

1. The amount of the alleged debt, including an itemized accounting
2. The name and address of the original creditor
3. Verification that you are licensed to collect debt in my state
4. Proof that you own the debt or are authorized to collect on behalf of the creditor
5. A copy of the original signed contract bearing my signature
6. The original account number with the creditor
7. Proof that the debt is within the statute of limitations

CEASE COLLECTION:
Until you provide the requested validation, please cease all collection activities pursuant to 15 U.S.C. § 1692g(b). This includes:
- Contacting me by phone, mail, or electronic means
- Reporting or threatening to report the debt to credit bureaus
- Any other collection activities

Please govern yourselves accordingly.

Sincerely,

_____________________________
{client.get('full_name', '')}
Date: {datetime.utcnow().strftime("%B %d, %Y")}

---
SEND VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED
"""
    
    def _generate_goodwill(self, dispute: Dict, client: Dict) -> str:
        """Generate goodwill adjustment letter"""
        return f"""{datetime.utcnow().strftime("%B %d, %Y")}

{dispute.get('creditor_name', '[CREDITOR NAME]')}
Customer Service Department
[Creditor Address]

Re: Goodwill Adjustment Request
Account #: {dispute.get('account_number', '[ACCOUNT NUMBER]')}

To Whom It May Concern:

I am writing to request a goodwill adjustment regarding the above-referenced account.

ACCOUNT HISTORY:
I have been a customer since [DATE] and have maintained the account in good standing. Unfortunately, I experienced [brief explanation - job loss, medical emergency, etc.] which caused me to miss a payment in [DATE].

This was an isolated incident, and I have since:
□ Brought the account current
□ Maintained on-time payments for [X] months
□ [Any other positive actions]

I take full responsibility for the oversight and have implemented [safeguards - autopay, calendar reminders, etc.] to prevent future occurrences.

REQUEST:
I respectfully request that you remove the negative reporting from my credit file as a goodwill gesture. This would greatly assist me as I [reason - qualifying for a mortgage, better interest rates, etc.].

Your consideration of this request would be deeply appreciated.

Thank you for your time and understanding.

Sincerely,

_____________________________
{client.get('full_name', '')}
Date: {datetime.utcnow().strftime("%B %d, %Y")}

---
SEND VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED
"""
    
    def _generate_direct_creditor(self, dispute: Dict, client: Dict) -> str:
        """Generate direct creditor dispute"""
        return f"""{datetime.utcnow().strftime("%B %d, %Y")}

{dispute.get('creditor_name', '[CREDITOR NAME]')}
Data Furnisher Department
[Creditor Address]

Re: Direct Dispute Under FCRA § 623
Account #: {dispute.get('account_number', '[ACCOUNT NUMBER]')}

To Whom It May Concern:

I am writing pursuant to Section 623 of the Fair Credit Reporting Act (15 U.S.C. § 1681s-2) to dispute information you are furnishing to consumer reporting agencies.

CONSUMER INFORMATION:
Name: {client.get('full_name', '')}
Address: {client.get('full_address', '')}
SSN: XXX-XX-{client.get('ssn_last_four', 'XXXX')}

DISPUTED INFORMATION:
Account: {dispute.get('account_number', '')}
Issue: {dispute.get('dispute_reason', 'Inaccurate information')}

LEGAL OBLIGATION:
Under 15 U.S.C. § 1681s-2(a)(1)(A), you are required to report accurate information. Section 1681s-2(a)(1)(B) requires you to correct and update information. Additionally, 15 U.S.C. § 1681s-2(b) imposes specific duties upon receipt of a dispute.

REQUESTED ACTION:
Please:
1. Conduct an immediate investigation
2. Correct the inaccurate information
3. Notify all credit bureaus of the correction
4. Cease reporting the disputed information until corrected

I request written confirmation of your actions within 30 days.

Sincerely,

_____________________________
{client.get('full_name', '')}
Date: {datetime.utcnow().strftime("%B %d, %Y")}

---
SEND VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED
"""
    
    def _generate_cfpb_warning(self, dispute: Dict, client: Dict) -> str:
        """Generate CFPB warning letter"""
        bureau = dispute.get("bureau", "")
        bureau_info = settings.BUREAU_INFO.get(bureau, {})
        
        return f"""{datetime.utcnow().strftime("%B %d, %Y")}

{bureau_info.get('name', bureau.upper())}
{bureau_info.get('address', '')}
{bureau_info.get('city_state_zip', '')}

Re: Final Notice Before CFPB Complaint
Previous Dispute Dates: [DATES]

To Whom It May Concern:

This is my [SECOND/THIRD] attempt to resolve inaccurate information in my credit report. Despite previous disputes sent via certified mail, you have failed to:

□ Conduct a reasonable investigation
□ Correct or delete inaccurate information
□ Respond within 30 days as required by law

PREVIOUS DISPUTES:
{self._format_previous_disputes(dispute.get('previous_attempts', []))}

LEGAL VIOLATIONS:
Your failure to comply may constitute violations of:
- 15 U.S.C. § 1681i(a)(1)(A) - Failure to investigate
- 15 U.S.C. § 1681e(b) - Failure to ensure accuracy
- 15 U.S.C. § 1681s-2 - Furnisher violations

NOTICE OF INTENDED ACTION:
If you do not resolve this matter within 15 days, I will file complaints with:
1. Consumer Financial Protection Bureau (CFPB)
2. State Attorney General
3. Consider legal action for FCRA violations

This is your final opportunity to comply voluntarily.

Sincerely,

_____________________________
{client.get('full_name', '')}
Date: {datetime.utcnow().strftime("%B %d, %Y")}

---
SEND VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED
"""
    
    def _generate_mov_request(self, dispute: Dict, client: Dict) -> str:
        """Generate Method of Verification request"""
        bureau = dispute.get("bureau", "")
        bureau_info = settings.BUREAU_INFO.get(bureau, {})
        
        return f"""{datetime.utcnow().strftime("%B %d, %Y")}

{bureau_info.get('name', bureau.upper())}
{bureau_info.get('address', '')}
{bureau_info.get('city_state_zip', '')}

Re: Method of Verification Request - FCRA § 611(a)(7)
Original Dispute Date: [DATE]

To Whom It May Concern:

I previously disputed inaccurate information in my credit file (dispute sent [DATE]). You responded by claiming the information was "verified."

Pursuant to 15 U.S.C. § 1681i(a)(7), I hereby request the method of verification used:

DISPUTED ITEM:
{dispute.get('dispute_description', '[ITEM DESCRIPTION]')}

REQUESTED INFORMATION:
1. The name of the furnisher who verified the information
2. The address and telephone number of the furnisher
3. A copy of any documentation provided by the furnisher
4. A detailed description of your verification procedures
5. The specific documents or information relied upon

LEGAL REQUIREMENT:
Section 1681i(a)(7) requires you to provide this information within 15 days of receipt.

Your failure to provide this information will constitute a violation of the FCRA.

Sincerely,

_____________________________
{client.get('full_name', '')}
Date: {datetime.utcnow().strftime("%B %d, %Y")}

---
SEND VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED
"""
    
    def _generate_cease_desist(self, dispute: Dict, client: Dict) -> str:
        """Generate cease and desist letter"""
        return f"""{datetime.utcnow().strftime("%B %d, %Y")}

{dispute.get('creditor_name', '[COLLECTION AGENCY]')}
[Address]

Re: Cease and Desist - FDCPA § 1692c(c)
Account #: {dispute.get('account_number', '[ACCOUNT NUMBER]')}

To Whom It May Concern:

I am writing pursuant to the Fair Debt Collection Practices Act, 15 U.S.C. § 1692c(c), to demand that you CEASE AND DESIST all communication with me regarding the alleged debt referenced above.

NOTICE:
Effective immediately, you are directed to:

□ CEASE all telephone calls to any number
□ CEASE all written correspondence
□ CEASE all electronic communications
□ CEASE all contact with third parties
□ CEASE all reporting to credit bureaus

This notice applies to all employees, agents, and assigns.

LEGAL WARNING:
Any further communication except as specifically permitted by 15 U.S.C. § 1692c(c)(2) will constitute a violation of federal law, subjecting you to statutory damages, actual damages, and attorney fees.

Please govern yourselves accordingly.

Sincerely,

_____________________________
{client.get('full_name', '')}
Date: {datetime.utcnow().strftime("%B %d, %Y")}

---
SEND VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED
"""
    
    def _generate_section_605b(self, dispute: Dict, client: Dict) -> str:
        """Generate Section 605B identity theft block request"""
        bureau = dispute.get("bureau", "")
        bureau_info = settings.BUREAU_INFO.get(bureau, {})
        
        return f"""{datetime.utcnow().strftime("%B %d, %Y")}

{bureau_info.get('name', bureau.upper())}
{bureau_info.get('address', '')}
{bureau_info.get('city_state_zip', '')}

Re: Identity Theft Block Request - FCRA § 605B
Fraudulent Account: {dispute.get('account_number', '[ACCOUNT NUMBER]')}
Creditor: {dispute.get('creditor_name', '[CREDITOR NAME]')}

To Whom It May Concern:

I am a victim of identity theft. The above-referenced account was fraudulently opened in my name without my authorization.

VICTIM INFORMATION:
Name: {client.get('full_name', '')}
Address: {client.get('full_address', '')}
SSN: XXX-XX-{client.get('ssn_last_four', 'XXXX')}
Date of Birth: {client.get('date_of_birth', '')}

FRAUD DETAILS:
□ I did not open this account
□ I did not authorize anyone to open this account
□ I did not make any charges on this account
□ I discovered the fraud on [DATE]

LEGAL REQUIREMENT:
Under 15 U.S.C. § 1681c-2, you are required to block this adverse information from my credit report within four (4) business days of receiving:
1. Appropriate identification
2. An identity theft report (FTC affidavit and police report)

ATTACHMENTS:
□ Copy of government-issued photo ID
□ Copy of utility bill
□ FTC Identity Theft Report
□ Police Report

Please confirm the block within 5 business days.

Sincerely,

_____________________________
{client.get('full_name', '')}
Date: {datetime.utcnow().strftime("%B %d, %Y")}

---
SEND VIA CERTIFIED MAIL, RETURN RECEIPT REQUESTED
"""
    
    def _format_disputed_items(self, items: List[Dict]) -> str:
        """Format disputed items for letter"""
        if not items:
            return "[ITEM DETAILS TO BE INSERTED]"
        
        formatted = []
        for i, item in enumerate(items, 1):
            formatted.append(f"""
Item {i}:
- Creditor: {item.get('creditor_name', '')}
- Account #: {item.get('account_number', '')}
- Reason: {item.get('reason', '')}
""")
        return "\n".join(formatted)
    
    def _format_previous_disputes(self, attempts: List[Dict]) -> str:
        """Format previous dispute attempts"""
        if not attempts:
            return "□ [Previous dispute information]"
        
        formatted = []
        for attempt in attempts:
            formatted.append(f"□ {attempt.get('date', '')} - {attempt.get('method', '')}")
        return "\n".join(formatted)
    
    def _get_specific_legal_citation(self, error_type: str) -> str:
        """Get specific legal citation based on error type"""
        citations = {
            "outdated_negative": "15 U.S.C. § 1681a(1) - Items older than 7 years must be removed",
            "outdated_inquiry": "15 U.S.C. § 1681a(3) - Inquiries older than 2 years must be removed",
            "balance_exceeds_limit": "15 U.S.C. § 1681s-2(a)(1) - Furnishers must report accurate information",
            "duplicate_account": "15 U.S.C. § 1681e(b) - Reporting must be accurate",
            "identity_theft": "15 U.S.C. § 1681c-2 - Identity theft block required"
        }
        return citations.get(error_type, "15 U.S.C. § 1681i - Right to dispute inaccurate information")