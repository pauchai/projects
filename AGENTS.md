# AGENTS.md

This file provides coding conventions and workflows for agentic agents operating in this repository.

---

## 1. Build / Lint / Test Commands

### Running the full test suite

```bash
# Python
pytest

# JavaScript / TypeScript
npm test
```

### Running a single test

```bash
# Python - by name
pytest -k test_my_function

# Python - by file
pytest tests/test_example.py

# JS/TS - by file
npx jest tests/example.test.ts

# JS/TS - by name pattern
npx jest --testNamePattern="my function"
```

### Linting and type checking

```bash
# Python
ruff check .
ruff format .

# JS / TypeScript
npm run lint
npm run typecheck
npx eslint "src/**/*.ts"
```

### Building

```bash
# JS / TypeScript
npm run build

# Python (package)
pip install -e .
```

---

## 2. Code Style Guidelines

### Imports

- **Python**: Use `ruff` import sorting (`isort` convention). Group: stdlib → third-party → local. One import per line. No wildcard imports.
- **JS/TS**: Use absolute imports via path aliases (`@/`). Group: node builtins → external → internal. No default re-exports.

### Formatting

- **Python**: 88-char line limit (Black default). Use `ruff format`.
- **JS/TS**: 100-char line limit (Prettier default). Use `prettier --write`.
- Never commit unformatted code. Run the formatter before every commit.

### Types

- **Python**: Use type hints on all public functions and class methods. Avoid `Any`. Use `Protocol` for structural typing. Prefer `TypedDict` over `Dict[str, Any]`.
- **TypeScript**: Strict mode (`"strict": true`). No `any`. Use `unknown` and narrow. Avoid type assertions (`as`) in hot paths.

### Naming Conventions

| Language   | Variables / Functions | Classes / Types | Constants                        | Files           |
|------------|----------------------|-----------------|----------------------------------|-----------------|
| Python     | `snake_case`         | `PascalCase`    | `SCREAMING_SNAKE_CASE`           | `snake_case.py` |
| TypeScript | `camelCase`          | `PascalCase`    | `camelCase` or `PascalCase`      | `kebab-case.ts` |

- **Do not use abbreviations** unless universally understood (e.g., `id`, `url`, `html`).
- Name booleans with `is_`, `has_`, `can_`, or `should_` prefixes.
- Prefer descriptive names over terse ones.

### Error Handling

- **Python**: Raise specific exceptions. Never swallow exceptions silently (at minimum, log). Use custom exception classes for domain errors.
- **JS/TS**: Use `Result` pattern (union types) or try/catch. Never `throw` for expected errors.

### Async / Concurrency

- Prefer async/await over raw callbacks or Promise chains.
- Do not mix sync and async code in the same call chain.

### Performance

- Do not optimize prematurely. Profile first.
- **Python**: Avoid loading large dataframes/datasets at module scope.
- **JS/TS**: Avoid creating new arrays/objects in render paths without memoization.

### Security

- Never hardcode secrets. Use environment variables or a secrets manager.
- Never log sensitive data (passwords, tokens, PII).
- Sanitize user input before using in SQL queries, shell commands, or HTML output.

### Documentation

- **Python**: Write docstrings for all public APIs.
- **JS/TS**: Write JSDoc comments for all public APIs.
- Keep docs in sync with code. Stale docs are worse than no docs.

### Testing

- Name test files `*_test.py` (Python) / `*.test.ts` (TypeScript).
- Name test functions `test_<function>_<scenario>` (Python) / `it("<does something>")` (JS/TS).
- One assertion concept per test (AAA: Arrange, Act, Assert).
- Mock external dependencies. Do not hit real APIs or databases in unit tests.
- Aim for >80% coverage on business logic. Do not chase coverage on boilerplate.

### Git Workflow

- **Commits**: Conventional commit messages: `<type>(<scope>): <description>` (e.g., `feat(auth): add login form`). Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.
- **Branches**: `type/ticket-description` (e.g., `feat/123-add-login`).
- **PRs**: Keep PRs small (<400 lines). One concern per PR.
- **Never commit** generated files, lock files you didn't update, secrets, or temporary files.

---

## 3. SOLID Principles

Каждый принцип описан по единой схеме: суть, правила, чеклист для код-ревью, примеры "до/после" (Python + TypeScript), типичные антипаттерны.

---

### 3.1 S — Single Responsibility Principle (SRP)

**Суть:** Класс (модуль, функция) должен иметь одну и только одну причину для изменения. Если при изменении бизнес-правила вам приходится править тот же файл, что и при изменении формата логирования — SRP нарушен.

**Правила:**

- Один файл = одна доменная ответственность.
- Сервисы не содержат логику представления (форматирование ответов, шаблоны).
- Утилиты не зависят от бизнес-логики.
- Функция делает одно действие. Если нужен комментарий "// а теперь делаем X" — вынесите X в отдельную функцию.
- Максимальный размер класса: ~200 строк. Если больше — ищите скрытые ответственности.

**Чеклист для код-ревью:**

- [ ] Можете ли вы описать назначение класса/модуля одним предложением без союза "и"?
- [ ] Зависит ли этот модуль от менее чем 5 внешних модулей?
- [ ] Изменение одного бизнес-требования затрагивает только один файл?

**Антипаттерны:**

- "God class" — класс `UserManager`, который и валидирует, и сохраняет в БД, и отправляет email, и генерирует отчёты.
- Смешение I/O и бизнес-логики в одном методе (чтение файла + парсинг + вычисления).
- Контроллер, который содержит SQL-запросы.

**Пример — Python:**

```python
# BAD: класс делает всё сразу
class UserService:
    def register(self, data: dict) -> None:
        # валидация
        if not data.get("email"):
            raise ValueError("Email required")
        # сохранение в БД
        db.execute("INSERT INTO users ...", data)
        # отправка письма
        smtp.send(data["email"], "Welcome!")
        # логирование
        logger.info(f"User {data['email']} registered")

# GOOD: каждый класс — одна ответственность
class UserValidator:
    def validate(self, data: dict) -> None:
        if not data.get("email"):
            raise ValueError("Email required")

class UserRepository:
    def save(self, user: User) -> None:
        db.execute("INSERT INTO users ...", user)

class WelcomeMailer:
    def send_welcome(self, email: str) -> None:
        smtp.send(email, "Welcome!")

class UserRegistrationService:
    """Оркестрирует регистрацию, делегируя каждый шаг."""

    def __init__(
        self,
        validator: UserValidator,
        repository: UserRepository,
        mailer: WelcomeMailer,
    ) -> None:
        self._validator = validator
        self._repository = repository
        self._mailer = mailer

    def register(self, data: dict) -> None:
        self._validator.validate(data)
        user = User(**data)
        self._repository.save(user)
        self._mailer.send_welcome(user.email)
```

---

### 3.2 O — Open/Closed Principle (OCP)

**Суть:** Модуль открыт для расширения и закрыт для модификации. Новое поведение добавляется через новый код (новый класс, функция, плагин), а не через правку существующего.

**Правила:**

- Если добавление нового типа/формата требует правки `if/elif/else` или `switch/case` — это нарушение OCP.
- Используйте стратегии, реестры, декораторы, плагины для точек расширения.
- Новый тип экспорта, провайдер оплаты, валидатор = новый класс, реализующий существующий интерфейс.
- Конфигурация поведения через данные (словари, маппинги) предпочтительнее ветвлений.

**Чеклист для код-ревью:**

- [ ] Можно ли добавить новый вариант поведения без изменения существующего кода?
- [ ] Нет ли растущего `if/elif/else` по типу сущности?
- [ ] Используется ли полиморфизм или реестр стратегий вместо ветвлений?

**Антипаттерны:**

