import json
import time
from pathlib import Path
from string import Template
from typing import Optional, Dict, List

from PIL import Image

# === Конфигурация ===

from settings import *

# Поддерживаемые расширения изображений
supported_extensions = {'.png', '.jpg', '.jpeg', '.webp'}

# === Встроенный HTML-шаблон (будет заполнен данными позже) ===

html_template = Template("""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Галерея</title>
    <style>
      body {
        background: #0e0e0e;
        color: #eee;
        font-family: "Segoe UI", sans-serif;
        margin: 0;
        display: flex;
        flex-direction: column;
        height: 100vh;
      }
      .main-container {
        display: flex;
        flex: 1;
        overflow: hidden;
      }
      .selector {
        display: flex;
        position: absolute;
        left: 10px;
        top: 10px;
        opacity: 0.05;
        transition: opacity 0.2s ease;
        pointer-events: auto;
        z-index: 10;
      }
      .selector:hover {
        opacity: 1;
      }
      .image-container {
        flex: 3;
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
        padding: 10px;
        overflow: hidden;
      }
      .image-wrapper {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
      }
      #content {
        width: 100%;
        height: 100%;
        max-width: 100%;
        max-height: 100%;
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
        box-sizing: border-box;
      }
      #main-image {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        display: block;
        border-radius: 12px;
        transition: transform 0.2s;
        cursor: zoom-in;
      }
      .info-panel {
        width: 47%;
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 10px;
        box-sizing: border-box;
        height: 100%;
        position: relative;
      }
      .text-block {
        position: relative;
        flex: 1;
        display: flex;
        flex-direction: column;
      }
      .info-panel textarea {
        background: #1e1e1e;
        color: white;
        border: none;
        padding: 10px 34px 10px 10px;
        border-radius: 8px;
        resize: none;
        width: 100%;
        font-family: inherit;
        flex: 1;
        box-sizing: border-box;
        min-height: 0;
      }
      .text-block.prompt { flex: 5; }
      .text-block.negative { flex: 2; }
      .text-block.params { flex: 3; }
      .copy-btn {
        position: absolute;
        top: 6px;
        right: 8px;
        background: none;
        border: none;
        color: #aaa;
        font-size: 16px;
        cursor: pointer;
        z-index: 2;
        opacity: 0.3;
        transition: opacity 0.2s;
        padding: 0;
      }
      .text-block:hover .copy-btn {
        opacity: 1;
      }
      .copy-all-btn {
        position: absolute;
        right: 10px;
        bottom: 10px;
        z-index: 2;
        background: none;
        border: none;
        color: #aaa;
        font-size: 16px;
        cursor: pointer;
        opacity: 0.3;
        transition: opacity 0.2s;
      }
      .copy-all-btn:hover {
        opacity: 1;
      }
      .thumbnail-strip {
        height: 110px;
        background-color: #1a1a1a;
        display: flex;
        align-items: center;
        overflow-x: auto;
        padding: 2px;
        box-sizing: border-box;
        user-select: none;
        cursor: grab;
      }
      .thumbnail-strip img {
        height: 80px;
        margin-right: 10px;
        border-radius: 6px;
        transition: transform 0.2s, border 0.2s;
        border: 2px solid transparent;
        object-fit: cover;
      }
      .thumbnail-strip img:hover {
        transform: scale(1.1);
        border-color: #3ea6ff;
      }
      .arrow {
        font-size: 32px;
        color: #eee;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 50%;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s, transform 0.2s;
        margin: 0 10px;
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        opacity: 0;
        pointer-events: none;
        cursor: pointer;
        z-index: 10;
      }
      .arrow:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: translateY(-50%) scale(1.1);
      }
      .arrow.show {
        opacity: 1;
        pointer-events: auto;
      }
      #left-arrow { left: 10px; }
      #right-arrow { right: 10px; }
      ::-webkit-scrollbar {
        width: 8px;
      }
      ::-webkit-scrollbar-thumb {
        background: #333;
        border-radius: 4px;
      }
      ::-webkit-scrollbar-track {
        background: #1a1a1a;
      }
      .fullscreen-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 100;
      }
      .fullscreen-overlay img {
        max-width: 100%;
        max-height: 100%;
        cursor: grab;
      }
      .zoom-container {
        position: relative;
        overflow: hidden;
        cursor: zoom-out;
        user-select: none;
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
      }
      .zoom-container.dragging {
        cursor: grabbing;
      }
      .zoom-content {
        position: absolute;
        transform-origin: 0 0;
        will-change: transform;
        width: auto;
        height: 98%;
      }
    </style>
</head>
<body>
    <div class="selector">
      <select id="folder-select" onchange="filterByFolder()">
        ${folder_options}
      </select>
    </div>
  <div class="main-container">
    <div class="image-container" id="image-container">
        <div class="image-wrapper">
          <div id="content">
            <img id="main-image" src="${first_image}" alt="Generated image" draggable="false">
          </div>
          <span class="arrow" id="left-arrow">&#8592;</span>
          <span class="arrow" id="right-arrow">&#8594;</span>
        </div>
    </div>
    <div class="info-panel">
      <div class="text-block prompt">
        <button class="copy-btn" onclick="copyText('prompt-text')">📋</button>
        <textarea id="prompt-text" readonly>${first_prompt}</textarea>
      </div>
      <div class="text-block negative">
        <button class="copy-btn" onclick="copyText('negative-text')">📋</button>
        <textarea id="negative-text" readonly>${first_negative}</textarea>
      </div>
      <div class="text-block params">
        <button class="copy-btn" onclick="copyText('params-text')">📋</button>
        <textarea id="params-text" readonly>${first_params}</textarea>
      </div>
      <button class="copy-all-btn" onclick="copyAll()">📋 Copy all</button>
    </div>
  </div>

  <div class="thumbnail-strip" id="thumbnail-strip">
    ${thumbnail_html}
  </div>

  <!-- Полноэкранный режим с зумом -->
  <div class="fullscreen-overlay" id="fullscreen-overlay">
    <div class="zoom-container" id="zoom-container">
      <div class="zoom-content" id="zoom-content">
        <img id="fullscreen-image" src="" alt="Fullscreen image" draggable="false" />
      </div>
    </div>
  </div>

    <script>
      const images = ${image_data_json};
      let filteredImages = images.slice();
      let currentIndex = 0;
      let isFullscreen = false;
    
      const img = document.getElementById('main-image');
      const container = document.getElementById('image-container');
      const leftArrow = document.getElementById('left-arrow');
      const rightArrow = document.getElementById('right-arrow');
      const fullscreenOverlay = document.getElementById('fullscreen-overlay');
      const fullscreenImage = document.getElementById('fullscreen-image');
    
      function filterByFolder() {
        const folder = document.getElementById('folder-select').value;
        filteredImages = folder === 'all'
          ? images.slice()
          : images.filter(img => img.folder === folder);
        currentIndex = 0;
        renderThumbnails();
        updateContent();
      }
    
      function sanitizeHash(str) {
        return str.replace(/[^a-zA-Z0-9\\-_]/g, '_');
      }
    
      function renderThumbnails() {
        const strip = document.getElementById('thumbnail-strip');
        strip.innerHTML = '';
        filteredImages.forEach((item, index) => {
          const thumb = document.createElement('img');
          thumb.src = item.src;
          thumb.onclick = () => {
            currentIndex = index;
            updateContent();
            location.hash = sanitizeHash(filteredImages[currentIndex].src);
          };
          strip.appendChild(thumb);
        });
      }
    
      function updateContent() {
        if (!filteredImages.length) return;
        const data = filteredImages[currentIndex];
        img.src = data.src;
        fullscreenImage.src = data.src;
        img.style.transform = 'scale(1)';
        img.style.cursor = 'zoom-in';
        document.getElementById('prompt-text').value = data.prompt;
        document.getElementById('negative-text').value = data.negative;
        document.getElementById('params-text').value = data.params;
    
        location.hash = sanitizeHash(data.src);
    
        const thumbnails = document.querySelectorAll('#thumbnail-strip img');
        thumbnails.forEach((thumb, i) => {
          thumb.style.borderColor = i === currentIndex ? '#3ea6ff' : 'transparent';
          if (i === currentIndex) {
            thumb.scrollIntoView({
              behavior: 'auto',
              inline: 'center',
              block: 'nearest'
            });
          }
        });
      }
    
      leftArrow.onclick = () => {
        if (isFullscreen) return;
        currentIndex = (currentIndex - 1 + filteredImages.length) % filteredImages.length;
        updateContent();
      };
    
      rightArrow.onclick = () => {
        if (isFullscreen) return;
        currentIndex = (currentIndex + 1) % filteredImages.length;
        updateContent();
      };
    
      container.addEventListener('mouseenter', () => {
        if (isFullscreen) return;
        leftArrow.classList.add('show');
        rightArrow.classList.add('show');
      });
    
      container.addEventListener('mouseleave', () => {
        leftArrow.classList.remove('show');
        rightArrow.classList.remove('show');
      });
    
      // Обработчик колёсика
      document.addEventListener('wheel', function(e) {
        if (isFullscreen) return;
        
        const thumbnailStrip = document.getElementById('thumbnail-strip');
        const isOverThumbnailStrip = thumbnailStrip.contains(e.target);
        const isOverTextArea = e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT';
    
        if (isOverTextArea) {
          e.preventDefault();
          e.target.scrollTop += e.deltaY;
        } else if (isOverThumbnailStrip) {
          e.preventDefault();
          thumbnailStrip.scrollLeft += e.deltaY;
        } else {
          e.preventDefault();
          currentIndex = e.deltaY > 0
            ? (currentIndex + 1) % filteredImages.length
            : (currentIndex - 1 + filteredImages.length) % filteredImages.length;
          updateContent();
        }
      }, { passive: false });
    
      img.addEventListener('click', () => {
        isFullscreen = true;
        fullscreenOverlay.style.display = 'flex';
        fullscreenImage.src = img.src;
      });
    
      fullscreenOverlay.addEventListener('click', (e) => {
        // Закрываем только если клик не на самом изображении
        if (e.target === fullscreenOverlay) {
          isFullscreen = false;
          fullscreenOverlay.style.display = 'none';
        }
      });

    const zoomContainer = document.getElementById('zoom-container');
    const zoomContent = document.getElementById('zoom-content');
    
    let scale = 1;
    let lastX = 0;
    let lastY = 0;
    
    function updateTransform() {
      zoomContent.style.transform = `translate($${lastX}px, $${lastY}px) scale($${
      scale})`;
    }
    
    // Масштабирование колесом мыши
    zoomContainer.addEventListener('wheel', function (e) {
      e.preventDefault();
    
      const zoomIntensity = 0.1;
      const delta = -Math.sign(e.deltaY) * zoomIntensity;
    
      const rect = zoomContainer.getBoundingClientRect();
    
      // Координаты курсора относительно контейнера
      const offsetX = e.clientX - rect.left;
      const offsetY = e.clientY - rect.top;
    
      // Координаты относительно текущего масштаба
      const x = (offsetX - lastX) / scale;
      const y = (offsetY - lastY) / scale;
    
      // Новый масштаб
      const newScale = Math.min(Math.max(0.1, scale * (1 + delta)), 10);
    
      // Корректируем смещение так, чтобы масштабирование происходило относительно курсора
      lastX -= x * (newScale - scale);
      lastY -= y * (newScale - scale);
    
      scale = newScale;
      updateTransform();
    });

    // Перетаскивание мышью
    let isDragging = false;
    let startX, startY;

    zoomContainer.addEventListener('mousedown', (e) => {
      e.preventDefault();
      isDragging = true;
      startX = e.clientX - lastX;
      startY = e.clientY - lastY;
      zoomContainer.classList.add('dragging');
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      lastX = e.clientX - startX;
      lastY = e.clientY - startY;
      updateTransform();
    });

    document.addEventListener('mouseup', () => {
      isDragging = false;
      zoomContainer.classList.remove('dragging');
    });

    // Блокируем браузерное поведение drag'n'drop
    zoomContent.addEventListener('dragstart', e => e.preventDefault());
    zoomContent.querySelectorAll('img').forEach(img => {
      img.addEventListener('dragstart', e => e.preventDefault());
    });

    // Открытие полноэкранного режима при клике на изображение
    const mainImage = document.getElementById('main-image');
    mainImage.addEventListener('click', () => {
      isFullscreen = true;
      fullscreenImage.src = mainImage.src;
      fullscreenOverlay.style.display = 'flex';
      scale = 1;
      lastX = 0;
      lastY = 0;
      updateTransform();
    });

    // Закрытие полноэкранного режима при клике
    fullscreenOverlay.addEventListener('click', (e) => {
      // Закрываем только если клик не на самом изображении или его контейнере
      if (e.target === fullscreenOverlay || e.target === zoomContainer) {
        isFullscreen = false;
        fullscreenOverlay.style.display = 'none';
      }
    });

      // Инициализация:
      renderThumbnails();
      updateContent();
    </script>
</body>
</html>
""")


