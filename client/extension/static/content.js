
chrome.runtime.onMessage.addListener(function(msg, sender, sendResponse) {
  if (msg.name === 'serverjockey-send-dom') {
    sendResponse(document.all[0].outerHTML);
  }
});
