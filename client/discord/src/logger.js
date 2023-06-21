'use strict';

require('./dateformat.js');

exports.raw = function(value) {
  console.log(value);
}

exports.info = function(value) {
  console.log(new Date().format('yyyy-mm-dd HH:MM:ss') + ' INFO ' + value);
}

exports.error = function(value) {
  if (value == null) return null;
  let timestamp = new Date().format('yyyy-mm-dd HH:MM:ss');
  if (Object.prototype.toString.call(value) === '[object String]') {
    console.error(timestamp + ' ERROR ' + value);
    return null;
  }
  if (value.name === 'AbortError') {
    // exports.info(value);
    return null;
  }
  console.error(timestamp + ' ERROR');
  console.error(value);
  return null;
}
