import fs from 'fs';
import fetch from 'node-fetch';
import * as util from '../util/util.js';
import * as logger from '../util/logger.js';

export function getconfig({ httptool, message, data }) {
  if (data.length === 0) return util.reactUnknown(message);
  httptool.doGet('/config/' + data[0], function(body) {
    const fname = data[0] + '-' + message.id + '.text';
    const fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      message.channel.send({ files: [{ attachment: fpath, name: fname }] })
        .finally(function() { fs.unlink(fpath, logger.error); });
    });
  });
}

export function setconfig({ httptool, message, data }) {
  const attachment = message.attachments.first();
  if (data.length === 0 || !attachment) return util.reactUnknown(message);
  fetch(attachment.url)
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.text();
    })
    .then(function(body) {
      if (body) { httptool.doPost('/config/' + data[0], body); }
    })
    .catch(function(error) {
      logger.error(error, message);
    });
}

export function deployment({ httptool, message, data }) {
  if (data.length === 0) return util.reactUnknown(message);
  const cmd = data[0];
  let body = null;
  if (cmd === 'backup-runtime' || cmd === 'backup-world') {
    if (data.length > 1) { body = { prunehours: data[1] }; }
  } else if (cmd === 'install-runtime') {
    body = { wipe: false, validate: true };
    if (data.length > 1) { body.beta = data[1]; }
  }
  httptool.doPostToFile('/deployment/' + cmd, body);
}