# === Обработка одного изображения ===

def extract_image_data(img_path: Path) -> Optional[Dict[str, str]]:
    """
    Извлекает метаданные изображения (prompt, negative prompt, параметры).
    Возвращает словарь или None, если данные не найдены или произошла ошибка.
    """
    try:
        with Image.open(img_path) as img:
            params_raw = img.info.get("parameters", "").strip()
            if not params_raw:
                return None

            lines = params_raw.splitlines()
            prompt_lines = []
            negative_prompt = ""
            other_lines = []
            in_negative = False

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.lower().startswith("negative prompt:"):
                    in_negative = True
                    negative_prompt = line.split(":", 1)[1].strip()
                elif in_negative and ":" not in line:
                    negative_prompt += ", " + line
                elif in_negative and ":" in line:
                    in_negative = False
                    other_lines.append(line)
                elif not in_negative and ":" not in line:
                    prompt_lines.append(line)
                else:
                    other_lines.append(line)

            # Обработка строки Steps (часто встречается в конце параметров)
            processed_other_lines = "\n".join(other_lines)
            if "Steps:" in processed_other_lines:
                pre, post = processed_other_lines.split("Steps:", 1)
                if pre:
                    prompt_lines.append(pre.strip())
                processed_other_lines = "Steps:" + post.strip()

            return {
                "src": str(img_path),
                "prompt": "\n".join(prompt_lines),
                "negative": negative_prompt,
                "params": processed_other_lines,
            }

    except Exception as e:
        print(f"Ошибка при обработке {img_path}: {e}")
        return None


