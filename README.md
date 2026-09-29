# kitbox-get-vm-count

Мониторинг Kit Vending: число активных автоматов, версии прошивок и доступность сервисов для страницы
https://kitbox.rockevents.ru/. С API работает через библиотеку [kitvending-api](https://github.com/embedcat/kitvending-api).

- `get_active_modems.py` — число активных автоматов и версии прошивок → `data/data.json`, `data/version_info.txt`;
- `check_servers.py` — доступность сервисов и MQTT → `data/server_status.json`. Кроме текущего статуса в файле лежит
  `history` — результаты проверок за последние 24 часа, по ним страница рисует график доступности (полосы по 30 минут:
  зелёная — все проверки успешны, жёлтая — часть, красная — ни одной, серая — нет данных);
- `publish.py` — выкладывает файлы из `data/` на сервер со страницей (`index.html`, `script.js`) через rsync.

Настройки — `.env` (образец `.env.example`), расписание — `crontab.example`.

```bash
pip install -r requirements-dev.txt
pytest
```

Версия `kitvending-api` зафиксирована тегом в `requirements.txt`. После её смены на сервере с cron нужен
`venv/bin/pip install -r requirements.txt`, одного `git pull` мало.
