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

export function dump(value) {
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
