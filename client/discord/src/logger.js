'use strict';

exports.raw = function(value) {
  console.log(value);
}

exports.info = function(value) {
  console.log(new Date().getTime().toString() + ' ' + value);
}

exports.error = function(value) {
  if (value == null) return null;
  if (value.name === 'AbortError') {
    exports.info(value);
    return null;
  }
  console.error(value);
  return null;
}
