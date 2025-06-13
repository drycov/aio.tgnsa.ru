// Функция для обновления системной информации
async function updateSystemInfo() {
    try {
        const response = await fetch('/api/system-info');
        const result = await response.json();
        
        if (result.status === 'success') {
            Object.entries(result.data).forEach(([key, value]) => {
                const element = document.querySelector(`[data-system-info="${key}"]`);
                if (element) {
                    // Добавляем анимацию при обновлении
                    element.classList.add('updating');
                    element.textContent = value;
                    setTimeout(() => element.classList.remove('updating'), 500);
                }
            });
        } else {
            console.error('Ошибка получения данных:', result.message);
        }
    } catch (error) {
        console.error('Ошибка при обновлении:', error);
    }
}

// Добавляем эффекты при наведении
document.querySelectorAll('.info-item').forEach(item => {
    item.addEventListener('mouseenter', () => {
        const icon = item.querySelector('.info-icon');
        if (icon) {
            icon.style.transform = 'scale(1.2) rotate(5deg)';
        }
    });

    item.addEventListener('mouseleave', () => {
        const icon = item.querySelector('.info-icon');
        if (icon) {
            icon.style.transform = 'none';
        }
    });
});

// Добавляем анимацию загрузки
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.info-item').forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        setTimeout(() => {
            item.style.transition = 'all 0.3s ease';
            item.style.opacity = '1';
            item.style.transform = 'none';
        }, index * 100);
    });
});

// Функция форматирования времени
function formatTime(date) {
    return date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'Asia/Almaty'  // Используем тот же часовой пояс, что и на сервере
    });
}

// Обновление времени
function updateTime() {
    const timeElement = document.querySelector('[data-system-info="current_time"]');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = formatTime(now);
        
        // Добавляем анимацию обновления
        timeElement.classList.add('updating');
        setTimeout(() => timeElement.classList.remove('updating'), 500);
    }
}

// Добавляем темную тему
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем сохраненную тему
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-theme');
    }

    // Форматируем время при первой загрузке
    const timeElement = document.querySelector('[data-system-info="current_time"]');
    if (timeElement && timeElement.textContent) {
        const time = new Date();
        timeElement.textContent = formatTime(time);
    }
    
    // Обновляем время каждую секунду
    setInterval(updateTime, 1000);
    
    // Обновляем системную информацию каждые 5 секунд
    setInterval(updateSystemInfo, 5000);
    
    // Первое обновление при загрузке
    updateSystemInfo();
});