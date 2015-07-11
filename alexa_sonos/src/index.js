// Alexa SDK for JavaScript v1.0.00
// Copyright (c) 2014-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved. Use is subject to license terms.

/**
 * This sample shows how to create a Lambda function for handling Alexa Skill requests that:
 * - Web service: communicate with an external web service to get tide data from NOAA CO-OPS API (http://tidesandcurrents.noaa.gov/api/)
 * - Multiple optional slots: has 2 slots (artist and source), where the user can provide 0, 1, or 2 values, and assumes defaults for the unprovided values
 * - DATE slot: demonstrates date handling and formatted date responses appropriate for speech
 * - LITERAL slot: demonstrates literal handling for a finite set of known values
 * - Dialog and Session state: Handles two models, both a one-shot ask and tell model, and a multi-turn dialog model.
 *   If the user provides an incorrect slot in a one-shot model, it will direct to the dialog model. See the
 *   examples section for sample interactions of these models.
 * Examples:
 * One-shot model:
 *  User:  "Alexa, tell Sonos Companion to play Neil Young on Pandora."
 *  Alexa: "Neil Young from Pandora will begin shortly"
 * Dialog model:
 *  User:  "Alexa, open Sonos Companion"
 *  Alexa: "Welcome to Sonos Companion. Which artist would you like to hear?
 *  User:  "Patty Griffin"
 *  Alexa: "From which source?"
 *  User:  "Amazon"
 *  Alexa: "Patty Griffin from Amazon will begin shortly"
 */

// The AlexaSkill prototype and helper functions
var AlexaSkill = require('./AlexaSkill');

var http = require('http');

// config.App_ID contains the app id for the skill
var config = require('./config');


// Define the SonosCompanion constructor
// Could also use function SonosCompanion() { ... } with no ; - not quite equivalent
var SonosCompanion = function () {
    AlexaSkill.call(this, config.APP_ID);
};

// Extend AlexaSkill by creating a SonosCompanion.prototype object that inherits from AlexaSkill.prototype.
SonosCompanion.prototype = Object.create(AlexaSkill.prototype);

// Set the "constructor" property to refer to SonosCompanion
SonosCompanion.prototype.constructor = SonosCompanion;

// ----------------------- Override AlexaSkill request and intent handlers -----------------------

SonosCompanion.prototype.eventHandlers.onSessionStarted = function (sessionStartedRequest, session) {
    console.log("onSessionStarted requestId: " + sessionStartedRequest.requestId
        + ", sessionId: " + session.sessionId);
    // any initialization logic goes here
};

SonosCompanion.prototype.eventHandlers.onLaunch = function (launchRequest, session, response) {
    console.log("onLaunch requestId: " + launchRequest.requestId + ", sessionId: " + session.sessionId);
    handleWelcomeRequest(response);
};

SonosCompanion.prototype.eventHandlers.onSessionEnded = function (sessionEndedRequest, session) {
    console.log("onSessionEnded requestId: " + sessionEndedRequest.requestId
        + ", sessionId: " + session.sessionId);
    // any cleanup logic goes here
};

/**
 * override intentHandlers to map intent handling functions.
 */
SonosCompanion.prototype.intentHandlers = {
    OneshotSonosIntent: function (intent, session, response) {
        handleOneshotSonosRequest(intent, session, response);
    },

    DialogSonosIntent: function (intent, session, response) {
        // Determine if this turn is for artist, for source, or an error.
        // We could be passed slots with values, no slots, slots with no value.
        var artistSlot = intent.slots.Artist;
        var sourceSlot = intent.slots.Source;
        if (artistSlot && artistSlot.value) {
            handleArtistDialogRequest(intent, session, response);
        } else if (sourceSlot && sourceSlot.value) {
            handleSourceDialogRequest(intent, session, response);
        } else {
            handleNoSlotDialogRequest(intent, session, response);
        }
    },

    SupportedArtistsIntent: function (intent, session, response) {
        handleSupportedArtistsRequest(intent, session, response);
    },

    HelpIntent: function (intent, session, response) {
        handleHelpRequest(response);
    }
};

// -------------------------- SonosCompanion Domain Specific Business Logic --------------------------

// current list of recognized artists
var ARTISTS = [
    'neil young',
    'patty griffin',
    'gillian welch',
    'lucinda williams',
    'deb talan'
];

// current list of recognized music sources
var SOURCES = [
      'pandora',
      'amazon' 
];

