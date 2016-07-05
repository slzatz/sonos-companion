'''
No mqtt
Requires three scripts:
echo_flask_sonos.py
echo_check_no_mqtt.py
sonos_echo_app.py

Also need ngrok http 5000
and url will look like 1234.ngrok.io/sonos
it is set on Alexa configuration page
Generic program to use Flask to be the https echo endpoint
'''
import json
from sonos_echo_app import lambda_handler
from flask import Flask, request

app = Flask(__name__)

@app.route("/sonos", methods = ['GET','POST'])
def route2handler():
    if request.method == 'POST':
        data = request.get_json()
        print data
        return json.dumps(lambda_handler(data))
    else:
        return "It was not a POST method."

try:
    app.run(debug=True,
            port=5000,
            threaded=False,
            use_reloader=False,
            use_debugger=True,
            host='0.0.0.0'
            )
finally:
    print "Disconnecting clients"

print "Done"

