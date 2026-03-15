from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup-choice/', views.signup_choice, name='signup_choice'),
    path('signup/doctor/', views.signup_doctor, name='signup_doctor'),
    path('signup/patient/', views.signup_patient, name='signup_patient'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    
    # Google Calendar OAuth URLs
    path('connect-calendar/', views.connect_google_calendar, name='connect_google_calendar'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('calendar-status/', views.calendar_status, name='calendar_status'),
    
    # Include app URLs
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('bookings/', include('bookings.urls')),
]
