Syrmax_bot 設置說明

1.啟動 Django 伺服器
    執行伺服器: python manage.py runserver
    Django 管理界面: http://127.0.0.1:8000/admin/

2.進入 Django 管理後台
    建立管理員帳號： python manage.py createsuperuser
    啟動伺服器後，瀏覽器進入 http://127.0.0.1:8000/admin
    登入後可直接在後台管理配置、交易對、策略等資料。

3.啟動交易機器人（背景交易器）
    執行 custom management command（假設名稱為 runbot 或 run_trader）：python manage.py runbot或  python manage.py run_trader

4. 修改機器人配置
    推薦方式：在 Django 管理後台（/admin）或透過 API 修改資料庫中的配置（如交易對、槓桿、風控參數等）。
    不推薦：直接編輯 config.py，除非該檔案還有被用到。


如何增加或修改功能？
1. 增加新功能
資料結構變動：在 trading_api/models.py 新增/修改 Model，執行 makemigrations 和 migrate。
API 介面：在 trading_api/views.py 增加對應邏輯，並在 urls.py 註冊新路由。
前端管理：如需在 Django admin 顯示，修改 admin.py。
交易邏輯：在 trading/trader.py 或相關策略檔案中擴充邏輯。
2. 修改現有功能
配置變更：直接在 admin 後台或 API 修改資料。
邏輯調整：修改對應的 Python 檔案（如策略、交易邏輯），重啟背景交易器。

API網址: 
1.策略組合: http://127.0.0.1:8000/api/strategy-combos/
2.策略執行: http://127.0.0.1:8000/api/strategies/execute/
