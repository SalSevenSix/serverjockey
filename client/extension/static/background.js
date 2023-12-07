const STEAM_WORKSHOP = 'https://steamcommunity.com/sharedfiles/filedetails/?id=';

// Allows users to open the side panel by clicking on the action toolbar icon
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch(function(error) { console.error(error); });

chrome.tabs.onUpdated.addListener(async function(tabId, info, tab) {
  if (!tab.url) return;
  if (tab.url.startsWith(STEAM_WORKSHOP)) {
    await chrome.sidePanel.setOptions({ tabId, path: 'index.html', enabled: true });
  } else {
    await chrome.sidePanel.setOptions({ tabId, enabled: false });
  }
});
