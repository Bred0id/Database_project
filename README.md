# Music Studio Database Project

## 1. Описание проекта

Проект представляет собой базу данных для системы бронирования музыкальных студий.

База данных позволяет хранить и обрабатывать информацию о:

- пользователях;
- музыкальных студиях;
- оборудовании студий;
- бронированиях;
- платежах;
- обслуживании оборудования;
- отзывах пользователей.

Основная цель проекта — спроектировать реляционную базу данных, реализовать ограничения целостности, заполнить таблицы тестовыми данными, написать запросы к данным, а также реализовать расширенную часть проекта: индексы, представления, функции и триггеры.

---

## 2. Структура проекта

```text
Khodyrev_Mikhail-project/
│
├── base_part/
│   ├── music_studio_create.sql
│   ├── music_studio_fill.sql
│   └── music_studio_selects.sql
│
├── advanced_part/
│   ├── indexes.sql
│   ├── views.sql
│   ├── functions.sql
│   └── triggers.sql
│
├── data/
│   ├── Bookings.csv
│   ├── Booking_equipment.csv
│   ├── Equipment.csv
│   ├── Equipment_maintenance.csv
│   ├── Payments.csv
│   ├── Reviews.csv
│   ├── Review_equipment.csv
│   ├── Studios.csv
│   ├── Users.csv
│   └── Промпт.docx
│
├── schemas/
│   ├── PhysScheme.xlsx
│   ├── Концептуальная.drawio
│   ├── Концептуальная.drawio.png
│   ├── Логическая.drawio
│   └── Логическая.drawio.png
│
├── tests/
│   └── test_advanced_part.py
│
└── README.md
```

### Назначение файлов и папок

| Путь | Назначение |
|---|---|
| `base_part/music_studio_create.sql` | Создание схемы `music_studio`, таблиц, ограничений и связей |
| `base_part/music_studio_fill.sql` | Заполнение таблиц тестовыми данными |
| `base_part/music_studio_selects.sql` | Основные SELECT-запросы к базе данных |
| `advanced_part/indexes.sql` | Создание индексов |
| `advanced_part/views.sql` | Создание представлений |
| `advanced_part/functions.sql` | Создание функций на PL/pgSQL |
| `advanced_part/triggers.sql` | Создание триггеров |
| `data/` | Исходные CSV-файлы с данными и вспомогательные материалы для генерации/подготовки данных |
| `schemas/` | Материалы проектирования: концептуальная схема, логическая схема и физическая схема |
| `tests/test_advanced_part.py` | Pytest-тесты для расширенной части проекта |

---

## 3. Предметная область

Система моделирует работу сервиса бронирования музыкальных студий.

Основные сущности:

- `users` — пользователи системы;
- `studios` — музыкальные студии;
- `equipment` — оборудование;
- `bookings` — бронирования студий;
- `payments` — платежи за бронирования;
- `booking_equipment` — связь бронирований и оборудования;
- `equipment_maintenance` — обслуживание оборудования;
- `reviews` — отзывы пользователей;
- `review_equipment` — связь отзывов и оборудования.

---

## 4. Требования

Для запуска проекта требуется:

- PostgreSQL;
- pgAdmin или другой SQL-клиент;
- Python 3.10+ для запуска тестов;
- `pytest`;
- `psycopg2-binary`.

Установка Python-зависимостей:

```bash
pip install pytest psycopg2-binary
```

---

## 5. Порядок запуска SQL-скриптов

Скрипты необходимо выполнять в базе данных PostgreSQL в указанном порядке.

### 5.1. Создание базовой части

```text
base_part/music_studio_create.sql
```

Скрипт создаёт схему `music_studio`, таблицы, первичные ключи, внешние ключи и ограничения.

### 5.2. Заполнение данными

```text
base_part/music_studio_fill.sql
```

Скрипт заполняет таблицы тестовыми данными.

### 5.3. Проверка базовых запросов

```text
base_part/music_studio_selects.sql
```

Скрипт содержит SELECT-запросы для проверки работы базовой части проекта.

### 5.4. Создание индексов

```text
advanced_part/indexes.sql
```

Скрипт создаёт индексы для ускорения часто используемых запросов.

### 5.5. Создание представлений

```text
advanced_part/views.sql
```

Скрипт создаёт представления для упрощения аналитических запросов.

### 5.6. Создание функций

```text
advanced_part/functions.sql
```

Скрипт создаёт функции на PL/pgSQL.

### 5.7. Создание триггеров

```text
advanced_part/triggers.sql
```

Скрипт создаёт триггеры, которые автоматически проверяют и изменяют данные при вставке и обновлении.

---

## 6. Работа через pgAdmin

Для запуска проекта через pgAdmin нужно:

1. Открыть pgAdmin.
2. Подключиться к серверу PostgreSQL.
3. Создать новую базу данных или выбрать существующую.
4. Открыть `Query Tool` для выбранной базы данных.
5. Последовательно выполнить SQL-скрипты из раздела 5.

