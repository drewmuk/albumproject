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
    path('login/',views.user_login, name='user_login'),
    path('sign_up/',views.sign_up),
    path('albums/most_similar', views.most_similar_albums, name='most_similar_albums'),
    path('spotify/callback/', views.spotify_callback),
    path('user-choice/', views.user_choice_view, name='user_choice'),
    path('logout/', views.user_logout, name='user_logout'),
    path('albums/all', views.all_albums, name='display_all_albums'),
    path('albums/random', views.choose_random, name='choose_random'),
    path('albums/add', views.add_to_lib, name='add_to_lib'),
    path('albums/remove', views.rem_from_lib, name='rem_from_lib')
]
