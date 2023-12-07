from django.urls import path
from DCAApp.views import landing_page, success_page_view, stopped_page_view, user_specific_text

urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('success/', success_page_view, name='success_page'),
    path('stopped/', stopped_page_view, name='stopped'),
    # Add other URLs as needed
    path('user-output/', user_specific_text, name='user_specific_text'),
]
