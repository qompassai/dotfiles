# /qompassai/dotfiles/.config/knot/default.vcl
# Qompass AI Varnish Default Config
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################
backend default {
    .host = "127.0.0.1";
    .port = "8080";
}
sub vcl_recv {
}
sub vcl_backend_response {
}
sub vcl_deliver {
}
