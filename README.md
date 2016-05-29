The scripts include:
 1. `add2queue_mqtt.py` that adds songs to the sonos queue by publishing the URIs of the chosen songs as an MQTT topic that `echo_check_mqtt.py` is subscribed to.
 1. `echo_check_mqtt.py` that subscribes to a topic looking for simple json content that instructs it to do things.
 1. `set_location.py` that sets the location between ct and nyc.
 1. `queue2solr.py` moves tracks from the queue to storage in Solr and assumes that the tracks are part of an album since it assigns track numbers
 

