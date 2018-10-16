# -*- coding: utf-8 -*-

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem, Dialog, DialogProgress
from xbmcplugin import addDirectoryItem, endOfDirectory

import urllib2
import urllib

import re
import json

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()
dialog = Dialog()

def Post(url,params):
    _params = urllib.urlencode(params)
    req = urllib2.Request(url,_params)
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:5.0)')
    return urllib2.urlopen(req).read()

def Get(url):
    # print(url)
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:5.0)')
    return urllib2.urlopen(req).read()

@plugin.route('/')
def index():
    addDirectoryItem(plugin.handle, plugin.url_for(
        show_search_input), ListItem("Search"), True)
    p = Get('http://jiqimao.tv/rank/jqm/show/tv/3/')
    it = re.finditer(r"""<a href="(.*?)" style="float: left;" target="_blank" onclick="(?:.*?)" >
            <div class="dl-cover" style="background: url\('(.*?)'\) no-repeat 10px -85px">
            </div>
        </a>
        <div class="dt-title-info">
            <p class="d-title movie-name">(.*?)</p>
            <p class="d-txt">(.*?)</p>
            <p class="d-lab">(.*?)</p>
        </div>
        <div class="dt-title-info info-type">
            <p class="d-title">(.*?)</p>
        </div>
        <div class="dt-title-info info-area">
            <p class="d-title">(.*?)</p>
        </div>""",p)
    for match in it:
        # id = re.search(r'(\d+)',match.group(1)).group()
        id = re.search(r'http://jiqimao.tv/movie/show/(.*)',match.group(1)).group(1)

        li = ListItem(match.group(3),thumbnailImage=match.group(2))
        addDirectoryItem(plugin.handle, plugin.url_for(show_detail, id=id, img=match.group(2)), li, True)

    endOfDirectory(plugin.handle)

@plugin.route('/search_input')
def show_search_input():
    s = dialog.input('Search')
    # print s
    p = Get('http://jiqimao.tv/search/video/' + s)
    # print p
    it = re.finditer( r"""<a href="(.*?)" target="_blank">
                <div class="search-tv-box">
                    <img class="search-tv-img" src="(.*?)" alt="(?:.*?)" onerror="loadDefaultMid\(\);">
                    <div class="search-tv-title">
                        (.*?)
                    </div>
                    <div class="search-tv-pa-type">
                        (.*?)
                    </div>""", p)

    for match in it:
        id = re.search(r'http://jiqimao.tv/movie/show/(.*)',match.group(1)).group(1)
        # print match.group(2)
        # print id
        addDirectoryItem(plugin.handle, plugin.url_for(
            show_detail, id=id, img=match.group(2)), ListItem(match.group(3),thumbnailImage=match.group(2)), True)

    endOfDirectory(plugin.handle)

# @plugin.route('/category/<category_id>')
# def show_category(category_id):
#     addDirectoryItem(
#         plugin.handle, "", ListItem("Hello category %s!" % category_id))
#     endOfDirectory(plugin.handle)

@plugin.route('/Detail')
def show_detail():
    img = plugin.args['img'][0]
    id = plugin.args['id'][0]
    print '=============detail==================='
    print id
    print img
    p = Get('http://jiqimao.tv/movie/show/' + id)
    it = re.finditer(r'<li(?: class="hide")?><a title="(?:.*?)" onclick="(?:.*)web_player_click_(.*?)\'\]\)" target="_blank" href="(.*?)">(?:.*?)</a></li>' ,p)

    plot = ''
    plotObj = re.search(r'<p><span>剧情介绍：</span>(.*?)</p>',p)
    if plotObj:
        plot = plotObj.group(1)

    for match in it:
        vid = re.search(r'http://jiqimao.tv/video/ckPlayer/(.*)',match.group(2)).group(1)
        title = match.group(1)
        li = ListItem(title,thumbnailImage=img)
        li.setInfo('video',{
            'title': title,
            'plot': plot
        })
        addDirectoryItem(plugin.handle, plugin.url_for(play_Video, video=vid, img=img, plot=plot, title=title), li, True)

    endOfDirectory(plugin.handle)

@plugin.route('/video')
def play_Video():
    img = plugin.args['img'][0]
    video_url = plugin.args['video'][0]
    plot = plugin.args['plot'][0]
    title = plugin.args['title'][0]
    print '=======================>'
    progress = DialogProgress()
    progress.create('Loading')
    # print video_url
    progress.update(30, "", 'Loading Video Info', "")
    jsonObj = json.loads(Get('http://apick.jiqimao.tv/service/ckplayer/parser?type=1&mode=phone&sid=' + video_url))
    progress.update(70, "", 'Loading M3U8 Files', "")

    p = Get(jsonObj['url'])
    url = re.search(r'.*\.m3u8',p).group()
    # print jsonObj['url']
    # print url
    # print jsonObj['url'].replace('index.m3u8',url)
    progress.update(100, "", "", "")
    progress.close()

    # match = re.search(r'\"url\":\"(.*?mp4)\"',p)
    # print match.group(1).replace('\/','/')
    # title = re.search(r'<h4 class=\"title\"><a href=\".*?\">(.*?)</a></h4>',p).group(1)
    # print info
    li = ListItem(title,thumbnailImage=img)
    #
    # # plot = ''
    # # plotObj = re.search(r'<span class=\"left text-muted\">简介：</span><p>(.*?)</p>',p)
    # # if plotObj:
    # #     plot = plotObj.group(1)
    #
    # # print '=======================>'
    # # print plot
    #
    li.setInfo("video",{
        'title': title,
        'plot': plot
    })
    # video_url = match.group(1).replace('\/','/')
    addDirectoryItem(plugin.handle, jsonObj['url'].replace('index.m3u8',url), li)
    endOfDirectory(plugin.handle)

def run():
    plugin.run()
