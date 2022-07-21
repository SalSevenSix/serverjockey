'use strict';

const logger = require('./logger.js');
const util = require('./util.js');
const fetch = require('node-fetch');

exports.Helper = class Helper {
  #context;

  constructor(context) {
    this.#context = context;
  }

  async daemon(subscribeUrl, dataHandler) {
    let context = this.#context;
    let url = null;
    while (context.running && url == null) {
      while (context.running && url == null) {
        url = await this.subscribe(subscribeUrl, function(pollUrl) {
          logger.info(subscribeUrl + ' => ' + pollUrl);
        });
        if (context.running && url == null) {
          await util.sleep(12000);
        }
      }
      if (context.running && url != null && url != false) {
        await this.poll(url, dataHandler);
      }
      if (url != false) {
        url = null;
      }
    }
  }

  async subscribe(subscribeUrl, dataHandler) {
    return await fetch(subscribeUrl, util.newPostRequest('application/json', this.#context.config.SERVER_TOKEN))
      .then(function(response) {
        if (response.status === 404) return false;
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        if (json === false) return false;
        dataHandler(json.url);
        return json.url;
      })
      .catch(logger.error);  // return null
  }

  async poll(url, dataHandler) {
    let signal = this.#context.signal;
    let polling = (url != null);
    while (this.#context.running && polling) {
      polling = await fetch(url, { signal })
        .then(function(response) {
          if (response.status === 404) return null;
          if (!response.ok) throw new Error('Status: ' + response.status);
          if (response.status === 204) return {};
          let ct = response.headers.get('Content-Type');
          if (ct.startsWith('text/plain')) return response.text();
          return response.json();
        })
        .then(function(data) {
          if (data == null) return false;
          if (util.isEmptyObject(data)) return true;
          return dataHandler(data);
        })
        .catch(function(error) {
          logger.error(error);
          return false;
        });
    }
  }

}
