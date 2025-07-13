import fs from 'fs';
import * as util from './util.js';
import * as logger from './logger.js';

function reactTo(message, emoji, retval = null) {
  if (message) { message.react(emoji); }
  return retval;
}

export function extractCommandLine(message) {
  let result = message.content;
  result = result.slice(result.indexOf(' ')).trim();
  return result;
}

export function extractUserTag(message) {
  let result = message.member.user.tag;
  result = '@' + result.split('#')[0];
  return result;
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

function sendChunked(message, value, codeblock) {
  const [start, end] = codeblock ? ['```\n', '\n```'] : ['', ''];
  value.forEach(function(chunk) {
    message.channel.send(start + util.arrayToText(chunk) + end);
  });
}

export function sendFile(message, value, prefix = 'file') {
  const fname = prefix + '-' + message.id + '.text';
  const fpath = '/tmp/' + fname;
  fs.writeFile(fpath, util.arrayToText(value), function(error) {
    if (error) return logger.error(error, message);
    message.channel.send({ files: [{ attachment: fpath, name: fname }] })
      .finally(function() { fs.unlink(fpath, logger.error); });
  });
  return null;
}

export function sendText(message, value, codeblock = true) {
  sendChunked(message, util.chunkStringArray(value), codeblock);
}

export function sendTextOrFile(message, value, prefix = 'file', threshold = 1, codeblock = true) {
  const chunked = util.chunkStringArray(value);
  if (chunked.length <= threshold) { sendChunked(message, chunked, codeblock); }
  else { sendFile(message, util.mergeStringArray(chunked), prefix); }
}
