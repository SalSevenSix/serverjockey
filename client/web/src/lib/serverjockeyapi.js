import { writable } from 'svelte/store';

export const instances = writable([]);
export const instance = writable({});

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
