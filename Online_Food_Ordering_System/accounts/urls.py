from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name="signup"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('profile/', views.profile_view, name="profile"),
    path('address/add/', views.add_address, name="add_address"),
    path('address/delete/<int:pk>/', views.delete_address, name="delete_address"),
    path('address/default/<int:pk>/', views.set_default_address, name="set_default_address"),
]