- Растущий `switch` по типу при добавлении каждого нового формата: `if format == "csv" ... elif format == "json" ... elif format == "xml" ...`.
- Правка ядра библиотеки ради одного клиента вместо создания расширения.
- Функция с 10+ параметрами-флагами, управляющими поведением.

**Пример — Python:**

```python
from typing import Protocol

# BAD: каждый новый формат — правка существующего метода
class ReportExporter:
    def export(self, data: list, fmt: str) -> str:
        if fmt == "csv":
            return self._to_csv(data)
        elif fmt == "json":
            return self._to_json(data)
        # ... ещё elif при каждом новом формате
        else:
            raise ValueError(f"Unknown format: {fmt}")

# GOOD: новый формат = новый класс, без правки существующих
class Exporter(Protocol):
    def export(self, data: list) -> str: ...

class CsvExporter:
    def export(self, data: list) -> str:
        # CSV-логика
        ...

class JsonExporter:
    def export(self, data: list) -> str:
        # JSON-логика
        ...

# Реестр стратегий — точка расширения
EXPORTERS: dict[str, Exporter] = {
    "csv": CsvExporter(),
    "json": JsonExporter(),
}

def export_report(data: list, fmt: str) -> str:
    exporter = EXPORTERS.get(fmt)
    if exporter is None:
        raise ValueError(f"Unknown format: {fmt}")
    return exporter.export(data)
```

---

### 3.3 L — Liskov Substitution Principle (LSP)

**Суть:** Подтип должен быть заменяемым на базовый тип без нарушения корректности программы. Если код работает с базовым типом, подстановка любого наследника не должна приводить к ошибкам или неожиданному поведению.

**Правила:**

- Наследник не усиливает предусловия (не требует "больше" от входных данных).
- Наследник не ослабляет постусловия (не возвращает "меньше", чем обещал базовый тип).
- Наследник не выбрасывает исключения, которых нет в контракте базового класса.
- Если переопределяете метод — сохраняйте семантику, а не только сигнатуру.
- Предпочитайте композицию наследованию. Наследуйте только если "is-a" отношение действительно имеет смысл.

**Чеклист для код-ревью:**

- [ ] Можно ли подставить любой подкласс вместо базового без `isinstance`-проверок в клиентском коде?
- [ ] Нет ли `NotImplementedError` / `throw new Error("Not supported")` в переопределённых методах?
- [ ] Не сужает ли наследник допустимые входные данные?
- [ ] Не возвращает ли наследник `None` / `null` там, где базовый тип гарантирует значение?

**Антипаттерны:**

- Классическая задача "Квадрат наследует Прямоугольник": `Square.set_width()` неявно меняет и высоту.
- `ReadOnlyRepository extends Repository` с `save()`, который бросает `NotImplementedError`.
- Подкласс, который молча игнорирует вызовы базового метода (пустое тело).

**Пример — Python:**

```python
from typing import Protocol

# BAD: наследник нарушает контракт
class Bird:
    def fly(self) -> str:
        return "flying"

class Penguin(Bird):
    def fly(self) -> str:
        raise NotImplementedError("Penguins can't fly")  # нарушение LSP

# GOOD: разделение интерфейсов по реальным способностям
class Walkable(Protocol):
    def walk(self) -> str: ...

class Flyable(Protocol):
    def fly(self) -> str: ...

class Sparrow:
    def walk(self) -> str:
        return "hopping"

    def fly(self) -> str:
        return "flying"

class Penguin:
    def walk(self) -> str:
        return "waddling"

    def swim(self) -> str:
        return "swimming"

# Функция принимает только то, что умеет летать
def take_off(bird: Flyable) -> str:
    return bird.fly()
```

---

### 3.4 I — Interface Segregation Principle (ISP)

**Суть:** Клиенты не должны зависеть от методов, которые они не используют. Много маленьких, специализированных интерфейсов лучше одного большого "универсального".

**Правила:**

- Один интерфейс (`Protocol` / `interface`) — одна роль (Reader, Writer, Closable).
- Если реализация оставляет методы пустыми или бросает `NotImplementedError` — интерфейс слишком толстый.
- Комбинируйте маленькие интерфейсы через множественное наследование / `extends` / пересечение типов.
- Максимум 3-5 методов на интерфейс. Если больше — ищите возможности для разделения.

**Чеклист для код-ревью:**

- [ ] Все ли методы интерфейса используются каждым клиентом, который от него зависит?
- [ ] Нет ли "пустых" реализаций (`pass`, `{}`, `throw`) в классах?
- [ ] Можно ли разбить интерфейс на 2-3 более мелких без потери смысла?

**Антипаттерны:**

- "Fat interface" с 10+ методами, из которых конкретная реализация использует 2-3.
- `Worker` интерфейс с `work()`, `eat()`, `sleep()` — роботу не нужны `eat()` и `sleep()`.
- Единый `Repository<T>` с `find`, `findAll`, `save`, `delete`, `count`, `aggregate`, `rawQuery` — когда 80% клиентов используют только `find`.

**Пример — Python:**

```python
from typing import Protocol

# BAD: слишком толстый интерфейс
class Storage(Protocol):
    def read(self, key: str) -> bytes: ...
    def write(self, key: str, data: bytes) -> None: ...
    def delete(self, key: str) -> None: ...
    def list_keys(self) -> list[str]: ...
    def get_metadata(self, key: str) -> dict: ...

# Клиенту нужен только read, но он вынужден зависеть от всех 5 методов

# GOOD: маленькие интерфейсы по ролям
class Readable(Protocol):
    def read(self, key: str) -> bytes: ...

class Writable(Protocol):
    def write(self, key: str, data: bytes) -> None: ...

class Deletable(Protocol):
    def delete(self, key: str) -> None: ...

class Listable(Protocol):
    def list_keys(self) -> list[str]: ...

# Композиция — конкретная реализация реализует нужные протоколы
class S3Storage:
    def read(self, key: str) -> bytes: ...
    def write(self, key: str, data: bytes) -> None: ...
    def delete(self, key: str) -> None: ...
    def list_keys(self) -> list[str]: ...

# Клиент зависит только от того, что ему нужно
def load_config(storage: Readable) -> dict:
    raw = storage.read("config.json")
    return json.loads(raw)
```

---

### 3.6 SOLID Code Review Checklist

Быстрый чеклист для проверки PR/MR перед мержем:

| # | Вопрос | Принцип |
|---|--------|---------|
| 1 | Можно ли описать назначение каждого класса/модуля одним предложением без "и"? | SRP |
| 2 | Можно ли добавить новый вариант поведения без правки существующего кода? | OCP |
| 3 | Можно ли подставить любой подтип вместо базового без `isinstance`/`typeof` проверок? | LSP |
| 4 | Все ли методы интерфейса используются каждым клиентом? | ISP |
| 5 | Принимает ли класс зависимости через конструктор, а не создаёт внутри? | DIP |
| 6 | Можно ли написать юнит-тест без реальной БД/сети/файловой системы? | DIP |
| 7 | Нет ли "пустых" реализаций (`pass`, `throw`, `{}`) в методах интерфейса? | LSP+ISP |

---

### 3.7 When NOT to Apply SOLID

SOLID — это инструмент, а не догма. Чрезмерное следование принципам ведёт к over-engineering.

**Не применяйте SOLID слепо, если:**

- **Простой скрипт или утилита** (<100 строк) — одноразовый скрипт миграции не нуждается в абстракциях.
- **Прототип / MVP** — сначала проверьте гипотезу, рефакторьте потом. Абстракции на этапе прототипа замедляют итерации.
- **Нет реального полиморфизма** — не создавайте интерфейс с единственной реализацией "на будущее" (YAGNI). Извлекайте абстракцию, когда появляется вторая реализация.
- **Простые DTO / data classes** — `dataclass` / `type` для чистых данных не нуждаются в ISP или DIP.
- **Глубина абстракций > 3** — если для понимания логики нужно пройти через 5 уровней интерфейсов, вы перестарались. Прагматичность важнее чистоты.

