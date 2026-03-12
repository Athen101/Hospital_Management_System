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
    path('profile/', views.profile, name='profile'),  # This line MUST be exactly this
    
    # Include app URLs
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('bookings/', include('bookings.urls')),
]