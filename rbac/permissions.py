from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, Session
from enum import Enum
from typing import Optional, List
from rbac.roles import Base, RoleManager, Role

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class DefaultPermission(str, Enum):
    QUERY_RAG = "QUERY_RAG"
    INGEST_DOCUMENTS = "INGEST_DOCUMENTS"
    MANAGE_USERS = "MANAGE_USERS"
    MANAGE_ROLES = "MANAGE_ROLES"
    VIEW_ANALYTICS = "VIEW_ANALYTICS"
    MANAGE_CONFIG = "MANAGE_CONFIG"

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class PermissionManager:
    """Manages permissions and their assignment to roles"""
    
    def __init__(self, session: Session):
        self.session = session

    def create_permission(self, name: str, description: str) -> Permission:
        perm = Permission(name=name, description=description)
        self.session.add(perm)
        self.session.commit()
        self.session.refresh(perm)
        return perm

    def get_permission(self, name: str) -> Optional[Permission]:
        return self.session.query(Permission).filter(Permission.name == name).first()

    def assign_permission_to_role(self, role_name: str, permission_name: str) -> None:
        role = self.session.query(Role).filter(Role.name == role_name).first()
        perm = self.get_permission(permission_name)
        if role and perm and perm not in role.permissions:
            role.permissions.append(perm)
            self.session.commit()

    def get_role_permissions(self, role_name: str) -> List[Permission]:
        role = self.session.query(Role).filter(Role.name == role_name).first()
        if role:
            return role.permissions
        return []

    def initialize_default_permissions(self) -> None:
        defaults = {
            DefaultPermission.QUERY_RAG: "Query the RAG system",
            DefaultPermission.INGEST_DOCUMENTS: "Ingest documents to RAG",
            DefaultPermission.MANAGE_USERS: "Manage users",
            DefaultPermission.MANAGE_ROLES: "Manage roles",
            DefaultPermission.VIEW_ANALYTICS: "View system analytics",
            DefaultPermission.MANAGE_CONFIG: "Manage system configuration"
        }
        for name, desc in defaults.items():
            if not self.get_permission(name):
                self.create_permission(name, desc)

    def setup_default_role_permissions(self) -> None:
        role_permissions_map = {
            "admin": [
                DefaultPermission.QUERY_RAG,
                DefaultPermission.INGEST_DOCUMENTS,
                DefaultPermission.MANAGE_USERS,
                DefaultPermission.MANAGE_ROLES,
                DefaultPermission.VIEW_ANALYTICS,
                DefaultPermission.MANAGE_CONFIG
            ],
            "data_scientist": [
                DefaultPermission.QUERY_RAG,
                DefaultPermission.INGEST_DOCUMENTS,
                DefaultPermission.VIEW_ANALYTICS
            ],
            "analyst": [
                DefaultPermission.QUERY_RAG,
                DefaultPermission.VIEW_ANALYTICS
            ],
            "viewer": [
                DefaultPermission.QUERY_RAG
            ]
        }
        
        for role_name, perms in role_permissions_map.items():
            for perm in perms:
                self.assign_permission_to_role(role_name, perm)