**Правило здравого смысла:** Если абстракция не упрощает понимание кода, не упрощает тестирование и не предоставляет реальную точку расширения — она не нужна.

---

## 4. Domain-Driven Design (DDD) — Strategic Patterns

Стратегический DDD определяет **границы** между частями системы и правила их взаимодействия. Эта секция покрывает: Ubiquitous Language, Bounded Contexts, Context Mapping, Subdomains, а также архитектурные стили (Layered, Hexagonal), которые позволяют реализовать эти концепции в коде.

> **Связь с SOLID:** DDD на стратегическом уровне — это SOLID, применённый к архитектуре в целом. Bounded Context — SRP на уровне модуля. Anti-Corruption Layer — DIP + OCP на уровне интеграции. Порты в Hexagonal Architecture — ISP для границ системы.

---

### 4.1 Ubiquitous Language (Единый язык)

**Суть:** Код, документация и коммуникация между разработчиками и бизнесом используют одни и те же доменные термины. Нет "перевода" между тем, что говорит бизнес, и тем, что написано в коде.

**Правила:**

- Имена классов, методов, переменных берутся из доменного словаря, согласованного с бизнесом.
- Если бизнес говорит "оформить заказ" — метод называется `place_order` / `placeOrder`, а не `process_data` или `handleSubmit`.
- Запрещены технические имена для доменных концепций: `DataProcessor` вместо `InvoiceGenerator`, `Manager` вместо `PolicyEnforcer`.
- Ведите глоссарий домена (в README, Wiki или в коде как комментарий к модулю). Обновляйте его при изменении терминологии.
- Если один и тот же термин значит разное в разных частях системы — это сигнал к выделению Bounded Context (см. 4.2).

**Чеклист для код-ревью:**

- [ ] Совпадают ли имена классов/функций с терминами, которые использует бизнес?
- [ ] Нет ли "технического жаргона" там, где должен быть доменный термин?
- [ ] Есть ли актуальный глоссарий, и соответствуют ли ему имена в коде?

**Связь с SOLID:** Если вы не можете описать назначение класса одним доменным термином без союза "и" — вероятно, нарушен **SRP** (см. 3.1).

**Антипаттерны:**

- Класс `UserManager` — "manager" не является доменным понятием. Что он делает? Регистрирует? Авторизует? Выставляет счета?
- Переменная `data` / `item` / `obj` вместо `invoice`, `shipment`, `policy`.
- Разные термины для одного понятия в разных местах кода: `client` в одном модуле, `customer` в другом, `user` в третьем — при том что это одна и та же сущность.

**Пример — Python:**

```python
# BAD: технические имена, не связанные с доменом
class DataProcessor:
    def process(self, data: dict) -> dict:
        result = self._transform(data)
        self._save(result)
        return result

# GOOD: имена из домена страхования
class ClaimAssessor:
    """Оценивает страховые заявки и выносит решение."""

    def assess_claim(self, claim: InsuranceClaim) -> ClaimVerdict:
        risk = self._evaluate_risk(claim)
        return self._render_verdict(claim, risk)
```

---

### 4.2 Bounded Contexts (Ограниченные контексты)

**Суть:** Разные части системы используют **разные модели** одной и той же сущности. `User` в контексте авторизации (логин, пароль, роли) != `User` в контексте биллинга (баланс, подписка, платёжные методы). Каждый контекст имеет свою модель, свой словарь и свои границы.

**Правила:**

- Один Bounded Context = один модуль/пакет/сервис. Не расшаривайте доменные модели между контекстами.
- Каждый контекст имеет свой собственный набор сущностей, даже если они "похожи" на сущности из другого контекста.
- Взаимодействие между контекстами — через явные контракты: API, события, shared DTOs (но не доменные модели).
- Если одна команда владеет несколькими контекстами — они могут жить в одном репозитории, но в разных пакетах с чёткими границами импортов.
- Если разные команды — отдельные сервисы / репозитории.

**Чеклист для код-ревью:**

- [ ] Не импортирует ли этот модуль доменные классы из другого контекста?
- [ ] Не переиспользуется ли одна и та же модель (например, `User`) в контекстах с разной семантикой?
- [ ] Определены ли явные контракты (DTO, события) для межконтекстного взаимодействия?

**Связь с SOLID:** Bounded Context — это **SRP на уровне модулей** (см. 3.1): каждый контекст имеет одну причину для изменения. Зависимости между контекстами следуют **DIP** (см. 3.5): через абстракции, а не конкретные реализации.

**Антипаттерны:**

- Единая модель `User` с 30 полями, используемая и в авторизации, и в биллинге, и в аналитике.
- Прямой импорт `from billing.models import Invoice` внутри модуля `shipping` — жёсткое сцепление контекстов.
- Общая база данных без разделения схем — контексты спутаны на уровне данных.

**Пример — структура проекта Python:**

```
project/
├── auth/                    # Bounded Context: Identity & Access
│   ├── domain/
│   │   ├── user.py          # AuthUser (login, password_hash, roles)
│   │   └── session.py
│   ├── application/
│   │   └── auth_service.py
│   └── infrastructure/
│       └── token_store.py
├── billing/                 # Bounded Context: Billing
│   ├── domain/
│   │   ├── customer.py      # BillingCustomer (balance, subscription, payment_methods)
│   │   └── invoice.py
│   ├── application/
│   │   └── billing_service.py
│   └── infrastructure/
│       └── payment_gateway.py
├── shipping/                # Bounded Context: Shipping
│   ├── domain/
│   │   ├── recipient.py     # Recipient (address, contact_name)
│   │   └── shipment.py
│   ├── application/
│   │   └── shipping_service.py
│   └── infrastructure/
│       └── carrier_client.py
└── shared_kernel/           # Shared Kernel: общие Value Objects
    ├── money.py
    ├── email_address.py
    └── events.py            # Базовые типы доменных событий
```

---

### 4.3 Context Mapping (Карта контекстов)

**Суть:** Паттерны взаимодействия между Bounded Contexts. Определяют, как один контекст зависит от другого и как защитить свою модель от чужих изменений.

**Основные паттерны:**

| Паттерн | Описание | Когда применять |
|---------|----------|----------------|
| **Shared Kernel** | Два контекста разделяют общий набор типов (Value Objects, события). Изменения координируются. | Контексты тесно связаны и принадлежат одной команде |
| **Customer-Supplier** | Один контекст (supplier) предоставляет данные, другой (customer) потребляет. Supplier учитывает нужды customer. | Upstream-сервис готов адаптировать API под downstream |
| **Anti-Corruption Layer (ACL)** | Слой-адаптер, который транслирует внешнюю модель во внутреннюю. Защищает домен от "загрязнения" чужими структурами. | Интеграция с legacy-системами, внешними API, сторонними сервисами |
| **Open Host Service** | Контекст публикует хорошо документированный API/протокол для всех потребителей. | Много потребителей, контекст готов поддерживать публичный контракт |
| **Published Language** | Общий формат обмена данными (JSON Schema, Protobuf, Avro). | Асинхронная интеграция через события, множество потребителей |
| **Conformist** | Consumer принимает модель supplier-а как есть, без трансляции. | Нет ресурсов на ACL, supplier не готов меняться, модель приемлема |
| **Separate Ways** | Контексты не интегрируются вовсе, каждый решает задачу независимо. | Стоимость интеграции выше стоимости дублирования |

**Правила:**

