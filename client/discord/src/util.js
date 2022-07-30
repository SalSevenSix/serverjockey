'use strict';

exports.sleep = function(millis) {
  return new Promise(function(resolve) { setTimeout(resolve, millis); });
}

exports.isString = function(value) {
  return (value != null && typeof value === 'string');
}

exports.isEmptyObject = function(value) {
  if (value == null) return false;
  return (typeof value === 'object' && value.constructor === Object && Object.keys(value).length === 0);
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
    var data = {};
    var units = [
      {label: 'millis', mod: 1000},
      {label: 'seconds', mod: 60},
      {label: 'minutes', mod: 60},
      {label: 'hours', mod: 24},
      {label: 'days', mod: 31}
    ];
    units.forEach(function(unit) {
      millis = (millis - (data[unit.label] = (millis % unit.mod))) / unit.mod;
    });
    return data.days + 'd ' + data.hours + 'h ' + data.minutes + 'm';
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

exports.stringToBase10 = function(string) {
  let utf8 = unescape(encodeURIComponent(string));
  let result = '';
  for (let i = 0; i < utf8.length; i++) {
    result += utf8.charCodeAt(i).toString().padStart(3, '0');
  }
  return result;
}

exports.base10ToString = function(number) {
  let character;
  let result = '';
  for (let i = 0; i < number.length; i += 3) {
    character = parseInt(number.substr(i, 3), 10).toString(16);
    result += '%' + ((character.length % 2 == 0) ? character : '0' + character);
  }
  return decodeURIComponent(result);
}

exports.newGetRequest = function(token) {
  return {
    method: 'get',
    headers: {
      'X-Secret': token
    }
  };
}

exports.newPostRequest = function(ct, token) {
  return {
    method: 'post',
    headers: {
      'Content-Type': ct,
      'X-Secret': token
    }
  };
}

exports.checkAdmin = function(message, adminRole) {
  let isAdmin = message.member.roles.cache.find(function(role) {
    return role.name === adminRole;
  });
  if (isAdmin == null) {
    message.react('🔒');
    return false;
  }
  return true;
}
