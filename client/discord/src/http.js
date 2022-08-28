'use strict';

const logger = require('./logger.js');
const util = require('./util.js');
const subs = require('./subs.js');
const fs = require('fs');
const fetch = require('node-fetch');

exports.MessageHttpTool = class MessageHttpTool {
  #context;
  #message;
  #baseurl;

  constructor(context, message, baseurl) {
    this.#context = context;
    this.#message = message;
    this.#baseurl = baseurl;
  }

  get baseurl() {
    return this.#baseurl;
  }

  error(value, message) {
    logger.error(value);
    message.react('⛔');
  }

  doGet(path, dataHandler) {
    let self = this;
    let message = this.#message;
    fetch(this.#baseurl + path, util.newGetRequest(this.#context.config.SERVER_TOKEN))
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        let ct = response.headers.get('Content-Type');
        if (ct.startsWith('text/plain')) return response.text();
        return response.json();
      })
      .then(function(data) {
        let result = dataHandler(data);
        if (!result) return;
        if (!!!result.forEach) { result = [result]; }
        result.forEach(function(text) {
          message.channel.send(text);
        });
      })
      .catch(function(error) {
        self.error(error, message);
      });
  }

  doPost(path, body = null, dataHandler = null) {
    let self = this;
    let context = this.#context;
    let message = this.#message;
    if (!util.checkAdmin(message, context.config.ADMIN_ROLE)) return;
    let request = util.newPostRequest('application/json', context.config.SERVER_TOKEN);
    if (util.isString(body)) {
      request = util.newPostRequest('text/plain', context.config.SERVER_TOKEN);
      request.body = body.replace(/\r\n/g, '\n');
    } else if (body != null) {
      request.body = JSON.stringify(body);
    }
    fetch(this.#baseurl + path, request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        if (response.status === 204) return null;
        return response.json();
      })
      .then(function(json) {
        if (json != null && json.hasOwnProperty('error')) throw new Error(json.error);
        if (dataHandler == null) {
          message.react('✅');
        } else {
          dataHandler(message, json);
        }
      })
      .catch(function(error) {
        self.error(error, message);
      })
      .finally(function() {
        if (message.content === context.config.CMD_PREFIX + 'shutdown') {
          context.shutdown();
        }
      });
    return true;
  }

  doPostToFile(path, body = null) {
    let context = this.#context;
    this.doPost(path, body, function(message, json) {
      if (json == null || !json.hasOwnProperty('url')) {
        message.react('✅');
        return;
      }
      message.react('⌛');
      let fname = message.id + '.text';
      let fpath = '/tmp/' + fname;
      let fstream = fs.createWriteStream(fpath);
      fstream.on('error', logger.error);
      new subs.Helper(context).poll(json.url, function(data) {
        fstream.write(data);
        fstream.write('\n');
        return true;
      }).then(function() {
          fstream.end();
          message.reactions.removeAll()
            .then(function() { message.react('✅'); })
            .catch(logger.error);
          message.channel.send({ files: [{ attachment: fpath, name: fname }] })
            .then(function() { fs.unlink(fpath, logger.error); });
        });
    });
  }

}