- **По умолчанию используйте ACL** при интеграции с внешними системами. Conformist — только как осознанный компромисс.
- ACL живёт в **инфраструктурном слое** потребляющего контекста, а не в доменном.
- Маппинг внешних DTO во внутренние доменные объекты — ответственность ACL. Домен никогда не знает о внешних структурах.
- Shared Kernel должен быть **минимальным**: только Value Objects и базовые типы событий. Чем больше Shared Kernel, тем сильнее связанность.

**Чеклист для код-ревью:**

- [ ] Не "протекает" ли внешняя модель (DTO стороннего API) в доменный слой?
- [ ] Есть ли ACL/адаптер между вашим контекстом и внешним сервисом?
- [ ] Определён ли тип взаимодействия между контекстами (Shared Kernel / Customer-Supplier / ACL)?

**Связь с SOLID:** ACL — это **OCP** (см. 3.2): замена внешнего поставщика не требует правки домена. Адаптер реализует интерфейс из домена — это **DIP** (см. 3.5) в чистом виде.

**Антипаттерны:**

- Прямое использование DTO от стороннего API внутри бизнес-логики: `order.stripe_payment_intent_id`.
- Отсутствие ACL при интеграции с legacy: доменный код завален `if legacy_format ...` ветвлениями.
- Shared Kernel, разросшийся до полноценной библиотеки с бизнес-логикой — превращается в "скрытый монолит".

**Пример ACL — Python:**

```python
from typing import Protocol
from dataclasses import dataclass

# --- Домен shipping-контекста (не знает о внешнем API) ---

@dataclass(frozen=True)
class GeoCoordinate:
    latitude: float
    longitude: float

@dataclass(frozen=True)
class ShipmentLocation:
    coordinate: GeoCoordinate
    status: str
    last_updated_at: str

class CarrierGateway(Protocol):
    """Порт: домен определяет контракт, инфраструктура реализует."""

    def locate(self, tracking_id: str) -> ShipmentLocation: ...

# --- Инфраструктура: ACL для конкретного перевозчика ---

class DhlApiClient:
    """Низкоуровневый HTTP-клиент для DHL API."""

    def get_tracking(self, waybill: str) -> dict:
        # Возвращает сырой JSON от DHL
        ...

class DhlCarrierAdapter:
    """ACL: транслирует модель DHL во внутреннюю модель домена."""

    def __init__(self, client: DhlApiClient) -> None:
        self._client = client

    def locate(self, tracking_id: str) -> ShipmentLocation:
        raw = self._client.get_tracking(tracking_id)
        # Трансляция внешней модели -> внутренняя
        return ShipmentLocation(
            coordinate=GeoCoordinate(
                latitude=raw["origin"]["geo"]["lat"],
                longitude=raw["origin"]["geo"]["lng"],
            ),
            status=self._map_status(raw["events"][-1]["typeCode"]),
            last_updated_at=raw["events"][-1]["date"],
        )

    def _map_status(self, dhl_code: str) -> str:
        status_map = {"PU": "picked_up", "IT": "in_transit", "DL": "delivered"}
        return status_map.get(dhl_code, "unknown")
```

---

### 4.4 Subdomains (Поддомены)

**Суть:** Не весь код одинаково важен. DDD делит систему на поддомены по бизнес-ценности, чтобы направить усилия туда, где они дают максимальную отдачу.

**Три типа поддоменов:**

| Тип | Описание | Пример |
|-----|----------|--------|
| **Core Domain** | Главная ценность бизнеса. Конкурентное преимущество. Здесь уникальная бизнес-логика, которую нельзя купить. | Алгоритм ценообразования, система рекомендаций, ядро трейдинговой платформы |
| **Supporting Subdomain** | Необходим для работы Core Domain, но не является конкурентным преимуществом. | Управление каталогом товаров, CRM, система уведомлений |
| **Generic Subdomain** | Типовая задача, не специфичная для бизнеса. Можно купить, использовать SaaS или open-source. | Аутентификация, отправка email, генерация PDF, платёжный шлюз |

**Матрица инвестиций:**

| Аспект | Core Domain | Supporting | Generic |
|--------|-------------|------------|---------|
| Качество кода | Максимальное. SOLID, DDD, полное покрытие тестами | Хорошее. Стандартные практики, разумное покрытие | Минимально достаточное. Используйте готовые решения |
| Кто пишет | Лучшие инженеры команды | Любой инженер | Сторонняя библиотека / SaaS / джуниор |
| Рефакторинг | Постоянный, инвестиции оправданы | По необходимости | Только при смене поставщика |
| Архитектура | Hexagonal / Clean, строгие границы | Layered, достаточные границы | Простейшая. Прямые зависимости допустимы |
| Тестирование | >90% покрытие бизнес-логики | >70% покрытие | Интеграционные тесты на границе |

**Правила:**

- Определите Core Domain **до начала проектирования**. Это решение принимается совместно с бизнесом.
- Не тратьте ресурсы на вылизывание Generic Subdomain. Используйте `Auth0`, `Stripe`, `SendGrid` вместо написания с нуля.
- Supporting Subdomain может начинаться простым CRUD и усложняться по мере роста требований.
- Если не можете определить, Core это или Supporting — скорее всего, Supporting.

**Чеклист для код-ревью:**

- [ ] Определён ли тип поддомена для этого модуля?
- [ ] Соответствует ли уровень сложности кода типу поддомена (не over-engineering для Generic, не упрощение для Core)?
- [ ] Используются ли готовые решения для Generic Subdomain вместо самописных?

---

### 4.5 Layered Architecture (Слоёная архитектура)

**Суть:** Код организован в слои с чётким правилом зависимостей: **зависимости направлены внутрь**, от инфраструктуры к домену. Домен не знает о базе данных, HTTP, фреймворках.

**Четыре слоя:**

```
┌──────────────────────────────────────────┐
│           Presentation Layer             │  Controllers, CLI, GraphQL resolvers
│       (зависит от Application)           │
├──────────────────────────────────────────┤
│           Application Layer              │  Use Cases, Application Services
│        (зависит от Domain)               │  Оркестрирует доменные объекты
├──────────────────────────────────────────┤
│            Domain Layer                  │  Entities, Value Objects, Domain Services
│        (не зависит ни от чего)           │  Repository interfaces (Protocols)
├──────────────────────────────────────────┤
│         Infrastructure Layer             │  ORM, HTTP-клиенты, очереди, файлы
│ (зависит от Domain — реализует порты)    │  Реализации Repository, Gateway
└──────────────────────────────────────────┘
```

**Правило зависимостей (Dependency Rule):**

- **Domain** — не импортирует ничего из других слоёв. Определяет интерфейсы (`Protocol` / `interface`), которые реализуются в Infrastructure.
- **Application** — импортирует только из Domain. Содержит Use Case / Application Service, который оркестрирует доменные объекты и вызывает порты.
- **Infrastructure** — импортирует из Domain (реализует его интерфейсы). Не содержит бизнес-логики.
- **Presentation** — импортирует из Application. Преобразует HTTP-запросы в вызовы Application Service и обратно.

**Правила:**

- Бизнес-правила живут **только** в Domain Layer. Ни в контроллере, ни в репозитории.
- Application Service не содержит `if/else` по бизнес-правилам — он делегирует домену.
- Infrastructure реализует интерфейсы из Domain — это **DIP** (см. 3.5) на уровне архитектуры.
- Каждый слой может зависеть только от слоя "ниже" (ближе к домену). Никогда не наоборот.

**Чеклист для код-ревью:**

