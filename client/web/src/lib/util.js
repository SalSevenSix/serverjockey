
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

export function humanDuration(millis) {
  let days = Math.floor(millis / 86400000);
  millis -= days * 86400000;
  let hours = Math.floor(millis / 3600000);
  millis -= hours * 3600000;
  let minutes = Math.floor(millis / 60000);
  return days + 'd ' + hours + 'h ' + minutes + 'm';
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

export function urlSafeB64encode(value) {
  let data = unescape(encodeURIComponent(value));
  return btoa(data).replaceAll('+', '-').replaceAll('/', '_');
}


export class RollingLog {
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
    return this;
  }

  append(text) {
    let newLines = text.split('\n');
    if (newLines.length > 200) {
      this.#lines = newLines.slice(-200);
      return this;
    }
    this.#lines = [...this.#lines, ...newLines];
    if (this.#lines > 200) {
      this.#lines = this.#lines.slice(-200);
    }
    return this;
  }

  toText() {
    if (this.#lines === 0) return '';
    return this.#lines.join('\n');
  }
}
