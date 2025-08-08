# 用戶認證 API 文檔

## 概述

SyrmaX 交易系統提供完整的用戶認證 API，支援用戶註冊、登入、登出、密碼管理、Email/手機驗證等功能。

## API 端點

### 1. 用戶註冊

**端點**: `POST /api/accounts/auth/users/`

**請求範例**:
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "first_name": "Test",
    "last_name": "User",
    "phone": "0912345678",
    "verification_method": "email"
}
```

**回應範例**:
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "phone": "0912345678",
    "verification_method": "email",
    "is_email_verified": false,
    "is_phone_verified": false,
    "date_joined": "2024-01-01T00:00:00Z"
}
```

### 2. 用戶登入

**端點**: `POST /api/accounts/token/`

**請求範例**:
```json
{
    "username": "testuser",
    "password": "securepass123"
}
```

**回應範例**:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Token 刷新

**端點**: `POST /api/accounts/token/refresh/`

**請求範例**:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 4. 獲取用戶資料

**端點**: `GET /api/accounts/profile/`

**請求標頭**:
```
Authorization: Bearer <access_token>
```

**回應範例**:
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "phone": "0912345678",
    "is_email_verified": false,
    "is_phone_verified": false,
    "verification_method": "email",
    "date_joined": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T12:00:00Z"
}
```

### 5. 更新用戶資料

**端點**: `PATCH /api/accounts/profile/update/`

**請求標頭**:
```
Authorization: Bearer <access_token>
```

**請求範例**:
```json
{
    "first_name": "Updated",
    "last_name": "Name",
    "phone": "0987654321"
}
```

### 6. 變更密碼

**端點**: `POST /api/accounts/password/change/`

**請求標頭**:
```
Authorization: Bearer <access_token>
```

**請求範例**:
```json
{
    "old_password": "oldpass123",
    "new_password": "newpass123",
    "new_password_confirm": "newpass123"
}
```

### 7. Email 驗證

**端點**: `POST /api/accounts/email/verify/`

**請求標頭**:
```
Authorization: Bearer <access_token>
```

**請求範例**:
```json
{
    "email": "test@example.com"
}
```

### 8. 手機驗證

**端點**: `POST /api/accounts/phone/verify/`

**請求標頭**:
```
Authorization: Bearer <access_token>
```

**請求範例**:
```json
{
    "phone": "0912345678",
    "verification_code": "123456"
}
```

### 9. 用戶登出

**端點**: `POST /api/accounts/logout/`

**請求標頭**:
```
Authorization: Bearer <access_token>
```

**請求範例**:
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 認證方式

### JWT Token 認證

系統使用 JWT (JSON Web Token) 進行認證：

1. **Access Token**: 用於 API 請求認證，有效期 1 小時
2. **Refresh Token**: 用於刷新 Access Token，有效期 7 天

### 請求標頭格式

```
Authorization: Bearer <access_token>
```

## 錯誤處理

### 常見錯誤回應

**400 Bad Request** - 請求資料錯誤
```json
{
    "username": ["用戶名已存在"],
    "email": ["Email 格式錯誤"],
    "password": ["密碼確認不匹配"]
}
```

**401 Unauthorized** - 認證失敗
```json
{
    "detail": "認證憑證未提供"
}
```

**403 Forbidden** - 權限不足
```json
{
    "detail": "您沒有執行此操作的權限"
}
```

## 權限控制

### 用戶權限等級

1. **匿名用戶**: 只能註冊和登入
2. **已認證用戶**: 可以訪問個人資料和基本功能
3. **已驗證用戶**: 可以訪問完整功能（需要 Email 或手機驗證）
4. **管理員用戶**: 可以訪問所有功能

### 自訂權限類別

- `IsOwnerOrReadOnly`: 只有擁有者可以編輯
- `IsVerifiedUser`: 只有已驗證用戶可以訪問
- `IsAdminUser`: 只有管理員可以訪問

## 測試

### 運行測試

```bash
python manage.py test accounts
```

### 測試覆蓋範圍

- 用戶模型測試
- API 端點測試
- 認證流程測試
- 權限控制測試
- 密碼變更測試

## 安全注意事項

1. **密碼安全**: 使用 Django 內建密碼驗證
2. **Token 安全**: JWT Token 有過期時間
3. **HTTPS**: 生產環境必須使用 HTTPS
4. **Rate Limiting**: 建議實作請求頻率限制
5. **Logging**: 記錄所有認證相關活動

## 未來擴展

1. **社交登入**: 支援 Google、Facebook 等第三方登入
2. **雙因素認證**: 支援 2FA
3. **API 金鑰**: 支援 API 金鑰認證
4. **角色權限**: 更細緻的權限控制
5. **審計日誌**: 詳細的用戶活動記錄
