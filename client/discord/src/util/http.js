import fs from 'fs';
import fetch from 'node-fetch';
import * as cutil from 'common/util/util';
import * as util from './util.js';
import * as logger from './logger.js';
import * as msgutil from './msgutil.js';
import * as subs from './subs.js';

export class MessageHttpTool {
  #context;

  #message;

  #baseurl;

  constructor(context, message, baseurl) {
    this.#context = context;
    this.#message = message;
    this.#baseurl = baseurl;
  }

  async getJson(path, baseurlOverride = null) {
    const [context, message] = [this.#context, this.#message];
    const aBaseurl = baseurlOverride ? baseurlOverride : this.#baseurl;
    const aPath = path.url ? path.url : path;
    return await fetch(aBaseurl + aPath, util.newGetRequest(context.config.SERVER_TOKEN))
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(data) { return data; })
      .catch(function(error) { return logger.error(error, message); });
  }

  doGet(path, dataHandler) {
    const [context, message] = [this.#context, this.#message];
    fetch(this.#baseurl + path, util.newGetRequest(context.config.SERVER_TOKEN))
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        if (response.headers.get('Content-Type').startsWith('text/plain')) return response.text();
        return response.json();
      })
      .then(function(data) {
        const result = dataHandler(data);
        if (!result) return;
        msgutil.sendText(message, result, Array.isArray(result));
      })
      .catch(function(error) {
        logger.error(error, message);
      });
  }

  doPost(path, body = null, dataHandler = null) {
    const [context, message] = [this.#context, this.#message];
    let request = util.newPostRequest('application/json', context.config.SERVER_TOKEN);
    if (cutil.isString(body)) {
      request = util.newPostRequest('text/plain', context.config.SERVER_TOKEN);
      request.body = body.replace(/\r\n/g, '\n');
    } else if (body) {
      request.body = JSON.stringify(body);
    }
    fetch(this.#baseurl + path, request)
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        if (response.status === 204) return null;
        if (response.headers.get('Content-Type').startsWith('text/plain')) return response.text();
        return response.json();
      })
      .then(function(data) {
        if (dataHandler) { dataHandler(data); }
        else { msgutil.reactSuccess(message); }
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
    const [context, message] = [this.#context, this.#message];
    this.doPost(path, body, function(json) {
      if (!json || !cutil.hasProp(json, 'url')) return msgutil.reactSuccess(message);
      msgutil.reactWait(message);
      const fname = message.id + '.text';
      const fpath = '/tmp/' + fname;
      const fstream = fs.createWriteStream(fpath);
      fstream.on('error', logger.error);
      new subs.Helper(context).poll(json.url, function(data) {
        fstream.write(data);
        fstream.write('\n');
        return true;
      }).then(function() {
        fstream.end(function() {
          msgutil.rmReacts(message, msgutil.reactSuccess, logger.error);
          message.channel.send({ files: [{ attachment: fpath, name: fname }] })
            .finally(function() { fs.unlink(fpath, logger.error); });
        });
      });
    });
  }
}
