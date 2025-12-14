SOLR_JAVA_HOME=""
SOLR_STOP_WAIT="180"
SOLR_START_WAIT="$SOLR_STOP_WAIT"
SOLR_HEAP="512m"
SOLR_JAVA_MEM="-Xms512m -Xmx512m"
GC_LOG_OPTS='-Xlog:gc*'
GC_LOG_OPTS="-verbose:gc -XX:+PrintHeapAtGC -XX:+PrintGCDetails \
  -XX:+PrintGCDateStamps -XX:+PrintGCTimeStamps -XX:+PrintTenuringDistribution -XX:+PrintGCApplicationStoppedTime"
GC_TUNE=" \
-XX:+ExplicitGCInvokesConcurrent \
-XX:SurvivorRatio=4 \
-XX:TargetSurvivorRatio=90 \
-XX:MaxTenuringThreshold=8 \
-XX:+UseConcMarkSweepGC \
-XX:ConcGCThreads=4 -XX:ParallelGCThreads=4 \
-XX:+CMSScavengeBeforeRemark \
-XX:PretenureSizeThreshold=64m \
-XX:+UseCMSInitiatingOccupancyOnly \
-XX:CMSInitiatingOccupancyFraction=50 \
-XX:CMSMaxAbortablePrecleanTime=6000 \
-XX:+CMSParallelRemarkEnabled \
-XX:+ParallelRefProcEnabled"

# Set the ZooKeeper connection string if using an external ZooKeeper ensemble
# e.g. host1:2181,host2:2181/chroot
# Leave empty if not using SolrCloud
#ZK_HOST=""

#ZK_CREATE_CHROOT=true
#ZK_CLIENT_TIMEOUT="30000"
#SOLR_HOST="192.168.1.1"
#SOLR_WAIT_FOR_ZK="30"
SOLR_DELETE_UNKNOWN_CORES=false
SOLR_TIMEZONE="UTC"
ENABLE_REMOTE_JMX_OPTS="false"
RMI_PORT=18983
SOLR_OPTS="$SOLR_OPTS -Dsolr.autoSoftCommit.maxTime=3000"
SOLR_OPTS="$SOLR_OPTS -Dsolr.autoCommit.maxTime=60000"

SOLR_CLUSTERING_ENABLED=true
SOLR_PID_DIR=
SOLR_HOME=
SOLR_DATA_HOME=

#LOG4J_PROPS=/var/solr/log4j2.xml
SOLR_LOG_LEVEL=INFO
SOLR_LOGS_DIR=logs
SOLR_REQUESTLOG_ENABLED=true
SOLR_PORT=8983
#   127.0.0.1, 192.168.0.0/24, [::1], [2000:123:4:5::]/64
#SOLR_IP_ALLOWLIST=
SOLR_IP_DENYLIST=
SOLR_JETTY_HOST="127.0.0.1"
#SOLR_ZK_EMBEDDED_HOST="127.0.0.1"
#SOLR_SSL_ENABLED=true
#SOLR_SSL_KEY_STORE=etc/solr-ssl.keystore.p12
#SOLR_SSL_KEY_STORE_PASSWORD=secret
#SOLR_SSL_TRUST_STORE=etc/solr-ssl.keystore.p12
#SOLR_SSL_TRUST_STORE_PASSWORD=secret
#SOLR_SSL_NEED_CLIENT_AUTH=false
# Enable clients to authenticate (but not require)
#SOLR_SSL_WANT_CLIENT_AUTH=false
#SOLR_SSL_CLIENT_HOSTNAME_VERIFICATION=false
SOLR_SSL_CHECK_PEER_NAME=true
SOLR_SSL_KEY_STORE_TYPE=PKCS12
SOLR_SSL_TRUST_STORE_TYPE=PKCS12
SOLR_SSL_RELOAD_ENABLED=true

#SOLR_SSL_CLIENT_KEY_STORE=
#SOLR_SSL_CLIENT_KEY_STORE_PASSWORD=
#SOLR_SSL_CLIENT_TRUST_STORE=
#SOLR_SSL_CLIENT_TRUST_STORE_PASSWORD=
#SOLR_SSL_CLIENT_KEY_STORE_TYPE=
#SOLR_SSL_CLIENT_TRUST_STORE_TYPE=
# * solr.jetty.keystore.password
# * solr.jetty.truststore.password
# Set the two below if you want to set specific store passwords for HTTP client
# * javax.net.ssl.keyStorePassword
# * javax.net.ssl.trustStorePassword
# More info: https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-common/CredentialProviderAPI.html
#SOLR_HADOOP_CREDENTIAL_PROVIDER_PATH=localjceks://file/home/solr/hadoop-credential-provider.jceks
#SOLR_OPTS=" -Dsolr.ssl.credential.provider.chain=hadoop"
#SOLR_AUTHENTICATION_CLIENT_BUILDER="org.apache.solr.client.solrj.impl.PreemptiveBasicAuthClientBuilderFactory"
#SOLR_AUTH_TYPE="basic"
#SOLR_AUTHENTICATION_OPTS="-Dbasicauth=solr:SolrRocks"
#SOLR_ZK_CREDS_AND_ACLS="-DzkACLProvider=org.apache.solr.common.cloud.DigestZkACLProvider \
#  -DzkCredentialsProvider=org.apache.solr.common.cloud.DigestZkCredentialsProvider \
#  -DzkCredentialsInjector=org.apache.solr.common.cloud.VMParamsZkCredentialsInjector \
#  -DzkDigestUsername=admin-user -DzkDigestPassword=CHANGEME-ADMIN-PASSWORD \
#  -DzkDigestReadonlyUsername=readonly-user -DzkDigestReadonlyPassword=CHANGEME-READONLY-PASSWORD"
#SOLR_OPTS="$SOLR_OPTS $SOLR_ZK_CREDS_AND_ACLS"
#...
#   -DzkDigestCredentialsFile=/path/to/zkDigestCredentialsFile.properties
#...

