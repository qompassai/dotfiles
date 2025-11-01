# /qompassai/dotfiles/.config/metasploit/environments/production.rb
# Qompass AI Metasploit Production Environment Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if defined? Metasploit::Framework::Application
  Metasploit::Framework::Application.configure do
    config.log_level = :info
  end
end
