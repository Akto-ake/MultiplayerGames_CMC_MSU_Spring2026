# multiplayer_games_CMC2026

## Описание:
Многопользовательское приложение с набором игр для двоих.

## Потенциально необходимые инструменты:
- язык программирования: Python;
- сетевое взаимодействие: socket, threading / asyncio;
- графический интерфейс: tkinter или pygame;

## Примерный набросок интерфейса
- **главное меню**:
  включает пункты:
  1) Список доступных игровых сеансов
  2) Информацию про доступные игры
  3) Создание игрового сеанса 
  4) подключение к существующему сеансу
  5) выход
   ![menu](media/menu.jpg)
   
- **Создание игрового сеанса**
  
   1) Выбор имени игрового сеанса
   2) Выбор игры
   ![connect](media/connect.jpg)
- **подключение к существующему сеансу**
  
  1) Подключение по ip или именни игрового сеанса

## Предполагаемые доступные игры:
- Подобие "Танки 1990"
- Пинг-понг
- Крестики-нолики 
- Морской бой
- Викторина
- Змейка

## Установка

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
```

## Запуск

```bash
python src/main_server.py
python src/main_client.py
```

После установки доступны точки входа:
```bash
main.server
main.client
```

## Автоматизация

```bash
doit list
doit i18n
doit test
doit html
doit wheel
```

## Сборка wheel

```bash
doit wheel

Далее в новом окружении:
pip install dist/multiplayer_games_cmc2026-0.1.0-py3-none-any.whl
```

## Просмотр документации

```bash
doit html
open docs/_build/html/index.html (MacOS)
xdg-open docs/_build/html/index.html (Linux)
Start-Process docs/_build/html/index.html (Windows)
```

