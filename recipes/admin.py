from django.contrib import admin
from .models import Recipe, CookLog  #
from .models import Recipe, CookLog, Comment

admin.site.register(Recipe)
admin.site.register(CookLog)  
admin.site.register(Comment)