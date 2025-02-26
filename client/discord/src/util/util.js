function reactTo(message, emoji, retval = null) {
  if (message) { message.react(emoji); }
  return retval;
}

export function getFirstKey(value) {
  if (!value) return null;
  const keys = Object.keys(value);
  return keys.length === 0 ? null : keys[0];
}

export function commandLineToList(line) {
  if (!line) return [];
  const regexp = /[^\s"]+|"([^"]*)"/gi;
  const result = [];
  let match = null;
  do {
    match = regexp.exec(line);
    if (match != null) {
      result.push(match[1] ? match[1] : match[0]);
    }
  } while (match != null);
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

export function checkHasRole(message, roles) {
  let hasRole = roles.includes('everyone');
  if (!hasRole && roles.length > 0) {
    hasRole = message.member.roles.cache.find(function(role) {
      return roles.includes(role.name);
    });
  }
  return hasRole ? true : reactTo(message, '🔒', false);
}

export function chunkStringArray(value, maxchars = 1600) {  // Discord limit is 2000 chars
  if (!value) return value;
  const result = [];
  let [chars, chunk] = [0, []];
  value.forEach(function(line) {
    chars += line.length + 1;
    if (chars > maxchars) {
      result.push(chunk);
      [chars, chunk] = [line.length + 1, []];
    }
    chunk.push(line);
  });
  if (chunk.length > 0) { result.push(chunk); }
  return result;
}

export function toSnowflake(value, prefix = '<@') {
  if (!value) return null;
  const result = value.length > prefix.length + 1 && value.startsWith(prefix) && value.endsWith('>')
    ? value.slice(prefix.length, -1) : value;
  if (result.length < 18) return null;
  return (/^\d*$/).test(result) ? result : null;
}

export function rmReacts(message, thenHandler, errorHandler, retval = null) {
  message.reactions.removeAll()
    .then(function() { thenHandler(message); })
    .catch(errorHandler);
  return retval;
}

export function reactUnknown(message) {
  return reactTo(message, '❓');
}

export function reactWait(message) {
  return reactTo(message, '⌛');
}

export function reactError(message) {
  return reactTo(message, '⛔');
}

export function reactSuccess(message) {
  return reactTo(message, '✅');
}
