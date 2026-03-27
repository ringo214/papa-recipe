from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 🍳 レシピ関連
    path('', views.recipe_list, name='recipe_list'),
    path('new/', views.recipe_new, name='recipe_new'),
    path('<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('<int:pk>/edit/', views.recipe_edit, name='recipe_edit'),
    path('shopping-list/', views.shopping_list, name='shopping_list'),
    path('cooklog/<int:pk>/comment/', views.add_comment, name='add_comment'),

    # 💰 家計簿関連
    path('budget/', views.budget_list, name='budget_list'),
    path('budget/create/', views.budget_create, name='budget_create'), # 👈 これを追加！
    path('budget/scan/', views.receipt_scan, name='receipt_scan'),
    path('budget/delete/<int:pk>/', views.budget_delete, name='budget_delete'),
    path('budget/edit/<int:pk>/', views.budget_edit, name='budget_edit'),
    path('budget/config/', views.budget_config, name='budget_config'),

    # 🌟 ログイン・ログアウト
    # (configの方に書いてもいいですが、一旦ここにまとめておきましょう)
    path('login/', auth_views.LoginView.as_view(template_name='recipes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('budget/config/', views.budget_config, name='budget_config'),

    # 🌟 「templates/」を削除して、その中身のパスだけを書く！
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html'
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # 🌟 冷蔵庫（在庫一覧＆登録）
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('receipt/save/', views.receipt_save, name='receipt_save'),

    # 🌟 在庫削除（使い切った！ボタン用）
    path('inventory/delete/<int:pk>/', views.inventory_delete, name='inventory_delete'),
]