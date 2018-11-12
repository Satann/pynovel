# -*- coding: utf-8 -*-
# filename: main.py
import time, requests, chardet, web, sqlalchemy, gevent
from IPProxyPool.spider.HtmlDownloader import Html_Downloader
from lxml import etree
from langconv import *
import urllib
import types, os
import json
import chardet
import datetime
from pymongo.errors import DuplicateKeyError
import traceback,hashlib
from pymongo import MongoClient
import re

reload(sys)
sys.setdefaultencoding('utf-8')
from IPProxyPool.config import Data, gegelist

client = MongoClient('127.0.0.1', 27017)
book_db = client.web.book

def traditio2simpl(sentence):
    # return sentence
    sentence = Converter('zh-hans').convert(sentence)
    sentence.encode('utf-8')
    return sentence


def upsertBook(modl):
    try:
        if book_db.find_one({'name': modl.name}):
            book_db.update_one({'name': modl.name}, {'$set': {'id': modl.id, 'image': modl.image}})
        else:
            book_db.insert_one(modl.to_dict())
    except DuplicateKeyError, e:
        pass
    except Exception, e:
        print('db error:%s' % modl.name)


def updateId(modl):
    try:
        book_db.update_one({'name': modl.name}, {'$set': {'id': modl.id, 'image': modl.image, 'srcImg': modl.srcImg}})
    except Exception, e:
        print traceback.print_exc()
        print('db error:%s' % modl.name)



