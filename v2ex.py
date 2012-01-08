#!/usr/bin/env python
# encoding=utf-8

import os, sys
import logging
import curses
import time
import locale
import json
import re
import traceback
import yaml
import socket
from urllib import urlopen, urlencode
from BeautifulSoup import BeautifulSoup

locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
runtime_dir = os.path.realpath(os.path.dirname(__file__))
settings = yaml.load(file(os.path.join(runtime_dir + '/settings.vx'), 'r'))
fmt = '%(asctime)s [%(levelname)s,%(lineno)s] %(message)s'
filename = os.path.join(runtime_dir, 'v2ex.log')
logging.basicConfig(level=logging.DEBUG, filename=filename, format=fmt)
logger = logging.getLogger(__name__)
last = 0

# 很黄很暴力
class API(object):
    def __init__(self):
        pass

    def replies(self, topic_html):
        doc = BeautifulSoup(''.join(topic_html.replace('\r', '')))
        r = doc.findAll(id='replies')[0]
        items = []
        for reply in r.findAll('div', recursive=0):
            item = {}
            item['by'] = reply.find(attrs={'class':'dark'}).string
            item['content'] = reply.find(attrs={'class':'sep5'}).nextSibling.nextSibling.findAll(text=True)
            item['reply_meta'] = reply.find('small').contents[0].replace('&nbsp;', '').strip()
            items.append(item)
        return items

