'use strict';

function infoLogger(text) {
  console.log(new Date().getTime() + ' ' + text);
}

function sleep(millis) {
  return new Promise(function(resolve) { setTimeout(resolve, millis); });
}

infoLogger('*** START ServerLink Bot ***');
process.on('SIGTERM', function() {
  infoLogger('*** SIGTERM - END ServerLink Bot ***');
  sleep(2000).then(function() { process.exit(); } );
});

const fs = require('fs');
var stream = fs.createWriteStream('/tmpx/foo.text');
stream.on('error', function(error) { infoLogger('ERR ' + error); } );
stream.write('Hello\n');
stream.write('World\n');
stream.end();


