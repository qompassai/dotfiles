#!/bin/bash
export GDK_BACKEND=x11
export WEBKIT_DISABLE_COMPOSITING_MODE=1
export LIBGL_ALWAYS_SOFTWARE=0
gp-saml-gui -S \
  --clientos=Windows \
  --allow-insecure-crypto \
  --gateway \
  enwe01.tds.gtw.remotevpn.tds.net
