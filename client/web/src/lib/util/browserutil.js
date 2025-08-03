export const noStorage = typeof(Storage) === 'undefined';
export const browserName = getBrowserName();

function getBrowserName() {
  if (typeof(window) === 'undefined') return 'Chrome';
  const ua = window.navigator.userAgent;
  if (ua.includes('Firefox')) return 'Firefox';
  if (ua.includes('SamsungBrowser')) return 'SamsungBrowser';
  if (ua.includes('Opera') || ua.includes('OPR')) return 'Opera';
  if (ua.includes('Edge') || ua.includes('Edg')) return 'Edge';
  if (ua.includes('Chrome')) return 'Chrome';
  if (ua.includes('Safari')) return 'Safari';
  return 'Chrome';
}

export class ObjectUrls {
  #urls = [];

  openBlob(blob) {
    const url = URL.createObjectURL(blob);
    this.#urls.push(url);
    window.open(url).focus();
  }

  openObject(data) {
    const blob = new Blob([JSON.stringify(data)], { type : 'text/plain;charset=utf-8' });
    this.openBlob(blob);
  }

  cleanup() {
    this.#urls.forEach(function(url) {
      URL.revokeObjectURL(url);
    });
    this.#urls.length = 0;
  }
}
