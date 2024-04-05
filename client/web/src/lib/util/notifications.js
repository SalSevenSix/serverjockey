import { writable, get } from 'svelte/store';
import { generateId, sleep } from '$lib/util/util';

export const notifications = writable([]);


function notify(level, message) {
  const now = Date.now();
  if (get(notifications).reduce(function(result, value) {
    if (result) return true;
    return message === value['message'] && now - value['at'] < 500;
  }, false)) return;
  const identity = generateId();
  notifications.update(function(current) {
    return [{ 'id': identity, 'at': now, 'level': level, 'message': message }, ...current];
  });
  sleep(8000).then(function() {
    removeNotification(identity);
  });
}

export function removeNotification(identity) {
  notifications.update(function(current) {
    return current.filter(function(value) {
      return identity != value.id;
    });
  });
}

export function notifyInfo(message, retval = null) {
  notify('is-success', message);
  return retval;
}

export function notifyWarning(message, retval = null) {
  notify('is-warning', message);
  return retval;
}

export function notifyError(message, retval = null) {
  notify('is-danger', message);
  return retval;
}
