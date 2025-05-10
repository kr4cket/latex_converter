# PDF → LaTeX Converter

**Содержание**
1. [Обзор](#обзор)  
2. [Структура проекта](#структура-проекта)  
3. [Установка и зависимости](#установка-и-зависимости)  
4. [Конфигурация](#конфигурация)  
   - [Файл `config/application.yaml`](#файл-configapplicationyaml)  
   - [Добавление собственных обработчиков](#добавление-собственных-обработчиков)  
   - [Переменные окружения](#переменные-окружения)  
5. [Архитектура и Pipeline](#архитектура-и-pipeline)  
6. [API – FastAPI](#api--fastapi)  
7. [Запуск и пример использования](#запуск-и-пример-использования)  
8. [Очистка и временные файлы](#очистка-и-временные-файлы)  

---

## Обзор

Это сервис на FastAPI, который принимает на вход PDF-документ, распознаёт содержимое (текст, таблицы, формулы), прогоняет всё через AI-модель для сборки единой LaTeX-разметки и отдаёт результат в виде ZIP-архива с TeX-файлами.

**Приложение поддерживает гибкую конфигурацию** через файл `config/application.yaml`, позволяя добавлять и настраивать любые стадии обработки и препроцессоры без изменения исходного кода.

Ключевые компоненты:
- **API**: загрузка PDF и скачивание готового ZIP.  
- **Converter Service**: основной класс `Converter` управляет загрузкой конфигурации, построением и запуском пайплайна.  
- **Pipeline**: модульная цепочка препроцессоров и стадий, каждая из которых реализована в виде класса-наследника `Stage`.  

---

## Структура проекта

```text
├── .env                       # Переменные окружения (API_KEY, прокси и т.п.)
├── config
│   └── application.yaml       # Основная конфигурация пайплайна и путей
├── app
│   ├── main.py                # Точка входа FastAPI
│   ├── api
│   │   └── v1
│   │       ├── api.py         # Роутинг
│   │       └── endpoints
│   │           └── converter.py  # Эндпойнты загрузки и скачивания
│   └── converter
│       ├── service.py         # Класс Converter + инициализация Pipeline
│       ├── pipeline
│       │   ├── pipeline.py    # Класс Pipeline и базовый Stage
│       │   ├── ocr
│       │   ├── preprocessing
│       │   ├── file
│       │   └── models
│       └── utils
│           └── helpers.py     # Утилиты (расширение env, работа с файлами)
├── cache
│   └── formulas               # Кэш для распознавания формул
├── downloads                   # Директория для результирующих TeX
└── temp                       # Временные файлы при обработке
```

---

## Установка и зависимости

1. Клонировать репозиторий:
   ```bash
   git clone <https://github.com/kr4cket/latex_converter> && cd <latex_converter>
   ```
2. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. (Опционально) создать виртуальное окружение:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```

---

## Конфигурация

### Файл `config/application.yaml`

```yaml
default_tex_dir: &tex_dir "tex"

downloads:
  tex_dir: *tex_dir

pipeline:
  preprocessors:
    - name: ImagePreprocessor
      params:
        directory: "img"
        output_prefix: "page_"
  stages:
    - name: TextExtractor
    - name: TablesExtractor
    - name: FormulasExtractor
      params:
        required_symbols: ['\', '{', '}', '_', '^']
        math_keywords: ['\frac', '\sqrt', '\sum', '\int', '\alpha', '\beta']
        cache_dir: "cache/formulas"
    - name: AIExtractor
      params:
        api_key: "${API_KEY}"
        proxies:
          http: ""
          https: ""
    - name: TexExporter
      params:
        directory: *tex_dir
        output_prefix: "page_"
```

- **`downloads.tex_dir`** — папка, куда сохраняется сгенерированный ZIP с TeX-файлами.  
- **`pipeline.preprocessors`** — список препроцессоров (классы, наследующие `Stage`), выполняющихся до OCR.  
- **`pipeline.stages`** — список стадий обработки: OCR → AI → экспорт.  
- **`name`** — точное имя Python-класса в модуле `app.converter.pipeline`.  
- **`params`** — словарь параметров конструктора класса; поддерживается расширение переменных окружения.

### Добавление собственных обработчиков

Для добавления пользовательских стадий или препроцессоров:

1. Создайте класс, наследующий базовый `Stage`:
   ```python
   from app.converter.stage.stage import Stage
   
   class CustomStage(Stage):
       def __init__(self, param1, param2):
           super().__init__()
           self.param1 = param1
           self.param2 = param2
       
       def process(self, page_data):
           # Ваша логика обработки
           return modified_page_data
   ```
2. Убедитесь, что класс доступен в импорте (либо задайте полный путь, если он в другом модуле).  
3. Добавьте запись в `config/application.yaml`:
   ```yaml
   pipeline:
     preprocessors:
       - name: YourCustomPreprocessor
         params:
           paramA: valueA
     stages:
       - name: CustomStage
         params:
           param1: value1
           param2: value2
   ```
Благодаря гибкой конфигурации приложение автоматически создаст и запустит ваши кастомные компоненты без правки исходного кода.

### Переменные окружения

- В `.env` указываются секреты:
  ```
  API_KEY=<ваш OpenAI API ключ>
  ```

---

## Архитектура и Pipeline

### Базовый класс и Pipeline

```python
class Stage:
    def __init__(self):
        pass

    def process(self, page_data):
        raise NotImplementedError
```

```python
class Pipeline:
    def __init__(self):
        self.file_path = ""
        self.preprocessors = []
        self.stages = []
        self.pages_data = {}

    def set_file_path(self, file_path): ...

    def add_preprocessor(self, preprocessor: Stage): ...

    def add_stage(self, stage: Stage): ...

    def prepare(self):
        # Разбивка PDF → изображения страниц

    def run(self):
        # Последовательный запуск всех препроцессоров и стадий
        return self.pages_data
```

Каждая стадия и препроцессор вызывается методом `process` с обновлением данных страницы.

---

## API – FastAPI

- **Запуск**:
  ```bash
  uvicorn app.main:app --host localhost --port 8100 --reload --timeout-keep-alive 3600
  ```
- **Эндпойнты**:
  - `POST /api/v1/convert` — загрузка PDF, возвращает `download_url`.
  - `GET /api/v1/convert/{file_id}` — скачивание ZIP.

---

## Запуск и пример использования

```bash
# Запустить сервис
uvicorn app.main:app --reload

# Конвертация PDF
curl -F "file=@document.pdf" http://localhost:8000/api/v1/convert

# Скачивание результатов
curl http://localhost:8000/api/v1/convert/<file_id> --output result.zip
```

---

## Очистка и временные файлы

Метод `Converter.cleanup()`:
- Удаляет временные файлы из папки `temp/`.
- **Не очищает** директорию `downloads/`, где хранятся итоговые TeX-файлы.  
При необходимости очистки результатов делайте это вручную или расширяйте логику метода.

---

> **Важно:** все настройки пайплайна (порядок, состав стадий и препроцессоров) управляются из `config/application.yaml`.  
> Приложение поддерживает гибкую конфигурацию и расширение за счёт добавления новых классов-обработчиков, унаследованных от `Stage`.
