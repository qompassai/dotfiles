noblacklist ${HOME}/.ssh
whitelist ${HOME}/.ssh
protocol unix,inet,inet6
private-bin ssh,scp,sftp,ssh-agent,ssh-add
private-etc hosts,passwd,group,resolv.conf,ssl,ca-certificates,crypto-policies
whitelist ${HOME}/.ssh/known_hosts
include /etc/firejail/default.profile
