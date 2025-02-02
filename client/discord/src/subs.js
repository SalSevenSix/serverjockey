const cutil = require('common/util/util');
const util = require('./util.js');
const logger = require('./logger.js');
const fetch = require('node-fetch');

exports.Helper = class Helper {
  #context;

  constructor(context) {
    this.#context = context;
  }

  async daemon(subscribeUrl, dataHandler) {
    const context = this.#context;
    let url = null;
    let counter = 0;
    while (context.running && url == null) {
      while (context.running && url == null) {
        url = await this.subscribe(subscribeUrl);
        if (url == null) {
          counter = 60;  // Small sleeps in loop to allow quick exit if not running
          while (context.running && counter > 0) {
            await cutil.sleep(200);
            counter -= 1;
          }
        }
      }
      if (context.running && url) {
        await this.poll(url, dataHandler);
        url = null;
      }
    }
  }

  async subscribe(subscribeUrl) {
    return await fetch(subscribeUrl, util.newPostRequest('application/json', this.#context.config.SERVER_TOKEN))
      .then(function(response) {
        if (response.status === 404) return false;
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        if (json === false) return false;
        return json.url;
      })
      .catch(logger.error);
  }

  async poll(url, dataHandler) {
    const { signal } = this.#context;
    let polling = url != null;
    while (this.#context.running && polling) {
      polling = await fetch(url, { signal })
        .then(function(response) {
          if (response.status === 404) return false;
          if (!response.ok) throw new Error('Status: ' + response.status);
          if (response.status === 204) return true;
          const ct = response.headers.get('Content-Type');
          if (ct.startsWith('text/plain')) return response.text();
          return response.json();
        })
        .then(function(data) {
          if (data === false) return false;
          if (data === true) return true;
          return dataHandler(data);
        })
        .catch(function(error) {
          logger.error(error);
          return false;
        });
    }
  }
};
