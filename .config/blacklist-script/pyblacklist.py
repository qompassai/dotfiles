#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Fail2Ban black and white lists in Python.

Artamonov Mikhail [https://github.com/maximalisimus]
maximalis171091@yandex.ru
# License: GPL3
"""

import argparse
import json
import pathlib
import sys
import ipaddress
import socket
import subprocess
import re
from datetime import datetime
import logging

__author__ = 'Mikhail Artamonov'
__progname__ = str(pathlib.Path(sys.argv[0]).resolve().name)
__copyright__ = f"© The \"{__progname__}\". Copyright  by 2023."
__credits__ = ["Mikhail Artamonov"]
__license__ = "GPL3"
__version__ = "2.4.3"
__maintainer__ = "Mikhail Artamonov"
__email__ = "maximalis171091@yandex.ru"
__status__ = "Production"
__date__ = '09.07.2023'
__modifed__ = '11.08.2023'
__contact__ = 'VK: https://vk.com/shadow_imperator'

infromation = f"Author: {__author__}\nProgname: {__progname__}\nVersion: {__version__}\n" + \
			f"Date of creation: {__date__}\nLast modified date: {__modifed__}\n" + \
			f"License: {__license__}\nCopyright: {__copyright__}\nCredits: {__credits__}\n" + \
			f"Maintainer: {__maintainer__}\nStatus: {__status__}\n" + \
			f"E-Mail: {__email__}\nContacts: {__contact__}"

workdir = str(pathlib.Path(sys.argv[0]).resolve().parent)
if workdir.endswith('/'):
		workdir = workdir[:-1]
blacklist_name = 'ip-blacklist.json'
whitelist_name = 'ip-whitelist.json'
json_black = pathlib.Path(f"{workdir}").resolve().joinpath(blacklist_name)
json_white = pathlib.Path(f"{workdir}").resolve().joinpath(whitelist_name)

blackwhite_name = 'ip-blackwhite.json'
blackwhite_file = pathlib.Path(f"{workdir}").resolve().joinpath(blackwhite_name)

script_name = pathlib.Path(sys.argv[0]).resolve().name
script_full = f"{workdir}/{script_name}"
script_tmp = f"{workdir}/tmpfile"

log_name = 'blacklist_log.log'
log_file = pathlib.Path(f"{workdir}").resolve().joinpath(log_name)

log_activity_name = 'blacklist_activity.log'
log_activity_file = pathlib.Path(f"{workdir}").resolve().joinpath(log_activity_name)

service_text = ''
st1 = '''[Unit]
Description=Blacklist service for banning and unbanning ip addresses of subnets.
Wants=fail2ban.service
After=fail2ban.service

[Service]
Type=oneshot
RemainAfterExit=yes'''
st2 = "ExecStart=blacklist"
st3 = "-c %i service -start"
st4 = "ExecStop=blacklist"
st5 = "-c %i service -stop"
st6 = "ExecReload=blacklist"
st7 = "-c %i service -reload"
st8 = "[Install]"
st9 = "WantedBy=multi-user.target"

timer_text = '''[Unit]
Description=Blacklist timer for banning and unbanning ip addresses of subnets.
Wants=fail2ban.service
After=fail2ban.service

[Timer]
Unit=blacklist@%i.service
OnBootSec=20s
AccuracySec=1s

[Install]
WantedBy=timers.target
'''

systemd_service_file = pathlib.Path('/etc/systemd/system/blacklist@.service').resolve()
systemd_timer_file = pathlib.Path('/etc/systemd/system/blacklist@.timer').resolve()

parser_dict = ""
logger = ""

class Arguments:
	''' Class «Arguments».
	
		Info: A class designed to store command-line values 
				by entering parameters through the «Argparse» module.
		
		Variables: All parameters are entered using the «createParser()» 
					method.
		
		Methods: 
			__getattr__(self, attrname):
				Access to a non-existent variable.
				Used when trying to get a parameter that does not exist. 
				In this case, «None» is returned to the user, instead 
				of an error.
			
			__str__(self):
				For STR Function output paramters.
			
			__repr__(self):
				For Debug Function output paramters.
	'''
	
	__slots__ = ['__dict__']
	
	def __getattr__(self, attrname):
		''' Access to a non-existent variable. '''
		return None

	def __str__(self):
		''' For STR Function output paramters. '''
		except_list = ['']
		#return '\t' + '\n\t'.join(tuple(map(lambda x: f"{x}: {getattr(self, x)}" if not x in except_list else f"", tuple(filter( lambda x: '__' not in x, dir(self))))))
		return '\t' + '\n\t'.join(f"{x}: {getattr(self, x)}" for x in dir(self) if not x in except_list and '__' not in x)
	
	def __repr__(self):
		''' For Debug Function output paramters. '''
		except_list = ['']
		return f"{self.__class__}:\n\t" + \
				'\n\t'.join(f"{x}: {getattr(self, x)}" for x in dir(self) if not x in except_list and '__' not in x)
				#'\n\t'.join(tuple(map(lambda x: f"{x}: {getattr(self, x)}" if not x in except_list else f"", tuple(filter( lambda x: '__' not in x, dir(self))))))

def createParser():
	''' The function of creating a parser with a certain hierarchy 
		of calls. Returns the parser itself and the sub-parser, 
		as well as groups of parsers, if any. '''
	global json_black, json_white, workdir, log_file, log_activity_file
	
	parser = argparse.ArgumentParser(prog=__progname__,description='The Fail2Ban black and white lists in Python.')
	parser.add_argument ('-v', '--version', action='version', version=f'{__progname__} {__version__}',  help='Version.')
	parser.add_argument ('-info', '--info', action='store_true', default=False, help='Information about the author.')
	
	subparsers = parser.add_subparsers(title='Management', description='Management commands.', help='commands help.')
	
	parser_systemd = subparsers.add_parser('systemd', help='Systemd management.')
	parser_systemd.add_argument ('-create', '--create', action='store_true', default=False, help='Create «blacklist@.service» and «blacklist@.timer».')
	parser_systemd.add_argument ('-delete', '--delete', action='store_true', default=False, help='Delete «blacklist@.service» and «blacklist@.timer».')
	parser_systemd.add_argument ('-status', '--status', action='store_true', default=False, help='Status «blacklist@.service».')
	parser_systemd.add_argument ('-istimer', '--istimer', action='store_true', default=False, help='Check the active and enabled is «blacklist@.timer».')
	parser_systemd.add_argument ('-isservice', '--isservice', action='store_true', default=False, help='Check the active and enabled is «blacklist@.service».')
	parser_systemd.add_argument ('-enable', '--enable', action='store_true', default=False, help='Enable «blacklist@.timer».')
	parser_systemd.add_argument ('-disable', '--disable', action='store_true', default=False, help='Disable «blacklist@.timer».')
	parser_systemd.add_argument ('-start', '--start', action='store_true', default=False, help='Start «blacklist@.service».')
	parser_systemd.add_argument ('-stop', '--stop', action='store_true', default=False, help='Stop «blacklist@.service».')
	parser_systemd.add_argument ('-reload', '--reload', action='store_true', default=False, help='Reload «blacklist@.service».')
	parser_systemd.add_argument ('-starttimer', '--starttimer', action='store_true', default=False, help='Start «blacklist@.timer».')
	parser_systemd.add_argument ('-stoptimer', '--stoptimer', action='store_true', default=False, help='Stop «blacklist@.timer».')
	parser_systemd.set_defaults(onlist='systemd')	
	
	parser_service = subparsers.add_parser('service', help='Program management.')
	parser_service.add_argument ('-start', '--start', action='store_true', default=False, help='Launching the blacklist.')
	parser_service.add_argument ('-stop', '--stop', action='store_true', default=False, help='Stopping the blacklist.')
	parser_service.add_argument ('-nostop', '--nostop', action='store_true', default=False, help='Stopping the blacklist without clearing {IP,IP6,NF}TABLES.')
	parser_service.add_argument ('-reload', '--reload', action='store_true', default=False, help='Restarting the blacklist.')
	parser_service.add_argument ('-show', '--show', action='store_true', default=False, help='Show the status of NETFILTER tables in a given chain.')
	parser_service.add_argument ('-parent', '--parent', action='store_true', default=False, help='Viewing the parent. Only for NFTABLES.')
	parser_service.add_argument ('-tb', '--tb', action='store_true', default=False, help='View a list of available tables.')
	parser_service.add_argument ('-link', '--link', action='store_true', default=False, help='Symlink to program on «/usr/bin/».')
	parser_service.add_argument ('-unlink', '--unlink', action='store_true', default=False, help='Unlink to program on «/usr/bin/».')
	parser_service.add_argument("-name", '--name', dest="name", metavar='NAME', type=str, default='blacklist', help='The name of the symlink for the location in the programs directory is «/usr/bin/». (Default "blacklist").')
	parser_service.add_argument("-grep", '--grep', dest="grep", metavar='GREP', type=str, default='', help='Filtering Netfilter output according to the specified regular expression.')
	parser_service.set_defaults(onlist='service')
	
	parser_blist = subparsers.add_parser('black', help='Managing blacklists.')
	parser_blist.add_argument ('-ban', '--ban', action='store_true', default=False, help='Block IP addresses in {IP,IP6,NF}TABLES.')
	parser_blist.add_argument ('-unban', '--unban', action='store_true', default=False, help='Unblock IP addresses in {IP,IP6,NF}TABLES.')
	parser_blist.add_argument ('-a', '--add', action='store_true', default=False, help='Add to the blacklist.')
	parser_blist.add_argument ('-d', '--delete', action='store_true', default=False, help='Remove from the blacklist.')
	parser_blist.add_argument ('-s', '--show', action='store_true', default=False, help='Read the blacklist.')
	parser_blist.add_argument ('-j', '--json', action='store_true', default=False, help='JSON fromat show.')
	parser_blist.add_argument("-indent", '--indent', metavar='INDENT', type=int, default=2, help='JSON indent (Default: 2).')
	parser_blist.add_argument ('-save', '--save', action='store_true', default=False, help='Save show info.')
	parser_blist.add_argument("-o", '--output', dest="output", metavar='OUTPUT', type=str, default=f"{json_black}", help='Output blacklist file.')
	parser_blist.add_argument ('-empty', '--empty', action='store_true', default=False, help='Clear the blacklist. Use carefully!')
	parser_blist.set_defaults(onlist='black')
	
	pgroup1 = parser_blist.add_argument_group('Addressing', 'IP address management.')
	pgroup1.add_argument("-ip", '--ip', metavar='IP', type=str, default=[], nargs='+', help='IP addresses.')
	pgroup1.add_argument("-m", '--mask', dest="mask", metavar='MASK', type=int, default=[], nargs='+', help='Network Masks.')
	
	parser_wlist = subparsers.add_parser('white', help='Managing whitelists.')
	parser_wlist.add_argument ('-ban', '--ban', action='store_true', default=False, help='Allow ip addresses in {IP,IP6,NF}TABLES.')
	parser_wlist.add_argument ('-unban', '--unban', action='store_true', default=False, help='Remove permissions from {IP,IP6,NF}TABLES.')
	parser_wlist.add_argument ('-a', '--add', action='store_true', default=False, help='Add to the whitelist.')
	parser_wlist.add_argument ('-d', '--delete', action='store_true', default=False, help='Remove from the whitelist.')
	parser_wlist.add_argument ('-s', '--show', action='store_true', default=False, help='Read the whitelist.')
	parser_wlist.add_argument ('-j', '--json', action='store_true', default=False, help='JSON fromat show.')
	parser_wlist.add_argument("-indent", '--indent', metavar='INDENT', type=int, default=2, help='JSON indent (Default: 2).')
	parser_wlist.add_argument ('-save', '--save', action='store_true', default=False, help='Save show info.')
	parser_wlist.add_argument("-o", '--output', dest="output", metavar='OUTPUT', type=str, default=f"{json_white}", help='Output whitelist file.')
	parser_wlist.add_argument ('-empty', '--empty', action='store_true', default=False, help='Clear the whitelist. Use carefully!')
	parser_wlist.set_defaults(onlist='white')
	
	pgroup2 = parser_wlist.add_argument_group('Addressing', 'IP address management.')
	pgroup2.add_argument("-ip", '--ip', metavar='IP', type=str, default=[], nargs='+', help='IP addresses.')
	pgroup2.add_argument("-m", '--mask', dest="mask", metavar='MASK', type=int, default=[], nargs='+', help='Network Masks.')
	
	group1 = parser.add_argument_group('Parameters', 'Settings for the number of bans.')
	group1.add_argument("-c", '--count', dest="count", metavar='COUNT', type=int, default=0, help='The number of locks after which the ip-address is entered in {IP,IP6,NF}TABLES (default 0).')
	group1.add_argument("-q", '--quantity', dest="quantity", metavar='QUANTITY', type=int, default=0, help='The number of ip address locks to be saved (default 0).')
	
	group2 = parser.add_argument_group('Files', 'Working with files.')
	group2.add_argument("-wd", '--workdir', dest="workdir", metavar='WORKDIR', type=str, default=f"{workdir}", help='Working directory.')
	group2.add_argument("-b", '--blacklist', dest="blacklist", metavar='BLACKLIST', type=str, default=f"{json_black}", help='Input blacklist file.')
	group2.add_argument("-w", '--whitelist', dest="whitelist", metavar='WHITELIST', type=str, default=f"{json_white}", help='Input whitelist file.')
	
	group3 = parser.add_argument_group('NFTABLES', 'Configuration NFTABLES.')
	group3.add_argument ('-personal', '--personal', action='store_true', default=False, help='Personal settings of NFTABLES tables, regardless of the data entered.')
	group3.add_argument ('-e', '-exit', '--exit', action='store_true', default=False, help='Finish creating the table/chain on NFTABLES.')
	group3.add_argument ('-run', '--run', action='store_true', default=False, help='Full starting NFTABLES tables from all settings. Use carefully!')
	group3.add_argument ('-fine', '--fine', action='store_true', default=False, help='Full clearing NFTABLES tables from all settings. Use carefully!')
	group3.add_argument("-net", "-network", '--network', dest="network", metavar='NETWORK', type=str, default='', help='The name of the interface through which the processed packet should be received. That is, the input network interface.')
	group3.add_argument ('-ipv6', '--ipv6', action='store_true', default=False, help='Forced IPV6 protocol selection.')
	group3.add_argument ('-nft', '--nftables', action='store_true', default=False, help='Select the NFTABLES framework (Default IP(6)TABLES).')
	group3.add_argument("-nftproto", '--nftproto', default='ip', choices=['ip', 'ip6', 'inet'], help='Select the protocol NFTABLES, before rule (Auto ipv4 on "ip" or -ipv6 to "ip6").')
	group3.add_argument("-table", '--table', dest="table", metavar='TABLE', type=str, default='filter', help='Select the table for NFTABLES (Default "filter").')
	group3.add_argument("-chain", '--chain', dest="chain", metavar='CHAIN', type=str, default='INPUT', help='Choosing a chain of rules (Default: "INPUT").')
	group3.add_argument ('-newtable', '--newtable', action='store_true', default=False, help='Add a new table in NFTABLES. Use carefully!')
	group3.add_argument ('-newchain', '--newchain', action='store_true', default=False, help='Add a new chain in NFTABLES. Use carefully!')
	group3.add_argument ('-Deltable', '--Deltable', action='store_true', default=False, help='Del the table in NFTABLES. Use carefully!')
	group3.add_argument ('-Delchain', '--Delchain', action='store_true', default=False, help='Del the chain in NFTABLES. Use carefully!')
	group3.add_argument ('-cleartable', '--cleartable', action='store_true', default=False, help='Clear the table in NFTABLES. Use carefully!')
	group3.add_argument ('-clearchain', '--clearchain', action='store_true', default=False, help='Clear the chain in NFTABLES. Use carefully!')
	
	parser_activity = subparsers.add_parser('active', help='Activity in log files.')
	parser_activity.add_argument("-filelog", '--filelog', dest="filelog", metavar='FILELOG', type=str, default=f"{log_activity_file}", help='The log file in which the activity of ip addresses from the blacklist is recorded.')
	parser_activity.add_argument("-search", '--search', metavar='SEARCH', type=str, default=[], nargs='+', help='List the log files in which to search for the activity of blacklist ip addresses, according to the specified number of locks.')
	parser_activity.add_argument ('-empty', '--empty', action='store_true', default=False, help='Clear the log file of ip addresses activity from the blacklist.')
	parser_activity.add_argument ('-s', '--show', action='store_true', default=False, help='View the activity log file, which records the activity of ip addresses according to the specified number of locks.')
	parser_activity.add_argument ('-save', '--save', action='store_true', default=False, help='Save show info.')
	parser_activity.add_argument("-o", '--output', dest="output", metavar='OUTPUT', type=str, default='', help='Save show info to file.')
	parser_activity.add_argument("-grep", '--grep', dest="grep", metavar='GREP', type=str, default='', help='Filtering the output of the ip addreses activity log according to the specified regular expression.')
	parser_activity.set_defaults(onlist='activity')
	
	pgroup3 = parser_activity.add_argument_group('Addressing', 'IP address management.')
	pgroup3.add_argument("-ip", '--ip', metavar='IP', type=str, default=[], nargs='+', help='IP addresses.')
	
	group4 = parser.add_argument_group('Settings', 'Configurations.')
	group4.add_argument("-con", '--console', dest="console", metavar='CONSOLE', type=str, default='sh', help='Enther the console name (Default "sh").')
	group4.add_argument ('-cmd', '--cmd', action='store_true', default=False, help='View the command and exit the program without executing it.')
	group4.add_argument ('-lslan', '--lslan', action='store_true', default=False, help='View a list of network interfaces.')
	group4.add_argument ('-sd', '--showdir', action='store_true', default=False, help='Show working directory.')
	group4.add_argument("-logfile", '--logfile', dest="logfile", metavar='LOGFILE', type=str, default=f"{log_file}", help='Log file.')
	group4.add_argument ('-nolog', '--nolog', action='store_false', default=True, help="Do not log events.")
	group4.add_argument ('-limit', '--limit', action='store_true', default=False, help='Limit the log file. Every day the contents of the log will be completely erased.')
	group4.add_argument ('-viewlog', '--viewlog', action='store_true', default=False, help='View the log file.')
	group4.add_argument ('-latest', '--latest', action='store_true', default=False, help='Output everything from the log by the last record date.')
	group4.add_argument("-fil", "-filtering", '--filtering', dest="filtering", metavar='FILTERING', type=str, default='', help='Filter the log output.')
	group4.add_argument ('-resetlog', '--resetlog', action='store_true', default=False, help='Reset the log file.')
	
	dict_parser = { 'parser': parser,  'subparsers': subparsers, 
					'parser_service': parser_service, 'parser_systemd': parser_systemd, 
					'parser_blist': parser_blist, 'parser_wlist': parser_wlist,
					'parser_activity': parser_activity,
					'pgroup1': pgroup1, 'pgroup2': pgroup2, 'pgroup3': pgroup3,
					'group1': group1, 'group2': group2, 'group3': group3, 'group4': group4
					}
	return dict_parser

def read_write_json(jfile, typerw, data = dict(), indent: int = 2):
	''' The function of reading and writing JSON objects. '''
	with open(jfile, typerw) as fp:
		if typerw == 'r':
			data = json.load(fp)
			return data
		else:
			json.dump(data, fp, indent=indent)

def read_write_text(onfile, typerw, data = ""):
	''' The function of reading and writing text files. '''
	with open(onfile, typerw) as fp:
		if typerw == 'r':
			data = fp.read()
		else:
			fp.write(data)
	return data

def ip_to_hostname(ip: str) -> str:
	''' Convert an ip address to a domain name. '''
	return socket.getfqdn(ip_no_mask(ip))

def ip_to_net(in_ip, in_mask = 32):	
	''' Convert an ip address to a network address with 
		a subnet via a backslash. '''
	net_ip = ip_no_mask(in_ip)
	out_ip = net_ip + '/' + mask_no_ip(in_ip, in_mask)
	my_host = ipaddress.ip_interface(out_ip)
	out_ip = f"{my_host.network}"
	return out_ip

def ip_no_mask(in_ip) -> str:
	''' Convert an ip address to an address without a network mask. '''
	return str(in_ip).split('/', 1)[0]

def mask_no_ip(in_ip, in_mask = 32) -> str:
	''' Get an ip address mask or assign a predefined value 
		or default value. '''
	if '/' in str(in_ip):
		net_mask = str(in_ip).split('/', 1)[1]
	else:
		net_mask = in_mask
	return str(net_mask)

def ip_to_version(in_ip, in_mask = 32):
	''' Convert ip address to version.'''
	net_ip = ip_no_mask(in_ip)
	out_ip = net_ip + '/' + mask_no_ip(in_ip, in_mask)
	my_version = ipaddress.ip_interface(out_ip)
	out_vers = f"{my_version.version}"
	return int(out_vers)

def shell_run(shell: str, cmd: str) -> str:
	''' Execute the command in the specified command shell. 
		Returns the result of executing the command, if any.'''
	proc = subprocess.Popen(shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
	sys.stdout.flush()
	proc.stdin.write(cmd + "\n")
	proc.stdin.close()
	out_data = f"{proc.stdout.read()}"
	err_data = f"{proc.stderr.read()}"
	# Close the 'Popen' process correctly
	proc.terminate()
	proc.kill()
	return out_data, err_data

def read_one_list(filelist):
	''' Read the one json files, if they are missing, 
		replace them with an empty dictionary. '''
	current_file = pathlib.Path(f"{filelist}").resolve()
	if current_file.exists():
		json_obj = read_write_json(current_file, 'r')
	else:
		json_obj = dict()
	return json_obj

def read_list(args: Arguments):
	''' Read the input json files, if they are missing, 
		replace them with an empty dictionary. '''
	args.blacklist_json = read_one_list(args.blacklist)
	args.whitelist_json = read_one_list(args.whitelist)

def read_blackwhite(args: Arguments):
	''' Read the blackwhite list security. '''
	args.blackwhite_json = read_one_list(args.blackwhite_file)

def add_dell_one_blackwhite(args: Arguments):
	''' Add or dell the blackwhite list security. '''
	if args.add:
		args.blackwhite_json[args.current_ip] = args.onlist
	else:
		if args.blackwhite_json.get(args.current_ip):
			del args.blackwhite_json[args.current_ip]

def check_blackwhite(args: Arguments):
	''' Check the blackwhite list security. '''
	args.blackwhite_diff = dict()
	for k, v in args.blackwhite_json.items():
		if v == 'white':
			if not k in args.whitelist_json.keys():
				args.blackwhite_diff[k] = v
		elif v == 'black':
			if not k in args.blacklist_json.keys():
				args.blackwhite_diff[k] = v

def unban_blackwhite(args: Arguments):
	''' Unban the blackwhite list security. '''
	args.bw_add = args.add
	args.add = False
	args.bw_list = args.onlist
	for k, v in args.blackwhite_diff.items():
		args.onlist = v
		args.current_ip = f"{k}"
		args.current_version = ip_to_version(args.current_ip, args.maxmask)
		if args.current_version == 6 and not args.ipv6:
			args4_to_args6(args)
		if not args.nftables:
			ban_unban_one(args)
		else:
			nft_ban_unban_one(args)
		if args.ischange:
			args6_to_args4(args)
	args.current_ip = None
	args.onlist = args.bw_list
	args.add = args.bw_add
	args.bw_add = None
	args.bw_list = None

def write_blackwhite(args: Arguments):
	''' Write the blackwhite list security. '''
	read_write_json(args.blackwhite_file, 'w', args.blackwhite_json)

def show_json(jobj: dict, counter: int = 0):
	''' Viewing a json object according to the specified criteria. '''
	if counter == 0:
		return tuple(f"{x}: {y}" for x, y in jobj.items())
	else:
		return tuple(f"{x}" for x,y in jobj.items() if y >= counter)

def search_handle(text: str, in_ip):
	count = 0
	rez = -1
	nomask = ip_no_mask(in_ip)
	for elem in text.split('\n'):
		if nomask in elem:
			rez = count
		count += 1
	if rez != -1:
		return text.split('\n')[rez].split(' ')[-1]
	else:
		return None

def nft_ban_unban_one(args: Arguments):
	''' NFTABLES ban or unban one ip address. '''
	
	global logger
	
	def banunban_nohost(not_found: str):
		''' A single team is banned and disbanded. '''
		global logger
		nonlocal comm
		nonlocal mess
		nonlocal on_handle
		nonlocal args
		comm = switch_cmds(args.onlist).get(str(args.add), not_found)
		mess = switch_messages(args.onlist).get(str(args.add), not_found)
		if not args.ipv6:
			on_handle = search_handle(args.iptables_info, args.current_ip)
			service_info, err = shell_run(args.console, switch_nftables(args, comm, on_handle))
		else:
			on_handle = search_handle(args.ip6tables_info, args.current_ip)
			service_info, err = shell_run(args.console, switch_nftables(args, comm, on_handle))
		if service_info != '':
			print(f"{service_info}")
		if args.nolog:
			if service_info != '':
				logger.info(f"{service_info}")
			if err != '':
				_commands = switch_nftables(args, comm, on_handle)
				logger.error(f"{err}{_commands}")
			else:
				logger.info(f"* {mess} {args.current_ip}")
		if err == '':
			print(f"* {mess} {args.current_ip}")
		else:
			print(f"{err}{_commands}")
	
	nomask = ip_no_mask(args.current_ip)
	comm = ''
	mess = ''
	on_handle = ''
	if args.add:
		if not args.ipv6:
			if not nomask in args.iptables_info:
				banunban_nohost('add-black')
				add_dell_one_blackwhite(args)
		else:
			if not nomask in args.ip6tables_info:
				banunban_nohost('add-black')
				add_dell_one_blackwhite(args)
	else:
		if not args.ipv6:
			if nomask in args.iptables_info:
				banunban_nohost('del-black')
				add_dell_one_blackwhite(args)
		else:
			if nomask in args.ip6tables_info:
				banunban_nohost('del-black')
				add_dell_one_blackwhite(args)

def ban_unban_one(args: Arguments):
	''' Ban or unban one ip address. '''
	
	global logger
	
	def banunban_host_nohost(not_found: str, ishostname: bool):
		''' A single team is banned and disbanded. '''
		global logger
		nonlocal hostname
		nonlocal nomask
		nonlocal args
		nonlocal hostname
		nonlocal comm
		comm = switch_cmds(args.onlist).get(str(args.add), not_found)
		mess = switch_messages(args.onlist).get(str(args.add), not_found)
		service_info, err = shell_run(args.console, switch_iptables(args, comm))
		if args.nolog:
			if service_info != '':
				logger.info(f"{service_info}")
			if err != '':
				_commands = switch_iptables(args, comm)
				logger.error(f"{err}{_commands}")
			else:
				logger.info(f"* {mess} {args.current_ip}")
		if err == '':
			print(f"* {mess} {args.current_ip}")
		else:
			print(f"{err}{_commands}")
	
	def quastion_hostname_nomask(not_found: str):
		''' The issue of processing a domain name 
			during a ban or unban. '''
		nonlocal hostname
		nonlocal nomask
		nonlocal args
		nonlocal hostname
		nonlocal comm
		if hostname != nomask:
			if not args.ipv6:
				if not hostname in args.iptables_info:
					banunban_host_nohost(not_found, True)
					add_dell_one_blackwhite(args)
			else:
				if not hostname in args.ip6tables_info:
					banunban_host_nohost(not_found, True)
					add_dell_one_blackwhite(args)
		else:
			banunban_host_nohost(not_found, False)
			add_dell_one_blackwhite(args)
	
	nomask = ip_no_mask(args.current_ip)
	hostname = ip_to_hostname(nomask)
	comm = ''
	if not args.ipv6:
		if args.add:
			if not nomask in args.iptables_info:
				quastion_hostname_nomask('add-black')
		else:
			if nomask in args.iptables_info:
				quastion_hostname_nomask('del-black')
			else:
				if hostname != nomask:
					if hostname in args.iptables_info:
						banunban_host_nohost('del-black', True)
						add_dell_one_blackwhite(args)
	else:
		if args.add:
			if not nomask in args.ip6tables_info:
				quastion_hostname_nomask('add-black')
		else:
			if nomask in args.ip6tables_info:
				quastion_hostname_nomask('del-black')
			else:
				if hostname != nomask:
					if hostname in args.ip6tables_info:
						banunban_host_nohost('del-black', True)
						add_dell_one_blackwhite(args)

def args4_to_args6(args: Arguments):
	''' Convert args ipv4 to ipv6. '''
	if not args.ipv6:
		args.ischange = True
		if args.nftproto != 'inet':
			args.nftproto = 'ip6'
		args.ipv6 = True
		if not args.nftables:
			args.protocol = 'iptables' if not args.ipv6 else 'ip6tables'
		else:
			args.protocol = 'ip' if not args.ipv6 else 'ip6'
		minmaxmask(args)

def args6_to_args4(args: Arguments):
	''' Convert args ipv6 to ipv4. '''
	if args.ipv6:
		args.ischange = False
		if args.nftproto != 'inet':
			args.nftproto = 'ip'
		args.ipv6 = False
		if not args.nftables:
			args.protocol = 'iptables' if not args.ipv6 else 'ip6tables'
		else:
			args.protocol = 'ip' if not args.ipv6 else 'ip6'
		minmaxmask(args)

def minmaxmask(args: Arguments):
	''' Edit min max mask on protocol. '''
	if not args.ipv6:
		args.minmask = 1
		args.maxmask = 32
	else:
		args.minmask = 1
		args.maxmask = 128

def cicle_list(data_list, current_list, isadd: bool, args: Arguments):
		''' A cycle of identical operations for different lists on 
			blacklist or whitelist to servicework. '''
		args.curr_list = args.onlist
		args.onlist = current_list
		args.isadd = args.add
		args.add = isadd
		for elem in range(len(data_list)):
			args.current_ip = f"{data_list[elem]}"
			args.current_version = ip_to_version(args.current_ip, args.maxmask)
			if args.current_version == 6 and not args.ipv6:
				args4_to_args6(args)
			if not args.nftables:
				ban_unban_one(args)
			else:
				nft_ban_unban_one(args)
			if args.ischange:
				args6_to_args4(args)
		args.current_ip = None
		args.onlist = args.curr_list
		args.curr_list = None
		args.add = args.isadd
		args.isadd = None

def grep_search(instr, args: Arguments):
	''' Grep search. '''
	outstr = ''
	if args.grep != '':
		regexp = re.compile(args.grep)
		match = re.finditer(regexp, instr)
		if match:
			re_math = [x for x in match if x != '']
			edit_str = '\n'.join(list(map(lambda x: instr[:x.start()].split('\n')[-1] + instr[x.start():].split('\n')[0], re_math)))
			outstr = edit_str
	return outstr

def switch_activity(args: Arguments, case = None):
	''' Selecting a command to execute in the command shell. '''
	return {
			'search': f"sudo cat \"{args.current_log}\" | grep -Ei \"{args.current_ip}\""
	}.get(case, None)

def search_activity(args: Arguments):
	''' Search for activity in logs. '''
	args.old_counts = -1
	if args.count == 0:
		args.old_counts = args.count
		args.count = 1
	data = show_json(args.blacklist_json, args.count) if len(args.ip) == 0 else args.ip
	out_info = ''
	out_err = ''
	out_commands = ''
	if args.cmd:
		for on_log in args.search:
			args.current_log = str(on_log)
			for ip in data:
				args.current_ip = ip_no_mask(ip)
				current_commands = switch_activity(args, 'search')
				print(current_commands)
		if args.old_counts == 0:
			args.count = 0
		args.current_ip = None
		args.current_log = None
		sys.exit(0)
	for on_log in args.search:
		args.current_log = str(on_log)
		for ip in data:
			args.current_ip = ip_no_mask(ip)
			current_commands = switch_activity(args, 'search')
			if current_commands != None:
				service_info, err = shell_run(args.console, current_commands)
				if service_info != '':
					out_commands += f"\n{current_commands}"
					out_info += f"\n{service_info}"
				if err != '':
					out_err += err
	if out_info != '':
		read_write_text(args.filelog, 'a', out_info)
	if out_err != '':
		read_write_text(args.filelog, 'a', f"{out_err}{out_commands}")
	if args.old_counts == 0:
		args.count = 0
	args.current_ip = None
	args.current_log = None

def choice_list_net():
	return f"ls /sys/class/net | xargs"

def switch_iptables(args: Arguments, case = None):
	''' Selecting a command to execute in the command shell. '''
	return {
			'add-white': f"sudo {args.protocol} -t {args.table} -A {args.chain} {args.interfaces} -s {args.current_ip} -j ACCEPT",
			'del-white': f"sudo {args.protocol} -t {args.table} -D {args.chain} {args.interfaces} -s {args.current_ip} -j ACCEPT",
			'add-black': f"sudo {args.protocol} -t {args.table} -A {args.chain} {args.interfaces} -s {args.current_ip} -j DROP",
			'del-black': f"sudo {args.protocol} -t {args.table} -D {args.chain} {args.interfaces} -s {args.current_ip} -j DROP",
			'read': f"sudo {args.protocol} -L {args.chain}",
			'list-net': f"ls /sys/class/net"
	}.get(case, f"sudo {args.protocol} -L {args.chain}")

def switch_nftables(args: Arguments, case = None, handle = None):
	''' Selecting a command to execute NFTABLES in the command shell. '''
	return {
			'add-white': f"sudo nft 'add rule {args.nftproto} {args.table} {args.chain} {args.interfaces} {args.protocol} saddr {args.current_ip} counter accept'",
			'del-white': f"sudo nft delete rule {args.nftproto} {args.table} {args.chain} handle {handle}",
			'add-black': f"sudo nft 'add rule {args.nftproto} {args.table} {args.chain} {args.interfaces} {args.protocol} saddr {args.current_ip} counter drop'",
			'del-black': f"sudo nft delete rule {args.nftproto} {args.table} {args.chain} handle {handle}",
			'read': f"sudo nft list chain {args.nftproto} {args.table} {args.chain}",
			'read-parent': f"sudo nft list table {args.nftproto} {args.table}",
			'read-tables': f"sudo nft list tables",
			'search': f"sudo nft --handle --numeric list chain {args.nftproto} {args.table} {args.chain} | grep -Ei 'ip saddr|# handle'" + \
			''' | sed 's/^[ \t]*//' | awk '!/^$/{print $0}' ''',
			'create-chain': f"nft add chain {args.nftproto} {args.table} {args.chain}" + ''' '{ type filter hook input priority 0; policy accept; }\'''',
			'create-table': f"nft add table {args.nftproto} {args.table}",
			'del-table': f"sudo nft delete table {args.nftproto} {args.table}",
			'del-chain': f"sudo nft delete chain {args.nftproto} {args.table} {args.chain}",
			'flush-table': f"sudo nft flush table {args.nftproto} {args.table}",
			'flush-chain': f"sudo nft flush chain {args.nftproto} {args.table} {args.chain}",
			'list-net': f"ls /sys/class/net"
	}.get(case, f"sudo nft list table {args.nftproto} {args.table}")

def switch_cmds(case = None):
	''' Selecting a command for the «switch_iptables» method. '''
	return {
			'black': {
					'True': 'add-black',
					'False': 'del-black'
					},
			'white': {
					'True': 'add-white',
					'False': 'del-white'
					},
	}.get(case, dict())

def switch_messages(case = None):
	''' Selecting a message to display on the screen. '''
	return {
			'black': {
					'True': 'Ban',
					'False': 'Unban'
				},
			'white': {
					'True': 'Ignore',
					'False': 'Del ignore'
				},
	}.get(case, dict())

def switch_systemd(case = None, counter = 3):
	''' Systemd control selection. '''
	return {
			'status': f"sudo systemctl status blacklist@{counter}.service",
			'start-service': f"sudo systemctl start blacklist@{counter}.service",
			'stop-service': f"sudo systemctl stop blacklist@{counter}.service",
			'enable': f"sudo systemctl enable blacklist@{counter}.timer",
			'disable': f"sudo systemctl disable blacklist@{counter}.timer",
			'start-timer': f"sudo systemctl start blacklist@{counter}.timer",
			'stop-timer': f"sudo systemctl stop blacklist@{counter}.timer",
			'is-timer': f"sudo systemctl is-active blacklist@{counter}.timer",
			'is-service': f"sudo systemctl is-active blacklist@{counter}.service",
			'is-enable-timer': f"sudo systemctl is-enabled blacklist@{counter}.timer",
			'is-enable-service': f"sudo systemctl is-enabled blacklist@{counter}.service"
	}.get(case, f"sudo systemctl status blacklist@{counter}.service")

def AppExit(args: Arguments):
	''' Shutting down the application. '''
	
	show_commands_fine(args)
	
	if args.onlist != 'systemd':
		AppFine(args)
	sys.exit(0)

def show_commands_fine(args: Arguments):
	''' View commands to delete tables and/or chains 
		before exiting the program. '''
	if args.nftables:
		if args.clearchain:
			if args.cmd:
				print(switch_nftables(args, 'flush-chain'))
		if args.Delchain:
			if args.cmd:
				print(switch_nftables(args, 'del-chain'))
		if args.cleartable:
			if args.cmd:
				print(switch_nftables(args, 'flush-table'))
		if args.Deltable:
			if args.cmd:
				print(switch_nftables(args, 'del-table'))
	if args.cmd:
		sys.exit(0)

def AppFine(args: Arguments):
	''' Commands to delete tables and/or chains 
		before exiting the program. '''
	
	global logger
	
	if args.nftables:
		if args.clearchain:
			if (args.table != 'filter') ^ (args.chain != 'INPUT'):
				print(f"Clear the сhain: «{args.chain}», protocol = «{args.nftproto}», tables = {args.tables}».")
				service_info, err = shell_run(args.console, switch_nftables(args, 'flush-chain'))
				if service_info != '':
					print(service_info)
				if err != '':
					_commands = switch_nftables(args, 'flush-chain')
					print(f"{err}{_commands}")
				if args.nolog:
					logger.info(f"Clear the сhain: «{args.chain}», protocol = «{args.nftproto}», tables = {args.tables}».")
					if service_info != '':
						logger.info(service_info)
					if err != '':
						logger.error(f"{err}{_commands}")
				if args.nftproto != 'inet':
					args4_to_args6(args)
					#
					print(f"Clear the сhain: «{args.chain}», protocol = «{args.nftproto}», tables = {args.tables}».")
					service_info, err = shell_run(args.console, switch_nftables(args, 'flush-chain'))
					if service_info != '':
						print(service_info)
					if err != '':
						_commands = switch_nftables(args, 'flush-chain')
						print(f"{err}{_commands}")
					if args.nolog:
						logger.info(f"Clear the сhain: «{args.chain}», protocol = «{args.nftproto}», tables = {args.tables}».")
						if service_info != '':
							logger.info(service_info)
						if err != '':
							logger.error(f"{err}{_commands}")
					#
					args6_to_args4(args)
		if args.Delchain:
			if (args.table != 'filter') ^ (args.chain != 'INPUT'):
				print(f"Delete the сhain: «{args.chain}», protocol = «{args.nftproto}», tables = {args.tables}».")
				service_info, err = shell_run(args.console, switch_nftables(args, 'del-chain'))
				if service_info != '':
					print(service_info)
				if err != '':
					_commands = switch_nftables(args, 'del-chain')
					print(f"{err}{_commands}")
				if args.nolog:
					logger.info(f"Delete the сhain: «{args.chain}», protocol = «{args.nftproto}», tables = {args.tables}».")
					if service_info != '':
						logger.info(service_info)
					if err != '':
						logger.error(f"{err}{_commands}")
				if args.nftproto != 'inet':
					args4_to_args6(args)
					#
					print(f"Delete the сhain: «{args.chain}», protocol = «{args.nftproto}», tables = {args.tables}».")
					service_info, err = shell_run(args.console, switch_nftables(args, 'del-chain'))
					if service_info != '':
						print(service_info)
					if err != '':
						_commands = switch_nftables(args, 'del-chain')
						print(f"{err}{_commands}")
					if args.nolog:
						logger.info(f"Delete the сhain: «{args.chain}», protocol = «{args.nftproto}», tables = {args.tables}».")
						if service_info != '':
							logger.info(service_info)
						if err != '':
							logger.error(f"{err}{_commands}")
					#
					args6_to_args4(args)
		if args.cleartable:
			if args.table != 'filter':
				print(f"Clear the table: «{args.table}», protocol = «{args.nftproto}».")
				service_info, err = shell_run(args.console, switch_nftables(args, 'flush-table'))
				if service_info != '':
					print(service_info)
				if err != '':
					_commands = switch_nftables(args, 'flush-table')
					print(f"{err}{_commands}")
				if args.nolog:
					logger.info(f"Clear the table: «{args.table}», protocol = «{args.nftproto}».")
					if service_info != '':
						logger.info(service_info)
					if err != '':
						logger.error(f"{err}{_commands}")
				if args.nftproto != 'inet':
					args4_to_args6(args)
					#
					print(f"Clear the table: «{args.table}», protocol = «{args.nftproto}».")
					service_info, err = shell_run(args.console, switch_nftables(args, 'flush-table'))
					if service_info != '':
						print(service_info)
					if err != '':
						_commands = switch_nftables(args, 'flush-table')
						print(f"{err}{_commands}")
					if args.nolog:
						logger.info(f"Clear the table: «{args.table}», protocol = «{args.nftproto}».")
						if service_info != '':
							logger.info(service_info)
						if err != '':
							logger.error(f"{err}{_commands}")
					#
					args6_to_args4(args)
		if args.Deltable:
			if args.table != 'filter':
				print(f"Delete the table: «{args.table}», protocol = «{args.nftproto}».")
				service_info, err = shell_run(args.console, switch_nftables(args, 'del-table'))
				if service_info != '':
					print(service_info)
				if err != '':
					_commands = switch_nftables(args, 'del-table')
					print(f"{err}{_commands}")
				if args.nolog:
					logger.info(f"Delete the table: «{args.table}», protocol = «{args.nftproto}».")
					if service_info != '':
						logger.info(service_info)
					if err != '':
						logger.error(f"{err}{_commands}")
				if args.nftproto != 'inet':
					args4_to_args6(args)
					#
					print(f"Delete the table: «{args.table}», protocol = «{args.nftproto}».")
					service_info, err = shell_run(args.console, switch_nftables(args, 'del-table'))
					if service_info != '':
						print(service_info)
					if err != '':
						_commands = switch_nftables(args, 'del-table')
						print(f"{err}{_commands}")
					if args.nolog:
						logger.info(f"Delete the table: «{args.table}», protocol = «{args.nftproto}».")
						if service_info != '':
							logger.info(service_info)
						if err != '':
							logger.error(f"{err}{_commands}")
					#
					args6_to_args4(args)

def service_build(args: Arguments):
	global service_text, st1, st2, st3, st4, st5, st6, st7, st8, st9
		
	service_tmp_text = []
	service_tmp_text.append(st1)
	if args.nftables:
		_nfproto = f"-nftproto {args.nftproto}"
		_tbl = f"-table {args.table}"
		_ch = f"-chain {args.chain}"
		
		if not args.run:
			_ntbl = '-newtable'
			_nch = '-newchain'
		else:
			_ntbl = '-run'
			_nch = ''
		
		if not args.fine:
			_dtbl = '-Deltable' if args.Deltable else ''
			_dch = '-Delchain' if args.Delchain else ''
			_ctbl = '-cleartable' if args.cleartable else ''
			_cch = '-clearchain' if args.clearchain else ''
		else:
			_dtbl = ''
			_dch = ''
			_ctbl = ''
			_cch = '-fine'
		
		_start_var = f"-nft {_nfproto} {_tbl} {_ch}".strip()
		_exec_var = f"{_start_var} {_ntbl} {_nch}".strip()
		_stop_var = f"{_start_var} {_cch} {_dch} {_ctbl} {_dtbl}".strip()
		
		if args.personal:
			start_sv_text = f"-nft -personal"
			stop_sv_text = f"-nft -personal"
			reload_sv_text = f"-nft -personal"
			if args.run:
				start_sv_text = f"{start_sv_text} -run"
			if args.fine:
				stop_sv_text = f"{stop_sv_text} -fine"
		else:
			start_sv_text = f"{_exec_var}"
			stop_sv_text = f"{_stop_var}"
			reload_sv_text = f"{_start_var}"		
	else:
		start_sv_text = f""
		stop_sv_text = f""
		reload_sv_text = f""
	
	service_tmp_text.append(f"{st2} {start_sv_text} {st3}")
	service_tmp_text.append(f"{st4} {stop_sv_text} {st5}")
	service_tmp_text.append(f"{st6} {reload_sv_text} {st7}")
	service_tmp_text.append(st8)
	service_tmp_text.append(st9)	
	service_text = '\n'.join(service_tmp_text) + '\n'

def systemdwork(args: Arguments):
	''' Systemd management. '''
	global service_text, timer_text, systemd_service_file, systemd_timer_file, parser_dict, logger
	
	if args.count == 0:
		args.count = 3
	
	if args.create:
		service_build(args)
		if args.cmd:
			print(f"sudo echo \"{service_text}\" > {systemd_service_file.resolve()}")
			print(f"sudo echo \"{timer_text}\" > {systemd_timer_file.resolve()}")
			sys.exit(0)
		print('Create systemd «blacklist@.service» and «blacklist@.timer».')
		shell_run(args.console, switch_systemd('stop-timer', args.count))
		shell_run(args.console, switch_systemd('stop-service', args.count))
		shell_run(args.console, switch_systemd('disable', args.count))
		read_write_text(systemd_service_file, 'w', service_text)
		read_write_text(systemd_timer_file, 'w', timer_text)
		if args.nolog:
			logger.info(f"Create systemd «blacklist@.service»:\n{service_text}")
			logger.info(f"Create systemd «blacklist@.timer»:\n{timer_text}")
		AppExit(args)
	if args.delete:
		if args.cmd:
			print(switch_systemd('stop-timer', args.count))
			print(switch_systemd('stop-service', args.count))
			print(switch_systemd('disable', args.count))
			print(f"sudo rm -rf {systemd_service_file.resolve()}")
			print(f"sudo rm -rf {systemd_timer_file.resolve()}")
			sys.exit(0)
		print('Delete systemd «blacklist@.service» and «blacklist@.timer».')
		shell_run(args.console, switch_systemd('stop-timer', args.count))
		shell_run(args.console, switch_systemd('stop-service', args.count))
		shell_run(args.console, switch_systemd('disable', args.count))
		systemd_service_file.unlink(missing_ok=True)
		systemd_timer_file.unlink(missing_ok=True)
		if args.nolog:
			logger.info(f"Delete systemd «blacklist@.service» and «blacklist@.timer».")
		AppExit(args)
	if systemd_service_file.exists() and systemd_timer_file.exists():
		if args.status:
			if args.cmd:
				print(switch_systemd('status', args.count))
				sys.exit(0)
			service_info, err = shell_run(args.console, switch_systemd('status', args.count))
			if service_info != '':
				print(f"{service_info}")
			if err != '':
				_commands = switch_systemd('status', args.count)
				print(f"{err}{_commands}")
			sys.exit(0)
		if args.istimer:
			if args.cmd:
				print(switch_systemd('is-timer', args.count))
				print(switch_systemd('is-enable-timer', args.count))
				sys.exit(0)
			service_info, err = shell_run(args.console, switch_systemd('is-timer', args.count))
			if service_info != '':
				print(f"{service_info}")
			if err != '':
				_commands = switch_systemd('is-timer', args.count)
				print(f"{err}{_commands}")
			service_info, err = shell_run(args.console, switch_systemd('is-enable-timer', args.count))
			if service_info != '':
				print(f"{service_info}")
			if err != '':
				_commands = switch_systemd('is-enable-timer', args.count)
				print(f"{err}{_commands}")
			sys.exit(0)
		if args.isservice:
			if args.cmd:
				print(switch_systemd('is-service', args.count))
				print(switch_systemd('is-enable-service', args.count))
				sys.exit(0)
			service_info, err = shell_run(args.console, switch_systemd('is-service', args.count))
			if service_info != '':
				print(f"{service_info}")
			if err != '':
				_commands = switch_systemd('is-service', args.count)
				print(f"{err}{_commands}")
			service_info, err = shell_run(args.console, switch_systemd('is-enable-service', args.count))
			if service_info != '':
				print(f"{service_info}")
			if err != '':
				_commands = switch_systemd('is-enable-service', args.count)
				print(f"{err}{_commands}")
			sys.exit(0)
		if args.enable:
			if args.cmd:
				print(switch_systemd('enable', args.count))
				sys.exit(0)
			print(f"Enable «blacklist@{args.count}.timer».")
			service_info, err = shell_run(args.console, switch_systemd('enable', args.count))
			if service_info != '':
				print(service_info)
			if err != '':
				_commands = switch_systemd('enable', args.count)
				print(f"{err}{_commands}")
			if args.nolog:
				logger.info(f"Enable «blacklist@{args.count}.timer».")
				if service_info != '':
					logger.info(service_info)
				if err != '':
					logger.error(f"{err}{_commands}")
			AppExit(args)
		if args.disable:
			if args.cmd:
				print(switch_systemd('disable', args.count))
				sys.exit(0)
			print(f"Disable «blacklist@{args.count}.timer».")
			service_info, err = shell_run(args.console, switch_systemd('disable', args.count))
			if service_info != '':
				print(service_info)
			if err != '':
				_commands = switch_systemd('disable', args.count)
				print(f"{err}{_commands}")
			if args.nolog:
				logger.info(f"Disable «blacklist@{args.count}.timer».")
				if service_info != '':
					logger.info(service_info)
				args.log_txt.append(f"Exit the blacklist ...")
				if err != '':
					logger.error(f"{err}{_commands}")
			AppExit(args)
		if args.start:
			if args.cmd:
				print(switch_systemd('start-service', args.count))
				sys.exit(0)
			print(f"Start «blacklist@{args.count}.service».")
			service_info, err = shell_run(args.console, switch_systemd('start-service', args.count))
			if service_info != '':
				print(service_info)
			if err != '':
				_commands = switch_systemd('start-service', args.count)
				print(f"{err}{_commands}")
			if args.nolog:
				logger.info(f"Start «blacklist@{args.count}.service».")
				if service_info != '':
					logger.info(service_info)
				if err != '':
					logger.error(f"{err}{_commands}")
			AppExit(args)
		if args.stop:
			if args.cmd:
				print(switch_systemd('stop-service', args.count))
				sys.exit(0)
			print(f"Stop «blacklist@{args.count}.service».")
			service_info, err = shell_run(args.console, switch_systemd('stop-service', args.count))
			if service_info != '':
				print(service_info)
			if err != '':
				_commands = switch_systemd('stop-service', args.count)
				print(f"{err}{_commands}")
			if args.nolog:
				logger.info(f"Stop «blacklist@{args.count}.service».")
				if service_info != '':
					logger.info(service_info)
				args.log_txt.append(f"Exit the blacklist ...")
				if err != '':
					logger.error(f"{err}{_commands}")
			AppExit(args)
		if args.reload:
			if args.cmd:
				print(switch_systemd('stop-service', args.count))
				print(switch_systemd('start-service', args.count))
				sys.exit(0)
			# Stop
			print(f"Reload «blacklist@{args.count}.service».")
			service_info, err = shell_run(args.console, switch_systemd('stop-service', args.count))
			if service_info != '':
				print(service_info)
			if err != '':
				_commands = switch_systemd('stop-service', args.count)
				print(f"{err}{_commands}")
			if args.nolog:
				logger.info(f"Reload «blacklist@{args.count}.service».")
				if service_info != '':
					logger.info(service_info)
				if err != '':
					logger.error(f"{err}{_commands}")
			# Start
			print(f"Reload «blacklist@{args.count}.service».")
			service_info, err = shell_run(args.console, switch_systemd('start-service', args.count))
			if service_info != '':
				print(service_info)
			if err != '':
				_commands = switch_systemd('start-service', args.count)
				print(f"{err}{_commands}")
			if args.nolog:
				logger.info(f"Reload «blacklist@{args.count}.service».")
				if service_info != '':
					logger.info(service_info)
				if err != '':
					logger.error(f"{err}{_commands}")
			AppExit(args)
		if args.starttimer:
			if args.cmd:
				print(switch_systemd('start-timer', args.count))
				sys.exit(0)
			print(f"Start «blacklist@{args.count}.timer».")
			service_info, err = shell_run(args.console, switch_systemd('start-timer', args.count))
			if service_info != '':
				print(service_info)
			if err != '':
				_commands = switch_systemd('start-timer', args.count)
				print(f"{err}{_commands}")
			if args.nolog:
				logger.info(f"Start «blacklist@{args.count}.timer».")
				if service_info != '':
					logger.info(service_info)
				if err != '':
					logger.error(f"{err}{_commands}")
			AppExit(args)
		if args.stoptimer:
			if args.cmd:
				print(switch_systemd('stop-timer', args.count))
				sys.exit(0)
			print(f"Stop «blacklist@{args.count}.timer».")
			service_info, err = shell_run(args.console, switch_systemd('stop-timer', args.count))
			if service_info != '':
				print(service_info)
			if err != '':
				_commands = switch_systemd('stop-timer', args.count)
				print(f"{err}{_commands}")
			if args.nolog:
				logger.info(f"Stop «blacklist@{args.count}.timer» ...")
				if service_info != '':
					logger.info(service_info)
				if err != '':
					logger.error(f"{err}{_commands}")
			AppExit(args)
	else:
		print(f"\nSystemd file «{systemd_service_file.name}» and «{systemd_timer_file.name}» not found!")
		print(f"Please enter «-create» to create system files before accessing Systemd functions!\n")
	if not args.log_txt:
		parser_dict['parser'].parse_args(['systemd', '-h'])
		sys.exit(0)

def servicework(args: Arguments):
	''' Processing of service commands. '''
	global script_full, script_name, script_tmp, parser_dict
	global logger
	
	def service_start_stop(args: Arguments):
		''' Launching or stopping the blacklist service. '''
		data_white = show_json(args.whitelist_json, 1)
		data_black = show_json(args.blacklist_json, args.count)
		cicle_list(data_white, 'white', args.add, args)
		cicle_list(data_black, 'black', args.add, args)
		args.current_ip = None
		args.onlist = None
		args.add = None
	
	CreateTableChain(args)
	
	read_list(args)
	args.add = args.start
	if args.count == 0:
		args.count = 3
	
	if args.link:
		script_full = pathlib.Path(f"{script_full}").resolve()
		script_usr_bin = pathlib.Path(f"/usr/bin/{args.name}").resolve()
		if args.cmd:
			print(f"sudo ln -s {script_full} {script_usr_bin}")
			print(f"sudo chmod +x {script_usr_bin}")
			sys.exit(0)
		print(f"Cryate the symlink to program on «/usr/bin/{args.name}».")
		shell_run(args.console, f"sudo ln -s {script_full} {script_usr_bin}")
		shell_run(args.console, f"sudo chmod +x {script_usr_bin}")
		if args.nolog:
			logger.info(f"Cryate the symlink to program on /usr/bin/{args.name}")
		AppExit(args)
	if args.unlink:
		src1 = pathlib.Path(script_full).resolve()
		src2 = pathlib.Path(script_tmp).resolve()
		if args.cmd:
			print(f"sudo mv {src1} {src2}")
			print(f"sudo rm -rf /usr/bin/{args.name}")
			print(f"sudo mv {src2} {src1}")
			sys.exit(0)
		print(f"Delete the symlink to program on «/usr/bin/{args.name}».")
		src1.rename(src2)
		shell_run(args.console, f"sudo rm -rf /usr/bin/{args.name}")
		src2.rename(src1)
		if args.nolog:
			logger.info(f"Delete the symlink to program on «/usr/bin/{args.name}».")
		AppExit(args)
	if args.show:
		if not args.nftables:
			if args.cmd:
				print(switch_iptables(args, 'read'))
				sys.exit(0)
			args.iptables_info, err = shell_run(args.console, switch_iptables(args, 'read'))
			if args.grep != '':
				grep_str = grep_search(args.iptables_info, args)
				if grep_str != '':
					args.iptables_info = grep_str
			if args.iptables_info != '':
				print(f"{args.iptables_info}")
			if err != '':
				_commands = switch_iptables(args, 'read')
				print(f"{err}{_commands}")
		else:
			if args.cmd:
				if args.parent:
					print(switch_nftables(args, 'read-parent'))
				elif args.tb:
					print(switch_nftables(args, 'read-tables'))
				else:
					print(switch_nftables(args, 'read'))
				sys.exit(0)
			if args.parent:
				args.iptables_info, err = shell_run(args.console, switch_nftables(args, 'read-parent'))
			elif args.tb:
				args.iptables_info, err = shell_run(args.console, switch_nftables(args, 'read-tables'))
			else:
				args.iptables_info, err = shell_run(args.console, switch_nftables(args, 'read'))
			if args.grep != '':
				grep_str = grep_search(args.iptables_info, args)
				if grep_str != '':
					args.iptables_info = grep_str
			if args.iptables_info != '':
				print(f"{args.iptables_info}")
			if err != '':
				if args.parent:
					_commands = switch_nftables(args, 'read-parent')
				elif args.tb:
					_commands = switch_nftables(args, 'read-tables')
				else:
					_commands = switch_nftables(args, 'read')
				print(f"{err}{_commands}")
		sys.exit(0)
	if args.start:
		if args.cmd:
			args.current_ip = 'ip/mask'
			if not args.nftables:
				print(switch_iptables(args, 'read'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_iptables(args, 'add-white'))
				print('\t',switch_iptables(args, 'add-black'))
				args4_to_args6(args)
				print(switch_iptables(args, 'read'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_iptables(args, 'add-white'))
				print('\t',switch_iptables(args, 'add-black'))
				args6_to_args4(args)
			else:
				print(switch_nftables(args, 'search').replace('\t','\\t'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_nftables(args, 'add-white', 'NUM'))
				print('\t',switch_nftables(args, 'add-black', 'NUM'))
				if not args.ipv6 and args.nftproto != 'inet':
					args4_to_args6(args)
					print(switch_nftables(args, 'search').replace('\t','\\t'))
					print('Repeat commands for all ip addresses:')
					print('\t',switch_nftables(args, 'add-white', 'NUM'))
					print('\t',switch_nftables(args, 'add-black', 'NUM'))
					args6_to_args4(args)
			sys.exit(0)
		print('Start the blacklist ...')
		if not args.nftables:
			args.iptables_info, err = shell_run(args.console, switch_iptables(args, 'read'))
			_commands = switch_iptables(args, 'read')
			args4_to_args6(args)
			args.ip6tables_info, err6 = shell_run(args.console, switch_iptables(args, 'read'))
			_commands6 = switch_iptables(args, 'read')
			args6_to_args4(args)
		else:
			args.iptables_info, err = shell_run(args.console, switch_nftables(args, 'search'))
			_commands = switch_nftables(args, 'search').replace('\t','\\t')
			if not args.ipv6 and args.nftproto != 'inet':
				args4_to_args6(args)
				args.ip6tables_info, err6 = shell_run(args.console, switch_nftables(args, 'search'))
				_commands6 = switch_nftables(args, 'search').replace('\t','\\t')
				args6_to_args4(args)
			else:
				args.ip6tables_info, err6, _commands6 = args.iptables_info, err, _commands
		if args.nolog:
			logger.info('Start the blacklist ...')
		service_start_stop(args)
		if err != '':
			print(f"{err}{_commands}")
		if err6 != '':
			print(f"{err6}{_commands6}")
		if args.nolog:
			if err != '':
				logger.error(f"{err}{_commands}")
			if err6 != '':
				logger.error(f"{err6}{_commands6}")
		check_blackwhite(args)
		unban_blackwhite(args)
		write_blackwhite(args)
		AppExit(args)
	if args.stop:
		if args.cmd:
			args.current_ip = 'ip/mask'
			if not args.nftables:
				print(switch_iptables(args, 'read'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_iptables(args, 'del-white'))
				print('\t',switch_iptables(args, 'del-black'))
				args4_to_args6(args)
				print(switch_iptables(args, 'read'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_iptables(args, 'del-white'))
				print('\t',switch_iptables(args, 'del-black'))
				args6_to_args4(args)
			else:
				print(switch_nftables(args, 'search').replace('\t','\\t'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_nftables(args, 'del-white', 'NUM'))
				print('\t',switch_nftables(args, 'del-black', 'NUM'))
				if not args.ipv6 and args.nftproto != 'inet':
					args4_to_args6(args)
					print(switch_nftables(args, 'search').replace('\t','\\t'))
					print('Repeat commands for all ip addresses:')
					print('\t',switch_nftables(args, 'del-white', 'NUM'))
					print('\t',switch_nftables(args, 'del-black', 'NUM'))
					args6_to_args4(args)
			sys.exit(0)
		print('Stopping the blacklist ...')
		if not args.nftables:
			args.iptables_info, err = shell_run(args.console, switch_iptables(args, 'read'))
			_commands = switch_iptables(args, 'read')
			args4_to_args6(args)
			args.ip6tables_info, err6 = shell_run(args.console, switch_iptables(args, 'read'))
			_commands6 = switch_iptables(args, 'read')
			args6_to_args4(args)
		else:
			args.iptables_info, err = shell_run(args.console, switch_nftables(args, 'search'))
			_commands = switch_nftables(args, 'search').replace('\t','\\t')
			if not args.ipv6 and args.nftproto != 'inet':
				args4_to_args6(args)
				args.ip6tables_info, err6 = shell_run(args.console, switch_nftables(args, 'search'))
				_commands6 = switch_nftables(args, 'search').replace('\t','\\t')
				args6_to_args4(args)
			else:
				args.ip6tables_info, err6, _commands6 = args.iptables_info, err, _commands
		if args.nolog:
			logger.info('Stopping the blacklist ...')
		service_start_stop(args)
		if err != '':
			print(f"{err}{_commands}")
		if err6 != '':
			print(f"{err6}{_commands6}")
		if args.nolog:
			if err != '':
				logger.error(f"{err}{_commands}")
			if err6 != '':
				logger.error(f"{err6}{_commands6}")
		check_blackwhite(args)
		unban_blackwhite(args)
		write_blackwhite(args)
		AppExit(args)
	if args.nostop:
		print('No stopped the blacklist.')
		print('Exit the blacklist ...')
		sys.exit(0)
	if args.reload:
		if args.cmd:
			args.current_ip = 'ip/mask'
			if not args.nftables:
				print(switch_iptables(args, 'read'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_iptables(args, 'del-white'))
				print('\t',switch_iptables(args, 'del-black'))
				print(switch_iptables(args, 'read'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_iptables(args, 'add-white'))
				print('\t',switch_iptables(args, 'add-black'))
				args4_to_args6(args)
				print(switch_iptables(args, 'read'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_iptables(args, 'del-white'))
				print('\t',switch_iptables(args, 'del-black'))
				print(switch_iptables(args, 'read'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_iptables(args, 'add-white'))
				print('\t',switch_iptables(args, 'add-black'))
				args6_to_args4(args)
			else:
				print(switch_nftables(args, 'search').replace('\t','\\t'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_nftables(args, 'del-white', 'NUM'))
				print('\t',switch_nftables(args, 'del-black', 'NUM'))
				print(switch_nftables(args, 'search').replace('\t','\\t'))
				print('Repeat commands for all ip addresses:')
				print('\t',switch_nftables(args, 'add-white', 'NUM'))
				print('\t',switch_nftables(args, 'add-black', 'NUM'))
				if not args.ipv6 and args.nftproto != 'inet':
					args4_to_args6(args)
					print(switch_nftables(args, 'search').replace('\t','\\t'))
					print('Repeat commands for all ip addresses:')
					print('\t',switch_nftables(args, 'del-white', 'NUM'))
					print('\t',switch_nftables(args, 'del-black', 'NUM'))
					print(switch_nftables(args, 'search').replace('\t','\\t'))
					print('Repeat commands for all ip addresses:')
					print('\t',switch_nftables(args, 'add-white', 'NUM'))
					print('\t',switch_nftables(args, 'add-black', 'NUM'))
					args6_to_args4(args)
			sys.exit(0)
		print('Reload the blacklist ...')
		if not args.nftables:
			args.iptables_info, err = shell_run(args.console, switch_iptables(args, 'read'))
			_commands = switch_iptables(args, 'read')
			args4_to_args6(args)
			args.ip6tables_info, err6 = shell_run(args.console, switch_iptables(args, 'read'))
			_commands6 = switch_iptables(args, 'read')
			args6_to_args4(args)
		else:
			args.iptables_info, err = shell_run(args.console, switch_nftables(args, 'search'))
			_commands = switch_nftables(args, 'search').replace('\t','\\t')
			if not args.ipv6 and args.nftproto != 'inet':
				args4_to_args6(args)
				args.ip6tables_info, err6 = shell_run(args.console, switch_nftables(args, 'search'))
				_commands6 = switch_nftables(args, 'search').replace('\t','\\t')
				args6_to_args4(args)
			else:
				args.ip6tables_info, err6, _commands6 = args.iptables_info, err, _commands
		if err != '':
			print(f"{err}{_commands}")
		if err6 != '':
			print(f"{err6}{_commands6}")
		if args.nolog:
			logger.info('Reload the blacklist ...')
			if err != '':
				logger.error(f"{err}{_commands}")
			if err6 != '':
				logger.error(f"{err6}{_commands6}")		
		args.add = False
		service_start_stop(args)
		args.add = True
		if not args.nftables:
			args.iptables_info, err = shell_run(args.console, switch_iptables(args, 'read'))
			_commands = switch_iptables(args, 'read')
			args4_to_args6(args)
			args.ip6tables_info, err6 = shell_run(args.console, switch_iptables(args, 'read'))
			_commands6 = switch_iptables(args, 'read')
			args6_to_args4(args)
		else:
			args.iptables_info, err = shell_run(args.console, switch_nftables(args, 'search'))
			_commands = switch_nftables(args, 'search').replace('\t','\\t')
			if not args.ipv6 and args.nftproto != 'inet':
				args4_to_args6(args)
				args.ip6tables_info, err6 = shell_run(args.console, switch_nftables(args, 'search'))
				_commands6 = switch_nftables(args, 'search').replace('\t','\\t')
				args6_to_args4(args)
			else:
				args.ip6tables_info, err6, _commands6 = args.iptables_info, err, _commands
		service_start_stop(args)
		if err != '':
			print(f"{err}{_commands}")
		if err6 != '':
			print(f"{err6}{_commands6}")
		if args.nolog:
			if err != '':
				logger.error(f"{err}{_commands}")
			if err6 != '':
				logger.error(f"{err6}{_commands6}")
		check_blackwhite(args)
		unban_blackwhite(args)
		write_blackwhite(args)
		AppExit(args)
	if not args.cmd:
		if not args.log_txt:
			parser_dict['parser'].parse_args(['service', '-h'])
			sys.exit(0)

def listwork(args: Arguments):
	''' Working with lists. '''
	
	global parser_dict, logger
	
	CreateTableChain(args)
	
	def show_list(args: Arguments):
		''' Displaying information on the screen, 
			according to the specified criteria. '''
		data = ''
		jobj = args.blacklist_json if args.onlist == 'black' else args.whitelist_json
		dict_filter  = dict()
		tmp_filter = dict()
		if args.ip:
			for elem in range(len(args.ip)):
				for x, y in jobj.items():
					if str(args.ip[elem]) in x:
						dict_filter[x] = y
		if not args.json:
			if dict_filter:
				data = '\n'.join(show_json(dict_filter, args.count))
			else:
				data = '\n'.join(show_json(jobj, args.count))
		else:
			if args.count == 0:
				if dict_filter:
					data = json.dumps(dict_filter, indent=args.indent)
				else:
					data = json.dumps(jobj, indent=args.indent)
			else:
				spcae = ' ' * args.indent
				data = '{\n'
				if dict_filter:
					data += ',\n'.join(tuple(f"{spcae}\"{x}\": {y}" for x,y in dict_filter.items() if y >= args.count))
				else:
					data += ',\n'.join(tuple(f"{spcae}\"{x}\": {y}" for x,y in jobj.items() if y >= args.count))
				data += '\n}'
		if args.save:
			read_write_text(args.output, 'w', data + '\n')
		else:
			print(data)
	
	def clear_list(args: Arguments):
		''' Clear (reset) the list. '''
		args.json_data = args.blacklist_json if args.onlist == 'black' else args.whitelist_json
		args.json_data = dict()
		if args.save:
			read_write_json(args.output, 'w', args.json_data)
	
	def ban_unban_full(args: Arguments):
		''' Ban or unban all entered ip addresses. '''
		global logger
		if not args.nftables:
			args.iptables_info, err = shell_run(args.console, switch_iptables(args, 'read'))
			_commands = switch_iptables(args, 'read')
			args4_to_args6(args)
			args.ip6tables_info, err6 = shell_run(args.console, switch_iptables(args, 'read'))
			_commands6 = switch_iptables(args, 'read')
			args6_to_args4(args)
		else:
			args.iptables_info, err = shell_run(args.console, switch_nftables(args, 'search'))
			_commands = switch_nftables(args, 'search').replace('\t','\\t')
			if not args.ipv6 and args.nftproto != 'inet':
				args4_to_args6(args)
				args.ip6tables_info, err6 = shell_run(args.console, switch_nftables(args, 'search'))
				_commands6 = switch_nftables(args, 'search').replace('\t','\\t')
				args6_to_args4(args)
			else:
				args.ip6tables_info, err6, _commands6 = args.iptables_info, err, _commands	
		if err != '':
			logger.error(f"{err}{_commands}")
		if err6 != '':
			logger.error(f"{err6}{_commands6}")
		for elem in range(len(args.ip)):
			args.current_ip = ip_to_net(args.ip[elem], args.mask[elem]) if len(args.mask) > elem else ip_to_net(args.ip[elem], args.maxmask)
			args.current_version = ip_to_version(args.current_ip, args.maxmask)
			if args.current_version == 6 and not args.ipv6:
				args4_to_args6(args)
				args.current_ip = ip_to_net(args.ip[elem], args.mask[elem]) if len(args.mask) > elem else ip_to_net(args.ip[elem], args.maxmask)
			if not args.nftables:
				ban_unban_one(args)
			else:
				nft_ban_unban_one(args)
			if args.ischange:
				args6_to_args4(args)
		args.current_ip = None
	
	def add_del_one(args: Arguments):
		''' Add or remove one ip address. '''
		global logger
		if args.delete:
			if args.json_data.get(args.current_ip):
				del args.json_data[args.current_ip]
				if args.nolog:
					logger.info(f"del {args.current_ip}")
		else:
			if args.json_data.get(args.current_ip, '-') != '-':
				args.json_data[args.current_ip] = args.json_data[args.current_ip] + 1 if args.quantity == 0 else args.quantity
				if args.nolog:
					logger.info(f"add {args.current_ip} = {args.json_data[args.current_ip]}")
			else:
				args.json_data[args.current_ip] = 1 if args.quantity == 0 else args.quantity
				if args.nolog:
					logger.info(f"add {args.current_ip} = {args.json_data[args.current_ip]}")
		
	def add_dell_full(args: Arguments):
		''' Adding or deleting all entered ip addresses. '''
		args.json_data = args.blacklist_json if args.onlist == 'black' else args.whitelist_json
		for elem in range(len(args.ip)):
			args.current_ip = ip_to_net(args.ip[elem], args.mask[elem]) if len(args.mask) > elem else ip_to_net(args.ip[elem], args.maxmask)
			args.current_version = ip_to_version(args.current_ip, args.maxmask)
			if args.current_version == 6:
				args4_to_args6(args)
				args.current_ip = ip_to_net(args.ip[elem], args.mask[elem]) if len(args.mask) > elem else ip_to_net(args.ip[elem], args.maxmask)
			add_del_one(args)
			if args.ischange:
				args6_to_args4(args)
		if args.save:
			read_write_json(args.output, 'w', args.json_data, args.indent)
		args.current_ip = None
		args.json_data = None
	
	if args.show:
		read_list(args)
		show_list(args)
		sys.exit(0)
	if args.empty:
		read_list(args)
		clear_list(args)
		args.file_data = args.blacklist if args.onlist == 'black' else args.whitelist
		print(f"Clear the {args.onlist} list file {args.file_data.name} and {'save' if args.save else 'no save'}.")
		if args.nolog:
			logger.info(f"Clear the {args.onlist} list file {args.file_data.name} and {'save' if args.save else 'no save'}.")
		AppExit(args)
	if args.ban:
		if args.cmd:
			args.current_ip = 'ip/mask'
			if not args.nftables:
				print(switch_iptables(args, 'read'))
				if args.onlist == 'black':
					print(switch_iptables(args, 'add-black'))
				else:
					print(switch_iptables(args, 'add-white'))
			else:
				print(switch_nftables(args, 'read'))
				if args.onlist == 'black':
					print(switch_nftables(args, 'add-black', 'NUM'))
				else:
					print(switch_nftables(args, 'add-white', 'NUM'))
			sys.exit(0)
		args.oldadd = args.add
		args.add = True
		ban_unban_full(args)
		args.add = args.oldadd
		args.oldadd = None
	if args.unban:
		if args.cmd:
			args.current_ip = 'ip/mask'
			if not args.nftables:
				print(switch_iptables(args, 'read'))
				if args.onlist == 'black':
					print(switch_iptables(args, 'del-black'))
				else:
					print(switch_iptables(args, 'del-white'))
			else:
				print(switch_nftables(args, 'search').replace('\t','\\t'))
				if args.onlist == 'black':
					print(switch_nftables(args, 'del-black', 'NUM'))
				else:
					print(switch_nftables(args, 'del-white', 'NUM'))
			sys.exit(0)
		args.oldadd = args.add
		args.add = False
		ban_unban_full(args)
		args.add = args.oldadd
		args.oldadd = None
	if args.add:
		read_list(args)
		add_dell_full(args)
	if args.delete:
		read_list(args)
		add_dell_full(args)
	if not args.cmd:
		if args.nolog:
			rez = args.show + args.ban + args.unban + args.add + args.delete
			if rez == 0:
				if args.onlist == 'black':
					parser_dict['parser'].parse_args(['black', '-h'])
				elif args.onlist == 'white':
					parser_dict['parser'].parse_args(['white', '-h'])
				sys.exit(0)
	AppExit(args)

def activity_work(args: Arguments):
	''' Working with the IP address activity log. '''
	if args.search:
		read_list(args)
		search_activity(args)
		sys.exit(0)
	if args.show:
		if args.filelog.exists():
			data = read_write_text(args.filelog, 'r')
			if args.grep:
				data_filter = grep_search(data, args)
				if data_filter != '':
					data = data_filter
			if args.save:
				args.output = pathlib.Path(str(args.output)).resolve()
				read_write_text(args.output, 'w', data)
			else:
				print(data)
		sys.exit(0)
	if args.empty:
		if args.save:
			read_write_text(args.filelog, 'w', '\n')
		else:
			print(f"{__progname__} {__version__}: To save the information, please enter the \"-save\" key.")
		sys.exit(0)
	parser_dict['parser'].parse_args(['active', '-h'])

def CreateTableChain(args: Arguments):
	''' Function to create your table, chain on NFTABLES '''
	global logger
	if args.cmd:
		if args.nftables:
			if args.newtable:
				print(switch_nftables(args, 'create-table'))
				if args.nftproto != 'inet':
					args4_to_args6(args)
					print(switch_nftables(args, 'create-table'))
					args6_to_args4(args)
			if args.newchain:
				print(switch_nftables(args, 'create-chain'))
				if args.nftproto != 'inet':
					args4_to_args6(args)
					print(switch_nftables(args, 'create-chain'))
					args6_to_args4(args)
	
	if not args.cmd:
		if args.nftables:
			if args.newtable:
				logger.info(f"New table in NFTABLES  = {args.table}, protocol = {args.nftproto}.")
				print(f"New table in NFTABLES  = {args.table}, protocol = {args.nftproto}.")
				service_info, err = shell_run(args.console, switch_nftables(args, 'create-table'))
				_commands = switch_nftables(args, 'create-table')
				if service_info != '':
					print(service_info)
				if err != '':
					print(f"{err}{_commands}")
				if args.nolog:
					if service_info != '':
						logger.info(service_info)
					if err != '':
						logger.error(f"{err}{_commands}")
				if args.nftproto != 'inet':
					args4_to_args6(args)
					#
					logger.info(f"New table in NFTABLES  = {args.table}, protocol = {args.nftproto}.")
					print(f"New table in NFTABLES  = {args.table}, protocol = {args.nftproto}")
					service_info, err = shell_run(args.console, switch_nftables(args, 'create-table'))
					_commands = switch_nftables(args, 'create-table')
					if service_info != '':
						print(service_info)
					if err != '':
						print(f"{err}{_commands}")
					if args.nolog:
						if service_info != '':
							logger.info(service_info)
						if err != '':
							logger.error(f"{err}{_commands}")
					#
					args6_to_args4(args)
			if args.newchain:
				logger.info(f"New chain in NFTABLES  = {args.chain}, protocol = {args.nftproto}, tables = {args.table}.")
				print(f"New chain in NFTABLES  = {args.chain}, protocol = {args.nftproto}, tables = {args.table}.")
				service_info, err = shell_run(args.console, switch_nftables(args, 'create-chain'))
				_commands = switch_nftables(args, 'create-chain')
				if service_info != '':
					print(service_info)
				if err != '':
					print(f"{err}{_commands}")
				if args.nolog:
					if service_info != '':
						logger.info(service_info)
					if err != '':
						logger.error(f"{err}{_commands}")
				if args.nftproto != 'inet':
					args4_to_args6(args)
					#
					logger.info(f"New chain in NFTABLES  = {args.chain}, protocol = {args.nftproto}, tables = {args.table}.")
					print(f"New chain in NFTABLES  = {args.chain}, protocol = {args.nftproto}, tables = {args.table}.")
					service_info, err = shell_run(args.console, switch_nftables(args, 'create-chain'))
					_commands = switch_nftables(args, 'create-chain')
					if service_info != '':
						print(service_info)
					if err != '':
						print(f"{err}{_commands}")
					if args.nolog:
						if service_info != '':
							logger.info(service_info)
						if err != '':
							logger.error(f"{err}{_commands}")
					#
					args6_to_args4(args)
			if args.exit:
				AppExit(args)

def EditTableParam(args: Arguments):
	''' Edit online param on {IP,IP6,NF}TABLES. '''
	
	if not args.nftables:
		args.protocol = 'iptables' if not args.ipv6 else 'ip6tables'
		args.table = 'filter'
		args.chain = 'INPUT'
		args.interfaces = f"-i {args.network}" if args.network != '' else ''
	else:
		args.interfaces = f"iifname \"{args.network}\"" if args.network != '' else ''
		args.protocol = 'ip' if not args.ipv6 else 'ip6'
		if args.nftproto != 'inet':
			args.nftproto = 'ip' if not args.ipv6 else 'ip6'
	
	minmaxmask(args)
	
	if args.fine:
		args.clearchain = True
		args.Delchain = True
		args.cleartable = True
		args.Deltable = True
	
	if args.run:
		args.newtable = True
		args.newchain = True
	
	if args.personal:
		if args.nftables:
			args.nftproto = 'inet'
			args.table = 'blackwhite'
			args.chain = 'INPUT'

def EditDirParam(args: Arguments):
	''' Edit online directoryes Params. '''	
	
	global workdir, json_black, json_white, blacklist_name, whitelist_name
	global blackwhite_file, log_activity_file, log_activity_name
	
	args.blackwhite_file = blackwhite_file
	read_blackwhite(args)
	
	if workdir != args.workdir:
		workdir = args.workdir
		json_black = pathlib.Path(f"{workdir}").resolve().joinpath(blacklist_name)
		json_white = pathlib.Path(f"{workdir}").resolve().joinpath(whitelist_name)
		if blacklist_name in args.blacklist:
			args.blacklist = json_black
		else:
			args.blacklist = pathlib.Path(f"{args.blacklist}").resolve()
		if whitelist_name in args.whitelist:
			args.whitelist = json_white
		else:
			args.whitelist = pathlib.Path(f"{args.whitelist}").resolve()
		if args.onlist == 'black':
			if blacklist_name in args.output:
				args.output = json_black
			else:
				args.output = pathlib.Path(f"{args.output}").resolve()
		elif args.onlist == 'white':
			if whitelist_name in args.output:
				args.output = json_white
			else:
				args.output = pathlib.Path(f"{args.output}").resolve()
		
		log_activity_file = pathlib.Path(f"{workdir}").resolve().joinpath(log_activity_name)
		if log_activity_name in args.filelog:
			args.filelog = log_activity_file
		else:
			args.filelog = pathlib.Path(f"{args.filelog}").resolve()
	
	args.blacklist = pathlib.Path(f"{args.blacklist}").resolve()
	args.whitelist = pathlib.Path(f"{args.whitelist}").resolve()
	args.filelog = pathlib.Path(f"{args.filelog}").resolve()
	if str(args.output) != '':
		if args.output != None:
			args.output = pathlib.Path(f"{args.output}").resolve()
	
	if args.logfile != '':
		if args.logfile != None:
			args.logfile = pathlib.Path(f"{args.logfile}").resolve()
	
	if not pathlib.Path(str(workdir)).resolve().exists():
		pathlib.Path(str(workdir)).resolve().mkdir(parents=True)
	
	if args.search:
		for k in range(len(args.search)):
			args.search[k] = pathlib.Path(f"{args.search[k]}").resolve()
	
	if args.showdir:
		print(workdir)
		sys.exit(0)

def EditLogParam(args: Arguments):
	''' Edit online Log Params. '''
		
	def stampToStr(timeStamp: int, strFormat = "%d.%m.%Y-%H:%M:%S") -> str:
		dateTime = datetime.fromtimestamp(timeStamp)
		datestr = dateTime.strftime(strFormat)
		return datestr
	
	global logger
	
	logging.basicConfig(level=logging.INFO, filename=str(args.logfile),filemode="a",
						format="%(asctime)s %(levelname)s \"%(message)s\"")
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	
	if args.logfile.exists():
		if args.limit:
			file_date = stampToStr(args.logfile.stat().st_mtime, "%d.%m.%Y")
			ondate = datetime.now().strftime("%d.%m.%Y")
			if file_date != ondate:
				read_write_text(args.logfile, 'w', '\n')
		if args.viewlog:
			out_log_info = ''
			if args.latest:
				latest_date = read_write_text(args.logfile, 'r').split('\n')[-2].split(' ')[0] if not read_write_text(args.logfile, 'r').split('\n')[-1] else read_write_text(args.logfile, 'r').split('\n')[-2].split(' ')[0]
				args.old_filtering = args.filtering
				args.grep = args.filtering = f"{latest_date}"
				out_log_info = grep_search(read_write_text(args.logfile, 'r'), args)
				args.filtering = args.old_filtering
				args.old_filtering = None
			if args.filtering != '':
				args.grep = args.filtering
				out_log_info = grep_search(out_log_info if out_log_info != '' else read_write_text(args.logfile, 'r'), args)
			if out_log_info != '':
				print(out_log_info)
			else:
				print(read_write_text(args.logfile, 'r'))
			sys.exit(0)
		if args.resetlog:
			read_write_text(args.logfile, 'w', '\n')
			sys.exit(0)

def test_edit_arguments(args: Arguments):
	''' Test and edit arguments and edit online parameters... '''
	
	if args.count < 0:
		print("The number of locks to display cannot be a negative number (from 0 and above.)!")
		args.count = 0
	if args.quantity < 0:
		print("The number of locks to save cannot be a negative number (from 0 and above.)!")
		args.quantity = 0
	
	EditDirParam(args)
	EditLogParam(args)
	EditTableParam(args)
	if args.exit:
		CreateTableChain(args)

def main(*argv):
	''' The main cycle of the program. '''
	
	global infromation, service_text, parser_dict
	
	parser_dict = createParser()
	args = Arguments()
	if len(argv) > 0:
		parser_dict['parser'].parse_args(args=argv, namespace=Arguments)
	else:
		parser_dict['parser'].parse_args(namespace=Arguments)
	
	test_edit_arguments(args)
	
	func = {
			'service': servicework,
			'systemd': systemdwork,
			'black': listwork,
			'white': listwork,
			'activity': activity_work
			}
	
	if args.info:
		print(infromation)
		sys.exit(0)
	
	if args.lslan:
		if not args.nftables:
			_commands = switch_iptables(args, 'list-net')
		else:
			_commands = switch_nftables(args, 'list-net')
		service_info, err = shell_run(args.console, _commands)
		if service_info != '':
			print(service_info)
		if err != '':
			print(f"{err}{_commands}")
		sys.exit(0)
	
	if args.onlist != None:
		func.get(args.onlist)(args)
	else:
		if args.exit:
			AppExit(args)
		parser_dict['parser'].parse_args(['-h'])

if __name__ == '__main__':
	main()
else:
	main()
