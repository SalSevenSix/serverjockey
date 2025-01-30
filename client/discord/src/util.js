function reactTo(message, emoji, retval = null) {
  if (message) { message.react(emoji); }
  return retval;
}

exports.getFirstKey = function(value) {
  if (value == null) return null;
  const keys = Object.keys(value);
  if (keys.length === 0) return null;
  return keys[0];
};

exports.commandLineToList = function(line) {
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
};

exports.shortISODateTimeString = function(dateobj = null) {
  if (!dateobj) { dateobj = new Date(); }
  return dateobj.toISOString().replace('T', ' ').substring(0, 19);
};

exports.newGetRequest = function(secret) {
  return {
    method: 'get',
    headers: {
      'X-Secret': secret
    }
  };
};

exports.newPostRequest = function(ct, secret) {
  return {
    method: 'post',
    headers: {
      'Content-Type': ct,
      'X-Secret': secret
    }
  };
};

exports.listifyRoles = function(line) {
  const roles = [];
  if (!line || !line.trim()) return roles;
  line.split('@').forEach(function(role) {
    role = role.trim();
    if (role) { roles.push(role); }
  });
  return roles;
};

exports.checkHasRole = function(message, roles) {
  let hasRole = roles.includes('everyone');
  if (!hasRole && roles.length > 0) {
    hasRole = message.member.roles.cache.find(function(role) {
      return roles.includes(role.name);
    });
  }
  if (hasRole) return true;
  return reactTo(message, '🔒', false);
};

exports.rmReacts = function(message, thenHandler, errorHandler, retval = null) {
  message.reactions.removeAll()
    .then(function() { thenHandler(message); })
    .catch(errorHandler);
  return retval;
};

exports.reactUnknown = function(message) {
  return reactTo(message, '❓');
};

exports.reactWait = function(message) {
  return reactTo(message, '⌛');
};

exports.reactError = function(message) {
  return reactTo(message, '⛔');
};

exports.reactSuccess = function(message) {
  return reactTo(message, '✅');
};
