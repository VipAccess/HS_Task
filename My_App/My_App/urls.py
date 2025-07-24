from django.contrib import admin
from django.urls import path

from referrals.views import AuthAPIView, VerifyAPIView, ProfileAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/phone/', AuthAPIView.as_view()),
    path('api/auth/verify/', VerifyAPIView.as_view()),
    path('api/profile/<str:phone>/', ProfileAPIView.as_view())
]
