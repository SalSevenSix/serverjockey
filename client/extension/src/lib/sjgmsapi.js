import { writable, get } from 'svelte/store';

export const connection = writable();
export const errorText = writable();


function sleep(millis) {
  return new Promise(function(resolve) { setTimeout(resolve, millis); });
}

export function logError(error) {
  if (!error) return;
  console.error(error);
  const text = error.toString();
  errorText.set(text);
  sleep(8000).then(function() {
    if (text === get(errorText)) { errorText.set(null); }
  });
}

export function baseurl(path) {
  return get(connection).url + path;
}

export function newGetRequest() {
  return {
    method: 'get',
    headers: {
      'X-Secret': get(connection).token
    }
  };
}

export function newPostRequest(ct = 'application/json') {
  return {
    method: 'post',
    headers: {
      'Content-Type': ct,
      'X-Secret': get(connection).token
    }
  };
}
