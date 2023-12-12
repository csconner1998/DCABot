from django.urls import path
import DCAApp.views as views

urlpatterns = [
    path('create/', views.dca_settings_create, name='dca_settings_create'),
    path('create/', views.dca_settings_create, name='create_dca_settings'),
    path('edit/<int:pk>', views.dca_settings_edit, name='edit_dca_settings'),
    path('edit/', views.dca_settings_edit_empty, name='edit_dca_empty_settings'),
    path('', views.view_all_dca_settings, name='view_all_dca_settings'),
    path('delete/<int:pk>', views.delete_dca_settings, name='delete_dca_settings'),
    path('stop_dca_settings/<int:pk>', views.stop_dca_settings, name='stop_dca_settings'),
    path('start_dca_settings/<int:pk>', views.start_dca_settings, name='start_dca_settings'),
    # Add other URLs as needed
    path('user-output/', views.user_specific_text, name='user_specific_text'),
    path('user-output/<int:pk>', views.bot_specific_specific, name='bot_specific_specific'),
    path('account_settings/', views.account_settings, name='account_settings'),
    path('api/calculate', views.calculate_api, name='calculate_api'),
    path('get_balance/', views.get_balance, name='get_balance'),
    path('login/', views.login_view, name='login'),    
]
