var connect = require('connect');

var app = connect()
    .use(connect.logger('dev'))
    .use(connect.static(__dirname + '/static'))
    .listen(9093);