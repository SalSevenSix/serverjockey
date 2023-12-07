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

export function newPostRequest() {
  return {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'X-Secret': get(connection).token
    }
  };
}
