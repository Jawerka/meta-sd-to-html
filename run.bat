@echo off
cd /d "%~dp0"  REM Переход в папку, где находится этот скрипт

REM Клонирование репозитория в временную папку, если она ещё не существует
if not exist "meta-sd-to-html" (
    echo Клонируем репозиторий...
    git clone https://github.com/Jawerka/meta-sd-to-html.git
)

REM Копируем все файлы из meta-sd-to-html в текущую директорию с заменой
xcopy /E /H /Y "meta-sd-to-html\*" .\

REM Удаляем временную папку с репозиторием после копирования файлов
rd /s /q "meta-sd-to-html"

REM Проверка наличия виртуального окружения
if not exist "venv" (
    echo Виртуальное окружение не найдено. Создаём...
    python -m venv venv  REM Создание виртуального окружения
)

REM Активируем виртуальное окружение
call venv\Scripts\activate

REM Установка зависимостей (если необходимо)
pip install -r requirements.txt

REM Запуск main.py
python main.py

REM Деактивация виртуального окружения
deactivate

pause
