/* Cookie / аналитика — баннер согласия (152-ФЗ, информирование о cookie и Яндекс.Метрике).
   "Принять" → запускается Яндекс.Метрика (window.ymInit, если объявлена на странице).
   "Отклонить" → Метрика НЕ запускается. Выбор хранится в localStorage.
   Стиль — матовое «стекло» сайта; акцент (фиолетовый/золотой) подхватывается со страницы. */
(function () {
  var KEY = 'cookieConsent';

  function runAnalytics() {
    if (typeof window.ymInit === 'function') window.ymInit();
  }

  function theme() {
    var cs = getComputedStyle(document.documentElement);
    var grad = (cs.getPropertyValue('--grad') || '').trim();
    var accent = (cs.getPropertyValue('--gold') || '').trim() || '#8965e0';
    return {
      grad: grad || ('linear-gradient(135deg,' + accent + ',' + accent + ')'),
      accent: accent
    };
  }

  function injectStyles() {
    if (document.getElementById('cookie-consent-style')) return;
    var css = '' +
      /* стеклянная подложка как у карточек сайта */
      '#cookie-consent{position:fixed;left:16px;right:16px;bottom:18px;z-index:9999;max-width:660px;margin:0 auto;' +
      'background:linear-gradient(135deg,rgba(20,14,38,0.62),rgba(6,4,16,0.62));' +
      'backdrop-filter:blur(22px) saturate(150%);-webkit-backdrop-filter:blur(22px) saturate(150%);' +
      'border:1px solid var(--cc-accent-border,rgba(137,101,224,0.35));border-radius:18px;' +
      'padding:20px 22px;display:flex;flex-wrap:wrap;align-items:center;gap:16px;' +
      'box-shadow:0 20px 60px rgba(0,0,0,0.55),0 0 0 1px rgba(255,255,255,0.03) inset,0 1px 0 rgba(255,255,255,0.06) inset;' +
      'font-family:"Montserrat",sans-serif;animation:ccUp .45s cubic-bezier(.2,.7,.2,1);}' +
      /* тонкая акцентная линия сверху, как ::before у карточек */
      '#cookie-consent::before{content:"";position:absolute;top:0;left:22px;right:22px;height:1px;border-radius:2px;' +
      'background:var(--cc-grad,linear-gradient(90deg,#5e72e4,#8965e0,#f5365c));opacity:.55;}' +
      '@keyframes ccUp{from{transform:translateY(24px);opacity:0}to{transform:translateY(0);opacity:1}}' +
      '#cookie-consent .cc-text{flex:1 1 290px;font-size:13px;line-height:1.55;color:rgba(240,240,240,0.82);}' +
      '#cookie-consent .cc-text a{color:var(--cc-accent,#8965e0);text-decoration:none;border-bottom:1px solid transparent;transition:.2s;}' +
      '#cookie-consent .cc-text a:hover{border-bottom-color:var(--cc-accent,#8965e0);}' +
      '#cookie-consent .cc-btns{display:flex;gap:10px;flex-shrink:0;}' +
      '#cookie-consent button{font-family:inherit;font-size:13px;font-weight:700;letter-spacing:.01em;border-radius:11px;' +
      'padding:11px 22px;cursor:pointer;border:1px solid transparent;transition:.2s;}' +
      /* "Принять" — градиентная кнопка как submit на сайте */
      '#cookie-consent .cc-accept{background:var(--cc-grad,linear-gradient(135deg,#5e72e4,#8965e0,#f5365c));color:#fff;' +
      'box-shadow:0 6px 20px rgba(94,114,228,0.35);}' +
      '#cookie-consent .cc-accept:hover{transform:translateY(-1px);box-shadow:0 10px 26px rgba(94,114,228,0.45);}' +
      /* "Отклонить" — стеклянная ghost-кнопка */
      '#cookie-consent .cc-decline{background:rgba(255,255,255,0.04);color:rgba(240,240,240,0.7);' +
      'border-color:var(--cc-accent-border,rgba(137,101,224,0.3));}' +
      '#cookie-consent .cc-decline:hover{color:#fff;background:rgba(255,255,255,0.08);' +
      'border-color:var(--cc-accent,#8965e0);}' +
      '@media(max-width:520px){#cookie-consent{flex-direction:column;align-items:stretch;text-align:left;left:12px;right:12px;bottom:12px;padding:18px;}' +
      '#cookie-consent .cc-btns{justify-content:stretch;}#cookie-consent .cc-btns button{flex:1;}}';
    var s = document.createElement('style');
    s.id = 'cookie-consent-style';
    s.textContent = css;
    document.head.appendChild(s);
  }

  function showBanner() {
    injectStyles();
    var t = theme();
    var bar = document.createElement('div');
    bar.id = 'cookie-consent';
    bar.setAttribute('role', 'dialog');
    bar.setAttribute('aria-label', 'Уведомление об использовании cookie');
    bar.style.setProperty('--cc-grad', t.grad);
    bar.style.setProperty('--cc-accent', t.accent);
    bar.style.setProperty('--cc-accent-border', hexToBorder(t.accent));
    bar.innerHTML =
      '<div class="cc-text">Мы используем файлы cookie и сервис Яндекс.Метрика для корректной работы сайта и аналитики. ' +
      'Подробнее — в <a href="/privacy.html" target="_blank" rel="noopener">Политике конфиденциальности</a>.</div>' +
      '<div class="cc-btns">' +
      '<button type="button" class="cc-decline">Отклонить</button>' +
      '<button type="button" class="cc-accept">Принять</button>' +
      '</div>';
    document.body.appendChild(bar);

    bar.querySelector('.cc-accept').addEventListener('click', function () {
      try { localStorage.setItem(KEY, 'accepted'); } catch (e) {}
      runAnalytics();
      fadeOut(bar);
    });
    bar.querySelector('.cc-decline').addEventListener('click', function () {
      try { localStorage.setItem(KEY, 'declined'); } catch (e) {}
      fadeOut(bar);
    });
  }

  /* акцент → полупрозрачная рамка того же тона */
  function hexToBorder(hex) {
    var m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex.trim());
    if (!m) return 'rgba(137,101,224,0.35)';
    return 'rgba(' + parseInt(m[1], 16) + ',' + parseInt(m[2], 16) + ',' + parseInt(m[3], 16) + ',0.4)';
  }

  function fadeOut(bar) {
    bar.style.transition = 'opacity .3s, transform .3s';
    bar.style.opacity = '0';
    bar.style.transform = 'translateY(16px)';
    setTimeout(function () { bar.remove(); }, 300);
  }

  function start() {
    var choice = null;
    try { choice = localStorage.getItem(KEY); } catch (e) {}
    if (choice === 'accepted') { runAnalytics(); return; }
    if (choice === 'declined') { return; }
    showBanner();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
