@echo off
chcp 65001  REM Устанавливаем кодировку UTF-8 для корректного отображения символов
cd /d "%~dp0"  REM Переход в папку, где находится этот скрипт

REM Проверка наличия репозитория
if not exist "meta-sd-to-html\.git" (
    if not exist "meta-sd-to-html" (
        echo Клонируем репозиторий...
        git clone https://github.com/Jawerka/meta-sd-to-html.git
    ) else (
        echo Папка "meta-sd-to-html" существует, но не является репозиторием.
        exit /b 1
    )
)

REM Копируем все файлы из meta-sd-to-html в текущую директорию с заменой
echo Копируем файлы...
xcopy /E /H /Y "meta-sd-to-html\*" .\

REM Удаляем временную папку с репозиторием после копирования файлов
echo Удаляем временную папку с репозиторием...
rd /s /q "meta-sd-to-html"

REM Проверка наличия виртуального окружения
if not exist "venv\Scripts\activate.bat" (
    echo Виртуальное окружение не найдено. Создаём...
    python -m venv venv  REM Создание виртуального окружения
    if not exist "venv\Scripts\activate.bat" (
        echo Ошибка: Не удалось создать виртуальное окружение.
        exit /b 1
    )
)

REM Активация виртуального окружения
echo Активируем виртуальное окружение...
call venv\Scripts\activate

REM Установка зависимостей (если необходимо)
if exist "requirements.txt" (
    echo Устанавливаем зависимости...
    pip install -r requirements.txt
) else (
    echo Внимание: файл requirements.txt не найден.
)

REM Проверка наличия main.py
if not exist "main.py" (
    echo Ошибка: main.py не найден.
    deactivate
    exit /b 1
)

REM Запуск main.py
echo Запускаем main.py...
python main.py

REM Деактивация виртуального окружения
echo Деактивируем виртуальное окружение...
deactivate

pause
