from django.urls import path

from apps.users.views import RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
]
