var assert = require('assert');
var express = require('express');
var step = require('step');
var app = express.createServer();
var mongo = require('mongodb');
var mongo_server = mongo.Server;
var mongo_db = mongo.Db;
var mongo_server_domotique = new mongo_server('127.0.0.1', 27017, { auto_reconnect: true, native_parser: true });
var mongo_db_domotique = new mongo_db('domotique', mongo_server_domotique, {});
var events_coll;

app.use(express.logger());
//app.use(express.favicon(__dirname + '/public/images/favicon.ico'));
app.use(express.methodOverride());
app.use(express.bodyParser());
// Seems it has to happen before cookieParser
app.use(express.cookieParser());
app.use(express.responseTime());
//app.use(express.session({secret: config.session.secret, key: "sid"}));

step(
    function(){
        console.log("Opening db");
        mongo_db_domotique.open(this);
    },
    function(err,db) {
        assert.equal(err, null);
        console.log("Retrieving events");
        db.collection('events',this);
    },
    function(err, events) {
        assert.equal(err,null);
        console.log("Ready to rock");
        events_coll = events;

        app.post("/postEvent",postEvent);

        app.listen(9090,'127.0.0.1');
    }
);

function postEvent(req, res) {
    var event = {};
    for(var prop in req.body) {
        if(req.body.hasOwnProperty(prop)) {
            if(prop == 'msg') {
                // String base64
                event[prop] = req.body[prop];
            } else {
                // Number for the rest
                event[prop] = Number(req.body[prop]);
            }
        }
    }
    console.log(event);
    events_coll.insert(event);
    res.end();
}

