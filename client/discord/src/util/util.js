import * as cutil from 'common/util/util';

export function getFirstKey(value) {
  if (!value) return null;
  const keys = Object.keys(value);
  return keys.length === 0 ? null : keys[0];
}

export function commandLineToList(value) {
  if (!value) return [];
  const regexp = /[^\s"]+|"([^"]*)"/gi;
  const [result, line] = [[], value.replaceAll('\n', ' ')];
  let match = null;
  do {
    match = regexp.exec(line);
    if (match != null) {
      result.push(match[1] ? match[1] : match[0]);
    }
  } while (match != null);
  return result;
}

export function clobCommandLine(data) {
  const result = [];
  let hold = null;
  data.forEach(function(value) {
    if (hold) {
      result.push(hold + value);
      hold = null;
    } else if (value.endsWith('=')) {
      hold = value;
    } else {
      result.push(value);
    }
  });
  return result;
}

export function newGetRequest(secret) {
  return { method: 'get', headers: { 'X-Secret': secret } };
}

export function newPostRequest(ct, secret) {
  return { method: 'post', headers: { 'Content-Type': ct, 'X-Secret': secret } };
}

export function listifyRoles(line) {
  const roles = [];
  if (!line || !line.trim()) return roles;
  line.split('@').forEach(function(role) {
    role = role.trim();
    if (role) { roles.push(role); }
  });
  return roles;
}

export function textToArray(value) {
  if (Array.isArray(value)) return value;
  if (cutil.isString(value)) return value.split('\n');
  return ['null'];
}

export function arrayToText(value) {
  if (cutil.isString(value)) return value;
  if (Array.isArray(value)) return value.join('\n');
  return 'null';
}

export function chunkStringArray(value, maxchars = 1600) {  // Discord limit is 2000 chars
  if (value == null) return null;
  const result = [];
  let [chars, chunk] = [0, []];
  textToArray(value).forEach(function(line) {
    chars += line.length + 1;
    if (chars > maxchars) {
      if (chunk.length > 0) { result.push(chunk); }
      [chars, chunk] = [line.length + 1, []];
    }
    chunk.push(line);
  });
  if (chunk.length > 0) { result.push(chunk); }
  return result;
}

export function mergeStringArray(value) {
  if (!value || !Array.isArray(value)) return value;
  const result = [];
  value.forEach(function(chunk) { result.push(...chunk); });
  return result;
}

export function toSnowflake(value, prefix = '<@') {
  if (!value) return null;
  const result = value.length > prefix.length + 1 && value.startsWith(prefix) && value.endsWith('>')
    ? value.slice(prefix.length, -1) : value;
  if (result.length < 18) return null;
  return (/^\d*$/).test(result) ? result : null;
}
