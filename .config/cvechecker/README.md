<!-- README.md -->
<!-- Qompass AI - [Add description here] -->
<!-- Copyright (C) 2025 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->
#
# Generic settings
# 

dbtype = "sqlite"; 
#dbtype="mysql";
cvecache = "/var/cvechecker/cache";
datadir = "/usr/share/cvechecker";
stringcmd = "/usr/bin/strings -n 3 '@file@'";
version_url = "https://raw.github.com/sjvermeu/cvechecker/master/versions.dat";
#userkey = "servertag";

#
# For Sqlite3
#
sqlite3: {
  localdb = "/var/cvechecker/local";
  globaldb = "/var/cvechecker/global.db";
};

# 
# For MySQL
# 
mysql: {
  dbname = "cvechecker";
  dbuser = "cvechecker_rw";
  dbpass = "password4cvechecker_rw";
  dbhost = "mysql.company.com";
};

