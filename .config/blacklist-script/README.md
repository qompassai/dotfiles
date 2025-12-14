# blacklist-scripts

---

* [Russian Text](#Russian)
* [English Text](#English)

---

## <a name="Russian">Russian README.</a>

Черный и белый списки Fail2Ban.

![Linux](./image/linux.svg "Linux") &nbsp;![Python-3](./image/python-3-icon.svg "Python-3")

## <a name="Oglavlenie">Оглавление</a>

1. [Установка.](#Setup)
2. [Обзор утилиты](#ShowUtilites)
3. [Об авторе.](#About)

---

## <a name="Setup">1. Установка.</a>

Для установки программы воспользуйтесь следующей командой при помощи **Makefile**:

```bash
cd ~
git clone https://github.com/maximalisimus/blacklist-scripts.git
cd blacklist-scripts
sudo make DESTDIR=/ install
```

Для контроля установки в **Makefile** предусмотрены некоторые переменные, которыми вы могли бы воспользоваться.

* **DESTDIR** - местоположение в системе, директория. По умолчанию задаётся корень системы.
* **POSTDIR** - установочная директория перед папкой с программой, т.е. родительская директория программы. По умолчанию равна **&laquo;etc&raquo;**. <u>Обязательно должна присутствовать. Не допускается устанавливать пустой.</u>
* **INSTALLDIR** - удалённый корень будущей системы. Используется для создания правильной символической ссылки в **&laquo;/usr/bin/&raquo;**.
* **TARGET** - название директории с самой программой.

Остальные переменные не рекомендуется менять каким-либо образом.

Если вам нужно изменить установочную директорию в системе - воспользуйтесь переменными *DESTDIR*, *POSTDIR* и *TARGET*. 

Например, я хочу установить программу в **&laquo;/opt/blacklist/&raquo;**.

```bash
sudo make DESTDIR=/ POSTDIR=opt TARGET=blacklist install
```

Если вам нужны фильтры для **NGINX** - установите их отдельно:

```bash
sudo make DESTDIR=/ install-filter
```

В данных предустановленных фильтрах для **Fail2ban** содержаться регулярные выражения для отдельного отслеживания всех ошибок самого *Nginx* как такового из файла **&laquo;/var/log/nginx/error.log&raquo;** или похожем, а также отслеживания статусных состояний &laquo;4xx ошибка в запросе&raquo; и &laquo;5xx ошибка сервера&raquo; из файла **&laquo;/var/log/nginx/access.log&raquo;** или похожем пользовательском.

**Обратите внимание!** Данные предустановленные регулярные варыжения в указанных фильтрах являются достаточно жесткими. Если вы не уверены в том, что сами не совершите ошибок во время настроек или при их использовании - откажитесь от их установки и применения!

Для установки действий **action**-ов для **Fail2ban**-а воспользуйтесь командой их установки:

```bash
sudo make DESTDIR=/ install-action
```

Также у черного списка имеются предустановленные **Jail**-правила, которые вы также можете установить, при таковой необходимости:

```bash
sudo make DESTDIR=/ install-jail
```

Если же вам нужны все предустановленные функции для **Fail2ban**-а (экшены, фильтры, правила), вы можете установить их одной командой:

```bash
sudo make DESTDIR=/ install-all
```

Или одновременной установки и самой программы и всех функций для **Fail2ban**-а (экшенов, фильтров, правил):

```bash
sudo make DESTDIR=/ all
```

Для удаления программы и / или дополнительных функций для **Fail2ban**-а в **Makefile** имеются соответствующие команды:

* uninstall - удалить пграмму,
* uninstall-action - удалить предустановленные экшены,
* uninstall-filter - удалить предустановленные фильтры,
* uninstall-jail - удалить предустановленные правила,
* uninstall-all - удалить все предустановленные функции **Fail2ban**-а.
* clear - удалить и саму программу и все предустановленные функции **Fail2ban**-а.

Если же вы хотите использовать способ установки с помощью **setup.py**, воспользуйтесь следующим методом.

С помощью следующей команды проверьте, что у вас установлена ​​актуальная версия setuptools.

```bash
Debian: $ sudo apt install python-virtualenv python3-virtualenv python3-venv virtualenv python3-virtualenvwrapper
Archlinux: $ sudo pacman -S python-virtualenv python-virtualenvwrapper
Python PIP: $ python -m pip install --upgrade pip setuptools virtualenv virtualenvwrapper --upgrade
```

Также клонируем репозиторий и переходим в него.

```bash
cd ~
git clone https://github.com/maximalisimus/blacklist-scripts.git
cd blacklist-scripts
```

Устанавливаем.

```bash
# Так
$ python setup.py install

# Или так
$ pip install .
```

Для сборки утилиты в 2 вида пакета - архив (скорее всего **.tar.gz**) со всеми необходимыми файлами и **.whl** файл для **PIP**-а, воспользутесь следующей командой.

```bash
# Сначала перейдите в каталог с репозиторием.
$ cd blacklist-scripts

# Можно собирать.
$ python setup.py sdist bdist_wheel

```

В папке dist должны повится 2 соответствующих архива.

---

[К оглавлению](#Oglavlenie)

---

## <a name="ShowUtilites">2. Обзор утилиты.</a>

Помощь программы выглядит следующим образом (Параметры и ключи. Русифицикация.):

```bash
$ ./py-blacklist.py -h

usage: py-blacklist.py [-h] [-v] [-info] [-c COUNT] [-q QUANTITY]
                       [-wd WORKDIR] [-b BLACKLIST] [-w WHITELIST] [-personal]
                       [-e] [-run] [-fine] [-ipv6] [-nft]
                       [-nftproto {ip,ip6,inet}] [-table TABLE] [-chain CHAIN]
                       [-newtable] [-newchain] [-Deltable] [-Delchain]
                       [-cleartable] [-clearchain] [-con CONSOLE] [-cmd] [-sd]
                       [-logfile LOGFILE] [-nolog] [-limit] [-viewlog]
                       [-resetlog]
                       {systemd,service,black,white} ...

Черный и белый списки Fail2Ban в Python.

options:
  -h, --help            показать справку и выйти
  -v, --version         Версия.
  -info, --info         Информация об авторе.

Управление:
  Команды управления.

  {systemd,service,black,white,active}
                        команды помощи.
    systemd             Управление Systemd.
    service             Управление программой.
    black               Управление черными списками.
    white               Управление белыми списками.
    active              Активность в файлах журнала.

Параметры:
  Настройки количества запретов.

  -c COUNT, --count COUNT
                        Количество блокировок, после которых адрес
                        добавляется в таблицы {IP,IP6,NF}TABLES (по умолчанию 0).
  -q QUANTITY, --quantity QUANTITY
                        Количество сохраняемых блокировок ip-адресов (по умолчанию
                        0).

Файлы:
  Работа с файлами.

  -wd WORKDIR, --workdir WORKDIR
                        Рабочая директория.
  -b BLACKLIST, --blacklist BLACKLIST
                        Входной файл черного списка.
  -w WHITELIST, --whitelist WHITELIST
                        Входной файл белого списка.

NFTABLES:
  Конфигурационные таблицы NFTABLES.

  -personal, --personal
                        Персональные настройки таблиц NFTABLES, 
                        независимо от введёных данных.
  -e, -exit, --exit     Завершение создание таблиц/цепочек в NFTABLES.
  -run, --run           Полный запуск таблиц NFTABLES из всех настроек.
                        Используйте осторожно!
  -fine, --fine         Полная очистка таблиц NFTABLES от всех настроек.
                        Используйте осторожно!
  -net NETWORK, -network NETWORK, --network NETWORK
                        Имя интерфейса, через который должен быть получен
                        обрабатываемый пакет. Т.е. входной сетевой интерфейс.
  -ipv6, --ipv6         Принудительный выбор протокола IPV6.
  -nft, --nftables      Выбер фреймворка NFTABLES (по умолчанию IP(6)TABLES).
  -nftproto {ip,ip6,inet}, --nftproto {ip,ip6,inet}
                        Выберите протокол NFTABLES, перед правилами 
                        (Автоматически для ipv4 "ip" или 
                        при ключе -ipv6 - "ip6").
  -table TABLE, --table TABLE
                        Выберите таблицу для NFTABLES (по умолчанию "filter").
  -chain CHAIN, --chain CHAIN
                        Выбор цепочки правил (по умолчанию "INPUT").
  -newtable, --newtable
                        Добавить новую таблицу в NFTABLES.
                        Используйте осторожно!
  -newchain, --newchain
                        Добавить новую цепочку в NFTABLES
                        Используйте осторожно!
  -Deltable, --Deltable
                        Удалить таблицы NFTABLES. 
                        Используйте осторожно!
  -Delchain, --Delchain
                        Удалить цепочку NFTABLES. 
                        Используйте осторожно!
  -cleartable, --cleartable
                        Очистить таблицу NFTABLES. 
                        Используйте осторожно!
  -clearchain, --clearchain
                        Очистить цепочку NFTABLES. 
                        Используйте осторожно!

Настройки:
  Конфигурация.

  -con CONSOLE, --console CONSOLE
                        Ввод имени консоли (по умолчанию "sh").
  -cmd, --cmd           Посмотреть команды и выйти без выполнения.
  -lslan, --lslan       Просмотр списка сетевых интерфейсов.
  -sd, --showdir        Показать рабочий каталог.
  -logfile LOGFILE, --logfile LOGFILE
                        Файл журнала.
  -nolog, --nolog       Не записывать события в журнал.
  -limit, --limit       Ограничьте размер файла журнала. Каждый день 
                        журнал будет стираться.
  -viewlog, --viewlog   Посмотреть журнал событий.
  -latest, --latest     Вывод журнала событий по последней дате.
  -fil FILTERING, -filtering FILTERING, --filtering FILTERING
                        Отфильтруйте выходные данные журнала.
  -resetlog, --resetlog
                        Сброс файла журнала.
```

При этом, если не вводить никаких ключей, пользователь автоматически перенаправляется на страницу помощи, причём в любом меню и под-меню.

По ключам **NFTABLES** необходимо сделать пояснение.

При введении ключа *-nft* вы начинаете работу с **NFTABLES**. Без него вы будете работать с **IPTABLES** и **IP6TABLES**.

При выборе ключа *-personal* и ключа *-nft* программа выбирет <u>предопределённые</u> таблицы и цепочки во фрейворке **NFTABLES**. При этом не имеет значения, что вы будете пытаться вводить соответствующими ключам. Все значения будут переопределены програмно.

Тоже самое касается ключей *-run* и *-fine*. Первый определяется вместо использования 2 ключей *-newtable* и *-newchain*. Ну т.е. когда используются оба последних ключа, проще указать один *-run* вместо 2 ключей. Для *-fine* соответственно будет аналогичное обращение ко всем функциям очистки и удаления таблиц и цепочек после завершения работы приложения.

Также такое обращение по указанным выше ключам будет автоматически применено в меню управления сервисом Systemd, т.е. учтено при создание сервиса и таймера.

Или вы можете использовать любые другие ключи без *-personal*, *-run* и *-fine* раздельно и не зависимо, например для мониторинга или создания определенных таблиц или цепочек.

При удалении и очистки таблиц и цепочек есть определённые ограничения, связанные со стандартными таблицами и цепочками системы в пакетах со слоем совместимости между **NFTABLES** и **IP(6)TABLES** Netfilter-а. Поэтому не удивляйтесь если таблица или цепочка не была удалена из системы или не была очищена. Это сделано только для безопасности. 

Но, есть одна маленькая хитрость. Вы можете с помощью ключей **-cmd**, **-fine** и **-e** посмотреть на все команды завершения, и использовать их на свой страх и риск. Или соответствующими ключами изменить наименование таблиц и / или цепочек и снова указать **-cmd**, **-fine** и **-e**, чтобы посмотреть на все команды завершения с изменёнными значениями и также использовать их на свой страх и риск.

При указании ключа **-net** появляется возможность привязки блокировки или разрешающего правила к определённому сетевому интерфейсу.

Соответственно, с помощью ключа **-lslan** можно посмотреть список всех доступных сетевых интерфейсов.

Ещё одно пояснение касается выбора протокола **-ipv6**. Вообще при вводе ip-адресов протокол определяется автоматически и также автоматически корректируется. Однако, протокол можно принудительно поменять.

Ключи **-latest** и **-fil** имеют смысл только при использовании ещё одного ключа - **-viewlog**. Т.е. только при просмотре журнала событий. Использовать одноврменно можно оба ключа - и **-latest**, и **-fil**. Первый из них выведет всё содержимое журнала согласно последней дате записи. Второй будет фильтровать всё оставшееся содержимое согласно введёной строке регулярного выражения в сам аргумент. Либо просто отфильтрует содержимое всего журнала согласно строке регулярного выражения, если ключ **-latest** не задан.

Например, выведем всё содержимое журнала по последней дате записи в него. И также, попробуем добавить фильтрацию по какой-нибудь строке, например, частичному ip-адресу.

```bash
$ ./py-blacklist.py -viewlog -latest
$ ./py-blacklist.py -viewlog -latest -fil "193"
```

А теперь попробуем отфильтровать только определнные записи, например, какой-нибудь ip-адрес или время или строка в конце записей журнала.

```bash
$ ./py-blacklist.py -viewlog -fil "193"
```

Рассмотрим меню Systemd.

```bash
$ ./py-blacklist.py systemd

Файл «blacklist@.service» и «blacklist@.timer» не найден!
Пожалуйста, введите «-create», чтобы создать системные файлы, перед тем как обращаться к функциям Systemd!

usage: py-blacklist.py systemd [-h] [-create] [-delete] [-status] [-istimer]
                               [-isservice] [-enable] [-disable] [-start]
                               [-stop] [-reload] [-starttimer] [-stoptimer]

options:
  -h, --help            Показать справку и выйти
  -create, --create     Создать «blacklist@.service» and «blacklist@.timer».
  -delete, --delete     Удалить «blacklist@.service» и «blacklist@.timer».
  -status, --status     Состояние «blacklist@.service».
  -istimer, --istimer   Проверить включен и запущен ли «blacklist@.timer».
  -isservice, --isservice
                        Проверить включен и запущен ли «blacklist@.service».
  -enable, --enable     Включить «blacklist@.timer».
  -disable, --disable   Выключить «blacklist@.timer».
  -start, --start       Запустить «blacklist@.service».
  -stop, --stop         Остановить «blacklist@.service».
  -reload, --reload     Перезапустить «blacklist@.service».
  -starttimer, --starttimer
                        Запустить «blacklist@.timer».
  -stoptimer, --stoptimer
                        Остановить «blacklist@.timer».
```
 
 Рассмотрим меню Service.
 
 ```bash
 $ ./py-blacklist.py service
 
 usage: py-blacklist.py service [-h] [-start] [-stop] [-nostop] [-reload]
                               [-show] [-link] [-unlink] [-name NAME]

Опции:
  -h, --help            Показать справку и выйти
  -start, --start       Запустить черный список.
  -stop, --stop         Остановить черный список.
  -nostop, --nostop     Остановка работы с черным списком без очистки
                        {IP,IP6,NF}TABLES.
  -reload, --reload     Перезапустить черный список.
  -show, --show         Перечислите правила в Netfilter.
  -parent, --parent     Просмотр родительского элемента. Только для NFTABLES.
  -tb, --tb             Просмотр списка доступных таблиц NFTABLES.
  -link, --link         Символическая ссылка на программу в «/usr/bin/».
  -unlink, --unlink     Удалить ссылку на программу в «/usr/bin/».
  -name NAME, --name NAME
                        Наименование символьной ссылки в «/usr/bin/». 
                        (по умолчанию "blacklist").
  -grep GREP, --grep GREP
                        Фильтрация просмотра правил Netfilter в соответствии 
                        с указанным регулярным выражением.
 ```

По умолчанию в прогрумму встроен метод работы из любого каталога. Если вы не устанавливали программу с помощью **Makefile**, вам может потребоваться функция создания символьной ссылки на скрипт в **«/usr/bin/»** и также безопасного удаления этой символьной ссылки. В качестве бонуса можете даже изменить наименование символьной ссылки, чтобы вам было удобно обращаться к скрипту без указания полного пути и его наименования.

При запуске, остановке или перезапуске программы обработаны будут оба списка - и черный и белый. При этом белый список будет внесён в **Netfilter** с обязательными разрешающими правилами, а черный с запрещающими. 

Программу можно запускать многократно. В отличии от ручного управления с помощью команд через терминал, здесь имеется защита от повторного добавления ip-адреса и в таблицы **NetFilter**-а и в сами файлы списков.

Ключ **-show** в данном меню служит для просмотра заданной таблицы и цепочки в **NFTABLES**. Ключ **-parent** позволяет посмотреть на всю заданную таблицу, а не только указанную цепочку.

Ключ **-grep** используется для фильтрации того, что должно быть выведено на экран при просмотре правил межсетевого экрана с помощью ключа **-show**. При этом даже не важно используется ли ключ предыдущего меню **-nft** или не используется.

Например, я не хочу смотреть на всю таблицу **IPTABLES** или **NFTABLES**, а хочу отфильтровать, т.е. уменьшить её до определённых строк, подобно утилите **GREP**. Пусть эти строки содержат адреса с цифрами, например, 193 и 185. При этом я не то, что не хочу использовать конвеер, а допустим, я новичок и не знаю как пользоваться конвеером в **Linux** дистрибутивах и пока ещё не знаю ни одну утилиту фильтрации вывода.

```bash
# Для iptables
$ ./py-blacklist.py service -show -grep "193|185"

# Для nftables
$ ./py-blacklist.py -nft service -show -grep "193|185"

# А вот так бы выглядело для iptables с конвеером
$ ./py-blacklist.py service -show | grep -Ei "193|185"

# Соответственно с конвеером для nftables
$ ./py-blacklist.py -nft service -show | grep -Ei "193|185"
```

Рассмотрим меню black.

```bash
 $ ./py-blacklist.py black

usage: py-blacklist.py black [-h] [-ban] [-unban] [-a] [-d] [-s] [-j] [-save]
                             [-o OUTPUT] [-empty] [-ip IP [IP ...]]
                             [-m MASK [MASK ...]]

Опции:
  -h, --help            Показать справку и выйти
  -ban, --ban           Заблокировать ip-адреса в {IP,IP6,NF}TABLES.
  -unban, --unban       Разблокировать ip-адреса в {IP,IP6,NF}TABLES.
  -a, --add             Добавить в черный список.
  -d, --delete          Удалить из черного списка.
  -s, --show            Посмотреть черный список.
  -j, --json            JSON формат просмотра.
  -indent INDENT, --indent INDENT
                        Отступ в формате JSON (по умолчанию: 2).
  -save, --save         Сохранить.
  -o OUTPUT, --output OUTPUT
                        Выходной файл черного списка.
  -empty, --empty       Очистить черный список. Используйте осторожно!

Addressing:
  IP address management.

  -ip IP [IP ...], --ip IP [IP ...]
                        IP адреса.
  -m MASK [MASK ...], --mask MASK [MASK ...]
                        Маски сетей.
```

Рассмотрим меню white.

```bash
 $ ./py-blacklist.py white

usage: py-blacklist.py white [-h] [-ban] [-unban] [-a] [-d] [-s] [-j] [-save]
                             [-o OUTPUT] [-empty] [-ip IP [IP ...]]
                             [-m MASK [MASK ...]]

Опции:
  -h, --help            Показать справку и выйти
  -ban, --ban           Разрешить ip-адреса в {IP,IP6,NF}TABLES.
  -unban, --unban       Удалить разрешения из {IP,IP6,NF}TABLES.
  -a, --add             Добавить в белый список.
  -d, --delete          Удалить из белого списка.
  -s, --show            Посмотреть белый список.
  -j, --json            JSON формат просмотра.
  -indent INDENT, --indent INDENT
                        Отступ в формате JSON (по умолчанию: 2).
  -save, --save         Сохранить.
  -o OUTPUT, --output OUTPUT
                        Выходной файл белого списка.
  -empty, --empty       Очистить белый список. Используйте осторожно!

Addressing:
  IP address management.

  -ip IP [IP ...], --ip IP [IP ...]
                        IP адреса.
  -m MASK [MASK ...], --mask MASK [MASK ...]
                        Маски сетей.
```

Оба меню **black** и **white** поддерживают множественное введение ip-адресов. Маска адреса указывается через обратный слеш - **&laquo;/&raquo;**. Например: 192.168.0.2/32. При этом вы вполне можете указать и ipv4 и ipv6 в одной команде. Как было описано выше протокол автоматически будет поправлен в процессе работы с адресом.

Например - добавим 2 адреса с разным протоколом в черный список:

```bash

./py-blacklist.py black -ip 192.168.0.2 2001:db8:abf2:29ea:5298:ad71:2ca0:4ff1 -a -save
```

или так:

```bash

./py-blacklist.py black -ip 192.168.0.2/32 2001:db8:abf2:29ea:5298:ad71:2ca0:4ff1/128 -a -save
```

Обратите внимание на то, что если вы не будете указывать маску - она будет применена автоматически. По умолчанию автоматическая маска ставится максимальной согласно протоколу адреса - **IPV4** или **IPV6**.

Либо маску можно указать отдельным ключом. <u>НО, в этом случае количество масок должно быть равно количеству вводимых ip-адресов!</u>

```bash

./py-blacklist.py black -ip 192.168.0.2 2001:db8:abf2:29ea:5298:ad71:2ca0:4ff1 -m 32 128 -a -save
```

Теперь разберем просмотр правил межсетевого экрана. Тут тоже есть нюансы.

Во первых стоит обратить внимание на ключ **-c** в первом меню. Этот ключ используется для фильтрации просмотра ip-адресов в файлах списков. Для сохранения тех же значений используется ключ **-q**.

В меню списков поддерживается просмотр в формате **JSON** с помощью ключа **-j**.

При чтении того или иного списка с ключом **-s** и указанием хотя бы частичного ip-адреса параметрах ключа **-ip** - выходные данные просмотра будут отфильтрованы по данному частичному тексту введёного значения адреса. Либо вы можете ввести полный адрес и с маской и без неё. Результат также будет отфильтрован.

Приведём несколько примеров.

```bash
# Простой просмотр списка.
$ ./py-blacklist.py black -s

# Простой просмотр списка в формате JSON.
$ ./py-blacklist.py black -s -j

# Отфильтруем все ip-адреса, которые заблокированы 3 и боолее раз
$ ./py-blacklist.py -c 3 black -s

# Отфильтруем все ip-адреса, которые заблокированы 3 и боолее раз в формате JSON
$ ./py-blacklist.py -c 3 black -s -j

```

Попробуем набрать те же самые команды, но при этом найдём в списке все адреса, которые содержат в себе цифры 193 и 185.

```bash
# Простой просмотр списка.
$ ./py-blacklist.py black -s -ip 193 185

# Простой просмотр списка в формате JSON.
$ ./py-blacklist.py black -s -j -ip 193 185

# Отфильтруем все ip-адреса, которые заблокированы 3 и боолее раз
$ ./py-blacklist.py -c 3 black -s -ip 193 185

# Отфильтруем все ip-адреса, которые заблокированы 3 и боолее раз в формате JSON
$ ./py-blacklist.py -c 3 black -s -j -ip 193 185

```

И при этом любой результат можно сохранить в любой файл. Например, пусть это будет **&laquo;./data.txt&raquo;**.

```bash
# Простой просмотр списка.
$ ./py-blacklist.py black -s -ip 193 185 -o ./data.txt -save

# Простой просмотр списка в формате JSON.
$ ./py-blacklist.py black -s -j -ip 193 185 -o ./data.txt -save

# Отфильтруем все ip-адреса, которые заблокированы 3 и боолее раз
$ ./py-blacklist.py -c 3 black -s -ip 193 185 -o ./data.txt -save

# Отфильтруем все ip-адреса, которые заблокированы 3 и боолее раз в формате JSON
$ ./py-blacklist.py -c 3 black -s -j -ip 193 185 -o ./data.txt -save

```

А теперь рассмотрим меню **active**. Это меню предназначено для анализа активности черного списка в заданных файлах логов. Также имеется возможность просматривать получившийся журнал активности и очищать. В дополинение можно изменить местоположение данного журнала в системе, а вывод на дисплей можно немного отфильтровать согласно ведённому регулярному выражению. Либо вы можете сохранить полученный результат в любой указанный вами файл.

```bash
$ ./py-blacklist.py active -h

usage: py-blacklist.py active [-h] [-filelog FILELOG]
                              [-search SEARCH [SEARCH ...]] [-empty] [-s]
                              [-save] [-o OUTPUT] [-grep GREP]

options:
  -h, --help            Показать справку и выйти
  -filelog FILELOG, --filelog FILELOG
                        Файл журнала, в который записывается активность 
                        ip-адресов из черного списка.
  -search SEARCH [SEARCH ...], --search SEARCH [SEARCH ...]
                        Перечислите файлы журналов, в которых следует 
                        искать активность ip-адресов из черного списка, 
                        в соответствии с указанным количеством блокировок.
  -empty, --empty       Очистить файл журнала активности ip-адресов 
                        из черного списка.
  -s, --show            Просмотрите файл журнала активности, 
                        в котором записывается активность ip-адресов 
                        в соответствии с указанным количеством блокировок.
  -save, --save         Сохраните информацию о просмотре.
  -o OUTPUT, --output OUTPUT
                        Сохраните информацию о просмотре в файл.
  -grep GREP, --grep GREP
                        Фильтрация выходных данных журнала активности 
                        ip-адресов в соответствии с указанным 
                        регулярным выражением.

Addressing:
  IP address management.

  -ip IP [IP ...], --ip IP [IP ...]
                        IP адреса.
```

Первое на что нужно обратить внимание - ключ **-search**. После него вы указываете полный пути ко всем нужным вам файлам логов, в которых необходимо произвести анализ активности имеющегося черного списка ip-адресов. Анализ активности вводимых вручную ip-адресов пока что не предусмотрен.

Например. В данном случае будут просканированы 2 лог-файла NGINX, причём не на все ip-адреса, а только на те, у которых количество блокировок в черном списке записано в количестве **3** единицы. Но можно просканировать и на все ip-адреса. Для этого достаточно либо указать 1, либо вообще не использовать ключ **-c**.

```bash
# Можно так
$ ./py-blacklist.py -c 3 active -search /var/log/nginx/access.log /var/log/my_service/access.log

# А можно и так.
$ ./py-blacklist.py active -search /var/log/nginx/access.log /var/log/my_service/access.log
```

Вот другой пример сканирования тех же самых файлов журналов **NGINX** на активность. Однако, здесь будет сканирование непосредственно заданных ip-адресов через ключ **-ip**.

```bash
$ sudo ./py-blacklist.py active -ip 172.96.172.196/32 35.247.128.229/32 34.101.106.173/32 146.190.24.151/32 193.35.18.89/32 -search /var/log/nginx/access.log /var/log/my_service/access.log
```

Только после того, как вы просканировали лог-файлы на активность, результат, сохранённый в отдельный файл, можно посмотреть и отфильтровать вывод на экран, чтобы просто уменьшить последний.

Пока что просто посмотрим на результат поиска активности.

```bash
$ ./py-blacklist.py active -s
```

Попробуем отфильтровать последний вывод и пока что опять просто выведем всё на экран. В данном случае на экран будут выведены, например, только строки с цифрами **&laquo;193&raquo;**.

```bash
$ ./py-blacklist.py active -s -grep "193"
```

А теперь сохраним и первый и второй результат просмотра в некий отдельный файл.

```bash
$ ./py-blacklist.py active -s -save -o ./activity.log
$ ./py-blacklist.py active -s -grep "193" -save -o ./activity.log
```

И наконец очистим журнал активности.

```bash
$ ./py-blacklist.py active -empty -save
```

---

## <a name="about">3. Обо Мне</a>

<details>
	<summary>Подробнее ...</summary>
	
Автор данной разработки **Shadow**: [maximalisimus](https://github.com/maximalisimus).

Имя автора: **maximalisimus**: [maximalis171091@yandex.ru](mailto:maximalis171091@yandex.ru).

Дата создания: **25.07.2023**

</details>

---

[К оглавлению](#Oglavlenie)

---

## <a name="English">English README.</a>

Fail2Ban black and white lists.

![Linux](./image/linux.svg "Linux") &nbsp;![Python-3](./image/python-3-icon.svg "Python-3")

## <a name="EngOglavlenie">Table of contents</a>

1. [Installation.](#SetupEng)
2. [Utility Overview.](#ShowUtilitesEng)
3. [About the author.](#AboutEng)

---

## <a name="SetupEng">1. Installation</a>

To install the program, use the following command using **Makefile**:

```bash
cd ~
git clone https://github.com/maximalisimus/blacklist-scripts.git
cd blacklist-scripts
sudo make DESTDIR=/ install
```

To control the installation, there are some variables in the **Makefile** that you could use.

* **DESTDIR** - location in the system, directory. By default, the root of the system is set.
* **POSTDIR** - the installation directory in front of the program folder, i.e. the parent directory of the program. By default, it is equal to **&laquo;etc&raquo;**. <u>Must be present. It is not allowed to set an empty one.</u>
* **INSTALLDIR** - the remote root of the future system. Used to create the correct symbolic link in **/usr/bin/**.
* **TARGET** - the name of the directory with the program itself.

It is not recommended to change the other variables in any way.

If you need to change the installation directory in the system, use the variables *DESTDIR*, *POSTDIR* and *TARGET*. 

For example, I want to install a program in **/opt/blacklist/**.

```bash
sudo make DESTDIR=/ POSTDIR=opt TARGET=blacklist install
```

If you need filters for **NGINX** - install them separately:

```bash
sudo make DESTDIR=/ install-filter
```

These preset filters for **Fail2ban** contain regular expressions for separate tracking of all errors of *Nginx itself* as such from the file **/var/log/nginx/error.log** or similar, as well as tracking the status states of "4xx error in the request" and "5xx server error" from the file **/var/log/nginx/access.log** or similar custom.

****Pay attention!** These preset regular expressions in the specified filters are quite rigid. If you are not sure that you yourself will not make mistakes during the settings or when using them - refuse to install and use them!

To install the **action**s for **Fail2ban**, use the command to install them:

```bash
sudo make DESTDIR=/ install-action
```

The blacklist also has pre-installed **Jail**-rules that you can also set, if necessary:

```bash
sudo make DESTDIR=/ install-jail
```

If you need all the preset functions for **Fail2ban** (actions, filters, rules), you can install them with one command:

```bash
sudo make DESTDIR=/ install-all
```

Or simultaneous installation of the program itself and all functions for **Fail2ban**-a (actions, filters, rules):

```bash
sudo make DESTDIR=/ all
```

To remove the program and/or additional functions for **Fail2ban**-and in **Makefile** there are appropriate commands:

* uninstall - remove the program,
* uninstall-action - remove pre-installed actions,
* uninstall-filter - remove pre-installed filters,
* uninstall-tool - remove preset rules,
* uninstall-all - remove all pre-installed functions **Fail2ban**-a.
* clear - delete both the program itself and all pre-installed functions **Fail2ban**-a.

If you want to use the installation method using **setup.py **, use the following method.

Use the following command to check that you have the current version of setuptools installed.

```bash
Debian: $ sudo apt install python-virtualenv python3-virtualenv python3-venv virtualenv python3-virtualenvwrapper
Archlinux: $ sudo pacman -S python-virtualenv python-virtualenvwrapper
Python PIP: $ python -m pip install --upgrade pip setuptools virtualenv virtualenvwrapper --upgrade
```

We also clone the repository and go to it.

```bash
cd ~
git clone https://github.com/maximalisimus/blacklist-scripts.git
cd blacklist-scripts
```

Installing.

```bash
# Так
$ python setup.py install

# Или так
$ pip install .
```

To build the utility into 2 types of packages - an archive (most likely **.tar.gz **) with all the necessary files and **.whl** file for **PIP**, use the following command.

```bash
# First, go to the repository directory.
$ cd blacklist-scripts

# You can collect.
$ python setup.py sdist bdist_wheel

```

2 corresponding archives should appear in the dist folder.

---

[To the table of contents](#EngOglavlenie)

---

## <a name="ShowUtilitesEng">2. Utility Overview.</a>

The program's help looks like this (Parameters and keys.):

```bash
./py-blacklist.py -h

usage: py-blacklist.py [-h] [-v] [-info] [-c COUNT] [-q QUANTITY]
                       [-wd WORKDIR] [-b BLACKLIST] [-w WHITELIST] [-personal]
                       [-e] [-run] [-fine] [-ipv6] [-nft]
                       [-nftproto {ip,ip6,inet}] [-table TABLE] [-chain CHAIN]
                       [-newtable] [-newchain] [-Deltable] [-Delchain]
                       [-cleartable] [-clearchain] [-con CONSOLE] [-cmd] [-sd]
                       [-logfile LOGFILE] [-nolog] [-limit] [-viewlog]
                       [-resetlog]
                       {systemd,service,black,white} ...

The Fail2Ban black and white lists in Python.

options:
  -h, --help            show this help message and exit
  -v, --version         Version.
  -info, --info         Information about the author.

Management:
  Management commands.

  {systemd,service,black,white,active}
                        commands help.
    systemd             Systemd management.
    service             Program management.
    black               Managing blacklists.
    white               Managing whitelists.
    active              Activity in log files.

Parameters:
  Settings for the number of bans.

  -c COUNT, --count COUNT
                        The number of locks after which the ip-address is
                        entered in {IP,IP6,NF}TABLES (default 0).
  -q QUANTITY, --quantity QUANTITY
                        The number of ip address locks to be saved (default
                        0).

Files:
  Working with files.

  -wd WORKDIR, --workdir WORKDIR
                        Working directory.
  -b BLACKLIST, --blacklist BLACKLIST
                        Input blacklist file.
  -w WHITELIST, --whitelist WHITELIST
                        Input whitelist file.

NFTABLES:
  Configuration NFTABLES.

  -personal, --personal
                        Personal settings of NFTABLES tables, regardless of
                        the data entered.
  -e, -exit, --exit     Finish creating the table/chain on NFTABLES.
  -run, --run           Full starting NFTABLES tables from all settings. Use
                        carefully!
  -fine, --fine         Full clearing NFTABLES tables from all settings. Use
                        carefully!
  -net NETWORK, -network NETWORK, --network NETWORK
                        The name of the interface through which the processed
                        packet should be received. That is, the input network
                        interface.
  -ipv6, --ipv6         Forced IPV6 protocol selection.
  -nft, --nftables      Select the NFTABLES framework (Default IP(6)TABLES).
  -nftproto {ip,ip6,inet}, --nftproto {ip,ip6,inet}
                        Select the protocol NFTABLES, before rule (Auto ipv4
                        on "ip" or -ipv6 to "ip6").
  -table TABLE, --table TABLE
                        Select the table for NFTABLES (Default "filter").
  -chain CHAIN, --chain CHAIN
                        Choosing a chain of rules (Default: "INPUT").
  -newtable, --newtable
                        Add a new table in NFTABLES. Use carefully!
  -newchain, --newchain
                        Add a new chain in NFTABLES. Use carefully!
  -Deltable, --Deltable
                        Del the table in NFTABLES. Use carefully!
  -Delchain, --Delchain
                        Del the chain in NFTABLES. Use carefully!
  -cleartable, --cleartable
                        Clear the table in NFTABLES. Use carefully!
  -clearchain, --clearchain
                        Clear the chain in NFTABLES. Use carefully!

Settings:
  Configurations.

  -con CONSOLE, --console CONSOLE
                        Enther the console name (Default "sh").
  -cmd, --cmd           View the command and exit the program without
                        executing it.
  -lslan, --lslan       View a list of network interfaces.
  -sd, --showdir        Show working directory.
  -logfile LOGFILE, --logfile LOGFILE
                        Log file.
  -nolog, --nolog       Do not log events.
  -limit, --limit       Limit the log file. Every day the contents of the log
                        will be completely erased.
  -viewlog, --viewlog   View the log file.
  -latest, --latest     Output everything from the log by the last record
                        date.
  -fil FILTERING, -filtering FILTERING, --filtering FILTERING
                        Filter the log output.
  -resetlog, --resetlog
                        Reset the log file.
```

At the same time, if you do not enter any keys, the user is automatically redirected to the help page, and in any menu and sub-menu.

For the keys **NFTABLES** it is necessary to make an explanation.

When you enter the *-nft* key, you start working with **NFTABLES**. Without it, you will work with **IPTABLES** and **IP6TABLES**.

When selecting the *-personal* key and the *-nft* key, the program will select <u>predefined</u> tables and chains in the **NFTABLES** framework. It does not matter what you will try to enter with the corresponding keys. All values will be redefined programmatically.

The same goes for the *-run* and *-fine* keys. The first one is defined instead of using 2 keys *-newtable* and *-newchain*. Well, that is, when both of the last keys are used, it is easier to specify one *-run* instead of 2 keys. For *-fine*, respectively, there will be a similar appeal to all the functions of cleaning and deleting tables and chains after the application is shut down.

Also, such an appeal using the above keys will be automatically applied in the Systemd service management menu, i.e. taken into account when creating the service and timer.

Or you can use any other keys without *-personal*, *-run* and *-fine* separately and independently, for example, to monitor or create certain tables or chains.

When deleting and cleaning tables and chains, there are certain limitations associated with standard tables and chains of the system in packages with a compatibility layer between **NFTABLES** and **IP(6)TABLES** Netfilter. Therefore, do not be surprised if the table or chain has not been deleted from the system or has not been cleaned up. This is done only for security. 

But, there is one little trick. You can use the keys **-cmd**, **-fine** and **-e** to look at all the completion commands, and use them at your own risk. Or use the appropriate keys to change the name of tables and/or chains and again specify **-cmd**, **-fine** and **-e** to look at all completion commands with changed values and also use them at your own risk.

When specifying the **-net** key, it becomes possible to bind a lock or a permissive rule to a specific network interface.

Accordingly, using the **-lslan** key, you can view a list of all available network interfaces.

Another explanation concerns the choice of protocol **-ipv6**. In general, when entering ip addresses, the protocol is determined automatically and also automatically corrected. However, the protocol can be forcibly changed.

The keys **-latest** and **-fil** make sense only when using another key - **-viewlog**. I.e. only when viewing the event log. HOWEVER, only one of the 2 keys can be used at the same time - either **-latest** or **-fil**. the first one will output the entire contents of the log according to the last record date. The second one will filter all the contents according to the entered regular expression string in the argument itself. 

For example, we will output all the contents of the log by the last date of entry into it. And also, let's try to add filtering by some string, for example, a partial ip address.

```bash
$ ./py-blacklist.py -viewlog -latest
$ ./py-blacklist.py -viewlog -latest -fil "193"
```

And now let's try to filter out only certain entries, for example, some ip address or time or a line at the end of the log entries.

```bash
$ ./py-blacklist.py -viewlog -fil "193"
```

Consider the Systemd menu.

```bash
./py-blacklist.py systemd

Systemd file «blacklist@.service» and «blacklist@.timer» not found!
Please enter «-create» to create system files before accessing Systemd functions!

usage: py-blacklist.py systemd [-h] [-create] [-delete] [-status] [-istimer]
                               [-isservice] [-enable] [-disable] [-start]
                               [-stop] [-reload] [-starttimer] [-stoptimer]

options:
  -h, --help            show this help message and exit
  -create, --create     Create «blacklist@.service» and «blacklist@.timer».
  -delete, --delete     Delete «blacklist@.service» and «blacklist@.timer».
  -status, --status     Status «blacklist@.service».
  -istimer, --istimer   Check the active and enabled is «blacklist@.timer».
  -isservice, --isservice
                        Check the active and enabled is «blacklist@.service».
  -enable, --enable     Enable «blacklist@.timer».
  -disable, --disable   Disable «blacklist@.timer».
  -start, --start       Start «blacklist@.service».
  -stop, --stop         Stop «blacklist@.service».
  -reload, --reload     Reload «blacklist@.service».
  -starttimer, --starttimer
                        Start «blacklist@.timer».
  -stoptimer, --stoptimer
                        Stop «blacklist@.timer».
```

Consider the Service menu.

```bash
./py-blacklist.py service

usage: py-blacklist.py service [-h] [-start] [-stop] [-nostop] [-reload]
                               [-show] [-link] [-unlink] [-name NAME]

options:
  -h, --help            show this help message and exit
  -start, --start       Launching the blacklist.
  -stop, --stop         Stopping the blacklist.
  -nostop, --nostop     Stopping the blacklist without clearing
                        {IP,IP6,NF}TABLES.
  -reload, --reload     Restarting the blacklist.
  -show, --show         List the rules in Netfilter.
  -tb, --tb             View a list of available tables NFTABLES.
  -link, --link         Symlink to program on «/usr/bin/».
  -unlink, --unlink     Unlink to program on «/usr/bin/».
  -name NAME, --name NAME
                        The name of the symlink for the location in the
                        programs directory is «/usr/bin/». (Default
                        "blacklist").
  -grep GREP, --grep GREP
                        Filtering Netfilter output according to the 
                        specified regular expression.
```

By default, the program has a built-in method of working from any directory. If you did not install the program using **Makefile**, you may need the function of creating a symbolic link to the script in **"/usr/bin/"** and also safely deleting this symbolic link. As a bonus, you can even change the name of the symbolic link so that it is convenient for you to access the script without specifying the full path and its name.

When starting, stopping or restarting the program, both black and white lists will be processed. In this case, the white list will be entered in **Netfilter** with mandatory permissive rules, and the black list with forbidding ones. 

The program can be run multiple times. Unlike manual control using commands via the terminal, there is protection against re-adding the IP address both to the **NetFilter** tables and to the list files themselves.

The **-grep** key is used to filter what should be displayed when viewing firewall rules using the **-show** key. At the same time, it does not even matter whether the key of the previous menu **-nft** is used or not.

For example, I don't want to look at the entire table **IPTABLES** or **NFTABLES**, but I want to filter, i.e. reduce it to certain rows, like the utility **GREP**. Let these lines contain addresses with numbers, for example, 193 and 185. At the same time, it's not that I don't want to use a conveyor, but let's say I'm a beginner and I don't know how to use a conveyor in **Linux** distributions and I don't know any output filtering utility yet.

```bash
# For iptables
$ ./py-blacklist.py service -show -grep "193|185"

# For nftables
$ ./py-blacklist.py -nft service -show -grep "193|185"

# And this is what it would look like for iptables with a conveyor.
$ ./py-blacklist.py service -show | grep -Ei "193|185"

# Accordingly, with the conveyor for nftables.
$ ./py-blacklist.py -nft service -show | grep -Ei "193|185"
```

Consider the black menu.

```bash
./py-blacklist.py black

usage: py-blacklist.py black [-h] [-ban] [-unban] [-a] [-d] [-s] [-j] [-save]
                             [-o OUTPUT] [-empty] [-ip IP [IP ...]]
                             [-m MASK [MASK ...]]

options:
  -h, --help            show this help message and exit
  -ban, --ban           Block IP addresses in {IP,IP6,NF}TABLES.
  -unban, --unban       Unblock IP addresses in {IP,IP6,NF}TABLES.
  -a, --add             Add to the blacklist.
  -d, --delete          Remove from the blacklist.
  -s, --show            Read the blacklist.
  -j, --json            JSON fromat show.
  -indent INDENT, --indent INDENT
                        JSON indent (Default: 2).
  -save, --save         Save show info.
  -o OUTPUT, --output OUTPUT
                        Output blacklist file.
  -empty, --empty       Clear the blacklist. Use carefully!

Addressing:
  IP address management.

  -ip IP [IP ...], --ip IP [IP ...]
                        IP addresses.
  -m MASK [MASK ...], --mask MASK [MASK ...]
                        Network Masks.
```

Consider the white menu.

```bash
./py-blacklist.py white

usage: py-blacklist.py white [-h] [-ban] [-unban] [-a] [-d] [-s] [-j] [-save]
                             [-o OUTPUT] [-empty] [-ip IP [IP ...]]
                             [-m MASK [MASK ...]]

options:
  -h, --help            show this help message and exit
  -ban, --ban           Allow ip addresses in {IP,IP6,NF}TABLES.
  -unban, --unban       Remove permissions from {IP,IP6,NF}TABLES.
  -a, --add             Add to the whitelist.
  -d, --delete          Remove from the whitelist.
  -s, --show            Read the whitelist.
  -j, --json            JSON fromat show.
  -indent INDENT, --indent INDENT
                        JSON indent (Default: 2).
  -save, --save         Save show info.
  -o OUTPUT, --output OUTPUT
                        Output whitelist file.
  -empty, --empty       Clear the whitelist. Use carefully!

Addressing:
  IP address management.

  -ip IP [IP ...], --ip IP [IP ...]
                        IP addresses.
  -m MASK [MASK ...], --mask MASK [MASK ...]
                        Network Masks.
```

Both **black** and **white** menus support multiple IP address entry. The address mask is specified using a backslash - **/**. For example: 192.168.0.2/32. At the same time, you can specify both ipv4 and ipv6 in the same command. As described above, the protocol will be automatically corrected in the process of working with the address.

For example - add 2 addresses with different protocol to the blacklist:

```bash

./py-blacklist.py black -ip 192.168.0.2 2001:db8:abf2:29ea:5298:ad71:2ca0:4ff1 -a -save
```

or so:

```bash

./py-blacklist.py black -ip 192.168.0.2/32 2001:db8:abf2:29ea:5298:ad71:2ca0:4ff1/128 -a -save
```

Please note that if you do not specify a mask, it will be applied automatically. By default, the automatic mask is set to the maximum according to the address protocol - **IPV4** or **IPV6**.

Or the mask can be specified with a separate key. <u>BUT, in this case, the number of masks should be equal to the number of ip addresses entered!</u>

```bash

./py-blacklist.py black -ip 192.168.0.2 2001:db8:abf2:29ea:5298:ad71:2ca0:4ff1 -m 32 128 -a -save
```

Now let's analyze the viewing of firewall rules. There are nuances here too.

First of all, you should pay attention to the **-c** key in the first menu. This key is used to filter the viewing of ip addresses in the list files. To save the same values, the key **-q** is used.

The list menu supports viewing in **JSON** format using the **-j** key.

When reading a list with the key **-s** and specifying at least a partial ip address in the key parameters **-ip** - the viewing output data will be filtered by this partial text of the entered address value. Or you can enter the full address with and without a mask. The result will also be filtered.

Here are some examples.

```bash
# Simple list view.
$ ./py-blacklist.py black -s

# Simple viewing of the list in JSON format.
$ ./py-blacklist.py black -s -j

# Filter out all ip addresses that are blocked 3 or more times.
$ ./py-blacklist.py -c 3 black -s

# Filter out all ip addresses that are blocked 3 or more times in JSON format.
$ ./py-blacklist.py -c 3 black -s -j

```

Let's try to type the same commands, but at the same time we will find in the list all the addresses that contain the numbers 193 and 185.

```bash
# Simple list view.
$ ./py-blacklist.py black -s -ip 193 185

# Simple viewing of the list in JSON format.
$ ./py-blacklist.py black -s -j -ip 193 185

# Filter out all ip addresses that are blocked 3 or more times.
$ ./py-blacklist.py -c 3 black -s -ip 193 185

# Filter out all ip addresses that are blocked 3 or more times in JSON format.
$ ./py-blacklist.py -c 3 black -s -j -ip 193 185

```

And at the same time, any result can be saved to any file. For example, let it be **&laquo;./data.txt&raquo;**.

```bash
# Simple list view.
$ ./py-blacklist.py black -s -ip 193 185 -o ./data.txt -save

# Simple viewing of the list in JSON format.
$ ./py-blacklist.py black -s -j -ip 193 185 -o ./data.txt -save

# Filter out all ip addresses that are blocked 3 or more times.
$ ./py-blacklist.py -c 3 black -s -ip 193 185 -o ./data.txt -save

# Filter out all ip addresses that are blocked 3 or more times in JSON format.
$ ./py-blacklist.py -c 3 black -s -j -ip 193 185 -o ./data.txt -save

```

And now let's look at the **active** menu. This menu is designed to analyze the activity of the blacklist in the specified log files. It is also possible to view the resulting activity log and clear it. In addition, you can change the location of this log in the system, and the output to the display can be filtered a little according to the entered regular expression. Or you can save the result to any file you specify.

```bash
$ ./py-blacklist.py active -h

usage: py-blacklist.py active [-h] [-filelog FILELOG]
                              [-search SEARCH [SEARCH ...]] [-empty] [-s]
                              [-save] [-o OUTPUT] [-grep GREP]

options:
  -h, --help            show this help message and exit
  -filelog FILELOG, --filelog FILELOG
                        The log file in which the activity of ip addresses
                        from the blacklist is recorded.
  -search SEARCH [SEARCH ...], --search SEARCH [SEARCH ...]
                        List the log files in which to search for the activity
                        of blacklist ip addresses, according to the specified
                        number of locks.
  -empty, --empty       Clear the log file of ip addresses activity from the
                        blacklist.
  -s, --show            View the activity log file, which records the activity
                        of ip addresses according to the specified number of
                        locks.
  -save, --save         Save show info.
  -o OUTPUT, --output OUTPUT
                        Save show info to file.
  -grep GREP, --grep GREP
                        Filtering the output of the ip addreses activity log
                        according to the specified regular expression.

Addressing:
  IP address management.

  -ip IP [IP ...], --ip IP [IP ...]
                        IP addresses.
```

The first thing you need to pay attention to is the **-search** key. After it, you specify the full paths to all the log files you need, in which you need to analyze the activity of the existing blacklist of ip addresses. Analysis of the activity of manually entered IP addresses is not yet provided.

For example. In this case, 2 NGINX log files will be scanned, and not to all ip addresses, but only to those whose number of blacklisted locks is recorded in the number **3** units. But you can also scan for all ip addresses. To do this, it is enough to either specify 1, or not use the **-c** key at all.

```bash
# You can do this
$ ./py-blacklist.py -c 3 active -search /var/log/nginx/access.log /var/log/my_service/access.log

# Or you can do that.
$ ./py-blacklist.py active -search /var/log/nginx/access.log /var/log/my_service/access.log
```

Here is another example of scanning the same **NGINX** log files for activity. However, there will be a scan of directly specified ip addresses via the **-ip** key.

```bash
$ sudo ./py-blacklist.py active -ip 172.96.172.196/32 35.247.128.229/32 34.101.106.173/32 146.190.24.151/32 193.35.18.89/32 -search /var/log/nginx/access.log /var/log/my_service/access.log
```

Only after you have scanned the log files for activity, the result saved in a separate file can be viewed and filtered out to the screen to simply reduce the latter.

For now, just look at the activity search result.

```bash
$ ./py-blacklist.py active -s
```

Let's try to filter out the last output and for now we'll just display everything on the screen again. In this case, only lines with numbers **&laquo;193&raquo;** will be displayed on the screen, for example.

```bash
$ ./py-blacklist.py active -s -grep "193"
```

And now we will save both the first and second viewing results in a separate file.

```bash
$ ./py-blacklist.py active -s -save -o ./activity.log
$ ./py-blacklist.py active -s -grep "193" -save -o ./activity.log
```

And finally clear the activity log.

```bash
$ ./py-blacklist.py active -empty -save
```

---

[To the table of contents](#EngOglavlenie)

---

## <a name="AboutEng">3. About the author.</a>


<details>
	<summary>More detailed ...</summary>

The author of this development **Shadow**: [maximalisimus](https://github.com/maximalisimus).

Author's name: **maximalisimus**: [maximalis171091@yandex.ru](mailto:maximalis171091@yandex.ru).

Date of creation: **25.07.2023**

</details>

---

[To the table of contents](#EngOglavlenie)

---
