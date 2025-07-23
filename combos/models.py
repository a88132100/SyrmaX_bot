from django.db import models

class Combo(models.Model):
    """
    對應 combos.generated.json 的策略組合 Django model。
    包含組合名稱、描述、條件、啟用狀態、組合模式、建立與更新時間。
    """
    name = models.CharField(max_length=255, unique=True, verbose_name="策略組合名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    conditions = models.JSONField(default=list, blank=True, verbose_name="策略條件")
    is_active = models.BooleanField(default=False, verbose_name="是否啟用")
    combo_mode = models.CharField(max_length=20, verbose_name="組合模式")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    def __str__(self):
        return f"{self.name} ({self.combo_mode}) - {'啟用中' if self.is_active else '未啟用'}" 