# Use a custom injector to inject ZK credentials into DigestZkACLProvider
# -DzkCredentialsInjector expects a class implementing org.apache.solr.common.cloud.ZkCredentialsInjector
# ...
#   -DzkCredentialsInjector=fully.qualified.class.CustomInjectorClassName"
# ...

# Jetty GZIP module enabled by default
#SOLR_GZIP_ENABLED=true

# Settings for common system values that may cause operational imparement when system defaults are used.
# Solr can use many processes and many file handles. On modern operating systems the savings by leaving
# these settings low is minuscule, while the consequence can be Solr instability. To turn these checks off, set
# SOLR_ULIMIT_CHECKS=false either here or as part of your profile.

# Different limits can be set in solr.in.sh or your profile if you prefer as well.
#SOLR_RECOMMENDED_OPEN_FILES=
#SOLR_RECOMMENDED_MAX_PROCESSES=
#SOLR_ULIMIT_CHECKS=

# When running Solr in non-cloud mode and if planning to do distributed search (using the "shards" parameter), the
# list of hosts needs to be defined in an allow-list or Solr will forbid the request. The allow-list can be configured
# in solr.xml, or if you are using the OOTB solr.xml, can be specified using the system property "solr.allowUrls".
# Alternatively host checking can be disabled by using the system property "solr.disable.allowUrls"
#SOLR_OPTS="$SOLR_OPTS -Dsolr.allowUrls=http://localhost:8983,http://localhost:8984"

# For a visual indication in the Admin UI of what type of environment this cluster is, configure
# a -Dsolr.environment property below. Valid values are prod, stage, test, dev, with an optional
# label or color, e.g. -Dsolr.environment=test,label=Functional+test,color=brown
#SOLR_OPTS="$SOLR_OPTS -Dsolr.environment=prod"

# Specifies the path to a common library directory that will be shared across all cores.
# Any JAR files in this directory will be added to the search path for Solr plugins.
# If the specified path is not absolute, it will be relative to `$SOLR_HOME`.
#SOLR_OPTS="$SOLR_OPTS -Dsolr.sharedLib=/path/to/lib"

# Runs solr in java security manager sandbox. This can protect against some attacks.
# Runtime properties are passed to the security policy file (server/etc/security.policy)
# You can also tweak via standard JDK files such as ~/.java.policy, see https://s.apache.org/java8policy
# This is experimental! It may not work at all with Hadoop/HDFS features.
#SOLR_SECURITY_MANAGER_ENABLED=true
# This variable provides you with the option to disable the Admin UI. if you uncomment the variable below and
# change the value to true. The option is configured as a system property as defined in SOLR_START_OPTS in the start
# scripts.
# SOLR_ADMIN_UI_DISABLED=false

# Solr is by default allowed to read and write data from/to SOLR_HOME and a few other well defined locations
# Sometimes it may be necessary to place a core or a backup on a different location or a different disk
# This parameter lets you specify file system path(s) to explicitly allow. The special value of '*' will allow any path
#SOLR_OPTS="$SOLR_OPTS -Dsolr.allowPaths=/mnt/bigdisk,/other/path"

# Solr can attempt to take a heap dump on out of memory errors. To enable this, uncomment the line setting
# SOLR_HEAP_DUMP below. Heap dumps will be saved to SOLR_LOG_DIR/dumps by default. Alternatively, you can specify any
# other directory, which will implicitly enable heap dumping. Dump name pattern will be solr-[timestamp]-pid[###].hprof
# When using this feature, it is recommended to have an external service monitoring the given dir.
# If more fine grained control is required, you can manually add the appropriate flags to SOLR_OPTS
# See https://docs.oracle.com/en/java/javase/11/troubleshoot/command-line-options1.html
# You can test this behavior by setting SOLR_HEAP=25m
#SOLR_HEAP_DUMP=true
#SOLR_HEAP_DUMP_DIR=/var/log/dumps

# Before version 9.0, Solr required a copy of solr.xml file in $SOLR_HOME. Now Solr will use a default file if not found.
# To restore the old behavior, set the variable below to true
#SOLR_SOLRXML_REQUIRED=false

# Some previous versions of Solr use an outdated log4j dependency. If you are unable to use at least log4j version 2.15.0
# then enable the following setting to address CVE-2021-44228
# SOLR_OPTS="$SOLR_OPTS -Dlog4j2.formatMsgNoLookups=true"

# The bundled plugins in the "modules" folder can easily be enabled as a comma-separated list in SOLR_MODULES variable
# SOLR_MODULES=extraction,ltr

# Configure the default replica placement plugin to use if one is not configured in cluster properties
# See https://solr.apache.org/guide/solr/latest/configuration-guide/replica-placement-plugins.html for details
#SOLR_PLACEMENTPLUGIN_DEFAULT=simple

# Solr internally doesn't use cookies other than for modules such as Kerberos/Hadoop Auth. If you don't need any of those
# And you don't need them for an external system (such as a load balancer), you can disable the use of a CookieStore with:
# SOLR_OPTS="$SOLR_OPTS -Dsolr.http.disableCookies=true"
