import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME = "CreditRepair Pro"
    VERSION = "1.0.0"
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://creditrepair:password123@localhost:5432/credit_repair")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET", "credit-reports-bucket")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    
    # Dispute settings
    DISPUTE_WAIT_DAYS = 30
    MAX_DISPUTES_PER_ROUND = 5
    FOLLOW_UP_DAYS = 35
    
    # Bureau information
    BUREAU_INFO = {
        "equifax": {
            "name": "Equifax Information Services LLC",
            "address": "P.O. Box 740256",
            "city_state_zip": "Atlanta, GA 30374-0256",
            "phone": "1-800-685-1111",
            "fax": "1-866-795-5599",
            "website": "www.equifax.com",
            "online_dispute": "https://www.equifax.com/personal/disputes/"
        },
        "experian": {
            "name": "Experian",
            "address": "P.O. Box 4500",
            "city_state_zip": "Allen, TX 75013",
            "phone": "1-888-397-3742",
            "fax": "1-972-390-3630",
            "website": "www.experian.com",
            "online_dispute": "https://www.experian.com/disputes/main.html"
        },
        "transunion": {
            "name": "TransUnion LLC",
            "address": "P.O. Box 2000",
            "city_state_zip": "Chester, PA 19016",
            "phone": "1-800-916-8800",
            "fax": "1-610-546-4603",
            "website": "www.transunion.com",
            "online_dispute": "https://www.transunion.com/credit-disputes"
        }
    }

settings = Settings()