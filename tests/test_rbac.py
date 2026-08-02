import pytest
from rbac.access_control import RoleBasedAccessControl

class TestRoleBasedAccessControl:
    @pytest.fixture
    def rbac(self):
        return RoleBasedAccessControl(database_url='sqlite:///:memory:')

    def test_register_user(self, rbac):
        user = rbac.register_user("testuser", "password123", "test@example.com")
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_register_duplicate_user(self, rbac):
        rbac.register_user("testuser", "password123", "test@example.com")
        with pytest.raises(Exception):
            rbac.register_user("testuser", "password456", "test2@example.com")

    def test_authenticate_success(self, rbac):
        rbac.register_user("testuser", "password123", "test@example.com")
        user = rbac.authenticate("testuser", "password123")
        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_failure(self, rbac):
        rbac.register_user("testuser", "password123", "test@example.com")
        user = rbac.authenticate("testuser", "wrongpassword")
        assert user is None

    def test_create_access_token(self, rbac):
        user = rbac.register_user("testuser", "password123", "test@example.com")
        token = rbac.create_access_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token(self, rbac):
        user = rbac.register_user("testuser", "password123", "test@example.com")
        token = rbac.create_access_token(user)
        payload = rbac.verify_token(token)
        assert payload is not None
        assert payload.get("sub") == "testuser"

    def test_check_permission_admin(self, rbac):
        user = rbac.register_user("adminuser", "password123", "admin@example.com", role_name="admin")
        assert rbac.check_permission(user, "MANAGE_USERS") is True
        assert rbac.check_permission(user, "QUERY_RAG") is True

    def test_check_permission_viewer(self, rbac):
        user = rbac.register_user("vieweruser", "password123", "viewer@example.com", role_name="viewer")
        assert rbac.check_permission(user, "QUERY_RAG") is True

    def test_check_permission_denied(self, rbac):
        user = rbac.register_user("vieweruser", "password123", "viewer@example.com", role_name="viewer")
        assert rbac.check_permission(user, "MANAGE_USERS") is False

    def test_get_user(self, rbac):
        rbac.register_user("testuser", "password123", "test@example.com")
        user = rbac.get_user("testuser")
        assert user is not None
        assert user.username == "testuser"

    def test_assign_role(self, rbac):
        user = rbac.register_user("testuser", "password123", "test@example.com", role_name="viewer")
        rbac.role_manager.assign_role_to_user(user, "admin")
        
        roles = [r.name for r in user.roles]
        assert "admin" in roles
        assert rbac.check_permission(user, "MANAGE_USERS") is True