- [ ] Не импортирует ли Domain Layer что-либо из Infrastructure / Application / Presentation?
- [ ] Не содержит ли Application Service бизнес-логику (условия, вычисления), которая должна быть в Domain?
- [ ] Не содержит ли контроллер прямых вызовов к базе данных, минуя Application Layer?
- [ ] Реализует ли Infrastructure интерфейсы, определённые в Domain, а не наоборот?

**Связь с SOLID:** Вся архитектура — прямое применение **DIP** (см. 3.5): домен определяет интерфейсы, инфраструктура реализует. Интерфейсы репозиториев сегрегированы по ролям — **ISP** (см. 3.4).

**Антипаттерны:**

- Контроллер, который содержит SQL-запросы или вызывает ORM напрямую.
- Domain Layer, который импортирует `sqlalchemy`, `prisma`, `axios`.
- Application Service с 500 строками бизнес-логики вместо делегирования доменным объектам.
- "Анемичная модель": Domain Layer содержит только data classes без поведения, вся логика — в Application Service.

**Пример — Python:**

```python
# domain/order.py — Domain Layer (нет внешних зависимостей)
from dataclasses import dataclass
from typing import Protocol

@dataclass
class Order:
    order_id: str
    customer_id: str
    total: float
    is_confirmed: bool = False

    def confirm(self) -> None:
        if self.total <= 0:
            raise ValueError("Cannot confirm order with zero total")
        self.is_confirmed = True

class OrderRepository(Protocol):
    """Порт: определён доменом, реализуется инфраструктурой."""

    def find_by_id(self, order_id: str) -> Order | None: ...
    def save(self, order: Order) -> None: ...

# application/confirm_order.py — Application Layer
class ConfirmOrderUseCase:
    """Оркестрирует домен. Не содержит бизнес-логику."""

    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def execute(self, order_id: str) -> None:
        order = self._repository.find_by_id(order_id)
        if order is None:
            raise LookupError(f"Order {order_id} not found")
        order.confirm()  # бизнес-логика — в домене
        self._repository.save(order)

# infrastructure/postgres_order_repo.py — Infrastructure Layer
class PostgresOrderRepository:
    """Реализует порт из домена. Зависит от Domain, а не наоборот."""

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def find_by_id(self, order_id: str) -> Order | None:
        row = self._conn.execute("SELECT ... WHERE id = %s", (order_id,))
        return Order(**row) if row else None

    def save(self, order: Order) -> None:
        self._conn.execute("INSERT ... ON CONFLICT UPDATE ...", order)

# presentation/api.py — Presentation Layer
def confirm_order_endpoint(request: Request) -> Response:
    use_case = get_confirm_order_use_case()  # из DI-контейнера
    use_case.execute(request.path_params["order_id"])
    return Response(status=200)
```

---

### 4.6 Hexagonal Architecture (Ports & Adapters)

**Суть:** Альтернативная визуализация Layered Architecture. Приложение — это ядро (домен + application), окружённое **портами** (интерфейсы) и **адаптерами** (реализации). Порты определяют, как внешний мир общается с приложением и как приложение общается с внешним миром.

```
                  ┌─ Driving Adapter ─┐
                  │   HTTP Controller  │
                  │   CLI Command      │
                  │   GraphQL Resolver │
                  └────────┬───────────┘
                           │ calls
                  ┌────────▼───────────┐
                  │   Driving Port     │  (Application Service interface)
                  │                    │
                  │   ┌────────────┐   │
                  │   │   Domain   │   │
                  │   │   Core     │   │
                  │   └────────────┘   │
                  │                    │
                  │   Driven Port      │  (Repository / Gateway Protocol)
                  └────────┬───────────┘
                           │ implemented by
                  ┌────────▼───────────┐
                  │  Driven Adapter    │
                  │   PostgreSQL Repo  │
                  │   Redis Cache      │
                  │   SMTP Mailer      │
                  │   S3 Storage       │
                  └────────────────────┘
```

**Два типа портов:**

| Тип | Направление | Определяет | Пример |
|-----|-------------|-----------|--------|
| **Driving Port** (входной) | Внешний мир → Приложение | Что приложение умеет делать | `ConfirmOrderUseCase`, `RegisterUserService` |
| **Driven Port** (выходной) | Приложение → Внешний мир | Что приложение ожидает от инфраструктуры | `OrderRepository`, `PaymentGateway`, `EmailSender` |

**Правила:**

- Driving Adapter (контроллер) вызывает Driving Port (Application Service). Адаптер знает о порте, порт не знает об адаптере.
- Driven Port (интерфейс репозитория) определяется в домене. Driven Adapter (Postgres-реализация) реализует этот порт.
- Домен **никогда** не зависит от адаптеров. Адаптеры зависят от портов.
- Адаптеры взаимозаменяемы: `PostgresOrderRepo` можно заменить на `InMemoryOrderRepo` в тестах без изменения домена.

**Чеклист для код-ревью:**

- [ ] Определены ли Driven Ports как `Protocol` (Python) / `interface` (TS) в доменном слое?
- [ ] Можно ли заменить любой Driven Adapter на мок в тестах без изменения бизнес-логики?
- [ ] Не зависит ли домен от конкретных адаптеров (ORM, HTTP-клиент)?
- [ ] Находятся ли адаптеры в Infrastructure Layer, а не рядом с доменом?

**Связь с SOLID:** Hexagonal Architecture — это **DIP** (см. 3.5) в чистейшей форме. Driven Ports — это сегрегированные интерфейсы (**ISP**, см. 3.4). Замена адаптеров без правки ядра — **OCP** (см. 3.2).

**Антипаттерны:**

- "Порт" с 15 методами, из которых каждый Use Case использует 2 — нарушение ISP.
- Driven Adapter, который содержит бизнес-логику (валидацию, расчёты) вместо чистого I/O.
- Отсутствие Driving Port: контроллер напрямую вызывает доменные объекты, минуя Application Service.

**Пример — Python:**

```python
from typing import Protocol

# --- Driven Port (определён в домене) ---
class NotificationSender(Protocol):
    """Порт: домен определяет, ЧТО нужно. Адаптер определяет, КАК."""

    def send(self, recipient: str, subject: str, body: str) -> None: ...

# --- Driving Port (Application Service) ---
class OrderNotificationService:
    """Входной порт: внешний мир вызывает этот сервис."""

    def __init__(self, sender: NotificationSender) -> None:
        self._sender = sender

    def notify_order_shipped(self, order: Order) -> None:
        self._sender.send(
            recipient=order.customer_email,
            subject=f"Order {order.order_id} shipped",
            body=f"Your order is on the way!",
        )

# --- Driven Adapter: email ---
class SmtpNotificationAdapter:
    def __init__(self, smtp_host: str, smtp_port: int) -> None:
        self._host = smtp_host
        self._port = smtp_port

    def send(self, recipient: str, subject: str, body: str) -> None:
        # SMTP-отправка
        ...

# --- Driven Adapter: Slack (альтернатива, без правки домена) ---
class SlackNotificationAdapter:
    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    def send(self, recipient: str, subject: str, body: str) -> None:
        # POST на Slack webhook
        ...

# --- Driving Adapter: HTTP-контроллер ---
def ship_order_endpoint(request: Request) -> Response:
    service = get_order_notification_service()  # DI
    service.notify_order_shipped(order)
    return Response(status=200)
```

---

### 4.7 Unit of Work (Единица работы)

**Суть:** Unit of Work (UoW) — тактический паттерн DDD, который отслеживает все изменения в агрегатах в рамках одной бизнес-операции и фиксирует их атомарно. UoW гарантирует: либо все изменения сохранены, либо ни одно. После успешного commit UoW отвечает за публикацию накопленных доменных событий.

**Правила:**

