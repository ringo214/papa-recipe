from django.contrib import admin
from .models import Recipe, CookLog  # ← CookLog を追加！

admin.site.register(Recipe)
admin.site.register(CookLog)  # ← お父様が入力できるように追加！