Рекомендуется выполнять скрипты по одному. Если при выполнении появляется ошибка, нужно остановиться, исправить проблему и только затем переходить к следующему файлу.

Проверить существование схемы можно запросом:

```sql
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'music_studio';
```

Проверить список таблиц схемы можно запросом:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'music_studio'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

---

## 7. Расширенная часть проекта

### 7.1. Индексы

В проекте реализованы следующие индексы.

#### `idx_bookings_studio_time`

Индекс по таблице `bookings`:

```sql
(studio_id, start_time, end_time)
```

Используется для поиска бронирований конкретной студии по временному интервалу.

#### `idx_bookings_user_time`

Индекс по таблице `bookings`:

```sql
(user_id, start_time)
```

Используется для поиска истории бронирований пользователя с сортировкой по времени.

#### `idx_equipment_problem_status`

Частичный индекс по таблице `equipment`:

```sql
(status)
WHERE status IN ('maintenance', 'broken')
```

Используется для поиска оборудования, которое находится на обслуживании или сломано.

В PostgreSQL по умолчанию используется индекс типа B-tree. В проекте явно не указан тип индекса, так как B-tree подходит для операций сравнения и диапазонных условий по времени. Hash-индексы не используются, так как они эффективны в основном для проверки равенства.

---

### 7.2. Представления

В проекте реализованы два представления.

#### `music_studio.v_active_bookings`

Представление показывает активные бронирования со статусами:

```text
created
confirmed
```

В представлении выводятся:

- идентификатор бронирования;
- идентификатор пользователя;
- имя пользователя;
- идентификатор студии;
- название студии;
- время начала и окончания бронирования;
- длительность бронирования в часах;
- цель бронирования;
- статус бронирования;
- итоговая стоимость.

Представление используется для удобного просмотра текущих бронирований без повторного написания JOIN-запросов.

#### `music_studio.v_studio_daily_load`

Представление показывает дневную загруженность студий.

Для каждой студии и даты выводятся:

- идентификатор студии;
- название студии;
- дата бронирований;
- количество бронирований;
- суммарное количество занятых часов;
- дневная выручка.

Представление используется для аналитики по загрузке студий.

---

### 7.3. Функции

В проекте реализованы три функции.

#### `music_studio.calculate_booking_cost`

Функция рассчитывает стоимость бронирования.

Параметры:

```sql
p_studio_id INT
p_start_time TIMESTAMP
p_end_time TIMESTAMP
```

Возвращает:

```sql
NUMERIC(12, 2)
```

Функция получает цену студии за час и умножает её на длительность бронирования.

#### `music_studio.is_studio_available`

Функция проверяет доступность студии в заданный временной интервал.

Параметры:

```sql
p_studio_id INT
p_start_time TIMESTAMP
p_end_time TIMESTAMP
p_exclude_booking_id INT DEFAULT NULL
```

Возвращает:

```sql
BOOLEAN
```

Функция проверяет:

- существует ли студия;
- имеет ли студия статус `available`;
- нет ли пересекающихся бронирований со статусами `created` или `confirmed`.

#### `music_studio.create_booking`

Функция создаёт бронирование и возвращает его идентификатор.

Параметры:

```sql
p_user_id INT
p_studio_id INT
p_start_time TIMESTAMP
p_end_time TIMESTAMP
p_purpose VARCHAR(100)
```

Возвращает:

```sql
INT
```

Функция проверяет:

- существует ли пользователь;
- активен ли пользователь;
- доступна ли студия;
- корректен ли временной интервал.

После проверок функция рассчитывает стоимость бронирования и вставляет запись в таблицу `bookings`.

---

### 7.4. Триггеры

В проекте реализованы два триггера.

#### `check_booking_before_insert_update`

Триггер срабатывает перед вставкой или обновлением бронирования.

Таблица:

```sql
music_studio.bookings
```

События:

```sql
BEFORE INSERT OR UPDATE OF user_id, studio_id, start_time, end_time
```

Триггер выполняет следующие проверки:

- пользователь существует;
- пользователь активен;
- студия существует;
- студия доступна;
- бронирование не пересекается по времени с другим активным бронированием.

Также триггер автоматически пересчитывает `total_cost`.

#### `process_payment_before_insert_update`

Триггер срабатывает перед вставкой или обновлением платежа.

Таблица:

```sql
music_studio.payments
```

События:

```sql
BEFORE INSERT OR UPDATE OF amount, status
```

Триггер проверяет:

- существует ли бронирование;
- совпадает ли сумма платежа со стоимостью бронирования;
- можно ли проводить платёж для отменённого бронирования.

Если платёж получает статус `paid`, статус бронирования автоматически меняется на `confirmed`.

Если платёж получает статус `refunded`, статус бронирования автоматически меняется на `cancelled`.

---

