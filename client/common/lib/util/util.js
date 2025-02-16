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

export function floatToPercent(value, rounding = 1, suffix = '%') {
  const result = (value * 100.0).toFixed(rounding);
  return suffix ? result + suffix : result;
}

export function moveArrayElement(value, index, positions) {
  [index, positions] = [parseInt(index, 10), parseInt(positions, 10)];
  if (index < 0 || index >= value.length) return value;
  let newIndex = index + positions;
  if (newIndex < 0) { newIndex = 0; }
  else if (newIndex >= value.length) { newIndex = value.length - 1; }
  if (newIndex === index) return value;
  const result = [...value];
  const element = result.splice(index, 1)[0];
  result.splice(newIndex, 0, element);
  return result;
}

function timezoneToMinutes(value) {
  if (!value) return 0;
  if (!isString(value)) return value;
  if (value === 'Z' || value === 'UTC' || value === 'GMT') return 0;
  let [result, op, hh, mm] = [null, value.substring(0, 1), 0, 0];
  if (op === '+' || op === '-') {
    result = value.slice(1).split(':');
  } else {
    result = value.split(':');
    op = '+';
  }
  if (result.length > 1) {
    [hh, mm] = result;
  } else {
    result = result[0];
    if (result.length > 2) {
      [hh, mm] = [result.substring(0, 2), result.slice(2)];
    } else {
      hh = result;
    }
  }
  result = parseInt(hh, 10) * 60;
  result += parseInt(mm, 10);
  if (isNaN(result)) return 0;
  return op === '-' ? 0 - result : result;
}

export function rangeCodeToMillis(value) {
  if (!value) return null;
  if (!isString(value)) return value;
  const incs = { s: 1000, m: 60000, h: 3600000, d: 86400000 };
  const idx = value.slice(-1).toLowerCase();
  const incsidx = hasProp(incs, idx) ? incs[idx] : 1;
  const result = parseInt(incsidx === 1 ? value : value.slice(0, -1), 10);
  return isNaN(result) ? 0 : result * incsidx;
}

export function presetDate(value, preset, tz = null) {
  if (!value) return null;
  let result = value instanceof Date ? value : new Date(value);
  if (!preset) return result;
  preset = preset.toUpperCase();
  if (tz) {
    result = result.getTime() + 60000 * result.getTimezoneOffset();
    result += 60000 * timezoneToMinutes(tz);
    result = new Date(result);
  }
  if (preset === 'LH' || preset === 'LAST HOUR') {
    result = new Date(result.getFullYear(), result.getMonth(), result.getDate(), result.getHours());
  } else if (preset === 'LD' || preset === 'LAST DAY') {
    result = new Date(result.getFullYear(), result.getMonth(), result.getDate());
  } else if (preset === 'LM' || preset === 'LAST MONTH') {
    result = new Date(result.getFullYear(), result.getMonth());
  } else if (preset === 'TM' || preset === 'THIS MONTH') {
    result = new Date(result.getFullYear(), result.getMonth() + 1);
  }
  if (tz) {
    result = result.getTime() - 60000 * result.getTimezoneOffset();
    result -= 60000 * timezoneToMinutes(tz);
    result = new Date(result);
  }
  return result;
}

export function parseDateToMillis(value, tz = null) {
  if (!value) return null;
  let result = parseInt(value, 10);
  if (result.toString() != value.toString()) { result = Date.parse(value); }
  if (isNaN(result)) return null;
  if (tz) {
    result -= 60000 * new Date(result).getTimezoneOffset();
    result -= 60000 * timezoneToMinutes(tz);
  }
  return result;
}

export function shortISODateTimeString(value, tzFlag = true) {
  if (!value) return '';
  let result = value instanceof Date ? value : new Date(value);
  let offset = 0;
  if (!tzFlag) {  // UTC
    // Pass
  } else if (tzFlag === true) {  // Local TZ
    offset = 0 - result.getTimezoneOffset();
  } else if (isString(tzFlag)) {  // Specific TZ as string
    offset = timezoneToMinutes(tzFlag);
  } else if (tzFlag) {  // Specific TZ as minutes
    offset = tzFlag;
  }
  if (offset) {
    offset *= 60000;
    result = new Date(result.getTime() + offset);
  }
  return result.toISOString().replace('T', ' ').substring(0, 19);
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
