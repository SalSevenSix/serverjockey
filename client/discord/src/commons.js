'use strict';

const logger = require('./logger.js');
const subs = require('./subs.js');
const fs = require('fs');
const fetch = require('node-fetch');

exports.server = function($) {
  if ($.data.length === 1) {
    let cmd = $.data[0];
    $.httptool.doPost('/server/' + cmd, null, function(message, json) {
      if (cmd === 'daemon' || cmd === 'start' || cmd === 'restart') {
        message.react('⌛');
        let helper = new subs.Helper($.context);
        helper.subscribe($.httptool.baseurl + '/server/subscribe', function(pollUrl) {
          helper.poll(pollUrl, function(data) {
            if (data != null && data.running && data.state === 'STARTED') {
              message.reactions.removeAll()
                .then(function() { message.react('✅'); })
                .catch(logger.error);
              return false;
            }
            return true;
          });
        });
      } else {
        message.react('✅');
      }
    });
    return;
  }
  $.httptool.doGet('/server', function(body) {
    let result = '```Server is ';
    if (!body.running) {
      result += 'DOWN```';
      return result;
    }
    result += body.state + '\n';
    let dtl = body.details;
    if (dtl.hasOwnProperty('version')) {
      result += 'Version:  ' + dtl.version + '\n';
    }
    if (dtl.hasOwnProperty('ip') && dtl.hasOwnProperty('port')) {
      result += 'Connect:  ' + dtl.ip + ':' + dtl.port + '\n';
    }
    if (dtl.hasOwnProperty('ingametime')) {
      result += 'Ingame:   ' + dtl.ingametime + '\n';
    }
    return result + '```';
  });
}

exports.getconfig = function($) {
  if ($.data.length < 1) return;
  $.httptool.doGet('/config/' + $.data[0], function(body) {
    let fname = $.data[0] + '-' + $.message.id + '.text';
    let fpath = '/tmp/' + fname;
    fs.writeFile(fpath, body, function(error) {
      if (error) return logger.error(error);
      $.message.channel.send({ files: [{ attachment: fpath, name: fname }] });
    });
    // TODO Delete file if possible
  });
}

exports.setconfig = function($) {
  if ($.data.length < 1) return;
  if ($.message.attachments.length < 1) return;
  fetch($.message.attachments.first().url)
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.text();
    })
    .then(function(body) {
      if (body == null) return;
      $.httptool.doPost('/config/' + $.data[0], body);
    })
    .catch(function(error) {
      $.httptool.error(error, $.message);
    });
}

exports.deployment = function($) {
  let data = [...$.data];
  if (data.length < 1) return;
  let cmd = data.shift();
  let body = null;
  if (cmd === 'install-runtime') {
    body = { wipe: true, validate: true };
    if (data.length > 0) { body.beta = data[0]; }
  }
  $.httptool.doPostToFile('/deployment/' + cmd, body);
}

exports.players = function($) {
  $.httptool.doGet('/players', function(body) {
    let line = 'Players currently online: ' + body.length;
    let chars = line.length;
    let chunk = [line];
    let result = [];
    for (let i = 0; i < body.length; i++) {
      if (body[i].steamid === false) {
        line = body[i].name;
      } else {
        line = 'LOGGING IN        ';
        if (body[i].steamid != null) { line = body[i].steamid; }
        line += ' ' + body[i].name;
      }
      chunk.push(line);
      chars += line.length;
      if (chars > 1600) {
        result.push('```\n' + chunk.join('\n') + '\n```');
        chars = 0;
        chunk = [];
      }
    }
    if (chunk.length > 0) {
      result.push('```\n' + chunk.join('\n') + '\n```');
    }
    return result;
  });
}
