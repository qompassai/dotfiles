# -*- coding: utf-8 -*-
# /qompassai/dotfiles/.config/webapps/postorius/urls.py
# Qompass AI Postorius URLs Config
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################
from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.urls import include, path, re_path, reverse_lazy
from django.views.defaults import server_error
from django.views.generic import RedirectView
def not_found(request):
    """A test view to return 404 error to test 400.html"""
    raise Http404('Page not Found.')
urlpatterns = [
    re_path(
        r'^$',
        RedirectView.as_view(url=reverse_lazy('list_index'), permanent=True),
    ),
    re_path(r'^postorius/', include('postorius.urls')),
    re_path(r'', include('django_mailman3.urls')),
    re_path(r'^accounts/', include('allauth.urls')),
    re_path(r'500/$', server_error),
    re_path(r'400/$', not_found),
    re_path(r'^admin/', admin.site.urls),
]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
