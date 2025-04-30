import fs from 'fs';
import * as util from './util.js';
import * as logger from './logger.js';

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

export function sendTextOrFile(message, value, prefix = 'file', threshold = 1) {
  const chunked = util.chunkStringArray(value);
  if (chunked.length <= threshold) { sendChunked(message, chunked, true); }
  else { sendFile(message, util.mergeStringArray(chunked), prefix); }
}