- UoW определяется как **Driven Port** (`Protocol`) в доменном слое. Реализация (SQLAlchemy, Django ORM) живёт в Infrastructure. Это прямое следствие **DIP** (см. 3.5).
- Одна бизнес-операция = один UoW. Не переиспользуйте UoW между разными Use Case.
- UoW **оркестрирует репозитории**, предоставляя их как свои атрибуты. Репозиторий не создаёт UoW; UoW создаёт/предоставляет репозитории.
- **Application Service** управляет жизненным циклом UoW (открытие, commit, rollback). Домен не знает о UoW. Контроллер не управляет UoW.
- Доменные события публикуются **после** успешного `commit()`, а не во время работы с агрегатами. Это предотвращает публикацию событий для откачённых транзакций.
- В Python используйте **context manager** (`__enter__` / `__exit__`) как идиоматичный способ управления жизненным циклом UoW.
- UoW не содержит бизнес-логику — только координацию транзакции (**SRP**, см. 3.1).

**Связь с SOLID:**

| Принцип | Проявление в UoW |
|---------|------------------|
| **SRP** | UoW отвечает только за атомарность транзакции, не за бизнес-логику |
| **OCP** | Замена реализации (Postgres → SQLite, InMemory для тестов) без правки домена и Application Service |
| **DIP** | Домен определяет `Protocol`, инфраструктура реализует |
| **ISP** | UoW предоставляет только те репозитории, которые нужны конкретному Use Case |

**Антипаттерны:**

- **UoW внутри репозитория.** Репозиторий вызывает `session.commit()` самостоятельно — невозможно объединить несколько операций в одну транзакцию.
- **UoW в контроллере.** Контроллер напрямую вызывает `uow.commit()` — размывание границ слоёв, бизнес-операция "протекает" в Presentation Layer.
- **Долгоживущий UoW.** UoW, открытый на всё время обработки HTTP-запроса, включая сериализацию ответа — блокирует соединение с БД, создаёт риск грязных чтений.
- **Публикация событий до commit.** Подписчики реагируют на событие, но транзакция откатывается — система в неконсистентном состоянии.

**Пример — Python:**

```python
from typing import Protocol
from contextlib import contextmanager

# --- Domain Layer: Port ---

class OrderRepository(Protocol):
    def find_by_id(self, order_id: str) -> Order | None: ...
    def save(self, order: Order) -> None: ...

class UnitOfWork(Protocol):
    """Driven Port: домен определяет контракт, инфраструктура реализует."""

    orders: OrderRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

# --- Infrastructure Layer: Adapter ---

class SqlAlchemyUnitOfWork:
    """Driven Adapter: реализация UoW поверх SQLAlchemy."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.orders = SqlAlchemyOrderRepository(self._session)
        return self

    def __exit__(self, *args: object) -> None:
        self.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

# --- Application Layer: Use Case ---

class ConfirmOrderUseCase:
    """Application Service управляет жизненным циклом UoW."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, order_id: str) -> None:
        with self._uow as uow:
            order = uow.orders.find_by_id(order_id)
            if order is None:
                raise LookupError(f"Order {order_id} not found")
            order.confirm()          # бизнес-логика — в домене
            uow.commit()             # атомарная фиксация

# --- Tests: Fake UoW (без БД) ---

class FakeUnitOfWork:
    """Fake для тестов. Реализует тот же Protocol, работает in-memory."""

    def __init__(self) -> None:
        self.orders = FakeOrderRepository()
        self.committed = False

    def __enter__(self) -> "FakeUnitOfWork":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass
```

---

### 4.8 DDD Code Review Checklist

Быстрый чеклист для проверки PR/MR с точки зрения DDD:

| # | Вопрос | Концепция |
|---|--------|-----------|
| 1 | Совпадают ли имена в коде с терминами, которые использует бизнес? | Ubiquitous Language |
| 2 | Не переиспользуется ли доменная модель одного контекста в другом? | Bounded Context |
| 3 | Есть ли ACL/адаптер при интеграции с внешней системой? | Context Mapping |
| 4 | Определён ли тип поддомена и соответствует ли ему уровень сложности кода? | Subdomains |
| 5 | Не импортирует ли Domain Layer что-либо из Infrastructure? | Layered Architecture |
| 6 | Содержит ли Domain Layer бизнес-логику, а не только данные (не анемичная модель)? | Layered Architecture |
| 7 | Определены ли Driven Ports в домене как `Protocol`/`interface`? | Hexagonal Architecture |
| 8 | Можно ли заменить адаптер (БД, SMTP) на мок без изменения домена? | Hexagonal Architecture |
| 9 | Управляет ли Application Service жизненным циклом UoW, а не контроллер или репозиторий? | Unit of Work |
| 10 | Публикуются ли доменные события только после успешного `commit()`? | Unit of Work |

---

### 4.9 When NOT to Apply DDD

DDD — мощный инструмент, но не универсальный. Чрезмерное применение ведёт к accidental complexity.

**Не применяйте стратегический DDD, если:**

- **Простое CRUD-приложение** — если бизнес-логика сводится к валидации полей и сохранению в БД, DDD создаст лишние абстракции без отдачи.
- **API-обёртка / BFF** — прокси-сервис, который агрегирует данные из других API, не имеет собственного домена.
- **Команда из 1-2 человек на раннем этапе** — накладные расходы на моделирование Bounded Contexts не окупаются, когда весь контекст помещается в голове одного человека.
- **Generic Subdomain** — аутентификация, отправка email, генерация PDF. Используйте готовые решения, не моделируйте домен.
- **Прототип / spike** — сначала проверьте гипотезу, моделируйте потом.

**Признаки того, что DDD оправдан:**

- Бизнес-логика сложная и часто меняется.
- Несколько команд работают над одной системой.
- Ошибки в моделировании стоят дорого (финансы, медицина, логистика).
- "Один и тот же" термин означает разное в разных частях системы.
- Стоимость неправильной модели > стоимости моделирования.

**Правило здравого смысла:** Начинайте с простого. Выделяйте Bounded Context, когда видите, что одна модель не справляется. Вводите ACL, когда внешняя модель начинает "протекать" в ваш код. DDD — это эволюционный подход, а не Big Design Up Front.

---

## 5. Test-Driven Development (TDD)

**TDD is the default development workflow in this repository.** Production code MUST NOT be written without a failing test that justifies it. This section defines the TDD cycle, rules, test classification, test doubles strategy, and review expectations.

> **Connection to SOLID & DDD:** TDD is the enforcement mechanism for SOLID and DDD. If a class is hard to test in isolation, it violates **DIP** (section 3.5). If a test needs 10 mocks, the class violates **SRP** (section 3.1). If the domain layer requires a database to be tested, the **Layered Architecture** (section 4.5) is broken. TDD makes design problems visible immediately.

---

### 5.1 The Three Laws of TDD

These three laws, formulated by Robert C. Martin, define the atomic constraints of the TDD workflow:

1. **You may not write production code unless you have first written a failing unit test.**
   A failing test is the only justification for writing new production code. No test = no code.

2. **You may not write more of a unit test than is sufficient to fail.**
   Stop writing the test as soon as it fails (compilation failure counts). Don't write the entire test up front — write just enough to get a single, clear failure.

3. **You may not write more production code than is sufficient to make the failing test pass.**
   Write the simplest code that turns the test green. Resist the urge to generalize, optimize, or add "obvious" features. That comes in the Refactor step.

**Why these constraints matter:**

- They prevent "test-after" development disguised as TDD.
- They keep the feedback loop under 60 seconds (write test → run → write code → run → green).
- They produce a fine-grained commit history where every production line is traceable to a test.
- They force incremental design — the code evolves in small, safe steps.

---

### 5.2 Red-Green-Refactor Cycle

The TDD workflow follows a strict three-phase cycle. Each iteration should take 1-10 minutes.

