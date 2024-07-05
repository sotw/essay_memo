import os, sys, re, codecs
import argparse
import logging
import urllib
import requests
import sqlite3

import asyncio

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
global staticStr
global ScreenI
global stockdb
global cursor
lock = asyncio.Lock()

staticStr = 'https://tw.stock.yahoo.com/quote/'
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

def getReleaseNoteDetail(tDetail):
	thisScreen = []
	resp = requests.get(tTarget)
	data = resp.text
	parser = etree.HTMLParser()
	tree = etree.parse(StringIO(data), parser)

	comments = tree.xpath('//comment()')
	for c in comments:
		p = c.getparent()
		p.remove(c)

	etree.strip_tags(tree,'p')
	etree.strip_tags(tree,'i')
	result = etree.tostring(tree.getroot(), pretty_print=True, method="html", encoding='utf-8')

	#mTitle = ''
	#titles = tree.xpath("//h1[@class='title']")

'''For programming'''
def paintRED(string,target):
	string = string.replace(target, clrTx(target,'RED'))
	return string

async def doStuff(tTarget,id,comment_id):
	#print("enter doStuff")
	global lock
	global ScreenI
	global stockdb
	global cursor
	updownSymbol = u'\u2197'
	num = id
	#cursor.execute(f"SELECT COMMENTID FROM SOI WHERE ID={num}")
	#my_rets = cursor.fetchone()
	#comment_id = my_rets[0]
	#print(f"comment id = {comment_id}")
	resp = requests.get(tTarget+str(num))
	data = resp.text
	#
	# print(data)
	parser = etree.HTMLParser(recover=True)
	tree = etree.parse(StringIO(data), parser)
	#etree.strip_tags(tree,'span')
	result = etree.tostring(tree.getroot(), pretty_print=True, method="html", encoding='utf-8')

	#print(repr(result))
	#print(paintRED(repr(result),'function(win)'))
    #print paintRED(result,'stkname')

	# current value
	#headLines = re.findall('<div class=".+?">(.+?)</div>',repr(result),re.DOTALL)
	#headLines = re.findall('<div class=".+?">(.+?)</div>',repr(result),re.DOTALL)
	titles = tree.xpath('//h1[@class="C($c-link-text) Fw(b) Fz(24px) Mend(8px)"]')
	contents = tree.xpath('//span[@class="Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c) C($c-trend-up)"]')
	if len(contents) == 0:
		contents = tree.xpath('//span[@class="Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c) C($c-trend-down)"]')
		updownSymbol = u'\u2198'
	if len(contents) == 0:
		contents = tree.xpath('//span[@class="Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c)"]')
		updownSymbol = u'\u2192'

	price = 0
	mytitle = 'NA'
	for content in contents:
		if content.text is not None:
			#print(content.get("value"))
			#print(content.text)
			price = content.text
			break
			
	for title in titles:
		if title.text is not None:
			mytitle = title.text
			break
                                       
	tread_nums = tree.xpath('//div[@class="D(f) Ai(fe) Mb(4px)"]/span')
	my_tread_num = "0"
	for tread_num in tread_nums:
		if tread_num.text is None:
			#print("text is none")
			for child in tread_num:
				#print(child.text)
				#print(child.tail)
				my_tread_num = child.tail
			#print(tread_num.tag)
			#print(tread_num.attrib)
			#print(tread_num.tail)
			#tread_nums.remove(tread_num)

	#diff = Decimal(price) - Decimal(my_price)
	#target_price = Decimal(Decimal(my_price)*Decimal('1.3'))
	ai_comment = " No comment"
	#print(f"my title={mytitle}")
	#ScreenI.append({'serial':num, 'title':mytitle, 'last':my_price, 'current':price, 'updownsymbol':updownSymbol,'diff':diff, 'updownvalue':my_tread_num})
	#print(f"INSERT OR REPLACE INTO SOI(ID, TITLE, COST, PRICE, UPDOWNSYMBOL, DIFF, TARGET_PRICE, AI, UPDOWNVALUE) values({str(num)},\
	#	'{str(mytitle)}','{str(my_price)}','{str(price)}','{str(updownSymbol)}','{str(diff)}','{str(target_price)}','{ai_comment}','{str(my_tread_num)}')")

	async with lock:
		cursor.execute(f"UPDATE SOI SET TITLE='{str(mytitle)}', PRICE='{str(price)}', AI='{ai_comment}' WHERE COMMENTID='{str(comment_id)}';")
		stockdb.commit()
		print(f"{mytitle} updated!             ", end='\r')

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
	parser.add_argument('-k', '--kill', dest='kill', action = 'store_true', default=False, help='remove a stock from monitor list')
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
	if not args.read and not args.kill and not args.add and not args.listme and not args.updateme and not args.show:
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
	cursor.execute('''CREATE TABLE IF NOT EXISTS SOI
	(COMMENTID INTEGER PRIMARY KEY AUTOINCREMENT,
	ID INTEGER NOT NULL,
	TITLE TEXT,
	TIME TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime')), 
	PRICE TEXT,
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
	ScreenI.append(f"    SN|GLOBAL COMMENT")
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


async def doDumpEx(num=0,update=0):
	global ScreenI
	global stockdb
	global cursor
	#for entry in ARGUDB:
	#	curr_idx+=1
	#	print(f"Handling {curr_idx}/{max_entrys}", end='\r')
	#	doStuff(staticStr,entry)

	if update == 1:
		my_tasks = []
		cursor.execute(f"SELECT COMMENTID,ID FROM SOI")
		for rets in cursor.fetchall():
			itask = asyncio.create_task(doStuff(staticStr,rets[1],rets[0]))
			my_tasks.append(itask)
		for mytask in my_tasks:
			await mytask
		
	#print("|"+clrTx("               TIME","CYAN")+"|"+clrTx("Serial","CYAN")+"|"+clrTx("    Name","CYAN")+"|"+clrTx(" Price","CYAN")+"|"+clrTx("MEMO","CYAN"))

	if num == 0:
		cursor.execute(f"SELECT * FROM SOI")
	else:
		cursor.execute(f"SELECT * FROM SOI WHERE ID = {num}")

	for record in cursor.fetchall():
		#print(record)		
		ScreenI.append("------------------------------------------------------------------")
		_MSGID=f"{record[0]}".zfill(3)
		_MSGID=clrTx(f"{_MSGID}","AUQA")
		_TIMESTAMP=clrTx(f"{record[3]}","GREY65")
		_STOCKNUM=clrTx(f"{record[1]:>6}","BOLD")
		_STOCKNAME=clrTx(f"{record[2]}","CYAN")
		_CURPRICE=clrTx(f"{record[4]}","YELLOW")
		ScreenI.append(f"{_MSGID}|{_TIMESTAMP}|{_STOCKNUM}|{_STOCKNAME}")
		ScreenI.append(f"Price:{_CURPRICE}|{record[5]}")
	
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
	else:
		msgs = msg.split(":")
		if(len(msgs) !=2):
			print(clrTx("you need to input [stock_num]:[comment]",'YELLOW'))
		cursor.execute(f"INSERT OR REPLACE INTO SOI(ID,COMMENT) values({msgs[0]},'{msgs[1]}')")
		stockdb.commit()

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
        cursor.execute(f"DELETE FROM SOI WHERE COMMENTID={msg}")
        stockdb.commit()

async def main():
	global stockdb
	global cursor
	global args
	if args.read and args.globalcomment:
		doDump()
	elif args.read :
		if len(tTarget) == 0:
			id = 0
		else:
			id  = int(tTarget)
		await doDumpEx(id,1) # doDumpex(specific target?, retrival or not)
	elif args.show and args.globalcomment:
		doDump()
	elif args.show:
		if len(tTarget) == 0:
			id = 0
		else:
			id  = int(tTarget)
		await doDumpEx(id,0) # doDumpex(specific target?, retrival or not)		
	elif args.kill:
		doKillALn(tTarget)
	elif args.add:
		doWriteLn(tTarget)
		doDump()
	elif args.updateme:
		await doDumpEx(0,1)
	stockdb.close()

if __name__ == '__main__':
	verify()
	refreshDb()
	asyncio.run(main())
