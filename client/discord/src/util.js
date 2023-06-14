'use strict';

exports.sleep = function(millis) {
  return new Promise(function(resolve) { setTimeout(resolve, millis); });
}

exports.isString = function(value) {
  return (value != null && typeof value === 'string');
}

exports.getFirstKey = function(value) {
  if (value == null) return null;
  let keys = Object.keys(value);
  if (keys.length === 0) return null;
  return keys[0];
}

exports.commandLineToList = function(line) {
  let regexp = /[^\s"]+|"([^"]*)"/gi;
  let result = [];
  let match = null;
  do {
    match = regexp.exec(line);
    if (match != null) {
      result.push(match[1] ? match[1] : match[0]);
    }
  } while (match != null);
  return result;
}

exports.humanDuration = function(millis) {
  let days = Math.floor(millis / 86400000);
  millis -= days * 86400000;
  let hours = Math.floor(millis / 3600000);
  millis -= hours * 3600000;
  let minutes = Math.floor(millis / 60000);
  return days + 'd ' + hours + 'h ' + minutes + 'm';
}

exports.humanFileSize = function(bytes, si=false, dp=1) {
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

exports.urlSafeB64encode = function(value) {
  let data = unescape(encodeURIComponent(value));
  return btoa(data).replaceAll('+', '-').replaceAll('/', '_');
}

exports.newGetRequest = function(secret) {
  return {
    method: 'get',
    headers: {
      'X-Secret': secret
    }
  };
}

exports.newPostRequest = function(ct, secret) {
  return {
    method: 'post',
    headers: {
      'Content-Type': ct,
      'X-Secret': secret
    }
  };
}

exports.checkAdmin = function(message, adminRoles) {
  let isAdmin = message.member.roles.cache.find(function(role) {
    return adminRoles.includes(role.name);
  });
  if (isAdmin) return true;
  message.react('🔒');
  return false;
}
