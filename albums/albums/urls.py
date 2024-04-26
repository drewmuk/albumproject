"""
URL configuration for albums project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from album_app import views
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/home/'), name='redirect-to-home'),
    path('home/', views.home_page, name='home_page'),
    #path('oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback),
    path('login/',views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('sign_up/',views.sign_up),
    path('user-choice/', views.user_choice_view, name='user_choice'),
    path('albums/most_similar', views.most_similar_albums, name='most_similar_albums'),
    path('albums/all', views.all_albums, name='display_all_albums'),
    path('albums/random', views.choose_random, name='choose_random'),
    path('albums/add_to_lib', views.add_to_lib, name='add_to_lib'),
    path('albums/remove_from_lib', views.rem_from_lib, name='rem_from_lib'),
    path('albums/<str:input_album_id>/', views.album_detail, name='album_detail'),
    path('lists/', views.display_list, name ='display_list'),
    path('lists/completed/add/<str:input_album_id>/', views.add_to_completed, name ='add_to_completed'),
    path('lists/completed/delete/<str:input_album_id>/', views.remove_from_completed, name='remove_from_completed'),
    path('lists/to_do/add/<str:input_album_id>/', views.add_to_to_do, name ='add_to_to_do'),
    path('lists/to_do/delete/<str:input_album_id>/', views.remove_from_to_do, name='remove_from_to_do'),
    path('profile/',views.profile_display, name='profile_display' ),
]
