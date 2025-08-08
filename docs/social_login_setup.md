# 社交登入配置指南

## 概述

SyrmaX 交易系統支援 Google 和 Facebook 社交登入，讓用戶可以快速註冊和登入。

## 配置步驟

### 1. Google OAuth2 配置

#### 1.1 創建 Google Cloud 專案
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 創建新專案或選擇現有專案
3. 啟用 Google+ API

#### 1.2 創建 OAuth2 憑證
1. 在 Google Cloud Console 中，前往「憑證」頁面
2. 點擊「建立憑證」→「OAuth 2.0 用戶端 ID」
3. 選擇「網頁應用程式」
4. 設定授權重新導向 URI：
   - 開發環境：`http://localhost:8000/api/accounts/social/complete/google-oauth2/`
   - 生產環境：`https://your-domain.com/api/accounts/social/complete/google-oauth2/`
5. 記錄下 Client ID 和 Client Secret

#### 1.3 更新 Django 設定
在 `syrmax_api/settings.py` 中更新：
```python
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'your-google-oauth2-key'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'your-google-oauth2-secret'
```

### 2. Facebook OAuth2 配置

#### 2.1 創建 Facebook 應用程式
1. 前往 [Facebook Developers](https://developers.facebook.com/)
2. 創建新應用程式
3. 選擇「消費者」應用程式類型

#### 2.2 配置 OAuth 設定
1. 在應用程式設定中，前往「Facebook 登入」
2. 設定有效的 OAuth 重新導向 URI：
   - 開發環境：`http://localhost:8000/api/accounts/social/complete/facebook/`
   - 生產環境：`https://your-domain.com/api/accounts/social/complete/facebook/`
3. 記錄下 App ID 和 App Secret

#### 2.3 更新 Django 設定
在 `syrmax_api/settings.py` 中更新：
```python
SOCIAL_AUTH_FACEBOOK_KEY = 'your-facebook-app-id'
SOCIAL_AUTH_FACEBOOK_SECRET = 'your-facebook-app-secret'
```

### 3. Email 服務配置

#### 3.1 Gmail SMTP 配置
1. 啟用 Gmail 的「兩步驟驗證」
2. 生成「應用程式密碼」
3. 在 `syrmax_api/settings.py` 中更新：
```python
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

#### 3.2 其他 Email 服務商
- **SendGrid**: 使用 SendGrid SMTP
- **Amazon SES**: 使用 Amazon SES SMTP
- **Mailgun**: 使用 Mailgun SMTP

## API 端點

### 社交登入端點

| 功能 | 端點 | 方法 | 說明 |
|------|------|------|------|
| Google 登入 | `/api/accounts/social/login/google-oauth2/` | GET | 重導向到 Google 登入 |
| Facebook 登入 | `/api/accounts/social/login/facebook/` | GET | 重導向到 Facebook 登入 |
| 社交登入完成 | `/api/accounts/social/complete/{provider}/` | GET | 處理登入回調 |
| 社交帳號狀態 | `/api/accounts/social/status/` | GET | 獲取用戶社交帳號 |

### Email 驗證端點

| 功能 | 端點 | 方法 | 說明 |
|------|------|------|------|
| 發送驗證 Email | `/api/accounts/email/verify/` | POST | 發送驗證 Email |
| 驗證 Email | `/api/accounts/email/verify/confirm/` | GET | 驗證 Email 連結 |

## 使用範例

### 1. 前端社交登入按鈕

```html
<!-- Google 登入 -->
<a href="/api/accounts/social/login/google-oauth2/" class="btn btn-google">
    <i class="fab fa-google"></i> 使用 Google 登入
</a>

<!-- Facebook 登入 -->
<a href="/api/accounts/social/login/facebook/" class="btn btn-facebook">
    <i class="fab fa-facebook"></i> 使用 Facebook 登入
</a>
```

### 2. JavaScript 處理登入

```javascript
// 檢查社交登入狀態
async function checkSocialStatus() {
    const response = await fetch('/api/accounts/social/status/', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    const data = await response.json();
    console.log('社交帳號:', data.social_accounts);
}

// 發送驗證 Email
async function sendVerificationEmail() {
    const response = await fetch('/api/accounts/email/verify/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            email: 'user@example.com'
        })
    });
    const data = await response.json();
    console.log('Email 發送結果:', data);
}
```

### 3. 後端處理社交登入

```python
# 在 views.py 中處理社交登入
from social_django.models import UserSocialAuth

def handle_social_login(request):
    """處理社交登入"""
    user = request.user
    if user.is_authenticated:
        # 獲取社交帳號資訊
        social_accounts = UserSocialAuth.objects.filter(user=user)
        
        # 處理用戶資料
        for social in social_accounts:
            if social.provider == 'google-oauth2':
                # 處理 Google 資料
                pass
            elif social.provider == 'facebook':
                # 處理 Facebook 資料
                pass
```

## 安全注意事項

### 1. OAuth2 安全
- 使用 HTTPS 在生產環境
- 定期更換 OAuth2 密鑰
- 限制授權範圍
- 監控異常登入活動

### 2. Email 安全
- 使用強密碼的 Email 帳號
- 啟用兩步驟驗證
- 定期更換應用程式密碼
- 監控 Email 發送狀態

### 3. 資料保護
- 加密敏感資料
- 定期備份用戶資料
- 遵守 GDPR 等隱私法規
- 提供用戶資料刪除功能

## 故障排除

### 常見問題

#### 1. Google OAuth2 錯誤
- **錯誤**: `redirect_uri_mismatch`
- **解決**: 檢查重新導向 URI 設定

#### 2. Facebook OAuth2 錯誤
- **錯誤**: `Invalid OAuth 2.0 Access Token`
- **解決**: 檢查 App ID 和 App Secret

#### 3. Email 發送失敗
- **錯誤**: `SMTPAuthenticationError`
- **解決**: 檢查 Gmail 應用程式密碼

#### 4. 社交登入後無法獲取 Token
- **錯誤**: 用戶創建但沒有 JWT Token
- **解決**: 檢查社交登入管道設定

### 調試技巧

1. **啟用詳細日誌**:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'social_core': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

2. **測試 Email 發送**:
```python
# 在 Django shell 中測試
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

3. **檢查社交帳號**:
```python
# 在 Django shell 中檢查
python manage.py shell
>>> from social_django.models import UserSocialAuth
>>> UserSocialAuth.objects.all()
```

## 生產環境部署

### 1. 環境變數
使用環境變數管理敏感資訊：
```bash
export GOOGLE_OAUTH2_KEY="your-key"
export GOOGLE_OAUTH2_SECRET="your-secret"
export FACEBOOK_APP_ID="your-app-id"
export FACEBOOK_APP_SECRET="your-app-secret"
export EMAIL_HOST_PASSWORD="your-app-password"
```

### 2. HTTPS 配置
確保生產環境使用 HTTPS：
```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### 3. 域名設定
更新域名設定：
```python
DOMAIN = 'your-domain.com'
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
```

## 未來擴展

1. **更多社交平台**:
   - Twitter OAuth
   - LinkedIn OAuth
   - GitHub OAuth

2. **進階功能**:
   - 社交帳號連結/解除連結
   - 社交帳號同步
   - 社交分享功能

3. **安全增強**:
   - 雙因素認證
   - 登入活動監控
   - 異常登入檢測
