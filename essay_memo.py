import os, sys, re, codecs
import argparse
import logging
import urllib
import requests
import sqlite3

from time import sleep
from time import time

from os.path import expanduser
from subprocess import PIPE
from subprocess import Popen
from lxml import etree
from io import StringIO
from pprint import pprint

from decimal import *

from requests.models import stream_decode_response_unicode
from HMTXCLR import clrTx
from textwrap import TextWrapper
from textwrap import dedent
from subprocess import Popen
from subprocess import PIPE
from subprocess import STDOUT

global DB
global tTarget
global args
global ARGUDB
global _wrap
global LINKS
global ctl
global ScreenI
global stockdb
global cursor

LINKS = []
ARGUDB = []
ScreenI = []
_wrap = TextWrapper()

def utf8len(s):
    return len(s.encode('utf-8'))

def prepareMailInfo(mailMsg):
	home = expanduser('~')
	iOut = []
	iOut.append('python')
	iOut.append(home+'/.hmDict/simpleMail.py')
	iOut.append(mailMsg)
	return iOut

def repeatStr(string_to_expand, length):
	return (string_to_expand * ((length/len(string_to_expand))+1))[:length]

def parseInt(sin):
	m = re.search(r'^(\d+)[.,]?\d*?',str(sin))
	return int(m.groups()[-1]) if m and not callable(sin) else None

'''For programming'''
def paintRED(string,target):
	string = string.replace(target, clrTx(target,'RED'))
	return string

def setup_logging(log_level):
	global DB
	DB = logging.getLogger('esssay_memo') #replace
	DB.setLevel(logging.DEBUG)
	handler = logging.StreamHandler(sys.stdout)
	handler.setLevel(level=log_level)
	handler.setFormatter(logging.Formatter('[%(module)s] [%(levelname)s] %(funcName)s| %(message)s'))
	DB.addHandler(handler)

def verify():
	global tTarget
	global args

	parser = argparse.ArgumentParser(description='This essay_memo is a personal essat memo system') #replace
	parser.add_argument('query', nargs='*', default=None)
	parser.add_argument('-d', '--database', dest='database', action = 'store', default='/.essay_memo/essay_memo.db') #replace
	parser.add_argument('-q', '--sqlite3', dest='sql3db', action = 'store', default='/.essay_memo/essay_memo.db3') #replace
	parser.add_argument('-a', '--add', dest='add', action = 'store_true', default=False, help='add classify number and the sentence you want to add')
	parser.add_argument('-g', '--global', dest='globalcomment', action = 'store_true', default=False, help='global comment without specific stock')
	parser.add_argument('-r', '--read', dest='read', action = 'store_true', default=False, help='dump records')
	parser.add_argument('-s', '--show', dest='show', action = 'store_true', default=False, help='show existing records')
	parser.add_argument('-t', '--showtitles', dest='show_all_titles', action = 'store_true', default=False, help='show all titles inside databse so far')
	parser.add_argument('-k', '--kill', dest='kill', action = 'store_true', default=False, help='remove a memo')
	parser.add_argument('-l', '--list', dest='listme', action = 'store_true', default=False, help='old interface, reserved')
	parser.add_argument('-u', '--update', dest='updateme', action = 'store_true', default=False, help='update')
	parser.add_argument('-v', '--verbose', dest='verbose', action = 'store_true', default=False, help='Verbose mode')
	
	args = parser.parse_args()
	tTarget = ' '.join(args.query)
	log_level = logging.WARNING
	if args.verbose:
		log_level = logging.DEBUG
	#if not tTarget:
	#	parser.print_help()
	#	exit()
	if args.read and args.kill:
		print("Flag conflict, some flag are exclusive")
		parser.print_help()
		exit()
	if not args.read and not args.kill and not args.add and not args.listme and not args.updateme and not args.show and not args.show_all_titles:
		parser.print_help()
		exit()
	setup_logging(log_level)

def refreshDb():
	global ARGUDB
	global DB
	global stockdb
	global cursor
	ARGUDB = []
	home = expanduser('~')
	if os.path.isfile(home+args.database) is True:
		f = open(home+args.database,'r')
		if f is not None:
			for line in f :
				if line != '\n' and line[0] != '#':
					line = line.rstrip('\n')
					ARGUDB.append(line)
		f.close()
	else:
		DB.debug('override file is not exist')
	stockdb = sqlite3.connect(home+args.sql3db)
	cursor = stockdb.cursor()
	DB.info("sqlite3 databse connected")
	cursor.execute('''CREATE TABLE IF NOT EXISTS EOI
	(COMMENTID INTEGER PRIMARY KEY AUTOINCREMENT,
	TITLE TEXT,
	TIME TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime')), 
	COMMENT TEXT,
	AI TEXT
	);''')
	stockdb.commit()
	DB.info("table SOI created or existed")
	cursor.execute('''CREATE TABLE IF NOT EXISTS KOKOROE
	(KOKOROEID INTEGER PRIMARY KEY AUTOINCREMENT,
	KOKOROE TEXT
	);''')
	stockdb.commit()
	DB.info("table kokoroecreated or existed")

