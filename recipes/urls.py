from django.urls import path
from . import views

urlpatterns = [
    # 何も指定しないトップページ（/）にアクセスしたら、さっきの司令塔を動かす
    path('', views.recipe_list, name='recipe_list'),
]