@echo off
setlocal enabledelayedexpansion
REM Переход в папку, где находится этот скрипт
cd /d "%~dp0"
set "TARGET_FILE=%cd%\settings.py"

REM Проверка наличия репозитория
if not exist ".git" (
    if not exist "meta-sd-to-html" (
        echo Cloning the repository...
        git clone https://github.com/Jawerka/meta-sd-to-html.git
    ) else (
        echo The "meta-sd-to-html" folder exists but is not a repository.
        exit /b 1
    )
)

REM Копируем все файлы из meta-sd-to-html в текущую директорию с заменой
if exist "meta-sd-to-html" (
    echo Copying files...
    xcopy /E /H /Y "meta-sd-to-html\*" .\
    )

REM Удаляем временную папку с репозиторием после копирования файлов
if exist "meta-sd-to-html" (
    echo Deleting the temporary repository folder...
    rd /s /q "meta-sd-to-html"
    )

REM Проверка наличия виртуального окружения
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating...
    REM Создание виртуального окружения
    python -m venv venv
    if not exist "venv\Scripts\activate.bat" (
        echo Error: Failed to create virtual environment.
        exit /b 1
    )
)

REM Активация виртуального окружения
echo Activating virtual environment...
call venv\Scripts\activate

REM Установка зависимостей (если необходимо)
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo Warning: requirements.txt file not found.
)

REM Проверяем, существует ли settings.py
if not exist "%TARGET_FILE%" (
    echo from pathlib import Path> "%TARGET_FILE%"
    echo.>> "%TARGET_FILE%"
    echo # Пути, где ищем изображения>> "%TARGET_FILE%"
	echo image_dir = ^[>> "%TARGET_FILE%"
	echo     Path^(r^"C:\AI\FirstFolder^"^),>> "%TARGET_FILE%"
	echo     Path^(r^"C:\AI\SecondFolder^"^),>> "%TARGET_FILE%"
	echo ^]>> "%TARGET_FILE%"
    echo.>> "%TARGET_FILE%"
    echo # Путь к выходному HTML-файлу>> "%TARGET_FILE%"
    echo output_html = Path^(r^"C:\AI\gallery.html^"^)>> "%TARGET_FILE%"
    echo The settings.py file was successfully created.
) else (
    echo The settings.py file already exists.
)

REM Проверка наличия main.py
if not exist "main.py" (
    echo Error: main.py not found.
    deactivate
    exit /b 1
)

REM Запуск main.py
echo Running main.py...
python main.py
pause

REM Деактивация виртуального окружения
echo Deactivating virtual environment...
deactivate

pause
