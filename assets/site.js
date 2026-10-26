/* Basket+ — minimalny skrypt pomocniczy (bez śledzenia, bez zewnętrznych zasobów).
   1) otwiera pytanie FAQ wskazane w adresie (#faq-3) oraz po kliknięciu linku do kotwicy,
   2) Esc / kliknięcie poza menu zamyka menu języków.
   Strona działa w pełni także bez tego pliku. */
(function () {
  function openFromHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    var el = document.getElementById(id);
    if (el && el.tagName === 'DETAILS') {
      el.open = true;
      el.scrollIntoView();
    }
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  var menu = document.querySelector('.lang-menu details');
  if (!menu) return;
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menu.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
  document.addEventListener('click', function (e) {
    if (menu.open && !menu.contains(e.target)) menu.open = false;
  });
})();
