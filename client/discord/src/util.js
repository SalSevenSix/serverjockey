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
  if (hasRole) return true;
  return reactTo(message, '🔒', false);
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
