#!bin/python

import requests
import sys
from config import ngrok_urls
from cmd2 import Cmd

slots = {'Mix':['myartista','myartistb'], 'Shuffle':['myartist'], 'PlayStation':['mystation'], 'PlayAlbum':['myalbum', 'myartist'], 'PlayTrack':['mytitle', 'myartist'], 'AddTrack':['mytitle', 'myartist'], 'TurnVolume':['volume'], 'SetVolume':['level'], 'AMAZON.ResumeIntent':[], 'AMAZON.PauseIntent':[], 'AMAZON.NextIntent':[], 'ListQueue':[],'ClearQueue':[], 'WhatIsPlaying':[], 'RecentTracks':[], 'Mute':[], 'UnMute':[]}

class CmdLineApp(Cmd):
    """ Example cmd2 application. """

    # Setting this true makes it run a shell command if a cmd2/cmd command doesn't exist
    # default_to_shell = True

    def __init__(self):
        self.raw = "Nothing"
        self.shortcuts.update({'p': 'play', 'a':'add'})
        self.intro = "Welcome to sonos_cli"
        self.prompt = "sonos>"
        self.quit = False
        self.intent = None

        # Set use_ipython to True to enable the "ipy" command which embeds and interactive IPython shell
        super().__init__(use_ipython=False)

    def preparse(self, s):
        self.raw = s
        return s

    def do_location(self, s):
        if s=='':
            s = input("what is the location? ")
        self.url = ngrok_urls.get(s)
        print(f"The location is {s}")

    def do_play(self, s):
        self.intent = 'PlayTrack'
        if 'by' in s:
            self.values = s.split(' by ')
        else:
            self.values = [s ,'']
        print(s)

    def do_add(self, s):
        self.intent = 'AddTrack'
        if 'by' in s:
            self.values = s.split(' by ')
        else:
            self.values = [s ,'']
        print(s, type(s)) #cmd2.ParsedString
        print(str(s), type(str(s)))

    def default(self, s):
        self.intent = 'PlayTrack'
        if 'by' in self.raw:
            self.values = self.raw.split(' by ')
        else:
            self.values = [self.raw ,'']
        print("play "+self.raw)

    def do_louder(self, s):
        self.intent = 'TurnVolume'
        self.values = ['up']

    def do_pause(self, s):
        self.intent = 'AMAZON.PauseIntent'

    def do_resume(self, s):
        self.intent = 'AMAZON.ResumeIntent'

    def do_next(self, s):
        self.intent = 'AMAZON.NextIntent'

    def do_quit(self, s):
        self.quit = True

    def postcmd(self, stop, s):
        if self.quit:
            return True

        if not self.intent:
            return

        slot_dict = {}
        for i,slot in enumerate(slots[self.intent]):
            s = {slot:{'name':slot, 'value':self.values[i]}}
            slot_dict.update(s)

        data = {'session':{}, 'request':{'type':'IntentRequest', 'intent':{'slots':slot_dict, 'name':self.intent}}}
        print(data)

        try:
            r = requests.post(self.url, json=data, timeout=10.0)
        except requests.exceptions.ReadTimeout as e: 
            print("request timed out to flask_ask: ",e)
        else:
            print("-->", r.json()['response']['outputSpeech']['text'])

        self.intent = None

if __name__ == '__main__':
    c = CmdLineApp()
    c.cmdloop()
