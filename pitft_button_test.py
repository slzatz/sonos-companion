from pitftgpio import PiTFT_GPIO

pitft = PiTFT_GPIO()

while True:
    if pitft.Button1:
        print "Button 1 pressed - screen off"
        pitft.Backlight(False)
    if pitft.Button2:
        print "Button 2 pressed - screen on"
        pitft.Backlight(True) 
    if pitft.Button3:
        print "Button 3 pressed"
    if pitft.Button4:
        print "Button 4 pressed"