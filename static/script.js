document.addEventListener('DOMContentLoaded', function() {
    // Элементы DOM
    const generateBtn = document.getElementById('generateBtn');
    const autoBtn = document.getElementById('autoBtn');
    const historyBtn = document.getElementById('historyBtn');
    const statsBtn = document.getElementById('statsBtn');
    const helpBtn = document.getElementById('helpBtn');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const refreshStatsBtn = document.getElementById('refreshStatsBtn');
    const copyBtn = document.getElementById('copyBtn');
    const shareBtn = document.getElementById('shareBtn');
    const favoriteBtn = document.getElementById('favoriteBtn');
    const speakBtn = document.getElementById('speakBtn');
    const exportBtn = document.getElementById('exportBtn');

    const jokeText = document.getElementById('jokeText');
    const jokeId = document.getElementById('jokeId');
    const jokeCategory = document.getElementById('jokeCategory');
    const jokeLanguage = document.getElementById('jokeLanguage');
    const jokeTime = document.getElementById('jokeTime');

    const historyPanel = document.getElementById('historyPanel');
    const statsPanel = document.getElementById('statsPanel');
    const helpPanel = document.getElementById('helpPanel');
    const historyList = document.getElementById('historyList');
    const statsContent = document.getElementById('statsContent');
    const notification = document.getElementById('notification');

    let autoModeInterval = null;
    let favorites = JSON.parse(localStorage.getItem('jokeFavorites')) || [];

    // Показать уведомление
    function showNotification(message, type = 'success') {
        notification.textContent = message;
        notification.style.background = type === 'success' ? '#48bb78' :
                                       type === 'error' ? '#f56565' :
                                       '#4299e1';
        notification.style.display = 'block';

        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }

    // Получить шутку
    async function fetchJoke() {
        const category = document.getElementById('category').value;
        const language = document.getElementById('language').value;

        try {
            const response = await fetch(`/get_joke?category=${category}&language=${language}`);
            const joke = await response.json();

            // Обновить интерфейс
            jokeText.textContent = joke.text;
            jokeId.textContent = joke.id;
            jokeCategory.textContent = joke.category_label;
            jokeLanguage.textContent = joke.language_label;
            jokeTime.textContent = joke.timestamp + ' ' + joke.date;


            // Авто-озвучивание (если включено в настройках)
            if (localStorage.getItem('autoSpeak') === 'true') {
                speakJoke(joke.text);
            }

            return joke;
        } catch (error) {
            console.error('Ошибка при получении шутки:', error);
            jokeText.textContent = 'Ошибка при загрузке шутки. Попробуйте еще раз.';
            showNotification('Ошибка при загрузке шутки', 'error');
        }
    }

    // Озвучить шутку
    function speakJoke(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = document.getElementById('language').value === 'ru' ? 'ru-RU' : 'en-US';
            utterance.rate = 0.9;
            speechSynthesis.speak(utterance);
        } else {
            showNotification('Озвучивание не поддерживается вашим браузером', 'warning');
        }
    }

    // Загрузить историю
    async function loadHistory() {
        try {
            const response = await fetch('/history');
            const history = await response.json();

            historyList.innerHTML = '';

            if (history.length === 0) {
                historyList.innerHTML = '<p class="empty-history">История пуста</p>';
                return;
            }

            history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.innerHTML = `
                    <div class="history-header">
                        <span class="history-id">#${item.id}</span>
                        <span class="history-meta">
                            <span class="badge">${item.category_label}</span>
                            <span class="badge">${item.language_label}</span>
                            <span class="time">${item.date} ${item.timestamp}</span>
                        </span>
                    </div>
                    <div class="history-text">${item.text}</div>
           
                `;

                // Клик по шутке в истории
                historyItem.querySelector('.history-text').addEventListener('click', () => {
                    jokeText.textContent = item.text;
                    jokeId.textContent = item.id;
                    jokeCategory.textContent = item.category_label;
                    jokeLanguage.textContent = item.language_label;
                    jokeTime.textContent = item.timestamp + ' ' + item.date;
                });


                historyList.appendChild(historyItem);
            });
        } catch (error) {
            console.error('Ошибка при загрузке истории:', error);
            historyList.innerHTML = '<p class="empty-history">Ошибка загрузки истории</p>';
        }
    }

    // Загрузить статистику
    async function loadStats() {
        try {
            const response = await fetch('/stats');
            const stats = await response.json();

            statsContent.innerHTML = `
                <div class="stat-card total">
                    <h4>Всего шуток</h4>
                    <div class="stat-value">${stats.total}</div>
                </div>
                
                <div class="stat-card languages">
                    <h4>По языкам</h4>
                    <div class="stat-details">
                        ${Object.entries(stats.by_language).map(([lang, data]) => `
                            <div class="stat-row">
                                <span>${lang}</span>
                                <span class="stat-number">${data.total}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="stat-card categories">
                    <h4>По категориям</h4>
                    <div class="stat-details">
                        ${Object.entries(stats.by_category).map(([cat, count]) => `
                            <div class="stat-row">
                                <span>${cat}</span>
                                <span class="stat-number">${count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                ${stats.last_5_jokes.length > 0 ? `
                <div class="stat-card recent">
                    <h4>Последние шутки</h4>
                    <div class="recent-jokes">
                        ${stats.last_5_jokes.map(joke => `
                            <div class="recent-joke">
                                <span class="recent-category">${joke.category_label}</span>
                                <span class="recent-text">${joke.text.substring(0, 50)}...</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            `;
        } catch (error) {
            console.error('Ошибка при загрузке статистики:', error);
            statsContent.innerHTML = '<p>Ошибка загрузки статистики</p>';
        }
    }


    // Переключить избранное
    function toggleFavorite(jokeId) {
        const index = favorites.indexOf(jokeId);

        if (index > -1) {
            favorites.splice(index, 1);
            showNotification('Удалено из избранного');
        } else {
            favorites.push(jokeId);
            showNotification('Добавлено в избранное');
        }

        localStorage.setItem('jokeFavorites', JSON.stringify(favorites));
    }

    // Экспорт истории
    function exportHistory() {
        const historyText = Array.from(document.querySelectorAll('.history-text'))
            .map((el, i) => `${i + 1}. ${el.textContent}`)
            .join('\n\n');

        const blob = new Blob([historyText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'история_шуток.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification('История экспортирована в файл');
    }

    // Обработчики событий
    generateBtn.addEventListener('click', fetchJoke);

    autoBtn.addEventListener('click', function() {
        if (autoModeInterval) {
            clearInterval(autoModeInterval);
            autoModeInterval = null;
            autoBtn.innerHTML = '<i class="fas fa-play"></i> Авто-режим (10 сек)';
            autoBtn.classList.remove('btn-danger');
            autoBtn.classList.add('btn-secondary');
            showNotification('Авто-режим отключен');
        } else {
            autoModeInterval = setInterval(fetchJoke, 10000);
            autoBtn.innerHTML = '<i class="fas fa-stop"></i> Остановить';
            autoBtn.classList.remove('btn-secondary');
            autoBtn.classList.add('btn-danger');
            showNotification('Авто-режим включен (10 сек)');
            fetchJoke();
        }
    });

    historyBtn.addEventListener('click', function() {
        const isVisible = historyPanel.style.display !== 'none';
        historyPanel.style.display = isVisible ? 'none' : 'block';
        statsPanel.style.display = 'none';
        helpPanel.style.display = 'none';

        if (!isVisible) {
            loadHistory();
        }
    });

    statsBtn.addEventListener('click', function() {
        const isVisible = statsPanel.style.display !== 'none';
        statsPanel.style.display = isVisible ? 'none' : 'block';
        historyPanel.style.display = 'none';
        helpPanel.style.display = 'none';

        if (!isVisible) {
            loadStats();
        }
    });

    helpBtn.addEventListener('click', function() {
        const isVisible = helpPanel.style.display !== 'none';
        helpPanel.style.display = isVisible ? 'none' : 'block';
        historyPanel.style.display = 'none';
        statsPanel.style.display = 'none';
    });

    clearHistoryBtn.addEventListener('click', async function() {
        if (confirm('Вы уверены, что хотите очистить всю историю шуток?')) {
            try {
                await fetch('/clear_history', { method: 'POST' });
                loadHistory();
                showNotification('История очищена');
            } catch (error) {
                console.error('Ошибка при очистке истории:', error);
                showNotification('Ошибка при очистке истории', 'error');
            }
        }
    });

    refreshStatsBtn.addEventListener('click', loadStats);

    copyBtn.addEventListener('click', function() {
        navigator.clipboard.writeText(jokeText.textContent)
            .then(() => showNotification('Шутка скопирована в буфер обмена!'))
            .catch(err => console.error('Ошибка при копировании:', err));
    });

    shareBtn.addEventListener('click', function() {
        if (navigator.share) {
            navigator.share({
                title: 'Случайная шутка',
                text: jokeText.textContent,
                url: window.location.href
            });
        } else {
            showNotification('Нажмите Ctrl+C чтобы скопировать шутку');
        }
    });


    speakBtn.addEventListener('click', function() {
        speakJoke(jokeText.textContent);
    });


    // Загрузить первую шутку при загрузке страницы
    fetchJoke();

    // Добавить стили для новых элементов
    const style = document.createElement('style');
    style.textContent = `
        .empty-history {
            text-align: center;
            padding: 2rem;
            color: #718096;
            font-style: italic;
        }
        
        
        .history-copy, .history-favorite {
            background: none;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 0.25rem 0.5rem;
            cursor: pointer;
            color: #718096;
        }
        
        .history-copy:hover, .history-favorite:hover {
            background: #f7fafc;
        }
        
        .stat-details {
            margin-top: 1rem;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .stat-row:last-child {
            border-bottom: none;
        }
        
        .stat-number {
            font-weight: bold;
            color: #667eea;
        }
        
        .recent-jokes {
            margin-top: 1rem;
        }
        
        .recent-joke {
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #48bb78;
        }
        
        .recent-category {
            display: block;
            font-size: 0.8rem;
            color: #718096;
            margin-bottom: 0.25rem;
        }
        
        .recent-text {
            font-size: 0.9rem;
            color: #2d3748;
        }
        
        .help-content {
            padding: 1rem;
        }
        
        .help-content ul {
            padding-left: 1.5rem;
            margin: 1rem 0;
        }
        
        .help-content li {
            margin-bottom: 0.5rem;
        }
    `;
    document.head.appendChild(style);
});