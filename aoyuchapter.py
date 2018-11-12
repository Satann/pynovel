# -*- coding: utf-8 -*-
# filename: aoyuchapter.py

import time, requests, chardet, web, sqlalchemy, gevent
from IPProxyPool.spider.HtmlDownloader import Html_Downloader
from lxml import etree
from langconv import *
import urllib
import types, os
import json
import chardet
import datetime
import traceback
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from IPProxyPool.config import Data, aoyulist

reload(sys)
sys.setdefaultencoding('utf-8')
client = MongoClient('127.0.0.1', 27017)
book_db = client.web.book


def upsertBook(modl):
    try:
        if book_db.find_one({'name': modl.name}):
            book_db.update_one({'name': modl.name}, {'$set': {'chapters': modl.chapters}})
        else:
            book_db.insert_one(modl.to_dict())
    except DuplicateKeyError,e:
        pass
    except Exception, e:
        print('db error:%s' % modl.name)

import hashlib
cpt_db = client.web.chapter
def insertChpter(modl):
    try:
        cpt_db.insert_one(modl)
    except DuplicateKeyError, e:
        pass
    except Exception, e:
        print('db error:%s' % modl.name)

if __name__ == "__main__":
    steps = 2000
    while True:
        bklist = list(book_db.find({"chapters": {"$elemMatch": {"status": 0, "catchcount": 0}}}).sort("id").skip(steps).limit(1))
        if not bklist:
            break
        bk = bklist[0]
        bookOne = Data(bk)
        cppt = 0
        ii = 0
        while ii < len(bookOne.chapters):
            cptOne = bookOne.chapters[ii]
            ii += 1
            if cptOne['status'] > 0:
                continue

            while True:
                try:
                    pgip, page_str = Html_Downloader.downloadProxyLittle(cptOne['url'])
                    page_str = page_str.encode('latin-1')
                    page_root = etree.HTML(page_str)
                    pgip = None
                    break
                except UnicodeDecodeError,e:
                    page_str = page_str.decode('gbk','ignore')
                    page_root = etree.HTML(page_str)
                    pgip = None
                    break
                except Exception, e:
                    if e.message == 'No JSON object could be decoded':
                        continue
                    print traceback.print_exc()
                    if pgip and page_str != None:
                        requests.get('http://127.0.0.1:8000/delete?ip=%s' % pgip)
                        print ('chapters response error, deeltip %s' % pgip)
                    #print page_str
                    continue

            cptOne['paragraphs'] = []
            page_contents = [pc.strip() for pc in page_root.xpath('//div[@id="BookText"]/text()') if pc.strip()]
            if not page_contents:
                cptOne['paragraphs'].append(page_str.decode('gbk','ignore').encode('utf-8').strip())
                cptOne['catchcount'] = cptOne.get('catchcount', 0) + 1
                cptOne['intime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                continue
            for pgraf in page_contents:
                cptOne['paragraphs'].append(pgraf)
            cptOne['status'] = 2
            cptOne['catchcount'] = cptOne.get('catchcount', 0) + 1
            cptOne['intime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cptOne['id'] = str(cptOne['index']) + '_' + hashlib.md5((cptOne['url']).encode('gbk')).hexdigest()
            cptOne['name'] = bookOne.name

            ##cpt table
            insertChpter(cptOne)
            cptOne['paragraphs'] = []
            cptOne.pop('id')
            cptOne.pop('name')
            if '_id' in cptOne:
                cptOne.pop('_id')
            cppt += 1
            print ('[%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), cptOne['title']))
            if cppt % 10 == 0:
                upsertBook(bookOne)
        upsertBook(bookOne)
