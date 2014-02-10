#!/usr/bin/env python
from soco import SoCo
from soco import SonosDiscovery

if __name__ == '__main__':

    sonos = SoCo('192.168.1.103') # Pass in the IP of your Sonos speaker

    pandora_email = sonos.get_music_service_email('Pandora')
    pandora_stations = sonos.get_pandora_stations(pandora_email)

    station_selector = {}
    counter = 1
    for station in pandora_stations:
        print counter,"-", station
        station_selector[counter] = station
        counter +=1
    station_selection = int(raw_input("Please select station by number:"))

    selected_station_name = station_selector[station_selection]
    selected_station_id = pandora_stations[selected_station_name]

    sonos.play_music_station('Pandora', selected_station_name, selected_station_id, pandora_email)
    sonos.play()