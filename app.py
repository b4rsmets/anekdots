from flask import Flask, render_template, request, jsonify, session
import pyjokes
import random
from datetime import datetime
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Категории шуток с русскими названиями
JOKE_CATEGORIES = [
    {'value': 'all', 'label': 'Все'},
    {'value': 'neutral', 'label': 'Нейтральные'},
    {'value': 'chuck', 'label': 'Чак Норрис'}
]

LANGUAGES = [
    {'value': 'en', 'label': '🇺🇸 Английский'},
    {'value': 'ru', 'label': '🇷🇺 Русский'}
]


class JokeGenerator:
    def __init__(self):
        self.joke_history = []
        self.joke_stats = {
            'ru': {'total': 0, 'by_category': {}},
            'en': {'total': 0, 'by_category': {}}
        }

    def get_category_label(self, category_value):
        """Получить русское название категории"""
        for cat in JOKE_CATEGORIES:
            if cat['value'] == category_value:
                return cat['label']
        return category_value

    def get_language_label(self, lang_value):
        """Получить русское название языка"""
        for lang in LANGUAGES:
            if lang['value'] == lang_value:
                return lang['label']
        return lang_value

    def get_joke(self, category='all', language='ru'):
        """Генерация шутки с указанной категорией и языком"""
        try:
            # Если выбрана категория 'all', берем случайную из доступных
            if category == 'all':
                available_cats = ['neutral', 'chuck']
                category = random.choice(available_cats)

            joke = pyjokes.get_joke(language=language, category=category)

            joke_data = {
                'text': joke,
                'category': category,
                'category_label': self.get_category_label(category),
                'language': language,
                'language_label': self.get_language_label(language),
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'date': datetime.now().strftime('%d.%m.%Y'),
                'id': len(self.joke_history) + 1
            }

            # Обновляем статистику
            self.joke_stats[language]['total'] = self.joke_stats[language].get('total', 0) + 1
            self.joke_stats[language]['by_category'][category] = \
                self.joke_stats[language]['by_category'].get(category, 0) + 1

            self.joke_history.append(joke_data)
            # Ограничиваем историю последними 100 шутками
            if len(self.joke_history) > 100:
                self.joke_history = self.joke_history[-100:]

            return joke_data
        except Exception as e:
            return {
                'text': f'Произошла ошибка: {str(e)}',
                'category': 'error',
                'category_label': 'Ошибка',
                'language': language,
                'language_label': self.get_language_label(language),
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'date': datetime.now().strftime('%d.%m.%Y'),
                'id': len(self.joke_history) + 1
            }

    def get_history(self):
        """Получение истории шуток"""
        return self.joke_history[::-1]  # Новые сначала

    def clear_history(self):
        """Очистка истории"""
        self.joke_history = []
        self.joke_stats = {'ru': {'total': 0, 'by_category': {}}, 'en': {'total': 0, 'by_category': {}}}

    def get_stats(self):
        """Получение статистики"""
        return self.joke_stats


# Инициализация генератора
joke_gen = JokeGenerator()


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html',
                           categories=JOKE_CATEGORIES,
                           languages=LANGUAGES,
                           current_category='all',
                           current_language='ru')


@app.route('/get_joke', methods=['GET', 'POST'])
def get_joke():
    """API endpoint для получения шутки"""
    if request.method == 'POST':
        data = request.get_json()
        category = data.get('category', 'all')
        language = data.get('language', 'ru')  # По умолчанию русский
    else:
        category = request.args.get('category', 'all')
        language = request.args.get('language', 'ru')

    joke = joke_gen.get_joke(category, language)
    return jsonify(joke)


@app.route('/history')
def history():
    """Получение истории шуток"""
    return jsonify(joke_gen.get_history())


@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Очистка истории"""
    joke_gen.clear_history()
    return jsonify({'status': 'success', 'message': 'История очищена'})


@app.route('/stats')
def stats():
    """Статистика по шуткам"""
    stats_data = joke_gen.get_stats()
    history_data = joke_gen.get_history()

    result = {
        'total': sum(stats['total'] for stats in stats_data.values()),
        'by_language': {},
        'by_category': {},
        'last_5_jokes': history_data[:5] if history_data else []
    }

    # Статистика по языкам
    for lang, data in stats_data.items():
        lang_label = joke_gen.get_language_label(lang)
        result['by_language'][lang_label] = {
            'total': data['total'],
            'categories': {joke_gen.get_category_label(k): v for k, v in data['by_category'].items()}
        }

    # Общая статистика по категориям
    all_categories = {}
    for lang_data in stats_data.values():
        for cat, count in lang_data['by_category'].items():
            cat_label = joke_gen.get_category_label(cat)
            all_categories[cat_label] = all_categories.get(cat_label, 0) + count

    result['by_category'] = all_categories

    return jsonify(result)


@app.route('/categories_info')
def categories_info():
    """Информация о категориях"""
    info = {
        'all': 'Смешанные шутки из всех категорий',
        'neutral': 'Нейтральные шутки без обидного юмора',
        'chuck': 'Шутки про Чака Норриса'
    }
    return jsonify(info)


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    print("=" * 50)
    print("Генератор шуток запущен!")
    print(f"Доступен по адресу: http://{host}:{port}")
    print("Поддерживаемые языки: русский, английский")
    print("=" * 50)

    app.run(host=host, port=port, debug=debug)