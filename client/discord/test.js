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

class HandlerProjectZomboid {
  isString(value) {
    return (value != null && typeof value === 'string');
  }
}
/*
const handler = new HandlerProjectZomboid();
console.log(handler.hasOwnProperty('isString'));
console.log(typeof handler.isString === 'function');
console.log(typeof handler.fooBar);
console.log(Object.getOwnPropertyNames(HandlerProjectZomboid.prototype))
console.log(Object.getOwnPropertyNames(HandlerProjectZomboid.prototype).includes('isString'))
console.log(handler['isString']({}))
console.log('pz.server'.split('.'));
console.log('server'.split('.'));
*/

const value = { yay: { foo: 'xxx', bar: 'yyy' } };

console.log(value.hasOwnProperty('yayx'));