```
   ┌──────────────┐
   │   🔴 RED      │  Write a failing test
   │   (< 2 min)  │  that describes the desired behavior
   └──────┬───────┘
          │
   ┌──────▼───────┐
   │   🟢 GREEN    │  Write the MINIMUM code
   │   (< 5 min)  │  to make the test pass
   └──────┬───────┘
          │
   ┌──────▼───────┐
   │   🔵 REFACTOR │  Improve code quality
   │   (< 5 min)  │  without changing behavior (all tests stay green)
   └──────┬───────┘
          │
          └──────→ repeat
```

#### Phase 1: RED — Write a Failing Test

- Write a single test that describes one new behavior or requirement.
- The test MUST fail for the right reason (missing method, wrong return value — not a syntax error or import failure).
- Name the test using the pattern: `test_<function>_<scenario>_<expected>` (Python) / `it("should <behavior> when <condition>")` (JS/TS).
- Use the AAA pattern: Arrange → Act → Assert. One assertion concept per test.

#### Phase 2: GREEN — Make It Pass

- Write the simplest, most naive code that makes the test pass.
- It's acceptable to hardcode return values, use `if` chains, or duplicate code at this stage.
- Do NOT refactor during GREEN. Do NOT add "extra" functionality the test doesn't require.
- If making the test pass takes more than 5 minutes, the step you took was too large. Revert and write a simpler test.

#### Phase 3: REFACTOR — Improve the Design

- All tests are green. Now improve the code: extract methods, remove duplication, rename for clarity, apply SOLID principles.
- Run tests after each refactoring step. If a test breaks, revert the last change.
- Refactoring targets: production code AND test code. Tests deserve the same quality as production code.
- Common refactors: Extract Method, Extract Class, Inline Variable, Replace Conditional with Polymorphism, Introduce Parameter Object.

**Rules:**

- Never skip the RED phase. If you can't write a failing test, you don't understand the requirement.
- Never skip the REFACTOR phase. Green code without refactoring accumulates technical debt.
- Commit after each completed cycle (or after a meaningful group of cycles).
- If a test is hard to write, the design is wrong — change the design, not the testing approach.

---

### 5.3 Test Types and the Test Pyramid

Not all tests are equal. The Test Pyramid defines the optimal distribution:

```
         ╱  E2E Tests  ╲           Few, slow, expensive
        ╱───────────────╲          (< 5% of suite)
       ╱Integration Tests╲        Moderate count, moderate speed
      ╱───────────────────╲       (15-25% of suite)
     ╱    Unit Tests        ╲      Many, fast, cheap
    ╱─────────────────────────╲   (70-80% of suite)
```

#### Unit Tests

