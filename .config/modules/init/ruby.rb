# define modules runtime quarantine configuration
#ENV['MODULES_RUN_QUARANTINE'] = 'ENVVARNAME'

# setup quarantine if defined
_mlre = ''
if ENV.has_key?('MODULES_RUN_QUARANTINE') then
   ENV['MODULES_RUN_QUARANTINE'].split(' ').each do |_mlv|
      if _mlv =~ /^[A-Za-z_][A-Za-z0-9_]*$/ then
         if ENV.has_key?(_mlv) then
            _mlre << "__MODULES_QUAR_" + _mlv + "='" + ENV[_mlv].to_s + "' "
         end
         _mlrv = 'MODULES_RUNENV_' + _mlv
         _mlre << _mlv + "='" + ENV[_mlrv].to_s + "' "
      end
   end
   unless _mlre.empty?
      _mlre = 'env ' + _mlre + '__MODULES_QUARANTINE_SET=1 '
   end
end

# define module command and surrounding initial environment (default value
# for MODULESHOME, MODULEPATH, LOADEDMODULES and parse of init config files)
eval `#{_mlre}/usr/bin/tclsh '/usr/lib/env-modules/modulecmd.tcl' ruby autoinit`
