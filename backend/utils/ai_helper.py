import openai
import os

class AIHelper:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY", "")
    
    def analyze_credit_report(self, report_text: str):
        """Use AI to analyze credit report text"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a credit report analyzer. Extract key information and identify potential errors."},
                    {"role": "user", "content": f"Analyze this credit report:\n\n{report_text[:4000]}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI analysis error: {str(e)}"
    
    def generate_dispute_reason(self, error_type: str, account_info: dict):
        """Generate AI-powered dispute reason"""
        try:
            prompt = f"Generate a professional dispute reason for: {error_type}\nAccount: {account_info}"
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a credit repair specialist. Write professional dispute reasons."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Dispute reason: {error_type} - Please investigate and correct this information."