import { writable, get } from 'svelte/store';

export const connection = writable();


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
