from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('info', views.info, name='info'),
    path('trips', views.trips, name='trips'),
    path('application', views.application_view, name='application'),
    path('trips_applications', views.hikes_applications, name='hikes_applications'),
    path('add_hike', views.add_hike, name='add_hike'),
    path('logout', views.logout_view, name='logout'),
    path('change_password', views.change_password, name='change_password'),
    path('profile_update', views.profile_update, name='profile_update'),
    path('change_userdata/<int:user_id>/', views.change_userdata, name='change_userdata'),
    path('change_hike', views.get_change_hike, name='change_hike'),
    path('change_hike/<int:hike_id>/', views.change_hike, name='change_hike_id'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('query', views.query, name='query'),
    path('users', views.users_view, name='users'),
    path('tourists', views.tourists_view, name='tourists'),
    path('staff', views.staff_view, name='staff'),
]
