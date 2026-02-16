from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import User, Client, AuditLog
from config import settings
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """JWT Authentication service"""
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def register_user(self, db: Session, user_data: dict) -> dict:
        """Register a new user"""
        # Check if email exists
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            return {"success": False, "error": "Email already registered"}
        
        # Create user
        hashed_password = self.get_password_hash(user_data["password"])
        
        user = User(
            email=user_data["email"],
            password_hash=hashed_password,
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            role=user_data.get("role", "client"),
            verification_token=User.generate_token()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Registered user: {user.email}")
        
        return {
            "success": True,
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "message": "User registered successfully"
        }
    
    def register_client(self, db: Session, client_data: dict) -> dict:
        """Register a new client with user account"""
        # Create client record
        client = Client(
            first_name=client_data["first_name"],
            last_name=client_data["last_name"],
            email=client_data["email"],
            phone=client_data.get("phone"),
            address=client_data.get("address"),
            city=client_data.get("city"),
            state=client_data.get("state"),
            zip_code=client_data.get("zip_code"),
            ssn_last_four=client_data.get("ssn_last_four"),
            date_of_birth=client_data.get("date_of_birth")
        )
        
        db.add(client)
        db.flush()  # Get client.id without committing
        
        # Create user account for client
        hashed_password = self.get_password_hash(client_data["password"])
        
        user = User(
            email=client_data["email"],
            password_hash=hashed_password,
            first_name=client_data["first_name"],
            last_name=client_data["last_name"],
            role="client",
            client_id=client.id,
            verification_token=User.generate_token()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        db.refresh(client)
        
        # Create audit log
        audit_log = AuditLog(
            user_id=user.id,
            action="client_registered",
            details=f"Client {client.full_name} registered",
            ip_address=client_data.get("ip_address")
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Registered client: {client.email}")
        
        return {
            "success": True,
            "client_id": client.id,
            "user_id": user.id,
            "email": user.email,
            "message": "Client registered successfully"
        }
    
    def login_user(self, db: Session, email: str, password: str, ip_address: str = None) -> dict:
        """Login a user"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not self.verify_password(password, user.password_hash):
            return {"success": False, "error": "Invalid email or password"}
        
        if not user.is_active:
            return {"success": False, "error": "Account is deactivated"}
        
        # Update login info
        user.last_login = datetime.utcnow()
        user.login_count += 1
        
        # Create refresh token
        refresh_token = self.create_refresh_token({"sub": user.email, "user_id": user.id})
        user.refresh_token = refresh_token
        user.refresh_token_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Create audit log
        audit_log = AuditLog(
            user_id=user.id,
            action="login",
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        
        # Create access token
        access_token = self.create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
        
        logger.info(f"User logged in: {user.email}")
        
        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "client_id": user.client_id
            }
        }
    
    def refresh_access_token(self, db: Session, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        payload = self.decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            return {"success": False, "error": "Invalid refresh token"}
        
        user = db.query(User).filter(
            User.id == payload.get("user_id"),
            User.refresh_token == refresh_token
        ).first()
        
        if not user or not user.is_active:
            return {"success": False, "error": "Invalid refresh token"}
        
        if user.refresh_token_expires and user.refresh_token_expires < datetime.utcnow():
            return {"success": False, "error": "Refresh token expired"}
        
        # Create new access token
        access_token = self.create_access_token({
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        })
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    def change_password(self, db: Session, user_id: int, current_password: str, new_password: str) -> dict:
        """Change user password"""
        user = db.query(User).get(user_id)
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        if not self.verify_password(current_password, user.password_hash):
            return {"success": False, "error": "Current password is incorrect"}
        
        user.password_hash = self.get_password_hash(new_password)
        db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return {"success": True, "message": "Password changed successfully"}
    
    def request_password_reset(self, db: Session, email: str) -> dict:
        """Request password reset"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if email exists
            return {"success": True, "message": "If this email exists, a reset link has been sent"}
        
        # Generate reset token
        user.reset_token = User.generate_token()
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        logger.info(f"Password reset requested for: {email}")
        
        return {
            "success": True,
            "reset_token": user.reset_token,
            "message": "Password reset token generated"
        }
    
    def reset_password(self, db: Session, reset_token: str, new_password: str) -> dict:
        """Reset password with token"""
        user = db.query(User).filter(
            User.reset_token == reset_token,
            User.reset_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            return {"success": False, "error": "Invalid or expired reset token"}
        
        user.password_hash = self.get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        
        logger.info(f"Password reset completed for: {user.email}")
        
        return {"success": True, "message": "Password reset successfully"}