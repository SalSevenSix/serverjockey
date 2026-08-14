export async function fetchJson(url) {
  return await fetch(url)
    .then(function(response) { return response.json(); })
    .then(function(json) { return json; })
    .catch(function(error) { return error; });
}
