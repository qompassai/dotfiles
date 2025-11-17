-- /qompassai/dotfiles/.config/algernon/algernon.conf
-- Qompass AI Algernon Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
-----------------------------------------
LogTo("/var/log/algernon.log")
DenyHandler(function()
  content("text/html")
  print[[<!doctype html><html><head><title>Permission denied</title><link href='//fonts.googleapis.com/css?family=Lato:300' rel='stylesheet' type='text/css'></head><body style="background-color: #f0f0f0; color: #101010; font-family: 'Lato', sans-serif; font-weight: 300; margin: 4em; font-size: 2em;">]]
  print("<strong>HTTP "..method()..[[</strong> <font color="red">denied</font> for ]]..urlpath().." (based on the current permission settings).")
  print([[</body></html>]])
end)
