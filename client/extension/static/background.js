const BASEURL_STEAM_COMMUNITY = 'https://steamcommunity.com/';

function iconPaths(enabled) {
  return { path: {
    16: 'images/icon-16' + (enabled ? '.png' : '-disabled.png'),
    48: 'images/icon-48' + (enabled ? '.png' : '-disabled.png'),
    128: 'images/icon-128' + (enabled ? '.png' : '-disabled.png')
  }};
}

function handleUpdate(tabId, url) {
  if (!url) return;
  if (url.startsWith(BASEURL_STEAM_COMMUNITY)) {
    chrome.sidePanel.setOptions({ tabId, path: 'index.html', enabled: true });
    chrome.action.setIcon(iconPaths(true));
  } else {
    chrome.sidePanel.setOptions({ tabId, enabled: false });
    chrome.action.setIcon(iconPaths(false));
  }
}

chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch(function(error) { console.error(error); });

chrome.tabs.onUpdated.addListener(function(tabId, info, tab) {
  handleUpdate(tabId, tab.url);
});

chrome.tabs.onActivated.addListener(function(activeInfo) {
  chrome.tabs.get(activeInfo.tabId).then(function(tab) {
    handleUpdate(activeInfo.tabId, tab.url);
  });
});
