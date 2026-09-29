# kitbox-get-vm-count

Мониторинг Kit Vending: число активных автоматов, версии прошивок и доступность сервисов для страницы
https://kitbox.rockevents.ru/. С API работает через библиотеку [kitvending-api](https://github.com/embedcat/kitvending-api).

- `get_active_modems.py` — число активных автоматов и версии прошивок → `data/data.json`, `data/version_info.txt`. Ответ API по
  полному аккаунту идёт около 8 минут, поэтому таймаут 15 минут (`API_TIMEOUT`), а запуск раз в сутки в 4:00.
  В `data.json` лежит `devices` — семейства прошивок с числом автоматов и разбивкой по версиям, по нему страница рисует список
  семейств (полосы по размеру, по клику на семейство — его версии). `device_count` — тот же список семейств строками
  «имя - число», оставлен для страницы старой версии; если в `data.json` нет `devices`, страница показывает его как простой список;
- `check_servers.py` — доступность сервисов и MQTT → `data/server_status.json`. Кроме текущего статуса в файле лежит
  `history` — результаты проверок за последние 24 часа, по ним страница рисует график доступности (полосы по 30 минут:
  зелёная — все проверки успешны, жёлтая — часть, красная — ни одной, серая — нет данных; `null` вместо `true`/`false` —
  «не измерялось», такая проверка на график не влияет). Тап или клик по полосе (на десктопе достаточно навести) показывает
  всплывашку с периодом и числом успешных проверок;
- `publish.py` — выкладывает файлы из `data/` на сервер со страницей (`index.html`, `script.js`) через rsync.

Настройки — `.env` (образец `.env.example`), расписание — `crontab.example`.

```bash
pip install -r requirements-dev.txt
pytest
```

Версия `kitvending-api` зафиксирована тегом в `requirements.txt`. После её смены на сервере с cron нужен
`venv/bin/pip install -r requirements.txt`, одного `git pull` мало.

## Развёртывание

Изменения выкладываются двумя `git pull` после пуша в GitHub, автоматики нет:

- коллектор (`kit@kit-invest.work`): `cd ~/kitvendig-api && git pull` (плюс `pip install`, если менялся `requirements.txt`);
- VPS со страницей: `ssh kip@rockevents.ru 'git -C /srv/kitbox-src pull --ff-only'`.

На VPS в `/srv/kitbox-src` лежит клон этого репозитория, а `/var/www/kitbox/index.html` и `script.js` — симлинки
на его файлы. Наружу отдаются только они и `data/`. Ключ коллектора пишет лишь в `data/` и код страницы менять не может.
Откат страницы: `git -C /srv/kitbox-src checkout <hash>`, вернуться на master — `git -C /srv/kitbox-src checkout master`.
