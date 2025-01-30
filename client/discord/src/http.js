const cutil = require('common/util/util');
const util = require('./util.js');
const logger = require('./logger.js');
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

  doGet(path, dataHandler) {
    const context = this.#context;
    const message = this.#message;
    if (!util.checkHasRole(message, context.config.PLAYER_ROLE)) return;
    fetch(this.#baseurl + path, util.newGetRequest(context.config.SERVER_TOKEN))
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        const ct = response.headers.get('Content-Type');
        if (ct.startsWith('text/plain')) return response.text();
        return response.json();
      })
      .then(function(data) {
        const result = dataHandler(data);
        if (!result) return;
        if (cutil.isString(result)) {
          message.channel.send(result);
        } else {
          result.forEach(function(text) { message.channel.send(text); });
        }
      })
      .catch(function(error) {
        logger.error(error, message);
      });
  }

  doPost(path, body = null, dataHandler = null, allowRoles = null) {
    const context = this.#context;
    const message = this.#message;
    if (allowRoles && !util.checkHasRole(message, allowRoles)) return;
    if (!allowRoles && !util.checkHasRole(message, context.config.ADMIN_ROLE)) return;
    let request = util.newPostRequest('application/json', context.config.SERVER_TOKEN);
    if (cutil.isString(body)) {
      request = util.newPostRequest('text/plain', context.config.SERVER_TOKEN);
      request.body = body.replace(/\r\n/g, '\n');
    } else if (body != null) {
      request.body = JSON.stringify(body);
    }
    fetch(this.#baseurl + path, request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        if (response.status === 204) return null;
        const ct = response.headers.get('Content-Type');
        if (ct.startsWith('text/plain')) return response.text();
        return response.json();
      })
      .then(function(data) {
        if (dataHandler) {
          dataHandler(data);
        } else {
          util.reactSuccess(message);
        }
      })
      .catch(function(error) {
        logger.error(error, message);
      })
      .finally(function() {
        if (message.content === context.config.CMD_PREFIX + 'shutdown') {
          context.shutdown();
        }
      });
    return true;
  }

  doPostToFile(path, body = null) {
    const context = this.#context;
    const message = this.#message;
    this.doPost(path, body, function(json) {
      if (json == null || !cutil.hasProp(json, 'url')) return util.reactSuccess(message);
      util.reactWait(message);
      const fname = message.id + '.text';
      const fpath = '/tmp/' + fname;
      const fstream = fs.createWriteStream(fpath);
      fstream.on('error', logger.error);
      new subs.Helper(context).poll(json.url, function(data) {
        fstream.write(data);
        fstream.write('\n');
        return true;
      }).then(function() {
        fstream.end();
        util.rmReacts(message, util.reactSuccess, logger.error);
        message.channel.send({ files: [{ attachment: fpath, name: fname }] })
          .finally(function() { fs.unlink(fpath, logger.error); });
      });
    });
  }
};
