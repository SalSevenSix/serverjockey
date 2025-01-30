const cutil = require('common/util/util');
const util = require('./util.js');

exports.raw = function(value) {
  console.log(value);
};

exports.info = function(value) {
  console.log(util.shortISODateTimeString() + ' INFO ' + value);
};

exports.dump = function(value) {
  if (!value) return;
  const clone = {};
  for (const key in value) {
    if (value[key] && key.toUpperCase().endsWith('TOKEN') && cutil.isString(value[key])) {
      clone[key] = '*'.repeat(value[key].length);
    } else {
      clone[key] = value[key];
    }
  }
  console.log(JSON.stringify(clone, null, 2).split('\n').slice(1, -1).join('\n'));
};

exports.error = function(value, message = null) {
  if (!value) return util.reactError(message);
  if (cutil.isString(value)) {
    console.error(util.shortISODateTimeString() + ' ERROR ' + value);
  } else {
    if (value.name === 'AbortError') return null;
    console.error(util.shortISODateTimeString() + ' ERROR');
    console.error(value);
  }
  return util.reactError(message);
};
