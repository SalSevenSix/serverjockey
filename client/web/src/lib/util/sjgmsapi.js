import { writable, get } from 'svelte/store';
import { base } from '$app/paths';
import { sleep } from '$lib/util/util';
import { notifyError } from '$lib/util/notifications';

export const securityToken = writable();


export function surl(path) {
  if (path && path.startsWith('http')) return path;  // Assuming full urls are correct
  if (base && path) return base + path;
  if (path) return path;
  return base ? base : '';
}

export function newGetRequest() {
  return { method: 'get', headers: { 'X-Secret': get(securityToken) }};
}

export function newPostRequest(ct='application/json') {
  const headers = ct ? { 'Content-Type': ct, 'X-Secret': get(securityToken) } : { 'X-Secret': get(securityToken) };
  return { method: 'post', headers: headers };
}


export class SubscriptionHelper {
  #controller;
  #running;

  constructor() {
    this.#controller = new AbortController();
    this.#running = false;
  }

  async start(subscribeUrl, dataHandler) {
    this.#running = true;
    let url = null;
    while (this.#running) {
      url = null;
      while (this.#running && url == null) {
        url = await SubscriptionHelper.#subscribe(subscribeUrl);
        if (this.#running && url == null) {
          await sleep(12000);
        }
      }
      if (url === false) {
        this.#running = false;  // Exit loop
      }
      if (this.#running) {
        await this.#doPoll(url, this.#controller.signal, dataHandler);
      }
    }
  }

  poll(pollingUrl, dataHandler) {
    this.#running = (pollingUrl != null);
    return this.#doPoll(pollingUrl, this.#controller.signal, dataHandler);
  }

  stop() {
    this.#running = false;
    this.#controller.abort();
  }

  static async #subscribe(subscribeUrl) {
    return await fetch(surl(subscribeUrl), newPostRequest())
      .then(function(response) {
        if (response.status === 404) return false;
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        if (json === false) return false;
        return json.url;
      })
      .catch(function() {
        return notifyError('Communication error. Check connection and server. Refresh page.');
      });
  }

  async #doPoll(url, signal, dataHandler) {
    let failcount = 5;
    let polling = (url != null);
    while (this.#running && polling) {
      polling = await fetch(url, { signal })
        .then(function(response) {
          if (response.status === 404) return false;
          if (!response.ok) throw new Error('Status: ' + response.status);
          if (response.status === 204) return true;
          let ct = response.headers.get('Content-Type');
          if (ct.startsWith('text/plain')) return response.text();
          return response.json();
        })
        .then(function(data) {
          if (data === false) return false;
          if (data === true) return true;
          if (dataHandler(data)) return true;
          return false;
        })
        .catch(function() {
          return null;
        });
      if (polling === true) { failcount = 5; }
      if (this.#running && polling == null && failcount > 0) {
        failcount -= 1;
        await sleep(1200);
        polling = true;
      }
    }
  }
}
