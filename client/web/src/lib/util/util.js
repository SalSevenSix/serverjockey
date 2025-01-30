import { isString } from 'common/util/util';

export const noStorage = typeof(Storage) === 'undefined';
export const browserName = getBrowserName();

function getBrowserName() {
  const ua = window.navigator.userAgent;
  if (ua.includes('Firefox')) return 'Firefox';
  if (ua.includes('SamsungBrowser')) return 'SamsungBrowser';
  if (ua.includes('Opera') || ua.includes('OPR')) return 'Opera';
  if (ua.includes('Edge') || ua.includes('Edg')) return 'Edge';
  if (ua.includes('Chrome')) return 'Chrome';
  if (ua.includes('Safari')) return 'Safari';
  return null;
}

const textExtensions = ['txt', 'text', 'log'];
const stampExtRegex = /^[0-9_-]+$/;

export function guessTextFile(filename) {
    const parts = filename.split('.');
    if (parts.length < 2) return false;
    const extension = parts[parts.length - 1].toLowerCase();
    if (textExtensions.includes(extension)) return true;
    const prextion = parts.length > 2 ? parts[parts.length - 2].toLowerCase() : null;
    if (!prextion) return false;
    if (!textExtensions.includes(prextion)) return false;
    if (stampExtRegex.test(extension)) return true;
    if (extension.startsWith('prev')) return true;
    if (extension.startsWith('back')) return true;
    return false;
}

export function fNoop() {
  // Pass
}

export function fTrue() {
  return true;
}

export function generateId() {
  return Date.now().toString() + Math.random().toString().slice(2);
}

export function toCamelCase(value) {
  if (!isString(value)) return '';
  return value.split(' ').map(capitalize).join('');
}

export function capitalizeKebabCase(value) {
  if (!isString(value)) return '';
  return value.split('-').map(capitalize).join(' ');
}

export function capitalize(value) {
  if (!isString(value)) return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function floatToPercent(value, rounding = 1, suffix = '%') {
  const result = (value * 100.0).toFixed(rounding);
  return suffix ? result + suffix : result;
}

export function shortISODateTimeString(millis, utc = false) {
  let dateobj = new Date(millis);
  if (!utc) { dateobj = new Date(dateobj.getTime() + dateobj.getTimezoneOffset() * -60000); }
  return dateobj.toISOString().replace('T', ' ').substring(0, 19);
}

export function chunkArray(arr, rows = 20, columns = 3) {
  if (arr.length > rows * columns) {
    rows = Math.ceil(arr.length / columns);
  }
  const result = [];
  for (let i = 0; i < columns; i++) {
    result.push(arr.slice(i * rows, i * rows + rows));
  }
  return result;
}


export class RollingLog {
  #lines;
  #limit;

  constructor(limit = 200) {
    this.#limit = limit;
    this.#lines = [];
  }

  reset() {
    this.#lines = [];
    return this;
  }

  set(text) {
    this.#lines = text.split('\n');
    return this;
  }

  append(text) {
    const newLines = text.split('\n');
    if (newLines.length > this.#limit) {
      this.#lines = newLines.slice(0 - this.#limit);
      return this;
    }
    this.#lines = [...this.#lines, ...newLines];
    if (this.#lines.length > this.#limit) {
      this.#lines = this.#lines.slice(0 - this.#limit);
    }
    return this;
  }

  toText() {
    if (this.#lines === 0) return '';
    return this.#lines.join('\n');
  }
}


export class ObjectUrls {
  #urls = [];

  openBlob(blob) {
    const url = URL.createObjectURL(blob);
    this.#urls.push(url);
    window.open(url).focus();
  }

  openObject(data) {
    const blob = new Blob([JSON.stringify(data)], { type : 'text/plain;charset=utf-8' });
    this.openBlob(blob);
  }

  cleanup() {
    this.#urls.forEach(function(url) {
      URL.revokeObjectURL(url);
    });
    this.#urls.length = 0;
  }
}
