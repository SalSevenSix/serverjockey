import { writable } from 'svelte/store';

export const instance = writable({});
export const serverStatus = writable({});
export const eventDown = writable();
export const eventStarted = writable();
export const eventEndMaint = writable();
