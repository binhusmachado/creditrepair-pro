# CreditRepair Pro - Credit Repair SaaS

Complete credit repair platform with automated dispute letter generation.

## Local Development

```bash
docker-compose up -d
```

Access at http://localhost:3000

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values.

### Required
- DATABASE_URL
- OPENAI_API_KEY
- SECRET_KEY
- STRIPE_SECRET_KEY
- SMTP credentials