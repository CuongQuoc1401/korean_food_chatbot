from django.contrib import admin
from django.urls import path, include

from chatbot import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chatbot/', include('chatbot.urls')),
    path('', views.home_view, name='home_view'),
]