#!/usr/bin/python
# encoding=utf-8

from urllib import urlopen, urlencode
import json

def get_data(url, params=None):
    if params is not None:
        url = '%s/%s' % (url, urlencode(params))
    rs = urlopen(url)
    return rs.read()

class V2EX(object):
    def __init__(self):
        pass

if __name__ == '__main__':
    url = 'http://www.v2ex.com/api/topics/latest.json'
    topics = json.loads(get_data(url))
    for k, v in topics[0].items():
        print '\033[01;32m%s\033[00m: %s' % (k, v)
