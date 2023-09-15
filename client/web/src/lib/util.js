
const textExtensions = ['txt', 'text', 'log'];
const stampExtRegex = /^[0-9_-]+$/;

export function guessTextFile(filename) {
    let parts = filename.split('.');
    if (parts.length < 2) return false;
    let extension = parts[parts.length - 1].toLowerCase();
    if (textExtensions.includes(extension)) return true;
    let prextion = parts.length > 2 ? parts[parts.length - 2].toLowerCase() : null;
    if (!prextion) return false;
    if (textExtensions.includes(prextion)) {
      if (stampExtRegex.test(extension)) return true;
      if (extension.startsWith('prev')) return true;
      if (extension.startsWith('back')) return true;
    }
    return false;
}

export function generateId() {
  return Date.now().toString() + Math.random().toString().slice(2);
}

export function isBoolean(value) {
   return (value === false || value === true);
}

export function isString(value) {
  return (value != null && typeof value === 'string');
}

export function sleep(millis) {
  return new Promise(function(resolve) { setTimeout(resolve, millis); });
}

export function capitalizeKebabCase(value) {
  if (!isString(value)) return '';
  return value.split('-').map(capitalize).join(' ');
}

export function capitalize(value) {
  if (!isString(value)) return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
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
  let minutes = Math.floor(millis / 60000);
  let result = '';
  if (days > -1) { result += days + 'd '; }
  if (hours > -1) { result += hours + 'h '; }
  result += minutes + 'm';
  return result;
}

export function humanFileSize(bytes, si=false, dp=1) {
  if (bytes === 0) return '0 B';
  if (!bytes) return '';
  const thresh = si ? 1000 : 1024;
  if (Math.abs(bytes) < thresh) return bytes + ' B';
  const units = si
    ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
  const r = 10**dp;
  let u = -1;
  do {
    bytes /= thresh;
    ++u;
  } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);
  return bytes.toFixed(dp) + ' ' + units[u];
}

export function urlSafeB64encode(value) {
  let data = unescape(encodeURIComponent(value));
  return btoa(data).replaceAll('+', '-').replaceAll('/', '_');
}


export class RollingLog {

  #lines = [];

  reset() {
    this.#lines = [];
    return this;
  }

  set(text) {
    this.#lines = text.split('\n');
    return this;
  }

  append(text) {
    let newLines = text.split('\n');
    if (newLines.length > 200) {
      this.#lines = newLines.slice(-200);
      return this;
    }
    this.#lines = [...this.#lines, ...newLines];
    if (this.#lines.length > 200) {
      this.#lines = this.#lines.slice(-200);
    }
    return this;
  }

  toText() {
    if (this.#lines === 0) return '';
    return this.#lines.join('\n');
  }
}
