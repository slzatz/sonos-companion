import full_pandora
from full_pandora import SoCo
from soco import SoCo as SoCo_

sonos = SoCo('192.168.1.103')
sonos_ = SoCo_('192.168.1.103')

#response = sonos.get_pandora_stations('slzatz@gmail.com')

#def play_music_station(self, music_service, music_service_station_title, music_service_station_id, music_service_email):


#print response


z = '''{'R.E.M. Radio': '637630342339192386', 'Nick Drake Radio': '409866109213435458', 'Dar Williams Radio': '1823409579416053314', 'My Morning Jacket Radio': '1776327778550113858', 'Patty
 Griffin Radio': '52876609482614338', 'Lucinda Williams Radio': '360878777387148866', 'Neil Young Radio': '52876154216080962', 'Wilco Radio': '1025897885568558658', 'The Decemberists
 Radio': '686295066286974530', 'The Innocence Mission Radio': '686869410788632130', 'Kris Delmhorst Radio': '610111769614181954', 'Counting Crows Radio': '1727297518525703746', 'Iron
 & Wine Radio': '686507220491527746', 'Bob Dylan Radio': '1499257703118366274', "slzatz's QuickMix": 'qm86206018', 'Ray LaMontagne Radio': '1726130468537198146', 'Vienna Teng Radio':
 '138764603804051010'}
'''

#response = sonos.play_music_station('Pandora', 'Patty Griffin Radio', '52876609482614338', 'slzatz@gmail.com')
#print response
#sonos.play()

#body = PLAY_STATION_BODY_TEMPLATE.format(music_service = 'pndrradio', music_service_station_title = 'Patty Griffin Radio', music_service_station_id = '52876609482614338', music_service_email = 'slzatz@gmail.com')

PLAY_URI_BODY_TEMPLATE = '<u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><CurrentURI>{uri}</CurrentURI><CurrentURIMetaData>{meta}</CurrentURIMetaData></u:SetAVTransportURI>'

PLAY_STATION_BODY_TEMPLATE ='"<u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><CurrentURI>{music_service}:{music_service_station_id}</CurrentURI><CurrentURIMetaData>&lt;DIDL-Lite xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot; xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;xmlns:r=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot; xmlns=&quot;urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/&quot;&gt;&lt;item id=&quot;OOOX{music_service_station_id}&quot; parentID=&quot;0&quot; restricted=&quot;true&quot;&gt;&lt;dc:title&gt;{music_service_station_title}&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.audioItem.audioBroadcast&lt;/upnp:class&gt;&lt;desc id=&quot;cdudn&quot; nameSpace=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot;&gt;SA_RINCON3_{music_service_email}&lt;/desc&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;</CurrentURIMetaData></u:SetAVTransportURI></s:Body></s:Envelope>'

meta = '&lt;DIDL-Lite xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot; xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;xmlns:r=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot; xmlns=&quot;urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/&quot;&gt;&lt;item id=&quot;OOOX{music_service_station_id}&quot; parentID=&quot;0&quot; restricted=&quot;true&quot;&gt;&lt;dc:title&gt;{music_service_station_title}&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.audioItem.audioBroadcast&lt;/upnp:class&gt;&lt;desc id=&quot;cdudn&quot; nameSpace=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot;&gt;SA_RINCON3_{music_service_email}&lt;/desc&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;'.format(music_service = 'pndrradio', music_service_station_title = 'Patty Griffin Radio', music_service_station_id = '52876154216080962', music_service_email = 'slzatz@gmail.com')


meta = '&lt;DIDL-Lite xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot; xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;xmlns:r=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot; xmlns=&quot;urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/&quot;&gt;&lt;item id=&quot;OOOX{music_service_station_id}&quot; parentID=&quot;0&quot; restricted=&quot;true&quot;&gt;&lt;dc:title&gt;{music_service_station_title}&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.audioItem.audioBroadcast&lt;/upnp:class&gt;&lt;desc id=&quot;cdudn&quot; nameSpace=&quot;urn:schemas-rinconnetworks-com:metadata-1-0/&quot;&gt;SA_RINCON3_{music_service_email}&lt;/desc&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;'.format(music_service = 'pndrradio', music_service_station_title = "slzatz's QuickMix", music_service_station_id = 'qm86206018', music_service_email = 'slzatz@gmail.com')

#meta = ''
sonos_.play_uri('pndrradio:quickmix86206018', meta=meta)


z = '''def play_uri(self, uri='', meta=''):
        """ Play a given stream. Pauses the queue.

        Arguments:
        uri -- URI of a stream to be played.
        meta --- The track metadata to show in the player, DIDL format.

        Returns:
        True if the Sonos speaker successfully started playing the track.

        If an error occurs, we'll attempt to parse the error and return a UPnP
        error code. If that fails, the raw response sent back from the Sonos
        speaker will be returned.

        """

        body = PLAY_URI_BODY_TEMPLATE.format(uri=uri, meta=meta)

        response = self.__send_command(TRANSPORT_ENDPOINT, SET_TRANSPORT_ACTION, body)

        if (response == ENQUEUE_RESPONSE):
            # The track is enqueued, now play it.
            return self.play()
        else:
            return self.__parse_error(response)

'''
