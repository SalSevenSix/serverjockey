export async function fetchJson(url) {
  return await fetch(url)
    .then(function(response) { return response.json(); })
    .then(function(json) { return json; })
    .catch(function(error) { return error; });
}

export function truncName(name, maxlen) {
  if (!name || name.length <= maxlen) return name;
  return name.slice(0, maxlen - 1) + '~';
}