# === Обход одной директории и сбор изображений ===

def gather_images(directory: Path) -> List[Dict[str, str]]:
    image_data: List[Dict[str, str]] = []
    all_files = sorted(
        (file for file in directory.rglob("*")
         if file.is_file() and file.suffix.lower() in supported_extensions),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    for file in all_files:
        data = extract_image_data(file)
        if data:
            data["folder"] = directory.name  # <=== добавляем сюда
            image_data.append(data)

    return image_data



# === Главная функция ===

def main():
    start_time = time.time()
    image_data: List[Dict[str, str]] = []

    folder_options_html = '<option value="all">Все</option>\n'
    for folder in image_dir:
        folder_name = folder.name
        folder_options_html += f'<option value="{folder_name}">{folder_name}</option>\n'

    # Сбор всех изображений из всех директорий
    for image_dir_path in image_dir:
        image_data.extend(gather_images(image_dir_path))

    if not image_data:
        print("Нет изображений для обработки")
        return

    # Генерация миниатюр
    thumbnail_html = "".join(
        f'<img src="{item["src"]}" onclick="selectImage({i})" alt="Preview {i}">'
        for i, item in enumerate(image_data)
    )

    # Данные первого изображения
    first_image = image_data[0]
    image_data_json = json.dumps(image_data, indent=4, ensure_ascii=False)

    # Сохраняем HTML-файл
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_template.substitute(
            first_image=first_image['src'],
            first_prompt=first_image['prompt'].replace("$", "&#36;"),
            first_negative=first_image['negative'].replace("$", "&#36;"),
            first_params=first_image['params'].replace("$", "&#36;"),
            thumbnail_html=thumbnail_html,
            image_data_json=image_data_json,
            folder_options=folder_options_html,
        ))

    print(f"Галерея сохранена: {output_html} ({time.time() - start_time:.2f} сек.)")


if __name__ == '__main__':
    main()
