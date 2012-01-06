#!/usr/bin/env python
# encoding=utf-8

import os, sys
import logging
logging.basicConfig(level=logging.DEBUG, filename='v2ex.log')
import curses
import time
import locale
locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
from urllib import urlopen, urlencode
import json
import traceback
import yaml
settings = yaml.load(file(os.path.abspath(os.path.dirname(__file__)) + '/settings.vx', 'r'))

title = 'V2EX'

if __name__ == '__main__':
    sys.stdout.write('\x1b]0;%s\x07' % title)
    sys.stdout.flush()
    logging.info(settings)
    runtime_dir = os.path.realpath(os.path.dirname(__file__))
    logo = os.path.join(runtime_dir, 'logo', settings['logo'])
    logging.info(logo)
    try:
        sc = curses.initscr()
        curses.start_color()
        rows = curses.tigetnum('lines')
        cols = curses.tigetnum('cols')
        logging.info('lines: %d' % curses.tigetnum('lines'))
        logging.info('cols: %d' % curses.tigetnum('cols'))
        padding_left = int(settings['padding-left'])
        # sc.border(0)
        
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
        sc.bkgdset(curses.color_pair(7))
        
        last = 0
        #sc.addstr(0, 1, title, curses.color_pair(4) | curses.A_BOLD)
        for line in open(logo, 'r').readlines():
            sc.addstr(last, padding_left, line, curses.color_pair(4) | curses.A_BOLD)
            last += 1

        #sc.addstr(4, 6, '= way to explore', curses.color_pair(7) | curses.A_BOLD)
        sc.addstr(last + 1, padding_left, '最新主题', curses.color_pair(1))
        last += 3

        sc.addstr(rows - 1, padding_left, "`*'", curses.color_pair(6))
        sc.addstr(rows - 1, 5, "- shortcut", curses.color_pair(2))

        
        def topic(author, node, reply, title, l, i):
            i = str(i)
            logging.info('last: %d' % l)
            sc.addstr(l, padding_left, "`%s'" % i, curses.color_pair(2))
            offset = 6
            sc.addstr(l, offset, author, curses.color_pair(5))
            offset = offset + len(author) + 1
            sc.addstr(l, offset, 'in', curses.color_pair(7))
            offset = offset + 3
            sc.addstr(l, offset, node.encode('utf8'), curses.color_pair(3))
            sc.addstr(l, offset + len(node.encode('gbk')) + 1, '收到 %s 回复' % reply, curses.color_pair(7))
            sc.addstr(l + 1, 6, title.encode('utf8'), curses.color_pair(4) | curses.A_BOLD)

        url = 'http://www.v2ex.com/api/topics/latest.json'
        rs = urlopen(url)
        topics = json.loads(rs.read())

        index = 1
        for t in topics:
            logging.info(t['member']['username'])
            logging.info(t['node']['title'])
            logging.info(t['replies'])
            logging.info(t['title'])
            topic(t['member']['username'], t['node']['title'], t['replies'], t['title'], last, index)
            index = index + 1
            last = last + 3
            if last > rows - 5:
                break

        sc.refresh()
        time.sleep(2)
        sc.getch()
    except Exception, e:
        logging.error(e)
        logging.error(traceback.print_exc())
    finally:
        curses.endwin()
