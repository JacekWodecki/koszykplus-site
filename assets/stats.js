/* Basket+ stats: bez cookies, bez IP, bez danych osobowych. Worker: patrz data-w w <script>. */
(function () {
  var s = document.currentScript, W = s && s.getAttribute("data-w");
  if (!W || navigator.doNotTrack === "1" || /^(localhost|127\.|\[::1\])/.test(location.hostname)) return;
  try {
    var body = JSON.stringify({ p: location.pathname, l: document.documentElement.lang, r: document.referrer });
    if (!(navigator.sendBeacon && navigator.sendBeacon(W + "/hit", body)))
      fetch(W + "/hit", { method: "POST", body: body, keepalive: true, mode: "cors" });
  } catch (e) {}
  var a = document.querySelectorAll("a[data-c]");
  for (var i = 0; i < a.length; i++) a[i].href = W + "/go?c=" + a[i].getAttribute("data-c");
})();