function handleWelcomeRequest(response) {
    var whichArtistPrompt = "Which artist would you like to hear?";
    var speechOutput = "Welcome to Sonos Companion. " + whichArtistPrompt;
    /*var repromptText = "I can lead you through selecting a artist "
        + "For a list of artists, ask what artists are supported. "
        + whichArtistPrompt;*/
    var repromptText = "For a list of artists, ask what artists are supported.";

    response.ask(speechOutput, repromptText);
}

function handleHelpRequest(response) {
    var repromptText = "Which artist do you want to listen to?";
    var speechOutput = "I can lead you through selecting an artist and "
        + "For a list of supported artists, ask what artists are supported. "
        + "Or you can say exit."
        + repromptText;

    response.ask(speechOutput, repromptText);
}

/**
 * Handles the case where the user asked or for, or is otherwise being with supported artists
 */
function handleSupportedArtistsRequest(intent, session, response) {
    // get artist re-prompt
    var repromptText = "Which artist would you like to hear?";
    var speechOutput = "Currently, I know the following artists: " + getAllArtistsText()
        + repromptText;

    response.ask(speechOutput, repromptText);
}

/**
 * Handles the dialog step where the user provides a artist
 */
function handleArtistDialogRequest(intent, session, response) {

    var artist = getArtistFromIntent(intent, false);
    if (artist.error) {
        var repromptText = "Currently, I know information for the following artists: " + getAllArtistsText()
            + "Which artist would you like tide information for?";
        // if we received a value for the incorrect artist, repeat it to the user, otherwise we received an empty slot
        var speechOutput = artist.artist ? "I'm sorry, I don't have any data for " + artist.artist + ". " + repromptText : repromptText;

        response.ask(speechOutput, repromptText);
        return;
    }

    // if we don't have a source yet, go to source. If we have a source, we perform the final request
    if (session.attributes.source) {
        getFinalSonosResponse(artist, session.attributes.source, response);
    } else {
        // set artist in session and prompt for source
        session.attributes.artist =artist;
        var speechOutput = "From which source?";
        var repromptText = "From which source would you like  to play " + artist + "from?";

        response.ask(speechOutput, repromptText);
    }
}

/**
 * Handles the dialog step where the user provides a date
 */
function handleSourceDialogRequest(intent, session, response) {

    var source = getSourceFromIntent(intent, false);
    if (!source) {
        var repromptText = "Please try again by providing a source for the music, for example, Pandora. "
            + "Which source of music do you want?";
        var speechOutput = "I'm sorry, I didn't understand that source. " + repromptText;

        response.ask(speechOutput, repromptText);
        return;
    }

    // if we don't have a artist yet, go to artist. If we have an artist, we perform the final request
    if (session.attributes.artist) {
        getFinalSonosResponse(session.attributes.artist, source, response);
    } else {
        // The user provided a source out of turn. Set source in session and prompt for artist
        session.attributes.source = source;
        var speechOutput = "For which artist would you like music " + source.displaySource + "?";
        var repromptText = "For which artist?";

        response.ask(speechOutput, repromptText);
    }
}

/**
 * Handle no slots, or slot(s) with no values.
 * In the case of a dialog based skill with multiple slots,
 * when passed a slot with no value, we cannot have confidence
 * it is the correct slot type so we rely on session state to
 * determine the next turn in the dialog, and reprompt.
 */
function handleNoSlotDialogRequest(intent, session, response) {
    if (session.attributes.artist) {
        // get source re-prompt
        var repromptText = "Please try again saying a music source such as Pandora or Amazon. ";
        var speechOutput = repromptText;

        response.ask(speechOutput, repromptText);
    } else {
        // get source re-prompt
        handleSupportedArtistsRequest(intent, session, response);
    }
}

/**
 * This handles the one-shot interaction, where the user utters a phrase like:
 * 'Alexa, open Sonos Pooler and get tide information for Seattle on Saturday'.
 * If there is an error in a slot, this will guide the user to the dialog approach.
 */