**Scope:** A single function, method, or class in isolation. All external dependencies are replaced with [Test Doubles](#54-test-doubles-mock--stub--spy--fake).

**Properties:**

- Execute in < 50ms each.
- No I/O: no filesystem, no network, no database.
- Deterministic: same input → same output, every time, on every machine.
- Can run in any order, in parallel.

**TDD applies primarily here.** The Red-Green-Refactor cycle is driven by unit tests.

**File naming:** `*_test.py` (Python) / `*.test.ts` (TypeScript).

**Example — Python:**

```python
# tests/domain/test_order.py
import pytest
from domain.order import Order

class TestOrderConfirm:
    def test_confirm_sets_confirmed_flag(self) -> None:
        # Arrange
        order = Order(order_id="1", customer_id="c1", total=100.0)

        # Act
        order.confirm()

        # Assert
        assert order.is_confirmed is True

    def test_confirm_raises_when_total_is_zero(self) -> None:
        # Arrange
        order = Order(order_id="1", customer_id="c1", total=0.0)

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot confirm order with zero total"):
            order.confirm()
```

#### Integration Tests

**Scope:** The interaction between two or more components, including real infrastructure (database, HTTP API, message queue, filesystem).

**Properties:**

- Slower than unit tests (100ms — 5s each).
- May require external services (test database, Docker containers, test servers).
- Verify that components wire together correctly: serialization, SQL queries, HTTP contracts.
- Use real implementations for the component under test, mocks/stubs for everything else.

**When to write integration tests:**

- Repository implementations (verify SQL queries work with a real database).
- HTTP client adapters (verify serialization/deserialization against a real or recorded API).
- Message queue producers/consumers (verify message format and routing).
- Anti-Corruption Layer adapters (verify external model translation).

**File naming:** `*_integration_test.py` (Python) / `*.integration.test.ts` (TypeScript).

**Example — Python:**

```python
# tests/infrastructure/test_postgres_order_repo_integration.py
import pytest
from infrastructure.postgres_order_repo import PostgresOrderRepository
from domain.order import Order

@pytest.fixture
def repo(test_db_connection):
    return PostgresOrderRepository(test_db_connection)

class TestPostgresOrderRepository:
    def test_save_and_find_round_trip(self, repo) -> None:
        # Arrange
        order = Order(order_id="42", customer_id="c1", total=250.0)

        # Act
        repo.save(order)
        found = repo.find_by_id("42")

        # Assert
        assert found is not None
        assert found.order_id == "42"
        assert found.total == 250.0
```

#### End-to-End (E2E) Tests

**Scope:** The entire application stack from user input to database and back. Tests exercise real HTTP endpoints, real database, real external services (or sandboxes).

**Properties:**

- Slowest (seconds to minutes per test).
- Most brittle — sensitive to timing, network, external service availability.
- Most expensive to maintain.
- Cover critical user journeys only: registration → login → core action → result verification.

**Rules:**

- Keep E2E tests to a minimum (< 5% of the total test count).
- E2E tests are NOT part of the TDD cycle — they are written after the feature is implemented to verify the full integration.
- E2E tests should not duplicate logic already covered by unit and integration tests.
- Run E2E tests in CI, not on every local save.

**File naming:** `*_e2e_test.py` (Python) / `*.e2e.test.ts` (TypeScript).

---

### 5.4 Test Doubles (Mock / Stub / Spy / Fake)

Test doubles replace real dependencies in unit tests. Using the right type of double is critical for test quality and maintainability.

#### Taxonomy

| Double | Purpose | Behavior | Verification |
|--------|---------|----------|--------------|
| **Stub** | Provide canned responses to calls | Returns predefined values, no logic | Not verified — only used to satisfy dependencies |
| **Mock** | Verify that specific interactions occurred | Configured with expectations before execution | Verified: "was method X called with arguments Y?" |
| **Spy** | Record calls for later assertion | Delegates to real implementation, records calls | Verified after execution: "how many times was X called?" |
| **Fake** | A simplified working implementation | Contains real logic (e.g., in-memory database) | Not verified — behaves like the real thing but simpler |

#### When to Use Which

| Scenario | Recommended Double | Rationale |
|----------|--------------------|-----------|
| Dependency returns data the code under test uses | **Stub** | You need controlled input, not behavior verification |
| Verify that a side effect occurred (email sent, event published) | **Mock** | The test's purpose IS to verify the interaction |
| Need a working dependency but can't use the real one | **Fake** | In-memory repo, fake clock, fake filesystem |
| Debug or observe calls without changing behavior | **Spy** | Wraps the real object, records interactions |
| Dependency is slow, flaky, or has side effects (network, DB) | **Stub or Fake** | Isolation and speed |

#### Rules

- **Prefer Stubs and Fakes over Mocks.** Mocks couple tests to implementation details. If you refactor internals without changing behavior, mock-based tests break. Stub/Fake-based tests survive.
- **Never mock what you don't own.** Don't mock third-party libraries (`requests`, `axios`, `boto3`). Instead, define your own Port (Protocol/interface) and mock that. This aligns with **DIP** (section 3.5) — depend on abstractions you control.
- **One mock per test, maximum.** If a test needs 3+ mocks, the class under test has too many responsibilities (**SRP** violation, section 3.1).
- **Fakes for Repositories.** Create `InMemoryOrderRepository` implementing the same `OrderRepository` Protocol. Reuse it across all unit tests. This aligns with **Hexagonal Architecture** (section 4.6) — the fake is a Driven Adapter just like the real one.
- **Test behavior, not implementation.** Assert on outcomes (return values, state changes, emitted events), not on the sequence of internal method calls.

#### Example: Stub — Python

```python
# tests/application/test_confirm_order.py
from application.confirm_order import ConfirmOrderUseCase
from domain.order import Order

class StubOrderRepository:
    """Stub: returns a predefined order, records save calls."""

    def __init__(self, order: Order | None) -> None:
        self._order = order
        self.saved: list[Order] = []

    def find_by_id(self, order_id: str) -> Order | None:
        return self._order

    def save(self, order: Order) -> None:
        self.saved.append(order)

class TestConfirmOrderUseCase:
    def test_confirms_existing_order(self) -> None:
        # Arrange
        order = Order(order_id="1", customer_id="c1", total=100.0)
        repo = StubOrderRepository(order)
        use_case = ConfirmOrderUseCase(repo)

        # Act
        use_case.execute("1")

        # Assert
        assert order.is_confirmed is True
        assert len(repo.saved) == 1

    def test_raises_when_order_not_found(self) -> None:
        # Arrange
        repo = StubOrderRepository(None)
        use_case = ConfirmOrderUseCase(repo)

        # Act & Assert
        with pytest.raises(LookupError, match="Order 1 not found"):
            use_case.execute("1")
```

#### Example: Fake — Python

```python
# tests/fakes/fake_order_repository.py
from domain.order import Order

class FakeOrderRepository:
    """Fake: in-memory implementation with real storage behavior."""

    def __init__(self) -> None:
        self._storage: dict[str, Order] = {}

    def find_by_id(self, order_id: str) -> Order | None:
        return self._storage.get(order_id)

    def save(self, order: Order) -> None:
        self._storage[order.order_id] = order

    def find_all(self) -> list[Order]:
        return list(self._storage.values())
```

#### Example: Mock (interaction verification) — Python

```python
# Use mocks ONLY when the test's purpose is to verify a side effect.
from unittest.mock import Mock

class TestOrderNotificationService:
    def test_sends_notification_on_shipment(self) -> None:
        # Arrange
        sender = Mock()
        service = OrderNotificationService(sender)
        order = Order(order_id="1", customer_id="c1", total=100.0,
                      customer_email="user@example.com")

        # Act
        service.notify_order_shipped(order)

        # Assert — verifying the interaction IS the point of this test
        sender.send.assert_called_once_with(
            recipient="user@example.com",
            subject="Order 1 shipped",
            body="Your order is on the way!",
        )
```

---

### 5.5 TDD Walkthrough: Complete Red-Green-Refactor Example

This section demonstrates a complete TDD cycle building a `PriceCalculator` from scratch in three iterations.

#### Requirement

Calculate the total price for a list of items with quantity discounts: 10% off when buying 10+ of the same item.

---

#### Python Walkthrough

**Iteration 1: RED — basic price calculation**

```python
# tests/domain/test_price_calculator.py
from domain.price_calculator import PriceCalculator

def test_calculate_total_single_item() -> None:
    calculator = PriceCalculator()
    total = calculator.calculate([{"name": "Widget", "price": 25.0, "qty": 1}])
    assert total == 25.0
```

Run: `pytest -k test_calculate_total_single_item` → **RED** (ModuleNotFoundError).

**Iteration 1: GREEN — minimal implementation**

```python
# domain/price_calculator.py
class PriceCalculator:
    def calculate(self, items: list[dict]) -> float:
        return items[0]["price"] * items[0]["qty"]
```

Run: → **GREEN**.

**Iteration 2: RED — multiple items**

```python
def test_calculate_total_multiple_items() -> None:
    calculator = PriceCalculator()
    items = [
        {"name": "Widget", "price": 25.0, "qty": 2},
        {"name": "Gadget", "price": 50.0, "qty": 1},
    ]
    total = calculator.calculate(items)
    assert total == 100.0
```

Run: → **RED** (returns 50.0 instead of 100.0).

**Iteration 2: GREEN — handle multiple items**

```python
class PriceCalculator:
    def calculate(self, items: list[dict]) -> float:
        total = 0.0
        for item in items:
            total += item["price"] * item["qty"]
        return total
```

Run: → **GREEN**.

**Iteration 3: RED — quantity discount**

```python
def test_applies_10_percent_discount_for_10_or_more() -> None:
    calculator = PriceCalculator()
    items = [{"name": "Widget", "price": 10.0, "qty": 10}]
    total = calculator.calculate(items)
    assert total == 90.0  # 100 - 10% = 90
```

Run: → **RED** (returns 100.0).

**Iteration 3: GREEN — add discount logic**

```python
class PriceCalculator:
    def calculate(self, items: list[dict]) -> float:
        total = 0.0
        for item in items:
            line_total = item["price"] * item["qty"]
            if item["qty"] >= 10:
                line_total *= 0.9
            total += line_total
        return total
```

Run: → **GREEN**.

**REFACTOR — extract types and methods**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class LineItem:
    name: str
    price: float
    qty: int

BULK_DISCOUNT_THRESHOLD = 10
BULK_DISCOUNT_RATE = 0.10

class PriceCalculator:
    def calculate(self, items: list[LineItem]) -> float:
        return sum(self._line_total(item) for item in items)

    def _line_total(self, item: LineItem) -> float:
        subtotal = item.price * item.qty
        if item.qty >= BULK_DISCOUNT_THRESHOLD:
            subtotal *= 1 - BULK_DISCOUNT_RATE
        return subtotal
```

Run all tests: → **GREEN**. (Update tests to use `LineItem` dataclass.)

---

### 5.6 TDD Code Review Checklist

Quick checklist for reviewing PRs in a TDD-first workflow:

| # | Question | What to look for |
|---|----------|------------------|
| 1 | Were tests written before the production code? | Git history: test commits precede or accompany implementation commits. No large "add tests" commit at the end. |
| 2 | Does every public method/function have at least one test? | Check coverage of the public API. Private methods are tested through public ones. |
| 3 | Are tests named descriptively? | `test_<what>_<when>_<expected>` (Python) or `it("should <behavior> when <condition>")` (TS). No `test1`, `testHelper`. |
| 4 | Does each test follow AAA (Arrange-Act-Assert)? | Clear separation of setup, execution, and verification. One assertion concept per test. |
| 5 | Are test doubles appropriate? | Stubs/Fakes for data dependencies. Mocks only for verifying side effects. No mocking of third-party libraries directly. |
| 6 | Is there at most one mock per test? | Multiple mocks indicate SRP violation in the class under test. |
| 7 | Do tests verify behavior, not implementation? | Tests assert on return values and state, not on internal method call sequences. |
| 8 | Are tests independent and deterministic? | No shared mutable state between tests. No dependency on execution order. No `time.sleep()` or `setTimeout`. |
| 9 | Is the test pyramid respected? | Majority unit tests, moderate integration tests, minimal E2E tests. No "ice cream cone" (more E2E than unit). |
| 10 | Can tests run without external services? | Unit tests need no DB, no network, no filesystem. Integration tests use test containers or fixtures. |
| 11 | Is test code maintained with the same quality as production code? | No duplication, clear helpers, readable setup. Test code is not "throwaway." |
| 12 | Are edge cases and error paths covered? | Not just happy path. Tests for null/empty input, boundary values, error responses, timeouts. |

---
