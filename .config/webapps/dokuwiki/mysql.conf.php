<?php
/*
* /qompassai/dotfiles/.config/webapps/dokuwiki/docuwiki.php
* Qompass AI DokuWiki MySQL Config
* Copyright (C) 2025 Qompass AI, All rights reserved
 ****************************************************
*/
$conf['plugin']['authmysql']['server']   = '';
$conf['plugin']['authmysql']['user']     = '';
$conf['plugin']['authmysql']['password'] = '';
$conf['plugin']['authmysql']['database'] = '';
$conf['plugin']['authmysql']['debug'] = 0;
$conf['plugin']['authmysql']['forwardClearPass'] = 0;
$conf['plugin']['authmysql']['TablesToLock']= array("users", "users AS u","groups", "groups AS g", "usergroup", "usergroup AS ug");
$conf['plugin']['authmysql']['checkPass']   = "SELECT pass
                                               FROM usergroup AS ug
                                               JOIN users AS u ON u.uid=ug.uid
                                               JOIN groups AS g ON g.gid=ug.gid
                                               WHERE login='%{user}'
                                               AND name='%{dgroup}'";
$conf['plugin']['authmysql']['getUserInfo'] = "SELECT pass, CONCAT(firstname,' ',lastname) AS name, email AS mail
                                               FROM users
                                               WHERE login='%{user}'";
$conf['plugin']['authmysql']['getGroups']   = "SELECT name as `group`
                                               FROM groups g, users u, usergroup ug
                                               WHERE u.uid = ug.uid
                                               AND g.gid = ug.gid
                                               AND u.login='%{user}'";
$conf['plugin']['authmysql']['getUsers']    = "SELECT DISTINCT login AS user
                                               FROM users AS u
                                               LEFT JOIN usergroup AS ug ON u.uid=ug.uid
                                               LEFT JOIN groups AS g ON ug.gid=g.gid";
$conf['plugin']['authmysql']['FilterLogin'] = "login LIKE '%{user}'";
$conf['plugin']['authmysql']['FilterName']  = "CONCAT(firstname,' ',lastname) LIKE '%{name}'";
$conf['plugin']['authmysql']['FilterEmail'] = "email LIKE '%{email}'";
$conf['plugin']['authmysql']['FilterGroup'] = "name LIKE '%{group}'";
$conf['plugin']['authmysql']['SortOrder']   = "ORDER BY login";
$conf['plugin']['authmysql']['addUser']     = "INSERT INTO users
                                               (login, pass, email, firstname, lastname)
                                               VALUES ('%{user}', '%{pass}', '%{email}',
                                               SUBSTRING_INDEX('%{name}',' ', 1),
                                               SUBSTRING_INDEX('%{name}',' ', -1))";
$conf['plugin']['authmysql']['addGroup']    = "INSERT INTO groups (name)
                                               VALUES ('%{group}')";
$conf['plugin']['authmysql']['addUserGroup']= "INSERT INTO usergroup (uid, gid)
                                               VALUES ('%{uid}', '%{gid}')";
$conf['plugin']['authmysql']['delGroup']    = "DELETE FROM groups
                                               WHERE gid='%{gid}'";
$conf['plugin']['authmysql']['getUserID']   = "SELECT uid AS id
                                               FROM users
                                               WHERE login='%{user}'";
$conf['plugin']['authmysql']['delUser']     = "DELETE FROM users
                                               WHERE uid='%{uid}'";
$conf['plugin']['authmysql']['delUserRefs'] = "DELETE FROM usergroup
                                               WHERE uid='%{uid}'";
$conf['plugin']['authmysql']['updateUser']  = "UPDATE users SET";
$conf['plugin']['authmysql']['UpdateLogin'] = "login='%{user}'";
$conf['plugin']['authmysql']['UpdatePass']  = "pass='%{pass}'";
$conf['plugin']['authmysql']['UpdateEmail'] = "email='%{email}'";
$conf['plugin']['authmysql']['UpdateName']  = "firstname=SUBSTRING_INDEX('%{name}',' ', 1),
                                               lastname=SUBSTRING_INDEX('%{name}',' ', -1)";
$conf['plugin']['authmysql']['UpdateTarget']= "WHERE uid=%{uid}";
$conf['plugin']['authmysql']['delUserGroup']= "DELETE FROM usergroup
                                               WHERE uid='%{uid}'
                                               AND gid='%{gid}'";
$conf['plugin']['authmysql']['getGroupID']  = "SELECT gid AS id
                                               FROM groups
                                               WHERE name='%{group}'";
?>