function handleOneshotSonosRequest(intent, session, response) {

    // Determine artist, using default if none provided
    var artist = getArtistFromIntent(intent, true);
    if (artist.error) {
        // invalid artist. move to the dialog
        var repromptText = "Currently, I only know about the following artists: " + getAllArtistsText()
            + "Which artist would you like?";
        // if we received a value for an artist we don't recongize, repeat it to the user, otherwise we received an empty slot
        var speechOutput = artist.artist ? "I'm sorry, I don't know " + artist.artist + " yet. " + repromptText : repromptText;

        response.ask(speechOutput, repromptText);
        return;
    }

    // Determine source to play the music
    var source = getSourceFromIntent(intent, true);
    if (!source) {
        // Invalid source. set artist in session and prompt for source
        session.attributes.artist = artist;
        var repromptText = "Please try again saying a source, for example, Pandora. "
            + "For which source do you want?";
        var speechOutput = "I'm sorry, I didn't understand that source. " + repromptText;

        response.ask(speechOutput, repromptText);
        return;
    }

    // all slots filled, either from the user or by default values. Move to final request
    getFinalSonosResponse(artist, source, response);
}

/**
 * Both the one-shot and dialog based paths lead to this method to issue the request, and
 * respond to the user with the final answer.
 */
function getFinalSonosResponse(artist, source, response) {

    // Issue the request, and respond to the user
    //makeSonosRequest(artist, source, function sonosResponseCallback(err, SonosResponse) {
    makeSonosRequest(artist, source, function sonosResponseCallback(err) {
        var speechOutput;

        if (err) {
            speechOutput = "Sorry, Steve's Amazon AWS site seems to be down";
        } else {
              speechOutput = artist.artist + " from " + source.source + " will start playing soon";
        }

        response.tellWithCard(speechOutput, "SonosCompanion", speechOutput)
    });
}

/**
 * Sends a query to my Amazon EC2 instance at 54....
 */

function makeSonosRequest(artist, source, sonosResponseCallback) {

    var endpoint = config.APP_URI
    var queryString = '/echo';
    queryString += '/' + artist.artist;
    queryString += '/' + source.source; 

   //http.get(...).on('error', ....)
    http.get(endpoint + queryString, function (res) {
        var sonosResponseString = '';

        res.on('data', function (data) {
            sonosResponseString += data;
        });

        res.on('end', function () {
            var sonosResponseObject = JSON.parse(sonosResponseString);

            if (sonosResponseObject.error) {
                console.log("Sonos error: " + sonosResponseObj.error.message);
                sonosResponseCallback(new Error(sonosResponseObj.error.message));
            } else {
                //var highSonos = ///////////////////////////////////////////////findHighSonos(sonosResponseObject);
                //sonosResponseCallback(null, highSonos);
                sonosResponseCallback(null);
            }
        });
    }).on('error', function (e) {
        console.log("Communications error: " + e.message);
        sonosResponseCallback(new Error(e.message));
    });
}

/**
 * Gets the artist from the intent, or returns an error
 */
function getArtistFromIntent(intent, assignDefault) {

    var artistSlot = intent.slots.Artist;
    // slots can be missing, or slots can be provided but with empty value.
    // must test for both.
    if (!artistSlot || !artistSlot.value) {
        if (!assignDefault) {
            return {
                error: true,
            }
        } else {
            // For artist default to neil young
            return {artist: 'neil young'}
        }
    } else {
        // lookup the artist - list of artists in ARTISTS.
        var artistName = artistSlot.value;
        if (ARTISTS.indexOf(artistName) > -1) {
            return {
                artist: artistName,
            }
        } else {
            return {
                error: true,
                artist: artistName
            }
        }
    }
}

/**
 * Gets the source from the intent, defaulting to pandora if none provided,
 * or returns an error
 */
function getSourceFromIntent(intent, assignDefault) {

    var sourceSlot = intent.slots.Source;
    // slots can be missing, or slots can be provided but with empty value.
    // must test for both.
    if (!sourceSlot || !sourceSlot.value) {
        if (!assignDefault) {
            return {error: true}
        } else {
        // for source default to pandora
        return {source: 'pandora'}
        }
    } else {

        // lookup the source - list of sources provided in SOURCES
        var sourceName = sourceSlot.value;
        if (SOURCES.indexOf(sourceName) > -1) {
            return {
                source: sourceName,
            }
        } else {
            return {
                error: true,
                source: sourceName
            }
        }
    }
}

function getAllArtistsText() {
    var artistList = '';
    for (var i=0; i < ARTISTS.length; i++)  {
        artistList += ARTISTS[i] + ", ";
    }

    return artistList;
}

// Create the handler that responds to the Alexa Request.
exports.handler = function (event, context) {
    var sonosCompanion = new SonosCompanion();
    sonosCompanion.execute(event, context);
};

