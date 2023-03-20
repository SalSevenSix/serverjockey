'use strict';

require('./dateformat.js');

exports.raw = function(value) {
  console.log(value);
}

exports.info = function(value) {
  console.log(new Date().format('yyyy-mm-dd HH:MM:ss.l ') + value);
}

exports.error = function(value) {
  if (value == null) return null;
  if (value.name === 'AbortError') {
    exports.info(value);
    return null;
  }
  console.error(new Date().format('yyyy-mm-dd HH:MM:ss.l'));
  console.error(value);
  return null;
}
