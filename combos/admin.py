from django.contrib import admin
from .models import Combo
 
@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ('name', 'combo_mode', 'is_active')
    search_fields = ('name',)
    list_filter = ('combo_mode', 'is_active') 