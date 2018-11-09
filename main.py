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
import  datetime

import traceback

reload(sys)
sys.setdefaultencoding('utf-8')
from IPProxyPool.config import Data, typelist


def traditio2simple(sentence):
    #return sentence
    sentence = Converter('zh-hans').convert(sentence)
    sentence.encode('utf-8')
    return sentence


def upsertBook(modl):
    try:
        if book_db.find_one({'name': modl.name}):
            print('book: %s in db already' % modl.name)
        else:
            book_db.insert_one(modl.to_dict())
    except Exception,e:
        print('db error:%s'% modl.name)

from pymongo import MongoClient

client = MongoClient('127.0.0.1', 27017)
book_db = client.web.book
if __name__ == "__main__":
    for tp in typelist:
        if not tp:
            continue
        for i in range(tp.pages + 1)[1:]:
            s = tp.name
            host1  = 'http://www.zhsxs.com'
            host = 'http://tw.zhsxs.com'
            urll = host + '/zhslist/' + s.encode('utf-8') + '_' + str(i) + '.html'
            try:
                response = Html_Downloader.downloadProxy((urll))
                root = etree.HTML(traditio2simple(response))
                rows = root.xpath('//*[@id = "newest"]//tr[@class="odd" or @class="even"]')
                for ri, r in enumerate(rows):
                    try:
                        bookOne = Data()
                        fenlei = r.xpath('*[@class="td1"]/a//text()')[0].strip()
                        last_page = r.xpath('*[@class="td3"]/a/text()')[0].strip()
                        author = r.xpath('*[@class="td4"][1]/text()')[0].strip()
                        last_time = r.xpath('*[@class="td5"]/text()')[0].strip()
                        book = r.xpath('*[@class="td2"]/a//text()')[0].strip()
                        bookOne.id = str(tp.base) + str(i + 200) + str(ri+ 600)
                        bookOne.type = fenlei
                        bookOne.name = book
                        bookOne.author = author
                        bookOne.chapters = []
                        bookOne.flags = [bookOne.type]
                        bookOne.image = ''
                        bookOne.click = 0
                        bookOne.status = 0
                        book_url = host + r.xpath('*[@class="td2"]//@href')[0].strip()
                        book_str = Html_Downloader.downloadProxy((book_url))
                        book_root = etree.HTML(traditio2simple(book_str))
                        bookOne.url = book_url

                        for flag in book_root.xpath('//td[@class="style2"]//div[2]/a[position()>1 and position() < last()-1]//text()'):
                            bookOne.flags.append(flag)
                        bookOne.profile = book_root.xpath('//td[@class="style2"]//div[2]//p')[1].tail[6:]
                        if book_root.xpath('//td/img/@src'):
                            img_url = book_root.xpath('//td/img/@src')[0].strip()
                            bookOne.image = bookOne.id + os.path.splitext(img_url)[1]
                            bookOne.srcImg = os.path.basename(img_url)
                            if img_url.find(host)> -1 or img_url.find(host1) > -1:
                                Html_Downloader.downimage(img_url, bookOne.image)
                            else:
                                Html_Downloader.downimage(host + img_url, bookOne.image)

                        ###chapter
                        chapter_url = host + '/zhschapter/' + book_url.strip('http://tw.zhsxs.com/zhsbook/')
                        cpt_str = Html_Downloader.downloadProxy((chapter_url))
                        cpt_root = etree.HTML(traditio2simple(cpt_str))
                        cpt_list = cpt_root.xpath('//td[@class="chapterlist"]/a')
                        for cpt in cpt_list:
                            page_title = cpt.text.strip()
                            page_url = host + cpt.attrib['href'].strip()
                            chapterOne = Data()
                            chapterOne.title = page_title
                            chapterOne.url = page_url
                            chapterOne.status = 0
                            chapterOne.readcount = 0
                            chapterOne.paragraphs = []
                            chapterOne.writetime = ''
                            chapterOne.intime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            bookOne.chapters.append(chapterOne)
                            del chapterOne

                        for cptOne in bookOne.chapters:
                            page_str = Html_Downloader.downloadProxy((cptOne.url))
                            if not page_str:
                                continue
                            page_root = etree.HTML(traditio2simple(page_str))
                            page_contents = page_root.xpath('//table[last()]//div[5]//text()[position()>1 and position()<last()]')
                            if not page_contents:
                                cptOne.paragraphs.append(page_str.strip())
                                continue
                            for pgraf in page_contents:
                                if pgraf.strip():
                                    cptOne.paragraphs.append(pgraf.strip())
                            if cptOne.title in cptOne.paragraphs and cptOne.paragraphs.index(cptOne.title) < len(cptOne.paragraphs) / 2:
                                cptOne.paragraphs = cptOne.paragraphs[cptOne.paragraphs.index(cptOne.title) + 1:]
                            cptOne.status = 1

                        bookOne.status =1
                        upsertBook(bookOne)
                    except Exception,e:
                        traceback.print_exc()
                        print('book error')
            except Exception,e:
                traceback.print_exc()
                print('all error')
print(3)
