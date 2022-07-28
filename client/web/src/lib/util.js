
export function sleep(millis) {
  return new Promise(function(resolve) { setTimeout(resolve, millis); });
}

export function capitalizeKebabCase(value) {
  if (typeof value != 'string') return '';
  return value.split('-').map(capitalize).join(' ');
}

export function capitalize(value) {
  if (typeof value != 'string') return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function humanFileSize(bytes, si=false, dp=1) {
  if (bytes === 0) return '0 B';
  if (!bytes) return '';
  const thresh = si ? 1000 : 1024;
  if (Math.abs(bytes) < thresh) {
    return bytes + ' B';
  }
  const units = si
    ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
  let u = -1;
  const r = 10**dp;
  do {
    bytes /= thresh;
    ++u;
  } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);
  return bytes.toFixed(dp) + ' ' + units[u];
}

export function stringToBase10(string) {
  let utf8 = unescape(encodeURIComponent(string));
  let result = '';
  for (let i = 0; i < utf8.length; i++) {
    result += utf8.charCodeAt(i).toString().padStart(3, '0');
  }
  return result;
}


export class ReverseRollingLog {
  #lines;

  constructor() {
    this.#lines = [];
  }

  reset() {
    this.#lines = [];
    return this;
  }

  set(text) {
    this.#lines = text.split('\n');
    this.#lines.reverse();
    return this;
  }

  append(text) {
    let newLines = text.split('\n');
    if (newLines.length > 200) {
      this.#lines = newLines.slice(-200);
      this.#lines.reverse();
      return this;
    }
    newLines.reverse();
    this.#lines = [...newLines, ...this.#lines];
    if (this.#lines > 200) {
      this.#lines = this.#lines.slice(0, 200);
    }
    return this;
  }

  toText() {
    if (this.#lines === 0) return '';
    return this.#lines.join('\n');
  }
}
