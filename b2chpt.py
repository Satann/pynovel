# -*- coding: utf-8 -*-
# filename: b2chpt.py

import hashlib
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
from IPProxyPool.config import Data, aoyulist
from  pymongo.errors import DuplicateKeyError

reload(sys)
sys.setdefaultencoding('utf-8')
client = MongoClient('127.0.0.1', 27017)
book_db = client.web.book
cpt_db = client.web.chapter


def upsertBook(modl):
    try:
        if book_db.find_one({'name': modl.name}):
            book_db.update_one({'name': modl.name}, {'$set': {'chapters': modl.chapters}})
        else:
            book_db.insert_one(modl.to_dict())
    except DuplicateKeyError, e:
        pass
    except Exception, e:
        print('db error:%s' % modl.name)


def insertChpter(modl):
    try:
        cpt_db.insert_one(modl)
    except DuplicateKeyError, e:
        pass
    except Exception, e:
        print('db error:%s' % modl.name)


if __name__ == "__main__":
    ij = 0
    while True:
        bklist = list(book_db.find({"chapters": {"$elemMatch": {"status": 1}}}).sort("id", -1).limit(1))
        if not bklist:
            break
        bk = bklist[0]
        bookOne = Data(bk)
        cppt = 0
        ii = 0
        while ii < len(bookOne.chapters):
            cptOne = bookOne.chapters[ii]
            ii += 1
            if cptOne['status'] == 1:
                cptOne['status'] = 2
                cptOne['id'] = str(cptOne['index']) + '_' + hashlib.md5((cptOne['url']).encode('gbk')).hexdigest()
                cptOne['name'] = bookOne.name
                insertChpter(cptOne)
                cptOne['paragraphs'] = []
                cptOne.pop('id')
                cptOne.pop('name')
                if '_id' in cptOne:
                    cptOne.pop('_id')
        upsertBook(bookOne)
        ij += 1
        print ij,bookOne.name
