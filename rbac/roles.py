from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship, Session
from enum import Enum
import datetime
from typing import Optional, List

Base = declarative_base()

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

class DefaultRole(str, Enum):
    ADMIN = "admin"
    DATA_SCIENTIST = "data_scientist"
    ANALYST = "analyst"
    VIEWER = "viewer"

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    roles = relationship("Role", secondary=user_roles, back_populates="users")

class RoleManager:
    """Manages role creation and assignment"""
    
    def __init__(self, session: Session):
        self.session = session

    def create_role(self, name: str, description: str) -> Role:
        role = Role(name=name, description=description)
        self.session.add(role)
        self.session.commit()
        self.session.refresh(role)
        return role

    def get_role(self, name: str) -> Optional[Role]:
        return self.session.query(Role).filter(Role.name == name).first()

    def assign_role_to_user(self, user: User, role_name: str) -> None:
        role = self.get_role(role_name)
        if not role:
            role = self.create_role(role_name, f"Role: {role_name}")
        if role and role not in user.roles:
            user.roles.append(role)
            self.session.commit()

    def remove_role_from_user(self, user: User, role_name: str) -> None:
        role = self.get_role(role_name)
        if role and role in user.roles:
            user.roles.remove(role)
            self.session.commit()

    def get_user_roles(self, user: User) -> List[Role]:
        return user.roles

    def initialize_default_roles(self) -> None:
        defaults = {
            DefaultRole.ADMIN: "Administrator with full access",
            DefaultRole.DATA_SCIENTIST: "Data Scientist with access to models and ingestion",
            DefaultRole.ANALYST: "Analyst with access to queries and analytics",
            DefaultRole.VIEWER: "Viewer with read-only access"
        }
        for name, desc in defaults.items():
            if not self.get_role(name):
                self.create_role(name, desc)