class V2EX(object):
    def __init__(self, sc, settings):
        self.sc = sc
        self.rows = curses.tigetnum('lines')
        self.cols = curses.tigetnum('cols')
        logger.debug('terminal size: %dx%d' % (self.cols, self.rows))
        self.settings = settings
        logo = os.path.join(runtime_dir, 'logo', self.settings['logo'])
        logger.debug('logo: %s' % logo)
        self.logo = open(logo, 'r').readlines()
        self.padding_left = int(self.settings['padding-left'])
        self.last = 0
        self.buf = []
        self.nav = []
        self.p = 1

        self.render()

    def rmline(self, linenum):
        if linenum < self.rows:
            logger.debug('remove line: %d of %d' % (linenum, self.rows))
            logger.debug('%d' % len(' ' * (self.cols - 1)))
            self.sc.addstr(linenum, 0, ' ' * (self.cols - 1), curses.color_pair(7))

    # get data from internet
    def get_data(self, url, params=None):
        logger.debug('retrieve data from: %s' % url)
        logger.debug(params)
        try:
            if not params:
                logger.debug('GET')
                rs = urlopen(url)
            else:
                logger.debug('POST')
                rs = urlopen(url, urlencode(params))
            data = rs.read()
            #logger.debug('data: %s' % data)
            return data
        except socket.timeout, e:
            logger.error(e)
            self.error('timed out.')
        except socket.error, e:
            logger.error(e)
            self.error('socket error.')
        except Exception, e:
            logger.error(e)
            logger.error(traceback.print_exc())

    def get_json(self, url, params=None):
        try:
            return json.loads(self.get_data(url, params))
        except Exception, e:
            logger.error(e)
            logger.error(traceback.print_exc())

    def pageize(self):
        if isinstance(self.buf, dict):
            return
        logger.debug('pageize.')
        pages = {}
        p = []
        c = 1
        for item in self.buf:
            p.append(item)
            if item[-2]:
                self.last += 1

            if self.last > self.rows - 4:
                pages[c] = p
                p = []
                c += 1
                self.layout()

        if len(pages):
            if len(p) > 0:
                pages[c] = p
            self.buf = pages
            logger.info('total %d pages.' % len(pages))
            for p, data in pages.items():
                logger.debug("page %d: `%s'" % (p, data[0][1]))
        self.layout()

    def render(self):
        self.layout()
        self.pageize()

        if isinstance(self.buf, dict):
            buf = self.buf[self.p]
            logger.debug('go to page: %d' % self.p)
            if self.p != 1:
                logger.debug("`%s'" % buf[0][1])
            if len(self.buf) > 1:
                self.sc.addstr(self.rows - 2, self.padding_left, '(', curses.color_pair(4))
                self.sc.addstr(self.rows - 2, self.padding_left + 1, '%d' % self.p, curses.color_pair(3))
                self.sc.addstr(self.rows - 2, self.padding_left + len(str(self.p)) + 1, ' of ', curses.color_pair(7))
                self.sc.addstr(self.rows - 2, self.padding_left + len(str(self.p)) + 5, '%d' % len(self.buf), curses.color_pair(3))
                self.sc.addstr(self.rows - 2, self.padding_left + len(str(self.p)) + 6, ')', curses.color_pair(4))
        else:
            buf = self.buf

        for (padding, text, attr, newline, x) in buf:
            if x:
                self.sc.addstr(x, padding, text, attr)
            else:
                self.sc.addstr(self.last, padding, text, attr)
            if newline:
                self.last += 1

            if self.last > self.rows - 4:
                logger.warn('render overflow.')
                break
        self.sc.refresh()
        if not isinstance(self.buf, dict):
            self.buf = []

    # append to content buffer
    def w(self, padding, text, attr, newline=True, x=None):
        if not isinstance(self.buf, dict):
            self.buf.append((padding, text, attr, newline, x))

    # append new line to content buffer
    def n(self):
        self.w(self.padding_left, '', curses.color_pair(7))

    # logo and default status line
    def layout(self):
        self.last = 0
        self.sc.erase()
        for line in self.logo:
            self.sc.addstr(self.last, self.padding_left, line, curses.color_pair(4) | curses.A_BOLD)
            self.last += 1
        self.last += 1
        for (padding, text, attr, newline, x) in self.nav:
            if x:
                self.sc.addstr(x, padding, text, attr)
            else:
                self.sc.addstr(self.last, padding, text, attr)
            if newline:
                self.last += 1
        self.status()

    # default status line
    def status(self):
        x = self.rows - 1
        self.sc.addstr(x, self.padding_left, "`*'", curses.color_pair(2))
        self.sc.addstr(x, 5, "- shortcut", curses.color_pair(7))

        self.sc.addstr(x, 17, "`h'", curses.color_pair(2))
        self.sc.addstr(x, 21, "- home", curses.color_pair(7))

        self.sc.addstr(x, 29, "`q'", curses.color_pair(2))
        self.sc.addstr(x, 33, "- quit", curses.color_pair(7))

    # display error message
    def error(self, message):
        msg = message
        if len(message) < self.cols:
            message += ' ' * (self.cols - len(message) - 13)
        logger.debug("message[%d]: `%s'" % (len(message), msg))
        self.sc.addstr(self.rows - 1, self.padding_left, 'Oh, shit: ', curses.color_pair(1) | curses.A_BOLD)
        self.sc.addstr(self.rows - 1, self.padding_left + 10, message, curses.color_pair(7) | curses.A_BOLD)
        self.sc.refresh()

    # display loading message
    def loading(self, message):
        msg = message
        if len(message) < self.cols:
            message += ' ' * (self.cols - len(message) - 14)
        logger.debug("message[%d]: `%s'" % (len(message), msg))
        self.sc.addstr(self.rows - 1, self.padding_left, 'Loading ... ', curses.color_pair(3) | curses.A_BOLD)
        self.sc.addstr(self.rows - 1, self.padding_left + 12, message, curses.color_pair(7) | curses.A_BOLD)
        self.sc.refresh()

    def home(self):
        self.loading('latest topics.')
        self.buf = []
        self.nav = []
        self.nav.append((self.padding_left, '最新主题', curses.color_pair(1), True, None))
        self.nav.append((self.padding_left, '', curses.color_pair(7), True, None))

        def topic(author, node, reply, title, l=None, i=None):
            self.w(self.padding_left, "`%x'" % i, curses.color_pair(2), False)
            offset = 6
            self.w(offset, author, curses.color_pair(5), False)
            offset = offset + len(author) + 1
            self.w(offset, 'in', curses.color_pair(7), False)
            offset = offset + 3
            self.w(offset, node.encode('utf8'), curses.color_pair(3), False)
            self.w(offset + len(node.encode('gbk')) + 1, '收到 %s 回复' % reply, curses.color_pair(7))
            self.w(6, title.encode('utf8'), curses.color_pair(4) | curses.A_BOLD)
            self.n()

        url = '%sapi/topics/latest.json' % self.settings['api_url']
        topics = self.get_json(url)
        logger.info('latest topics: %d' % len(topics))

        index = 0
        shortcuts = {}
        for t in topics[0:16]:
            #logger.info(t['member']['username'])
            #logger.info(t['node']['title'])
            #logger.info(t['replies'])
            #logger.info(t['title'])
            key = '%x' % index
            shortcuts[key] = t['id']
            topic(t['member']['username'], t['node']['title'], t['replies'], t['title'], None, index)
            index = index + 1

        self.render()
        return shortcuts

    def show(self, id):
        self.nav = []
        self.buf = []
        self.p = 1
        self.loading('topic %s' % str(id))
        url = '%sapi/topics/show.json?id=%s' % (self.settings['api_url'], str(id))
        t = self.get_json(url)

        #logger.info(t)
        logger.info('title: %s' % t['title'])
        logger.info('node: %s' % t['node']['name'])
        #logger.info('node: %s' % t['node']['title'])
        logger.info('user: %s' % t['member']['username'])
        logger.info('content: %s' % t['content'])
        logger.info('replies: %s' % t['replies'])

        nav = '%s › %s' % (self.settings['title'], t['node']['name'].encode('utf8'))
        self.nav.append((self.padding_left, nav, curses.color_pair(1) | curses.A_BOLD, True, None))
        self.nav.append((self.padding_left, '', curses.color_pair(7), True, None))

        self.nav.append((self.padding_left, t['title'].encode('utf8'), curses.color_pair(1) | curses.A_BOLD, True, None))
        self.nav.append((self.padding_left, 'By', curses.color_pair(7), False, None))
        self.nav.append((self.padding_left + 3, t['member']['username'], curses.color_pair(5), True, None))
        self.nav.append((self.padding_left, '', curses.color_pair(7), True, None))

        lines = []
        content = t['content'].replace('\r', '\n').replace('\n\n', '\n').split('\n')
        for line in content:
            self.w(self.padding_left, line.encode('utf-8'), curses.color_pair(7))

        self.n()
        self.w(self.padding_left, '共收到', curses.color_pair(3), False)
        self.w(self.padding_left + 7, '%s' % t['replies'], curses.color_pair(2), False)
        self.w(self.padding_left + 8 + len(str(t['replies'])), '条回复', curses.color_pair(3))
        self.n()

        if int(t['replies']) > 0:
            url = '%st/%s' % (self.settings['api_url'], str(id))
            logger.info(url)
            api = API()
            replies = api.replies(self.get_data(url))
            url = '%sapi/replies/show.json?topic_id=%s' % (self.settings['api_url'], t['id'])
            #replies = self.get_json(url)
            #logger.info(self.get_json(url))
            logger.info(replies)
            for reply in replies:
                meta = re.search(r'^(#\d+)', reply['reply_meta'])
                meta = meta.group(0)
                reply['reply_meta'] = reply['reply_meta'].replace(meta, '')
                logger.info('meta: %s [%s]' % (meta, type(meta)))
                meta = meta.encode('utf-8')
                self.w(self.padding_left, meta, curses.color_pair(4), False)
                self.w(self.padding_left + len(meta), reply['reply_meta'], curses.color_pair(7), False)
                self.w(self.padding_left + len(meta + reply['reply_meta']) + 1, reply['by'], curses.color_pair(5))

                for line in reply['content']:
                    self.w(self.padding_left, line.encode('utf8'), curses.color_pair(7))
                self.n()

        self.render()

