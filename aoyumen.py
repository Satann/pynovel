# -*- coding: utf-8 -*-
# filename: aoyumain.py
import time, requests, chardet, web, sqlalchemy, gevent
from IPProxyPool.spider.HtmlDownloader import Html_Downloader
from lxml import etree
from langconv import *
import urllib
import types, os
import json
import chardet
import  datetime
import traceback
from pymongo import MongoClient
from IPProxyPool.config import Data, aoyulist

reload(sys)
sys.setdefaultencoding('utf-8')
client = MongoClient('127.0.0.1', 27017)
book_db = client.web.book


def upsertBook(modl):
    try:
        if book_db.find_one({'name': modl.name}):
            print('book: %s in db already' % modl.name)
        else:
            book_db.insert_one(modl.to_dict())
    except Exception,e:
        print traceback.print_stack()
        print('db error:%s'% modl.name)

if __name__ == "__main__":
    fenlist = 0
    while fenlist < len(aoyulist):
        tp = aoyulist[fenlist]
        fenlist += 1
    #for tp in aoyulist:
        if not tp:
            continue
        j = 1
        while j < tp.pages + 1:
            j += 1
            host  = 'http://www.aoyuge.com'
            while True:
                urll = host + '/fenlei-' + str(tp.index) + '-' + str(j -1) + '.html'
                try:
                    pip, response = Html_Downloader.downloadProxy((urll))
                    response = response.encode('latin-1')
                    root = etree.HTML(response)
                    rows = root.xpath('//ul[@class = "item-con"]/li')
                    pip = None
                    #response = None
                    break
                except UnicodeDecodeError,e:
                    response = response.decode('gbk','ignore')
                    root = etree.HTML(response)
                    rows = root.xpath('//ul[@class = "item-con"]/li')
                    pip = None
                    break
                except Exception,e:
                    if e.message == 'No JSON object could be decoded':
                        continue
                    if pip and response != None:
                        requests.get('http://127.0.0.1:8000/delete?ip=%s' % pip)
                        print ('aoyumen response error, deeltip %s' % pip)
                    traceback.print_exc()
                    print ('[#####]fenlei error: %s' % response)
                    continue
            for ri, r in enumerate(rows):
                try:
                    bookOne = Data()
                    book = r.xpath('*[@class="s2"]/a//text()')[0].strip()
                    if book_db.find_one({'name': book}):
                        bookOne = None
                        continue

                    fenlei = r.xpath('*[@class="s1"]//text()')[0].strip()[1:-1]
                    book_url = r.xpath('*[@class="s2"]/a//@href')[0].strip()
                    if book_url.find(host) == -1:
                        book_url = host + book_url
                    bookOne.url = book_url
                    bookOne.id = str(tp.base) + str(j - 1 + 200) + str(ri+ 600)
                    bookOne.type = fenlei
                    bookOne.name = book
                    bookOne.chapters = []
                    bookOne.flags = [bookOne.type]
                    bookOne.image = ''
                    bookOne.click = 0
                    bookOne.status = 0
                    bookOne.numbers = 0
                    bookOne.intime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    bookOne.writetime = ''
                    bookOne.author = ''
                    bookOne.lastpage = ''
                    bookOne.lasttime = ''

                    try:
                        last_page = r.xpath('*[@class="s2"]/i/a/text()')[0].strip()
                        author = r.xpath('*[@class="s3"]/text()')[0].strip()
                        last_time = r.xpath('*[@class="s4"]/text()')[0].strip()
                    except Exception,e:
                        print traceback.print_exc()
                        response = response.decode('gbk','ignore')
                        root1 = etree.HTML(response)
                        r1 = root1.xpath('//ul[@class = "item-con"]/li')[ri]
                        last_page = r1.xpath('*[@class="s2"]/i/a/text()')[0].strip()
                        author = r1.xpath('*[@class="s3"]/text()')[0].strip()
                        last_time = r1.xpath('*[@class="s4"]/text()')[0].strip()

                    bookOne.author = author
                    bookOne.lastpage = last_page
                    bookOne.lasttime = last_time

                    while True:
                        try:
                            bip, book_str = Html_Downloader.downloadProxy((book_url))
                            book_str = book_str.encode('latin-1')
                            book_root = etree.HTML(book_str)
                            bip = None
                            #book_str = None
                            break
                        except Exception,e:
                            if e.message == 'No JSON object could be decoded':
                                continue
                            print traceback.print_exc()
                            if bip and book_str != None:
                                requests.get('http://127.0.0.1:8000/delete?ip=%s' % bip)
                                print ('book response error, deeltip %s' % bip)
                                print book_str
                            if not bip and not book_str:
                                break
                            continue
                    bookOne.profile = ''.join(book_root.xpath('//div[@id="container"]//p[@class="intro"]/text()')).strip()
                    try:
                        bookOne.numbers = int(book_root.xpath('//p[@class="stats"]/span/i[1]/text()')[0])
                    except:
                        book_str = book_str.decode('gbk','ignore')
                        book_root = etree.HTML(book_str)
                        bookOne.numbers = int(book_root.xpath('//p[@class="stats"]/span/i[1]/text()')[0])

                    ###chapters
                    cpt_list = book_root.xpath('//*[@class="chapterlist"]//a')
                    for cptindex, cpt in enumerate(cpt_list):
                        chapterOne = Data()
                        chapterOne.index = cptindex + 1
                        chapterOne.status = 0
                        chapterOne.readcount = 0
                        chapterOne.catchcount = 0
                        chapterOne.recommend = 0
                        chapterOne.price = 0
                        chapterOne.paragraphs = []
                        chapterOne.writetime = ''
                        chapterOne.intime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        page_title = cpt.text.strip() if cpt.text else ''
                        page_url = cpt.attrib['href'].strip()
                        if page_url.find(host) == -1:
                            page_url = host + page_url
                        chapterOne.title = page_title
                        chapterOne.url = page_url
                        bookOne.chapters.append(chapterOne)
                        del chapterOne

                    #for cptOne in bookOne.chapters:
                    #    while True:
                    #        try:
                    #            pgip, page_str = Html_Downloader.downloadProxy((cptOne.url))
                    #            page_str = page_str.encode('latin-1').decode('gbk', 'ignore')
                    #            page_root = etree.HTML(page_str)
                    #            break
                    #        except Exception,e:
                    #            if pgip and page_str != None:
                    #                requests.get('http://127.0.0.1:8000/delete?ip=%s' % pgip)
                    #                print ('chapters response error, deeltip %s' % pgip)
                    #            print page_str
                    #            continue
                    #    page_contents = [pc.strip() for pc in page_root.xpath('//div[@id="BookText"]/text()') if pc.strip()]
                    #    if not page_contents:
                    #        cptOne.paragraphs.append(page_str.strip())
                    #        continue
                    #    for pgraf in page_contents:
                    #        cptOne.paragraphs.append(pgraf)
                    #    cptOne.status = 1
                    #    print ('[%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),cptOne.title))

                    bookOne.status =1
                    upsertBook(bookOne)
                    print unicode(bookOne.name)
                    bookOne = None
                except Exception,e:
                    traceback.print_exc()
                    upsertBook(bookOne)
