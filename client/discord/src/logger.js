const cutil = require('common/util/util');
const util = require('./util.js');

function timestamp() {
  return cutil.shortISODateTimeString(new Date(), true);
}

export function raw(value) {
  console.log(value);
}

export function info(value) {
  console.log(timestamp() + ' INFO ' + value);
}

export function dump(obj) {
  if (!obj) return;
  let result = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value && key.toUpperCase().endsWith('TOKEN') && cutil.isString(value)) {
      result[key] = '*'.repeat(value.length);
    } else {
      result[key] = value;
    }
  }
  result = JSON.stringify(result, null, 2);
  result = result.split('\n').slice(1, -1).join('\n');
  console.log(result);
}

export function error(value, message = null) {
  if (!value) return util.reactError(message);
  if (cutil.isString(value)) {
    console.error(timestamp() + ' ERROR ' + value);
  } else {
    if (value.name === 'AbortError') return null;
    console.error(timestamp() + ' ERROR');
    console.error(value);
  }
  return util.reactError(message);
}
