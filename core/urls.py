from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # This URL catches 'yes' or 'no' from the buttons

    path('availability/<str:status>/', views.toggle_availability, name='toggle_availability'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/chat/', views.chat_messages, name='chat_messages'),
    path('event/<int:event_id>/chat/send/', views.send_message, name='send_message'),
    path('event/<int:event_id>/logistics/', views.update_logistics, name='update_logistics'),
    path('event/create/', views.create_manual_event, name='create_manual_event'),
    path('event/<int:event_id>/join/', views.join_match, name='join_match'),
    path('profile/', views.profile, name='profile'),
    path('profile/remove_sport/<int:usersport_id>/', views.remove_sport, name='remove_sport'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]