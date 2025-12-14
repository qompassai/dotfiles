# define modules runtime quarantine configuration
#$ENV{'MODULES_RUN_QUARANTINE'} = 'ENVVARNAME';

# setup quarantine if defined
my $_mlre = '';
if (defined $ENV{'MODULES_RUN_QUARANTINE'}) {
  foreach my $_mlv (split(' ', $ENV{'MODULES_RUN_QUARANTINE'})) {
     if ($_mlv =~ /^[A-Za-z_][A-Za-z0-9_]*$/) {
        if (defined $ENV{$_mlv}) {
           $_mlre .= "__MODULES_QUAR_${_mlv}='$ENV{$_mlv}' ";
        }
        my $_mlrv = "MODULES_RUNENV_$_mlv";
        $_mlre .= "$_mlv='$ENV{$_mlrv}' ";
    }
  }
  if ($_mlre ne "") {
     $_mlre = "env ${_mlre}__MODULES_QUARANTINE_SET=1 ";
  }
}

eval `${_mlre}/usr/bin/tclsh '/usr/lib/env-modules/modulecmd.tcl' perl autoinit`;

# clean temp variable used to setup quarantine
undef $_mlre;

1;
