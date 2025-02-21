import { isString } from 'common/util/util';

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
