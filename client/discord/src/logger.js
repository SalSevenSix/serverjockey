'use strict';

const util = require('./util.js');

exports.raw = function(value) {
  console.log(value);
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
