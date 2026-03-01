from django.urls import path
from . import views

urlpatterns = [
    # 何も指定しないトップページ（/）にアクセスしたら、さっきの司令塔を動かす
    path('', views.recipe_list, name='recipe_list'),
    path('<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('shopping-list/', views.shopping_list, name='shopping_list'),
    path('cooklog/<int:pk>/comment/', views.add_comment, name='add_comment'),
]