## 8. Примеры ручной проверки

### 8.1. Проверка представлений

```sql
SELECT *
FROM music_studio.v_active_bookings
LIMIT 5;
```

```sql
SELECT *
FROM music_studio.v_studio_daily_load
LIMIT 5;
```

### 8.2. Проверка функции расчёта стоимости

```sql
SELECT music_studio.calculate_booking_cost(
    2,
    TIMESTAMP '2035-01-01 10:00:00',
    TIMESTAMP '2035-01-01 12:00:00'
);
```

### 8.3. Проверка функции создания бронирования

Перед выполнением запроса нужно выбрать существующего активного пользователя и доступную студию:

```sql
SELECT user_id, full_name, status
FROM music_studio.users
WHERE status = 'active'
ORDER BY user_id
LIMIT 10;
```

```sql
SELECT studio_id, studio_name, status
FROM music_studio.studios
WHERE status = 'available'
ORDER BY studio_id
LIMIT 10;
```

Пример создания бронирования:

```sql
SELECT music_studio.create_booking(
    3,
    2,
    TIMESTAMP '2035-01-02 10:00:00',
    TIMESTAMP '2035-01-02 12:00:00',
    'Test booking'
);
```

Функция должна вернуть `booking_id` созданного бронирования.

### 8.4. Проверка запрета пересекающегося бронирования

```sql
SELECT music_studio.create_booking(
    3,
    2,
    TIMESTAMP '2035-01-02 11:00:00',
    TIMESTAMP '2035-01-02 13:00:00',
    'Test booking overlap'
);
```

Ожидаемый результат: ошибка, так как временной интервал пересекается с уже существующим бронированием.

### 8.5. Проверка индексов

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'music_studio'
ORDER BY indexname;
```

### 8.6. Проверка триггера платежа

Сначала нужно найти созданное бронирование:

```sql
SELECT booking_id, total_cost
FROM music_studio.bookings
WHERE purpose = 'Test booking'
ORDER BY booking_id DESC
LIMIT 1;
```

После этого нужно подставить найденные `booking_id` и `total_cost`:

```sql
INSERT INTO music_studio.payments (
    booking_id,
    amount,
    payment_method,
    status
)
VALUES (
    181,
    2000.00,
    'card',
    'paid'
);
```

Значения `181` и `2000.00` нужно заменить на реальные `booking_id` и `total_cost`, которые вернёт предыдущий запрос.

Проверка изменения статуса бронирования:

```sql
SELECT booking_id, status
FROM music_studio.bookings
WHERE booking_id = 181;
```

Ожидаемый результат:

```text
confirmed
```

---

## 9. Запуск тестов

Перед запуском тестов база данных должна быть уже создана, заполнена и содержать объекты расширенной части проекта.

Должны быть выполнены:

```text
base_part/music_studio_create.sql
base_part/music_studio_fill.sql
advanced_part/indexes.sql
advanced_part/views.sql
advanced_part/functions.sql
advanced_part/triggers.sql
```

### 9.1. Установка зависимостей

```bash
pip install pytest psycopg2-binary
```

### 9.2. Настройка подключения

Тесты используют переменные окружения:

```text
PGHOST
PGPORT
PGDATABASE
PGUSER
PGPASSWORD
```

Пример для PowerShell:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="postgres"
$env:PGUSER="postgres"
$env:PGPASSWORD="your_password"
```

Пример для Linux или Git Bash:

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=postgres
export PGUSER=postgres
export PGPASSWORD=your_password
```

В `PGDATABASE` нужно указать имя базы данных, в которой создана схема `music_studio`.

### 9.3. Запуск тестов

Из корня проекта:

```bash
python -m pytest tests -v
```

Тесты выполняются в транзакциях. После каждого теста выполняется `ROLLBACK`, поэтому тестовые данные не сохраняются в базе.

---

## 10. Что проверяют тесты

Тесты проверяют:

- существование индексов;
- соответствие индексов ожидаемым таблицам и столбцам;
- возможность использования индексов в подходящих запросах;
- структуру представлений;
- корректность фильтрации и вычислений в представлениях;
- корректность функций;
- ошибки при некорректных входных данных;
- работу триггеров при прямом `INSERT`;
- запрет пересекающихся бронирований;
- автоматическое изменение статуса бронирования после платежа.

---

## 11. Порядок полной проверки проекта

Рекомендуемый порядок проверки:

1. Выполнить `base_part/music_studio_create.sql`.
2. Выполнить `base_part/music_studio_fill.sql`.
3. Выполнить `base_part/music_studio_selects.sql`.
4. Выполнить `advanced_part/indexes.sql`.
5. Выполнить `advanced_part/views.sql`.
6. Выполнить `advanced_part/functions.sql`.
7. Выполнить `advanced_part/triggers.sql`.
8. Выполнить ручные проверки из раздела 8.
9. Запустить pytest-тесты из раздела 9.
