from django.urls import path

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
]
