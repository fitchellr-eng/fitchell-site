/* Отправка заявок с внутренних страниц (Продажи / Управление / Тренеры).
   На главной свой обработчик внутри index.html — этот файл там НЕ подключается.
   Поля страниц (team, role, format, comment) приводятся к формату, который
   понимает Cloud Function: name, phone, company, program, message, page, consent. */
(function () {
  var ENDPOINT = 'https://functions.yandexcloud.net/d4e0bieu6ein4udol75t';

  var form = document.getElementById('contactForm');
  if (!form) return;
  var btn = form.querySelector('button[type="submit"]');

  var LABELS = {
    team: 'Размер команды',
    role: 'Роль',
    format: 'Формат'
  };

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var fd = new FormData(form);
    var get = function (k) { return (fd.get(k) || '').toString().trim(); };

    var extras = [];
    ['role', 'team'].forEach(function (k) {
      if (get(k)) extras.push(LABELS[k] + ': ' + get(k));
    });

    var message = [get('comment') || get('message'), extras.join('\n')]
      .filter(Boolean).join('\n\n');

    var payload = {
      name: get('name'),
      phone: get('phone'),
      company: get('company'),
      program: get('program') || get('format'),
      message: message,
      page: location.href,
      consent: !!(form.consent && form.consent.checked)
    };

    var original = btn ? btn.textContent : '';
    if (btn) { btn.textContent = 'Отправляю...'; btn.disabled = true; }

    fetch(ENDPOINT, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }
    })
      .then(function (res) {
        if (!res.ok) throw new Error('bad status');
        if (btn) { btn.textContent = '✓ Заявка отправлена!'; btn.style.background = '#2a6e47'; }
        form.reset();
      })
      .catch(function () {
        if (!btn) return;
        btn.textContent = 'Ошибка — попробуйте ещё раз';
        btn.style.background = '#7a2d2d';
        btn.disabled = false;
        setTimeout(function () {
          btn.textContent = original;
          btn.style.background = '';
        }, 3000);
      });
  });
})();
