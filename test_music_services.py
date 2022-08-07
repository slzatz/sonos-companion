#!bin/python

from time import sleep
from random import choice
import soco
from soco.music_services import MusicService
from soco.discovery import by_name
from soco.data_structures import to_didl_string

def confirm_work(service):
    t = MusicService(service)
    z = by_name("Office2")

    # Print the search categories. TIDAL e.g. has 4 search categories:
    # ['artists', 'albums', 'tracks', 'playlists']
    print(t.available_search_categories)

    for search_category in t.available_search_categories:
        z.clear_queue()
        sleep(1)
        # Clear queue
        print("Search category:", search_category)
        results = t.search(search_category, "Aimee Mann Mental Illness", count=100)
        print(len(results))
        if search_category in ("tracks", "albums"):
            z.clear_queue()
            try:
                ##z.add_to_queue(choice(results))
                item = results[0]
                print("-> (" + type(item).__name__ + ")", item.title)
                #print(f"{item.metadata.get('track_metadata', 'Nope').metadata=}")
                print(f"{item.metadata.get('track_metadata', {'artist': None}).metadata['artist']=}")
                print(f"{dir(item.metadata.keys)=}")
                print(to_didl_string(item))
                z.add_to_queue(item)
            except soco.exceptions.SoCoUPnPException:
                print("Cannot play")
            else:
                print("Can play")
                print(str(z.get_queue())[:250])
                z.play()
                sleep(10)
                z.stop()

    root_content = t.get_metadata()
    print("\nGot {} items in root content".format(len(root_content)))
    print("\nTest browse root items:")
    for item in root_content:
        content = t.get_metadata(item.id)
        print("Got {} items under: {}".format(len(content), item.title))

    ##print("\nTest browse until tracks")
    for item in t.get_metadata():
        # print("J")
        if item.title == "My Music":
            while True:
                print("-> (" + type(item).__name__ + ")", item.title)
                if type(item).__name__ == "MSPlaylist":
                    z.clear_queue()
                    try:
                        ##z.add_to_queue(choice(results))
                        print("-> (" + type(item).__name__ + ")", item.title)
                        print(to_didl_string(item))
                        z.add_to_queue(item)
                    except soco.exceptions.SoCoUPnPException:
                        print("Cannot play")
                        break
                    else:
                        print("Can play")
                        print(str(z.get_queue())[:250])
                        z.play()
                        #sleep(10)
                        #z.stop()
                        break
                items = t.get_metadata(item.id)
                if len(items) == 0 or items[0].id == item.id:
                    print("... STOP\n")
                    break
                item = items[0]

    return

confirm_work("Amazon Music")

