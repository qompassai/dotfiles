# python-rssd [RU](https://gitflic.ru/project/ksandr/python-rssd)
### A service for displaying the latest news from RSS feeds via notify.

The news feed is installed by default Archlinux.  
The service is started in the user systemd.

![Example](https://gitflic.ru/project/ksandr/python-rssd/blob/raw?file=screenshot.png)

#### Installation in Arch linux

Due to the execution of the service in user mode,  
the option of installing the package is offered only for a specific user.  
In the user directory, create a directory for pacman files.  
And the installation is done in the user's directory.

To install the package in a user environment, run the following commands:

``` 
% git clone https://aur.archlinux.org/python-rssd-usermode.git
% cd python-rssd-usermode
% makepkg -s
% mkdir $HOME/.local/pacman $HOME/.local/pacman/cache

# pacman --dbpath=$HOME/.local/pacman --logfile=$HOME/.local/pacman/log --cachedir=$HOME/.local/pacman/cache -Uddv python-rssd-usermode-1-1-x86_64.pkg.tar.zst
```

> Note: python-rssd-usermode-1-1-x86_64.pkg.tar.zst - package for the first version of the program.

To remove, run the command:

```
# pacman -R python-rssd-usermode --dbpath=$HOME/.local/pacman
```

> Note: If there are no other programs installed in the user's environment, the $HOME/.local/pacman directory can be deleted.

#### Using

To test the work, you can run the python-rssd.desktop file.
To run in the current session, run the command:

```
% systemctl --user start python-rssd.timer
```

To enable autorun at login:

```
% systemctl --user enable python-rssd.timer
```

> Note: execute commands on behalf of the user (not from root)

#### List of files

* python-rssd.py        - a script that downloads RSS and generates notify.
* python-rssd.pyс       - compiled version.(The command to compile: python -m compileall python-rssd.py -b)
* python-rssd.service   - file to run via systemd.
* python-rssd.timer     - timer for systemd, to run at certain intervals.
* python-rssd.desktop   - Application shortcut for manual single launch.
* settings.ini          - file with settings
* ~/.config/python-rssd/ - directory for program files.
* ~/.local/share/icons/hicolor/48x48/apps/ - folder for icons.

#### Configuring the service

##### The setting of trigger timers can be changed by editing the python-rssd.timer file

Parameters:

OnBootSec=5 - delay when starting the service.  
OnUnitActiveSec=60 - start interval in seconds.  

After saving the changes, you need to run the command:

```
% systemctl --user daemon-reload
```

##### Adding RSS feeds.

Add/remove the RSS feed by editing the settings.ini
