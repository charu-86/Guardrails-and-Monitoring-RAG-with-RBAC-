import yaml
import pathlib
import datetime
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rbac.roles import Base, User, Role, RoleManager
from rbac.permissions import Permission, PermissionManager

class RoleBasedAccessControl:
    """Core class for Role-Based Access Control logic, auth, and JWT"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.config = self._load_config()
        self.db_url = database_url or self.config.get("database_url", "sqlite:///./rag_rbac.db")
        
        self.engine = create_engine(
            self.db_url, 
            connect_args={"check_same_thread": False} if "sqlite" in self.db_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        Base.metadata.create_all(bind=self.engine)
        
        self.session = self.SessionLocal()
        self.role_manager = RoleManager(self.session)
        self.permission_manager = PermissionManager(self.session)
        
        self.role_manager.initialize_default_roles()
        self.permission_manager.initialize_default_permissions()
        self.permission_manager.setup_default_role_permissions()
        
        pwd_scheme = self.config.get("password_hash_scheme", "bcrypt")
        self.pwd_context = CryptContext(schemes=[pwd_scheme], deprecated="auto")
        
        self.secret_key = self.config.get("jwt_secret", "YOUR_SECRET_KEY")
        self.algorithm = self.config.get("jwt_algorithm", "HS256")
        self.token_expiry = self.config.get("jwt_token_expiry_minutes", 30)

    def _load_config(self) -> Dict[str, Any]:
        config_path = pathlib.Path(__file__).parent.parent / "config" / "config.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f).get("rbac", {})
        return {}

    def _hash_password(self, password: str) -> str:
        import bcrypt
        pwd_bytes = password.encode('utf-8')[:72]
        try:
            return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')
        except Exception:
            return self.pwd_context.hash(password[:72])

    def _verify_password(self, plain: str, hashed: str) -> bool:
        import bcrypt
        pwd_bytes = plain.encode('utf-8')[:72]
        try:
            return bcrypt.checkpw(pwd_bytes, hashed.encode('utf-8'))
        except Exception:
            return self.pwd_context.verify(plain[:72], hashed)

    def _log_auth_event(self, event_type: str, username: str, success: bool, details: Optional[str] = None) -> None:
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"[AUTH] {event_type} | User: {username} | Status: {status}"
        if details:
            log_msg += f" | Details: {details}"
        print(log_msg)

    def register_user(self, username: str, password: str, email: str, role_name: Optional[str] = None) -> User:
        hashed_password = self._hash_password(password)
        user = User(username=username, hashed_password=hashed_password, email=email)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        
        role_to_assign = role_name or "viewer"
        self.role_manager.assign_role_to_user(user, role_to_assign)
        
        self._log_auth_event("REGISTER", username, True, f"Assigned role: {role_to_assign}")
        return user

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.get_user(username)
        if not user or not self._verify_password(password, user.hashed_password):
            self._log_auth_event("LOGIN", username, False, "Invalid credentials")
            return None
        self._log_auth_event("LOGIN", username, True)
        return user

    def create_access_token(self, user: User, expires_delta: Optional[datetime.timedelta] = None) -> str:
        to_encode = {"sub": user.username, "roles": [role.name for role in user.roles]}
        expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=self.token_expiry))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def check_permission(self, user: User, permission_name: str) -> bool:
        for role in user.roles:
            for perm in role.permissions:
                if perm.name.lower() == permission_name.lower():
                    self._log_auth_event("CHECK_PERMISSION", user.username, True, f"Permission {permission_name} granted via role {role.name}")
                    return True
        self._log_auth_event("CHECK_PERMISSION", user.username, False, f"Permission {permission_name} denied")
        return False

    def get_user(self, username: str) -> Optional[User]:
        return self.session.query(User).filter(User.username == username).first()