def	doDump():
	#for entry in ARGUDB:
	#	print(entry)
	global stockdb
	global cursor
	global ScreenI
	ScreenI.clear()
	cursor.execute(f"SELECT * FROM KOKOROE ORDER BY KOKOROEID DESC")
	ScreenI.append(f"    SN|GLOBAL THOUGHT")
	for record in cursor.fetchall():
		#print(record)
		_MY_KOKOROE_SN=f"{record[0]:>6}"
		_MY_KOKOROE=f"{record[1]}"
		ScreenI.append(f"{_MY_KOKOROE_SN}|{_MY_KOKOROE}")
	toggleColor=False
	for item in ScreenI:
		if toggleColor is True:
			print(clrTx(f"{item}","CYAN"))
			toggleColor=False
		else:
			print(clrTx(f"{item}","YELLOW"))
			toggleColor=True

def doDumpDistinctOneColumn(COLNAME):
	global stockdb
	global cursor
	global ScreenI
	ScreenI.clear()
	cursor.execute(f"SELECT DISTINCT {COLNAME} FROM EOI")
	for record in cursor.fetchall():
		#print(record)
		_MY_TITLE=f"{record[0]}"
		ScreenI.append(f"{_MY_TITLE}")			
	toggleColor=False
	for item in ScreenI:
		if toggleColor is True:
			print(clrTx(f"{item}","CYAN"))
			toggleColor=False
		else:
			print(clrTx(f"{item}","YELLOW"))
			toggleColor=True

def doDumpEx(TITLE):
	global ScreenI
	global stockdb
	global cursor

	if TITLE == '':
		cursor.execute(f"SELECT * FROM EOI")
	else:
		cursor.execute(f"SELECT * FROM EOI WHERE TITLE = '{TITLE}'")

	for record in cursor.fetchall():
		#print(record)		
		#ScreenI.append("------------------------------------------------------------------")
		_MSGID=f"{record[0]}".zfill(3)
		_MSGID=clrTx(f"{_MSGID}","AUQA")
		_TIMESTAMP=clrTx(f"{record[2]}","GREY65")
		_TITLE=clrTx(f"{record[1]:>6}","BOLD")
		_MYTHOUGHT=clrTx(f"{record[3]}","CYAN")
		ScreenI.append(f"{_MSGID}|{_TIMESTAMP}|{_TITLE}|{_MYTHOUGHT}")
	
	for item in ScreenI:
		print(item)

def doWriteLn(msg):
	global DB
	global stockdb
	global cursor
	home = expanduser('~')
	if args.globalcomment:
		cursor.execute(f"INSERT OR REPLACE INTO KOKOROE(KOKOROE) values('{msg}')")
		stockdb.commit()
		doDump()
	else:
		msgs = msg.split(":")
		if(len(msgs) <= 1):
			print(clrTx("you need to input [TITLE]:[INFORMATION]",'YELLOW'))
		else:
			headtag = msgs[0]
			message = ':'.join(msgs[1:])
			cursor.execute(f"INSERT OR REPLACE INTO EOI(TITLE,COMMENT) values('{headtag}','{message}')")
			stockdb.commit()
			doDumpEx(f'{msgs[0]}')

def doKillALn(msg):
    global DB
    global stockdb
    global cursor
    home = expanduser('~')
    if args.globalcomment:
        cursor.execute(f"DELETE FROM KOKOROE WHERE KOKOROEID={msg}")
        doDump()
        stockdb.commit()
    else:
        cursor.execute(f"DELETE FROM EOI WHERE COMMENTID='{msg}'")
        stockdb.commit()

def main():
	global stockdb
	global cursor
	global args
	if args.read and args.globalcomment:
		doDump()
	elif args.read :
		if len(tTarget) == 0:
			id = '0'
		else:
			id  = tTarget
		doDumpEx(id) # doDumpex(specific target?, retrival or not)
	elif args.show and args.globalcomment:
		doDump()
	elif args.show:
		if len(tTarget) == 0:
			id = ''
		else:
			id = tTarget
		doDumpEx(id) # doDumpex(specific target?, retrival or not)		
	elif args.kill:
		doKillALn(tTarget)
	elif args.add:
		doWriteLn(tTarget)
	elif args.updateme:
		pass
	elif args.show_all_titles:
		doDumpDistinctOneColumn('TITLE')	
	stockdb.close()

if __name__ == '__main__':
	verify()
	refreshDb()
	main()
