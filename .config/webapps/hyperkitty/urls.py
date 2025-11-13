# -*- coding: utf-8 -*-
# /qompassai/dotfiles/.config/webapps/hyperkitty/urls.py
# Qompass AI HyperKitty URL Config
# Copyright (C) 2025 Qompass AI, All rights reserved
########################################################
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
urlpatterns = [
    path('', RedirectView.as_view(
        url=reverse_lazy('hk_root'))),
    path('hyperkitty/', include('hyperkitty.urls')),
    path('', include('django_mailman3.urls')),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
