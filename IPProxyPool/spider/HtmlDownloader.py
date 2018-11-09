# coding:utf-8

import random, sys

import config
import json
from db.DataStore import sqlhelper
from time import sleep
import datetime

__author__ = 'qiye'

import requests
import chardet

httpcount = 0
ipdict = {}


class Html_Downloader(object):
    @staticmethod
    def download(url):
        try:
            r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT)
            r.encoding = chardet.detect(r.content)['encoding']
            if (not r.ok) or len(r.content) < 500:
                raise ConnectionError
            else:
                return r.text
        except Exception:  #
            count = 0  # 重试次数
            proxylist = sqlhelper.select(100)
            if not proxylist:
                return None

            while count < config.RETRY_TIME:
                try:
                    proxy = random.choice(proxylist)
                    ip = proxy[0]
                    port = proxy[1]
                    proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}

                    r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
                    r.encoding = chardet.detect(r.content)['encoding']
                    if (not r.ok) or len(r.content) < 500:
                        raise ConnectionError
                    else:
                        return r.text
                except Exception:
                    count += 1

        return None

    @staticmethod
    def downloadProxy(url):
        count = 0  # 重试次数
        ip = None
        while count < config.RETRY_TIME:
            r127 = requests.get('http://127.0.0.1:8000/?types=0&count=10')
            if not r127.text: continue
            ip_ports = json.loads(r127.text)
            if not ip_ports:
                r127 = requests.get('http://127.0.0.1:8000/?types=2')
                ip_ports = json.loads(r127.text)
                if not ip_ports:
                    # raise Exception('no proxy')
                    print ('no proxy')
                    proxies = {}
            if ip_ports:
                proxy = random.choice(ip_ports)
                ip = proxy[0]
                port = proxy[1]
                proxies = {
                    'http': 'http://%s:%s' % (ip, port),
                    'https': 'http://%s:%s' % (ip, port)
                }
            global httpcount
            httpcount += 1
            if httpcount % 20 == 0:
                proxies = {}
                ip = None
            try:
                if proxies:
                    r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
                else:
                    r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT)
                # r.encoding = chardet.detect(r.content)['encoding']
                if 'r' in dir():
                    if r.text.find('Welcome To Zscaler Directory Authentication') > -1 or r.text.find(
                            'https://shared.ydstatic.com/images/favicon') > -1 or r.text.find(
                        'nonAvailableApplicationServers') > -1 or r.text.find(
                        'FILE: /home/website/thundersoft_new/ThinkPHP/Common/functions') > -1 or r.text.find(
                        'Your browser is not supported, click') > -1 or r.text.find(
                        'is not available because it is categorized as') > -1 or r.text.find(
                        'bottom navbar-fixed-bottom text-center padding-top padding-bottom ng-scope') > -1 or r.text == unicode(
                        '在线用户数超过了序列号允许。您需要购买或升级您的序列号。') or r.text == unicode(
                        '在線用戶數超過了序列號允許。您需要購買或升級您的序列號。') or r.text.find('is external user, blocked') > -1 or r.text.find(
                        unicode('验证结果: 禁止外部用户')) > -1 or r.text.find(unicode('您的访问非法！","time":"')) > -1 or r.text.find(
                        's permission. You need to purchase or upgrade your license') > -1 or r.text.find(
                        '<h1>Unauthorized ...</h1>') > -1 or r.text.find('Maximum number of open connections reached') > -1 or r.text.find(
                        unicode('净网卫士是江苏电信面向广大家长用户提供的一项增值服务')) > -1 or r.text.find(
                        '<head><title>404 Not Found</title></head>') > -1 or r.text.find(
                        '<title>404 - Not Found</title>') > -1 or r.text.find('<address>Apache/2.4.25 (Debian) Server a') > -1:
                        if ip:
                            requests.get('http://127.0.0.1:8000/delete?ip=%s' % ip)
                            print ('r.text.find, deeltip %s' % ip)
                        continue
                    if len(r.text) < 400 and r.status_code == 200:
                        if ip:
                            requests.get('http://127.0.0.1:8008/delete?ip=%s' % ip)
                            print ('r.text < 400, deeltip %s' % ip)
                            print r.text
                        continue
                if (not r.ok):  # if r.status_code != 200:  # or len(r.content) < 500:
                    if len(r.content) < 500:
                        print r.content
                    raise ConnectionError
                else:
                    if ip and proxies:
                        # print ('[%s]page ip: %s' % (datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S'), ip))
                        ipdict[ip] = 0
                    tmp = r.text
                    del r
                    return ip, tmp
            except Exception, e:
                count += 1
                sleep(0.1)
                if ip:
                    ct = ipdict.get(ip, 0)
                    ipdict[ip] = ct + 1
                    if ct > 16:
                        ipdict.pop(ip)
                        requests.get('http://127.0.0.1:8000/delete?ip=%s' % ip)
                        print ('count max, deeltip %s' % ip)

        return None, None

    @staticmethod
    def downloadProxyLittle(url):
        count = 0  # 重试次数
        ip = None
        while count < config.RETRY_TIME:
            global httpcount
            httpcount += 1
            if httpcount % 20 != 0:
                proxies = {}
                ip = None
            else:
                r127 = requests.get('http://127.0.0.1:8000/?types=0&count=10')
                if not r127.text: continue
                ip_ports = json.loads(r127.text)
                if not ip_ports:
                    r127 = requests.get('http://127.0.0.1:8000/?types=2')
                    ip_ports = json.loads(r127.text)
                    if not ip_ports:
                        # raise Exception('no proxy')
                        print ('no proxy')
                        proxies = {}
                if ip_ports:
                    proxy = random.choice(ip_ports)
                    ip = proxy[0]
                    port = proxy[1]
                    proxies = {
                        'http': 'http://%s:%s' % (ip, port),
                        'https': 'http://%s:%s' % (ip, port)
                    }
            try:
                if proxies:
                    r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
                else:
                    r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT)
                # r.encoding = chardet.detect(r.content)['encoding']
                if 'r' in dir():
                    if r.text.find('Welcome To Zscaler Directory Authentication') > -1 or r.text.find(
                            'https://shared.ydstatic.com/images/favicon') > -1 or r.text.find(
                        'nonAvailableApplicationServers') > -1 or r.text.find(
                        'FILE: /home/website/thundersoft_new/ThinkPHP/Common/functions') > -1 or r.text.find(
                        'Your browser is not supported, click') > -1 or r.text.find(
                        'is not available because it is categorized as') > -1 or r.text.find(
                        'bottom navbar-fixed-bottom text-center padding-top padding-bottom ng-scope') > -1 or r.text == unicode(
                        '在线用户数超过了序列号允许。您需要购买或升级您的序列号。') or r.text == unicode(
                        '在線用戶數超過了序列號允許。您需要購買或升級您的序列號。') or r.text.find('is external user, blocked') > -1 or r.text.find(
                        unicode('验证结果: 禁止外部用户')) > -1 or r.text.find(unicode('您的访问非法！","time":"')) > -1 or r.text.find(
                        's permission. You need to purchase or upgrade your license') > -1 or r.text.find(
                        '<h1>Unauthorized ...</h1>') > -1 or r.text.find('Maximum number of open connections reached') > -1 or r.text.find(
                        unicode('净网卫士是江苏电信面向广大家长用户提供的一项增值服务')) > -1 or r.text.find(
                        '<head><title>404 Not Found</title></head>') > -1 or r.text.find(
                        '<title>404 - Not Found</title>') > -1 or r.text.find('<address>Apache/2.4.25 (Debian) Server a') > -1:
                        if ip:
                            requests.get('http://127.0.0.1:8000/delete?ip=%s' % ip)
                            print ('r.text.find, deeltip %s' % ip)
                        continue
                    if len(r.text) < 400 and r.status_code == 200:
                        if ip:
                            requests.get('http://127.0.0.1:8008/delete?ip=%s' % ip)
                            print ('r.text < 400, deeltip %s' % ip)
                            print r.text
                        continue
                if (not r.ok):  # if r.status_code != 200:  # or len(r.content) < 500:
                    if len(r.content) < 500:
                        print r.content
                    raise ConnectionError
                else:
                    if ip and proxies:
                        # print ('[%s]page ip: %s' % (datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S'), ip))
                        ipdict[ip] = 0
                    tmp = r.content
                    del r
                    return ip, tmp
            except Exception:
                count += 1
                sleep(0.1)
                print 'little exception'
                if ip:
                    ct = ipdict.get(ip, 0)
                    ipdict[ip] = ct + 1
                    if ct > 16:
                        ipdict.pop(ip)
                        requests.get('http://127.0.0.1:8000/delete?ip=%s' % ip)
                        print ('count max, deeltip %s' % ip)

        return None, None

    @staticmethod
    def downimage(url, img_path):
        count = 0  # 重试次数
        proxylist = sqlhelper.select(100)
        if not proxylist:
            return None
        while count < config.RETRY_TIME:
            try:
                proxy = random.choice(proxylist)
                ip = proxy[0]
                port = proxy[1]
                proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}
                print ('img ip: %s' % ip)
                r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
                r.encoding = chardet.detect(r.content)['encoding']
                if r.status_code == 200:
                    if len(r.content) < 500:
                        continue
                    with open(config.image_path_base + img_path, 'wb') as file:
                        file.write(r.content)
                    del r
                    return None
            except Exception:
                sleep(0.1)
                count += 1
        return None
