from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自訂權限：只有擁有者可以編輯，其他用戶只能讀取
    """
    def has_object_permission(self, request, view, obj):
        # 讀取權限允許任何請求
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 寫入權限只允許對象的擁有者
        return obj == request.user


class IsVerifiedUser(permissions.BasePermission):
    """
    自訂權限：只有已驗證的用戶可以訪問
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # 檢查用戶是否已驗證 Email 或手機
        return request.user.is_email_verified or request.user.is_phone_verified


class IsAdminUser(permissions.BasePermission):
    """
    自訂權限：只有管理員可以訪問
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff
