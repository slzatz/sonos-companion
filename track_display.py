#!bin/python
'''
curses script that is called by listmanager_cli.py do_open method
To handle the edge case of the last page, we could add page_max_rows
which would always be the same as max_rows except for the last page
Not sure it's worth it so haven't implemented it

Note that when you press an arrow key getch sees three keys in rapid succession as follows:

\033
[
A, B, C or D

'''
import curses
from datetime import datetime
import time
import json
import random
from operator import itemgetter 
import pysolr
import sonos_actions
import lyrics
import sonos_actions

from config import solr_uri 

solr = pysolr.Solr(solr_uri+'/solr/sonos_companion/', timeout=10) 

actions = {'n':'note', 't':'title', 's':'select'}
keys = {'B':'j', 'A':'k', 'C':'l', 'D':'h'}

def track_display(artist):
    queue = [] #needs to be in function or only set to [] the first time function is called
    screen = curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(4, 15, -1)
    color_map = {'{blue}':3, '{red}':1, '{green}':2,'{white}':4}
    curses.curs_set(0)
    curses.cbreak() # respond to keys without needing Enter
    curses.noecho()
    size = screen.getmaxyx()
    screen.nodelay(True)
    font = curses.A_NORMAL

    win = curses.newwin(size[0]-2, size[1]-1, 1, 1)

    page = 0
    row_num = 1
    max_chars_line = size[1] - 10
    max_rows = size[0]-4

    s = 'artist:' + ' AND artist:'.join(artist.split())
    result = solr.search(s, fl='album,title,uri', rows=500) 
    count = len(result)
    last_page = count//max_rows
    if not count:
        return f"I couldn't find any tracks for {artist}"

    print(f"Total track count for {artist} was {count}")
    tracks = result.docs
    #titles = [t.get('title', '')+'-'+t.get('album', '') for t in tracks]
    #title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    #return f"I will shuffle:\n{title_list}."
    screen.clear()
    screen.addstr(0,0, f"Hello Steve. screen size = x:{size[1]},y:{size[0]} max_rows = {max_rows} last_page = {last_page}", curses.A_BOLD)

    s = "j:page down k: page up h:page left l:page right n:edit [n]ote t:edit [t]itle s:[s]elect and ENTER/RETURN no action"
    if len(s) > size[1]:
        s = s[:size[1]-1]
    screen.addstr(size[0]-1, 0, s, curses.color_pair(3)|curses.A_BOLD)
    screen.refresh()

    def draw():
        win.clear()
        win.box()
        page_tracks = tracks[max_rows*page:max_rows*(page+1)]
        n = 1
        for i,track in enumerate(page_tracks, page*max_rows+1):

            if n+2 == size[0]:
                break

            try:
                #z = '+' if i-1 in queue else '-'
                #screen.addstr(size[0]-1, 0, s, curses.color_pair(3)|curses.A_BOLD)
                if i-1 in queue:
                    win.addstr(n, 2, f"{i}. {track.get('title', '')[:max_chars_line]} {track.get('album', '')}", curses.color_pair(1)|curses.A_BOLD)  #(y,x)
                else:
                    win.addstr(n, 2, f"{i}. {track.get('title', '')[:max_chars_line]} {track.get('album', '')}")  #(y,x)
                    
                #win.addstr(n, 2, f"{i}. {task.title[:max_chars_line]} {'[c]' if task.completed else ''}")  #(y,x)
            except Exception as e:
                 pass

            n+=1

        win.refresh() 


    draw()
    win.addstr(row_num, 1, ">")  #j
    win.refresh()
    accum = []
    arrow = False
    while 1:
        n = screen.getch()
        if n == -1:
            continue

        c = chr(n)
        if arrow:
            accum.append(c)
            if len(accum) == 2:
                c = keys.get(accum[-1], 'z')
                accum = []
                arrow = False

        elif c == '\x1b': #o33:
            arrow = True
            continue

        elif c == '\n': #10:
            curses.nocbreak()
            screen.keypad(False)
            curses.echo()
            curses.endwin()
            return 

        elif c == 'q': #10:
            curses.nocbreak()
            screen.keypad(False)
            curses.echo()
            curses.endwin()
            uris = [tracks[i]['uri'] for i in queue]
            return uris


        if c == 's': #needs to be if and not elif
            #track = tracks[page*max_rows+row_num-1 # remove
            track_num = (page*max_rows)+row_num-1
            track = tracks[track_num]
            if track_num in queue:
                queue.remove(track_num)
                win.addstr(row_num, 2, f"{track_num+1}. {track.get('title', '')[:max_chars_line]} {track.get('album', '')}")  #(y,x)
            else:
                queue.append(track_num)
                win.addstr(row_num, 2, f"{track_num+1}. {track.get('title', '')[:max_chars_line]} {track.get('album', '')}", curses.color_pair(1)|curses.A_BOLD)  #(y,x)
                
            #uris.append(track.get('uri')) # remove
            win.refresh()
            
        elif c == 'k':
            win.addstr(row_num, 1, " ")  #k
            row_num-=1
            if row_num==0:
                page = (page - 1) if page > 0 else last_page
                row_num = max_rows
                draw()  
            win.addstr(row_num, 1, ">")  #k
            win.refresh()

        elif c == 'j':
            win.addstr(row_num, 1, " ")  #j
            row_num+=1
            if row_num==max_rows+1:
                page = (page + 1) if page < last_page else 0
                row_num = 1
                draw()  
            win.addstr(row_num, 1, ">")  #j
            win.refresh()

        elif c == 'h':
            win.addstr(row_num, 1, " ")  #j
            page = (page - 1) if page > 0 else last_page
            draw()  
            row_num = 1
            win.addstr(row_num, 1, ">")  #j
            win.refresh()

        elif c == 'l':
            win.addstr(row_num, 1, " ")  #j
            page = (page + 1) if page < last_page else 0
            # decided at moment not to implement changes that handle last page
            #if page==last_page:
            #    page_max_rows = len(tasks)%last_page
            draw()  
            row_num = 1
            win.addstr(row_num, 1, ">")  #j
            win.refresh()

        screen.move(0, size[1]-50)
        screen.clrtoeol()
        screen.addstr(0, size[1]-50, f"track num = {row_num}; char = {c}",
                      curses.color_pair(3)|curses.A_BOLD)
        screen.refresh()
            
        size_current = screen.getmaxyx()
        if size != size_current:
            size = size_current
            screen.addstr(0,0, f"screen size = x:{size[1]},y:{size[0]} max_rows = {max_rows}", curses.A_BOLD)
        time.sleep(.05)
