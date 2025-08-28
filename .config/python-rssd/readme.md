# python-rssd [EN](https://gitflic.ru/project/ksandr/python-rssd/blob?file=readme_EN.md)
### Cервис отображениея последних новостей из лент RSS через notify.
По умолчанию установлены ленты новостей Archlinux.  
Сервис запускается в пользовательском systemd.

![Пример](https://gitflic.ru/project/ksandr/python-rssd/blob/raw?file=screenshot.png)

#### Установка в Arch linux

По причине выполнения сервиса в пользовательком режиме,  
предлагается вариант установки пакета только для конкретного пользователя.  
В пользовательском каталоге создаём каталог для файлов pacman.  
И установка производиться в каталог пользователя.

Для установки пакета в пользовательское окружение необходимо выполнить команды:

``` 
% git clone https://aur.archlinux.org/python-rssd-usermode.git
% cd python-rssd-usermode
% makepkg -s
% mkdir $HOME/.local/pacman $HOME/.local/pacman/cache

# pacman --dbpath=$HOME/.local/pacman --logfile=$HOME/.local/pacman/log --cachedir=$HOME/.local/pacman/cache -Uddv python-rssd-usermode-1-1-x86_64.pkg.tar.zst
```

> Примечание: python-rssd-usermode-1-1-x86_64.pkg.tar.zst - пакет для первой версии программы.

Для удаления выполнить команду:

```
# pacman -R python-rssd-usermode --dbpath=$HOME/.local/pacman
```

> Примечание: Если других программ установленных в окружении пользователя нет - каталог $HOME/.local/pacman можно удалить.

#### Использование

Для проверки работы можно запусить файл python-rssd.desktop.  
Для запуска в текущем сеансе выполнить команду:

```
% systemctl --user start python-rssd.timer
```

Для включения автозапуска при входе:

```
% systemctl --user enable python-rssd.timer
```

> Примечание: выполнение команд делать от имени пользователя(не от рута)

#### Список файлов

* python-rssd.py        - скрипт выполняющий загрузку RSS и генерирующий notify.
* python-rssd.pyc       - скомпилированная версия.(Команда для компиляции: python -m compileall python-rssd.py -b)
* python-rssd.service   - файл для запуска через systemd.
* python-rssd.timer 	- таймер для systemd, для запуска через определённые промежутки времени.
* python-rssd.desktop   - Ярлык приложения для ручного единичного запуска.(Генерируется при установки программы)
* settings.ini 			- файл с настройками
* ~/.config/python-rssd/ - каталог для файлов программы.
* ~/.local/share/icons/hicolor/48x48/apps/ - папка для иконок.

#### Настройка сервиса

##### Настройка таймеров срабатывания можно изменить отредактировав файл python-rssd.timer

Параметры:

OnBootSec=5 		- отсрочка при запуске сервиса.  
OnUnitActiveSec=60 	- интервал запуска в секундах.  

После сохранения изменений необходимо выполнить команду:

```
% systemctl --user daemon-reload
```

##### Добавление лент RSS.

Добавить/убрать канал RSS отредактировав файл settings.ini
