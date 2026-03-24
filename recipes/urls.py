from django.urls import path
from . import views

urlpatterns = [
    # 何も指定しないトップページ（/）にアクセスしたら、さっきの司令塔を動かす
    path('', views.recipe_list, name='recipe_list'),
    path('new/', views.recipe_new, name='recipe_new'),
    path('<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('<int:pk>/edit/', views.recipe_edit, name='recipe_edit'),
    path('shopping-list/', views.shopping_list, name='shopping_list'),
    path('cooklog/<int:pk>/comment/', views.add_comment, name='add_comment'),
]