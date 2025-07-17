import * as cutil from 'common/util/util';
import { emojis } from './literals.js';

function timestamp() {
  return cutil.shortISODateTimeString(new Date(), true);
}

function sanitize(obj) {
  const result = {};
  for (const [key, value] of Object.entries(obj)) {
    const upkey = key.toUpperCase();
    if (value && cutil.isString(value) && (upkey.endsWith('TOKEN') || upkey.includes('APIKEY'))) {
      result[key] = '*'.repeat(value.length);
    } else if (value && typeof value === 'object' && !Array.isArray(value)) {
      result[key] = sanitize(value);
    } else {
      result[key] = value;
    }
  }
  return result;
}

function reactError(message) {
  if (message) { message.react(emojis.error); }
  return null;
}

export function raw(value) {
  console.log(value);
}

export function info(value) {
  console.log(timestamp() + ' INFO ' + value);
}

export function dump(obj) {
  if (!obj) return;
  let result = sanitize(obj);
  result = JSON.stringify(result, null, 2);
  result = result.split('\n').slice(1, -1).join('\n');
  console.log(result);
}

export function error(value, message = null) {
  if (!value) return reactError(message);
  if (cutil.isString(value)) {
    console.error(timestamp() + ' ERROR ' + value);
  } else {
    if (value.name === 'AbortError') return null;
    console.error(timestamp() + ' ERROR');
    console.error(value);
  }
  return reactError(message);
}
