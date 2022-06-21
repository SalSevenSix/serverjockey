'use strict';

// SETUP
//

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


var data = 'http://localhost:6164/instances/projectzomboid';
//data.split('/', 3).join('/')
infoLogger(data.split('/', 3).join('/'));

//(async () => {
//  while (true) {
//    await sleep(60000);
//    infoLogger('Still Alive');
//  }
//})();
