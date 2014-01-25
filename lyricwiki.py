# -*- coding: utf-8 -*-
#       lyricwiki.py
#       
#       Copyright 2009 Amr Hassan <amr.hassan@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import json, urllib, os, hashlib, time, requests

def _download(args):
    """
        Downloads the json response and returns it
    """
    
    base = "http://lyrics.wikia.com/api.php?"
    
    str_args = {}
    for key in args:
        str_args[key] = args[key].encode("utf-8")
    
    args = urllib.urlencode(str_args)
    
    return urllib.urlopen(base + args).read()

def _get_page_titles(artist, title):
    """
        Returns a list of available page titles
    """
    
    args = {"action": "query",
        "list": "search",
        "srsearch": artist + " " + title,
        "format": "json",
        }
    
    titles = ["%s:%s" %(artist, title), "%s:%s" %(artist.title(), title.title())]
    content = json.loads(_download(args))
	
    print content #########################
	
    for t in content["query"]["search"]:
        titles.append(t["title"])
    
    return titles

def _get_lyrics(artist, title):
    
    for page_title in _get_page_titles(artist, title):
        args = {"action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "titles": page_title,
            "format": "json",
            }
        
        revisions = json.loads(_download(args))["query"]["pages"].popitem()[1]
        
        if not "revisions" in revisions:
            continue
            
        content = revisions["revisions"][0]["*"]
        
        if content.startswith("#Redirect"):
            n_title = content[content.find("[[") + 2:content.rfind("]]")]
            return _get_lyrics(*n_title.split(":"))
        
        if "<lyrics>" in content:
            return content[content.find("<lyrics>") + len("<lyrics>") : content.find("</lyrics>")].strip()
        elif "<lyric>" in content:
            return content[content.find("<lyric>") + len("<lyric>") : content.find("</lyric>")].strip()

def get_lyrics(artist, title, cache_dir=None):
    """
        Get lyrics by artist and title
        set cache_dir to a valid (existing) directory
        to enable caching.
    """
    
    path = None
    
    if cache_dir and os.path.exists(cache_dir):
        digest = hashlib.sha1(artist.lower().encode("utf-8") + title.lower().encode("utf-8")).hexdigest()
        path = os.path.join(cache_dir, digest)
        
        if os.path.exists(path):
            fp = open(path)
            return json.load(fp)["lyrics"].strip()
    
    lyrics = _get_lyrics(artist, title)
    
    if path and lyrics:
        fp = open(path, "w")
        json.dump({"time": time.time(), "artist": artist, "title": title,
                    "source": "lyricwiki", "lyrics": lyrics }, fp, indent=4)
        fp.close()
    
    return lyrics
	
def get_lyrics2(artist, title):
    payload = {'func': 'getSong', 'artist': artist, 'song': title, 'fmt': 'json'}
    r = requests.get("http://httpbin.org/get", params=payload)
    print r.json()

#http://lyrics.wikia.com/api.php?func=getSong&artist=Tool&song=Schism&fmt=xml
