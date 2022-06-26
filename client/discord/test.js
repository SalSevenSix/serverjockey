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

class Logger {
  #foo = 'Hello';
  #name;
  constructor(name) {
    this.#name = name;
  }
  sayHello(age) {
    console.log(this.#foo + ' ' + this.#name + ' age: ' + age);
  }
}

const logger = new Logger('Bowden');
logger.sayHello(12);