if __name__ == "__main__":
    fenlist = 0
    while fenlist < len(gegelist):
        tp = gegelist[fenlist]
        fenlist += 1
        if not tp:
            continue

        j = 1
        while j < tp.pages + 1:
            j += 1
            s = tp.name
            host = 'http://www.ggdown.com'
            urll = host + str(tp.prefix) + str(j - 1) + '.html'
            while True:
                try:
                    pip, response = Html_Downloader.downloadProxy((urll))
                    response = response.encode('latin-1')
                    root = etree.HTML(response)
                    rows = root.xpath('//ul[@class = "item-con"]/li')
                    pip = None
                    #response = None
                    break
                except UnicodeDecodeError,e:
                    response = response.decode('gbk', 'ignore')
                    root = etree.HTML(response)
                    rows = root.xpath('//ul[@class = "item-con"]/li')
                    pip = None
                    break
                except Exception, e:
                    if e.message == 'No JSON object could be decoded':
                        continue
                    if pip and response != None:
                        requests.get('http://127.0.0.1:8008/delete?ip=%s' % pip)
                        print ('aoyumen response error, deeltip %s' % pip)
                    traceback.print_exc()
                    print ('[#####]fenlei error: %s' % response)
                    continue
            for ri, r in enumerate(rows):
                try:
                    bookOne = Data()
                    fenlei = r.xpath('*[@class="s1"]/text()')[0].strip()
                    book = r.xpath('*[@class="s2"]/a[1]//text()')[0].strip()
                    book_url = r.xpath('*[@class="s2"]/a[1]//@href')[0].strip()
                    if book_url.find(host) == -1:
                        book_url = host + book_url
                    author = r.xpath('*[@class="s3"]/text()')[0].strip()
                    last_time = r.xpath('*[@class="s4"]/text()')[0].strip()
                    last_page = r.xpath('*[@class="s2"]/i/a/text()')[0].strip()
                    bookOne.id = str(tp.base) + str(j - 1 + 1000) + str(ri + 1000)
                    bookOne.type = fenlei[1:-1] if len(fenlei) > 1 and fenlei[1:-1] else ''
                    bookOne.name = book
                    bookOne.author = author
                    if not book or not author:
                        pass
                    bookOne.chapters = []
                    bookOne.flags = [bookOne.type] if bookOne.type else []
                    bookOne.image = ''
                    bookOne.srcImg = ''
                    bookOne.click = 0
                    bookOne.status = 0
                    bookOne.state = 0
                    bookOne.numbers = 0
                    bookOne.recommend = 0
                    bookOne.url = book_url

                    while True:
                        try:
                            bip, book_str = Html_Downloader.downloadProxyLittle((book_url))
                            book_str = book_str.encode('latin-1')
                            book_root = etree.HTML(book_str)
                            bip = None
                            break
                        except UnicodeDecodeError,e:
                            book_str = book_str.decode('gbk', 'ignore')
                            book_root = etree.HTML(book_str)
                            pip = None
                            break
                        except Exception,e:
                            if e.message == 'No JSON object could be decoded':
                                continue
                            print traceback.print_exc()
                            if bip and book_str != None:
                                requests.get('http://127.0.0.1:8008/delete?ip=%s' % bip)
                                print ('book response error, deeltip %s' % bip)
                                print book_str
                            continue

                    try:
                        num_str = ''.join(book_root.xpath('//p[@class="book-stats"]/text()'))
                        num_res = re.search('\d+', num_str)
                        if num_res:
                            ff = num_res.group()
                            if len(ff) > 4:
                                bookOne.numbers = int(ff)
                            else:
                                pass

                        ###img
                        if book_root.xpath('//div[@class="book-img"]/img/@src'):
                            img_url = book_root.xpath('//div[@class="book-img"]/img/@src')[0].strip()
                            imgpath = hashlib.md5((bookOne.name + bookOne.author).encode('gbk')).hexdigest() + os.path.splitext(img_url)[1]
                            if img_url.find(host) == -1:
                                img_url = host + img_url if img_url[0] == '/' else host + '/' + img_url
                            bookOne.srcImg = img_url
                            imgret = Html_Downloader.downimage(img_url, imgpath)
                            if imgret:
                                bookOne.image = imgpath
                                imgret = None

                        ###url
                        book_url = book_root.xpath('//*[@class="book-link"]//a[2]//@href')[0].strip()
                        if book_url.find(host) == -1:
                            book_url = host + book_url if book_url[0] == '/' else host + '/' + book_url
                    except Exception, e:
                        print traceback.print_exc()
                    if book_db.find_one({'name': bookOne.name}):
                        updateId(bookOne)
                        bookOne = None
                        continue

                    ###chapters
                    while True:
                        try:
                            bip, page_str = Html_Downloader.downloadProxyLittle((book_url))
                            page_str = page_str.encode('latin-1')
                            page_root = etree.HTML(page_str)
                            bip = None
                            break
                        except UnicodeDecodeError,e:
                            page_str = page_str.decode('gbk', 'ignore')
                            page_root = etree.HTML(page_str)
                            pip = None
                            break
                        except Exception,e:
                            if e.message == 'No JSON object could be decoded':
                                continue
                            print traceback.print_exc()
                            if bip and page_str != None:
                                requests.get('http://127.0.0.1:8008/delete?ip=%s' % bip)
                                print ('book response error, deeltip %s' % bip)
                                print page_str
                            continue
                    bookOne.profile = ''.join(page_root.xpath('//p[@class="intro"]/text()')).strip()
                    cpt_list = page_root.xpath('//*[@class="chapterlist"]//a')
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
                        if page_title.find('ggdown.com') > -1:
                            page_title = page_title[page_title.find('ggdown.com') + len('ggdown.com') + 1:]
                        if page_title.find('GGDOWN.COM') > -1:
                            page_title = page_title[page_title.find('GGDOWN.COM') + len('GGDOWN.COM') + 1:]
                        page_url = cpt.attrib['href'].strip()
                        if page_url.find(host) == -1:
                            preff = ''
                            if page_url[0] != '/':
                                preff = '/'
                            page_url = '/'.join(book_url.split("/")[:-1]) + preff + page_url
                        chapterOne.title = page_title
                        chapterOne.url = page_url
                        bookOne.chapters.append(chapterOne)
                        del chapterOne

                    bookOne.status = 1
                    upsertBook(bookOne)
                    print bookOne.name
                    bookOne=None
                except Exception, e:
                    traceback.print_exc()
                    upsertBook(bookOne)
                    print('book error')
print(3)
