import { writable } from 'svelte/store';

export const instances = writable([]);
export const instance = writable({});
export const serverStatus = writable({ running: false, state: 'UNKNOWN' });


export async function loadInstances() {
  const result = await fetch('http://localhost:6164/instances')
    .then(function(response) { return response.json(); })
    .catch(function(error) { return 'Error ' + error; });
  let data = [];
  Object.keys(result).forEach(function(key) {
    data.push({ name: key, module: result[key].module, url: result[key].url });
  });
  instances.set(data);
}

export function postServerCommand(instance, command) {
  fetch(instance.url + '/server/' + command, newPostRequest())
    .catch(function(error) { alert('Error ' + error); });
}

export async function fetchPlayers(instance) {
  return await fetch(instance.url + '/players')
    .then(function(response) { return response.json(); })
    .catch(function(error) { return 'Error ' + error; });
}

export async function subscribeServerStatus(instance, dataHandler) {
  subscribe(instance.url + '/server/subscribe')
    .then(function(url) { poll(url, dataHandler); });
  return await fetchServerStatus(instance);
}



async function fetchServerStatus(instance) {
  return await fetch(instance.url + '/server')
    .then(function(response) { return response.json(); })
    .catch(function(error) { return 'Error ' + error; });
}

async function subscribe(url) {
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

async function poll(url, dataHandler) {
  var polling = (url != null);
  while (polling) {
    polling = await fetch(url)
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
        return dataHandler(data);
      })
      .catch(function(error) { return false } );
  }
}

function newPostRequest(ct = 'application/json') {
  return {
    method: 'post',
    headers: {
      'Content-Type': ct
    }
  };
}
