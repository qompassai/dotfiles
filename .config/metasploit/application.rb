# /qompassai/dotfiles/.config/metasploit/application.rb
# Qompass AI Metasploit Application Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
require 'fiddle'
Fiddle.const_set(:VERSION, '0.0.0') unless Fiddle.const_defined?(:VERSION)

require 'rails'
require File.expand_path('../boot', __FILE__)

require 'action_view'
# Monkey patch https://github.com/rails/rails/blob/v7.2.2.1/actionview/lib/action_view/helpers/tag_helper.rb#L51
raise unless ActionView::VERSION::STRING == '7.2.2.1'
module ActionView::Helpers::TagHelper
  class TagBuilder
    def self.define_element(name, code_generator:, method_name: name.to_s.underscore)
      code_generator.define_cached_method(method_name, namespace: :tag_builder) do |batch|
        batch.push(<<~RUBY) # unless instance_methods.include?(method_name.to_sym)
              def #{method_name}(content = nil, escape: true, **options, &block)
                tag_string("#{name}", content, options, escape: escape, &block)
              end
            RUBY
      end
    end
  end
end

all_environments = [
    :development,
    :production,
    :test
]

Bundler.require(
    *Rails.groups(
        coverage: [:test],
        db: all_environments,
        pcap: all_environments
    )
)

require 'action_controller/railtie'
require 'action_view/railtie'
require 'metasploit/framework/common_engine'
require 'metasploit/framework/database'
module Metasploit
  module Framework
    class Application < Rails::Application
      include Metasploit::Framework::CommonEngine
      config.paths['log']             = "#{Msf::Config.log_directory}/#{Rails.env}.log"
      config.paths['config/database'] = [Metasploit::Framework::Database.configurations_pathname.try(:to_path)]
      config.autoloader = :zeitwerk

      config.load_defaults 7.2

      config.eager_load = false
    end
  end
end

I18n.enforce_available_locales = true
require 'msfenv'
