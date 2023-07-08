import { dev } from '$app/environment';
import { writable, get } from 'svelte/store';
import { sleep } from '$lib/util';
import { notifyError } from '$lib/notifications';

export const baseurl = (dev ? 'http://localhost:6164' : '');
export const securityToken = writable();
export const instance = writable({});
export const serverStatus = writable({});
export const eventDown = writable();
export const eventStarted = writable();


export function newGetRequest() {
  return {
    method: 'get',
    headers: {
      'X-Secret': get(securityToken)
    }
  };
}

export function rawPostRequest() {
  return {
    method: 'post',
    headers: { 'X-Secret': get(securityToken) }
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

export function openFileInNewTab(url, errorCallback=null) {
  fetch(url, newGetRequest())
    .then(function(response) {
      if (!response.ok) throw new Error('Status: ' + response.status);
      return response.blob();
    })
    .then(function(blob) {
      window.open(window.URL.createObjectURL(blob)).focus();
    })
    .catch(function(error) {
      if (errorCallback) {
        errorCallback(error);
      } else {
        notifyError('Failed to load. File may not exist.');
      }
    });
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
        url = await this.#subscribe(subscribeUrl);
        if (this.#running && url == null) {
          await sleep(10000);
        }
      }
      if (url === false) {
        this.#running = false;  // exit loop
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

  async #subscribe(subscribeUrl) {
    return await fetch(subscribeUrl, newPostRequest())
      .then(function(response) {
        if (response.status === 404) return false;
        if (!response.ok) throw new Error('Status: ' + response.status);
        return response.json();
      })
      .then(function(json) {
        if (json === false) return false;
        return json.url;
      })
      .catch(function(error) {
        return notifyError('Subscription failed. Check connection and server. Refresh page.');
      });
  }

  async #doPoll(url, signal, dataHandler) {
    let polling = (url != null);
    while (this.#running && polling) {
      polling = await fetch(url, { signal })
        .then(function(response) {
          if (response.status === 404) return false;
          if (!response.ok) throw new Error('Status: ' + response.status);
          if (response.status === 204) return null;
          let ct = response.headers.get('Content-Type');
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
  }
}
