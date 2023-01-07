from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

app_name = 'taskmaster'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.TaskFormView.as_view(), name='form'),
    path('new/', views.new_task, name='new'),
    path('save/', views.save_task, name='save'),
    path('<int:pk>/toggle/', views.toggle, name='toggle'),
    path('purge/', views.purge, name='purge'),
    path('register/', views.register_request, name='register'),
    path('login', views.login_request, name='login'),
    path('logout', views.logout_request, name='logout'),
    path('password_reset', views.password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('taskmaster:password_reset_complete'), template_name="taskmaster/password/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
]
