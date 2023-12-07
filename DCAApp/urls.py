from django.urls import path
from DCAApp.views import landing_page

urlpatterns = [
    path('', landing_page, name='landing_page'),
    # Add other URLs as needed
]
