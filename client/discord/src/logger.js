'use strict';

const util = require('./util.js');

exports.raw = function(value) {
  console.log(value);
}

exports.dump = function(obj) {
  if (obj == null) return;
  const clone = {};
  for (let key in obj) {
    if (obj[key] && key.toUpperCase().endsWith('TOKEN') && util.isString(obj[key])) {
      clone[key] = '*'.repeat(obj[key].length);
    } else {
      clone[key] = obj[key];
    }
  }
  console.log(JSON.stringify(clone, null, 2).split('\n').slice(1, -1).join('\n'));
}

exports.info = function(value) {
  console.log(util.shortISODateTimeString() + ' INFO ' + value);
}

exports.error = function(value) {
  if (value == null) return null;
  if (Object.prototype.toString.call(value) === '[object String]') {
    console.error(util.shortISODateTimeString() + ' ERROR ' + value);
    return null;
  }
  if (value.name === 'AbortError') {
    // exports.info(value);
    return null;
  }
  console.error(util.shortISODateTimeString() + ' ERROR');
  console.error(value);
  return null;
}
