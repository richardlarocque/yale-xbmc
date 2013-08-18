#!/usr/bin/env python
# Copyright 2013 Richard Larocque. 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
import urllib
import urlparse
import re

import BeautifulSoup

import xbmcgui
import xbmcplugin

DEPARTMENTS_MODE = 'depts'
COURSES_MODE = 'courses'
LECTURES_MODE = 'lectures'
VIDEO_MODE = 'videos'

def maybe_set_viewmode():
    if xbmc.getSkinDir() == 'skin.confluence':
        xbmc.executebuiltin('Container.SetViewMode(503)')

def makeurl(base_url, params):
    encoded_params = urllib.urlencode(params)
    return base_url + '?' + encoded_params

BASE_URL = 'http://oyc.yale.edu'

def Departments():
    print 'Departments Mode'
    plugin_url = sys.argv[0]
    handle = int(sys.argv[1])

    f = urllib2.urlopen(BASE_URL)
    soup = BeautifulSoup.BeautifulSoup(f)
    f.close()
    rows = soup.findAll('div', 'hover_dept')

    count = len(rows)
    for r in rows:
        name = r.string
        dept_url = urlparse.urljoin(BASE_URL, r.parent.get('href'))
        url = makeurl(plugin_url, {
            'mode' : COURSES_MODE,
            'url' : dept_url })

        li = xbmcgui.ListItem(name)
        li.setInfo(type = 'video', infoLabels = { "Title" : name })
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True, totalItems=count)
        print 'URL:' + url

    xbmcplugin.endOfDirectory(handle)

def Courses(courses_url):
    print 'Courses Mode: ' + courses_url
    plugin_url = sys.argv[0]
    handle = int(sys.argv[1])

    f = urllib2.urlopen(courses_url)
    soup = BeautifulSoup.BeautifulSoup(f)
    f.close()

    body = soup.find('div', id='dept_body')
    rows = body.findAll('div', 'views-row')

    xbmcplugin.setContent(handle, 'episodes')
    maybe_set_viewmode()
    count = len(rows)
    for r in rows:
        name = r.find('div', 'views-field-title').span.a.string
        course_url_suffix = r.find('div', 'views-field-title').span.a.get('href')
        course_url = urlparse.urljoin(BASE_URL, course_url_suffix)
        desc = r.find('div', 'views-field-body').p.string
        img_url = r.find('img').get('src')

        url = makeurl(plugin_url, {
            'mode' : LECTURES_MODE,
            'url' : course_url })

        li = xbmcgui.ListItem(name)
        li.setInfo('video', { 'Title' : name,
                              'Plot' : desc })
        li.setThumbnailImage(img_url)
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True, totalItems=count)
    xbmcplugin.endOfDirectory(handle)

def Lectures(lecture_url):
    print 'Lectures Mode: ' + lecture_url
    plugin_url = sys.argv[0]
    handle = int(sys.argv[1])

    f = urllib2.urlopen(lecture_url)
    soup = BeautifulSoup.BeautifulSoup(f)
    f.close()

    table = soup.find('table', 'views-table')
    rows = table.findAll('tr')

    count = len(rows)
    for r in rows:
        if (r.find('th')):
            continue
        name1 = r.find('td', 'views-field-field-session-display-number-value').string.strip().encode('utf-8')
        name2 = r.find('td', 'views-field-field-session-display-title-value').a.contents[0]
        if name1.find('Lecture') == -1:
            continue
        name = '%s: %s' % (name1, name2)
        video_url_suffix = r.find('a').get('href')
        video_url = urlparse.urljoin(BASE_URL, video_url_suffix)

        url = makeurl(plugin_url, {
            'mode' : VIDEO_MODE,
            'url' : video_url })
        print 'name: ' + name.encode('utf-8')

        li = xbmcgui.ListItem(name)
        li.setInfo('video', { 'Title' : name } )
        li.setProperty('IsPlayable', 'true')

        xbmcplugin.addDirectoryItem(handle, url, li, totalItems=count)
    xbmcplugin.endOfDirectory(handle)

def Video(video_url):
    print 'Video Mode: ' + video_url
    handle = int(sys.argv[1])

    f = urllib2.urlopen(video_url)
    soup = BeautifulSoup.BeautifulSoup(f)
    f.close()

    player = soup.find('div', id='player_wrapper')
    junk = player.text

    play_url = re.search('http://\S*.mp4', junk).group(0)

    li = xbmcgui.ListItem(path=play_url)
    print 'Resolved URL: ' + video_url
    xbmcplugin.setResolvedUrl(handle, True, li)

if __name__ == '__main__':
    if len(sys.argv[2]) == 0:
        Departments()
        sys.exit()

    decoded_args = urlparse.parse_qs(sys.argv[2][1:])
    print 'Args: ' + str(decoded_args)

    mode = decoded_args['mode'][0]
    url = decoded_args['url'][0]

    if (mode == DEPARTMENTS_MODE):
        Departments()
    elif (mode == COURSES_MODE):
        Courses(url)
    elif (mode == LECTURES_MODE):
        Lectures(url)
    elif (mode == VIDEO_MODE):
        Video(url)

