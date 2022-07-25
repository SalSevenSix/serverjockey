import { dev } from '$app/env';
import { writable, get } from 'svelte/store';

export const baseurl = (dev ? 'http://localhost:6164' : '');
export const securityToken = writable();
export const instance = writable({});
export const serverStatus = writable({});


export class SubscriptionHelper {
  #controller;
  #running;

  constructor() {
    this.#controller = new AbortController();
    this.#running = false;
  }

  async start(url, dataHandler) {
    let pollingUrl = await this.#subscribe(url);
    this.#running = (pollingUrl != null);
    this.#poll(pollingUrl, this.#controller.signal, dataHandler);
  }

  stop() {
    this.#running = false;
    this.#controller.abort();
  }

  running() {
    return this.#running;
  }

  async #subscribe(url) {
    return await fetch(url, newPostRequest())
      .then(function(response) {
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        return json.url;
      })
      .catch(function(error) { alert('Error ' + error); });
  }

  async #poll(url, signal, dataHandler) {
    let polling = (url != null);
    while (this.#running && polling) {
      polling = await fetch(url, { signal })
        .then(function(response) {
          if (response.status === 404) return false;
          if (!response.ok) throw new Error('Status: ' + response.status);
          if (response.status === 204) return null;
          var ct = response.headers.get('Content-Type');
          if (ct.startsWith('text/plain')) return response.text();
          return response.json();
        })
        .then(function(data) {
          if (data === false) return false;
          if (data == null) return true;
          return dataHandler(data);
        })
        .catch(function(error) {
          return false;
        });
    }
    this.#running = false;
  }
}


export function newGetRequest() {
  return {
    method: 'get',
    headers: {
      'X-Secret': get(securityToken)
    }
  };
}

export function newPostRequest(ct = 'application/json') {
  return {
    method: 'post',
    headers: {
      'Content-Type': ct, 'X-Secret': get(securityToken)
    }
  };
}