if __name__ == '__main__':
    logger.debug('V2EX terminal startup.')
    logger.debug("set terminal title: `%s'" % settings['title'])
    sys.stdout.write('\x1b]0;%s\x07' % settings['title'])
    sys.stdout.flush()
    logger.debug(settings)
    try:
        sc = curses.initscr()
        """if curses.has_colors():
            sys.stderr.write('your terminal is not support colors.')
            sys.stderr.flush()
            raise Exception"""
        curses.noecho()
        curses.cbreak()
        sc.keypad(1)
        #sc.idlok(1)
        logger.info("terminal: `%s'", curses.termname())
        # sc.border(0)
        #sc.scrollok(True)
        
        # init colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

        # set background
        sc.bkgdset(curses.color_pair(7))

        v2ex = V2EX(sc, settings)
        topics_shortcuts = v2ex.home()

        # process keyboard events
        latest = {'location':'home'}
        while True:
            key = sc.getch()
            if key < 256:
                key = chr(key)
            if key in topics_shortcuts:
                logger.info('enter: %s' % key)
                topic_id = topics_shortcuts[key]
                logger.info('topic_id: %s' % str(topic_id))
                v2ex.show(topic_id)
                latest['location'] = 'topic'
                latest['topic_id'] = topic_id
            elif key == 'h':
                logger.info('home')
                topics_shortcuts = v2ex.home()
                latest['location'] = 'home'
            elif key == 'r':
                if latest['location'] == 'home':
                    logger.info('go to Home')
                    topics_shortcuts = v2ex.home()
                    latest['location'] = 'home'
                elif latest['location'] == 'topic' and 'topic_id' in latest:
                    logger.info('go to topic_id: %s' % str(latest['topic_id']))
                    v2ex.show(latest['topic_id'])
                    latest['location'] = 'topic'
                    latest['topic_id'] = latest['topic_id']
            elif key == curses.KEY_RIGHT:
                if v2ex.p + 1 <= len(v2ex.buf):
                    v2ex.p += 1
                    logger.info('page down.')
                    v2ex.render()
            elif key == curses.KEY_LEFT:
                if v2ex.p - 1 > 0:
                    v2ex.p -= 1
                    logger.info('page down.')
                    v2ex.render()
            elif key == 'q':
                #sc.addstr(v2ex.rows - 1, v2ex.padding_left, ' ' * (v2ex.rows - 2), curses.color_pair(7) | curses.A_BOLD)
                v2ex.rmline(v2ex.rows - 1)
                sc.addstr(v2ex.rows - 1, v2ex.padding_left, 'Do you want to exit? (y/n)', curses.color_pair(3) | curses.A_BOLD)
                sc.refresh()
                ch = sc.getch()
                if ch < 256 and chr(ch).lower() == 'y':
                    logger.info('exited.')
                    break
                else:
                    v2ex.rmline(v2ex.rows - 1)
                    #sc.addstr(v2ex.rows - 1, v2ex.padding_left, ' ' * (v2ex.rows - 2), curses.color_pair(7) | curses.A_BOLD)
                    v2ex.status()
                    sc.refresh()
            else:
                if isinstance(key, str) and key.isalpha():
                    key = ord(key)
                logger.debug("Enter: `%s'" % curses.keyname(key))

    except Exception, e:
        logger.critical(e)
        logger.critical(traceback.print_exc())
    finally:
        curses.nocbreak()
        curses.echo()
        curses.endwin()
