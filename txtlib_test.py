#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import platform
import pygame
import txtlib
from time import sleep

if platform.system() == 'Windows':
    os.environ['SDL_VIDEODRIVER'] = 'windib'
else:
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')

pygame.init()
pygame.mouse.set_visible(0)

screen = pygame.display.set_mode((320, 240)) #, pygame.FULLSCREEN) 320 240
screen.fill((0,0,0))

text = txtlib.Text((320, 240), 'freesans')
text.text = '''This is the proof of txtlib. You can print lines
like this one.
\n\nYou can also make bold text, italic text and underline text.
You can use colors: BLU, RED, GREEN, but you can use what color you want!!!
Don't forget of different fonts or texts SIZES.

Obviously you can combine different styles!!!

		And it support identations. This line has two tab character at the beginning.
	This line only one.'''

text.add_style(84, 93, txtlib.BOLD)
text.add_style(95, 106, txtlib.ITALIC)
text.add_style(111, 126, txtlib.UNDERLINE)
text.add_style(147, 150, txtlib.COLOR, (0, 0, 255))
text.add_style(152, 155, txtlib.COLOR, (255, 0, 0))
text.add_style(157, 162, txtlib.COLOR, (0, 255, 0))
text.add_style(229, 234, txtlib.FONT, 'freemono')
text.add_style(244, 249, txtlib.SIZE, 32)
text.add_style(252, 297, txtlib.SIZE, 24)
text.add_style(252, 297, txtlib.BOLD)
text.add_style(252, 297, txtlib.ITALIC)
text.add_style(252, 297, txtlib.UNDERLINE)
text.add_style(252, 297, txtlib.FONT, 'freeserif')
text.add_style(252, 297, txtlib.COLOR, (255, 165, 0))

text.html('\n\nProviamo formattazione <U><i><b>html</B></i></U>. <color="255, 0, 0">Colore</color>, <size="10">size</s>, <foNt="azfhh">font</FONT>')

text.update()

screen.blit(text.area, (0, 0))
pygame.display.flip() # Update the full display Surface to the screen

sleep(30)
#while True:
#	event = pygame.event.wait()
#	if event.type == pygame.QUIT:
#		exit(0)
