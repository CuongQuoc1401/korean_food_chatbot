from django.urls import path
from . import views

urlpatterns = [
    path('get_response/', views.get_chatbot_response, name='get_response'),
    path('', views.chatbot_view, name='chatbot_view'), # Đường dẫn đến trang chatbot
]