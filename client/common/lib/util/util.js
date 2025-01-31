export function isBoolean(value) {
  return value === false || value === true;
}

export function isString(value) {
  return value != null && typeof value === 'string';
}

export function sleep(millis) {
  return new Promise(function(resolve) { setTimeout(resolve, millis); });
}

export function hasProp(obj, prop) {
  return Object.hasOwn(obj, prop);
}

export function urlSafeB64encode(value) {
  const data = btoa(unescape(encodeURIComponent(value)));
  return data.replaceAll('+', '-').replaceAll('/', '_');
}

export function shortISODateTimeString(value, utc = false) {
  let dateobj = value instanceof Date ? value : new Date(value);
  if (!utc) {
    const offset = dateobj.getTimezoneOffset() * -60000;
    dateobj = new Date(dateobj.getTime() + offset);
  }
  return dateobj.toISOString().replace('T', ' ').substring(0, 19);
}

export function humanDuration(millis, parts = 3) {
  if (!millis) { millis = 0; }
  let days = -1;
  if (parts > 2) {
    days = Math.floor(millis / 86400000);
    millis -= days * 86400000;
  }
  let hours = -1;
  if (parts > 1) {
    hours = Math.floor(millis / 3600000);
    millis -= hours * 3600000;
  }
  const minutes = Math.floor(millis / 60000);
  let result = '';
  if (days > -1) { result += days + 'd '; }
  if (hours > -1) { result += hours + 'h '; }
  result += minutes + 'm';
  return result;
}

export function humanFileSize(bytes, dp = 1, si = false) {
  if (bytes === 0) return '0 B';
  if (!bytes) return '';
  const thresh = si ? 1000 : 1024;
  if (Math.abs(bytes) < thresh) return bytes + ' B';
  const units = si
    ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
  const r = 10 ** dp;
  let u = -1;
  do {
    bytes /= thresh;
    u += 1;
  } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);
  return bytes.toFixed(dp) + ' ' + units[u];
}
