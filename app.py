from flask import Flask, render_template, request, jsonify, session
import pyjokes
import random
from datetime import datetime
import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator  # Библиотека для перевода[citation:1]

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

# Поддерживаемые языки для интерфейса и перевода[citation:1]
LANGUAGES = [
    {'value': 'en', 'label': '🇺🇸 Английский'},
    {'value': 'ru', 'label': '🇷🇺 Русский'},
    {'value': 'fr', 'label': '🇫🇷 Французский'},
    {'value': 'de', 'label': '🇩🇪 Немецкий'},
    {'value': 'it', 'label': '🇮🇹 Итальянский'}
]


class JokeGenerator:
    def __init__(self):
        self.joke_history = []
        self.joke_stats = {}

        # Инициализируем статистику для всех языков
        for lang in [l['value'] for l in LANGUAGES]:
            self.joke_stats[lang] = {'total': 0, 'by_category': {}}

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

    def translate_text(self, text, target_lang='ru'):
        """Перевод текста на указанный язык[citation:1]"""
        try:
            if target_lang == 'en':
                return text  # Английский - исходный язык

            # Используем GoogleTranslator для перевода[citation:1]
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            return translated
        except Exception as e:
            print(f"Ошибка перевода: {e}")
            return text  # Возвращаем оригинал в случае ошибки

    def get_joke(self, category='all', language='ru'):
        """Генерация шутки: всегда на английском, с переводом если нужно"""
        try:
            # Всегда генерируем шутку на английском (исходный язык pyjokes)[citation:1]
            if category == 'all':
                available_cats = ['neutral', 'chuck']
                category = random.choice(available_cats)

            # Получаем шутку на английском
            english_joke = pyjokes.get_joke(language='en', category=category)

            # Переводим шутку, если выбран не английский язык[citation:1]
            if language != 'en':
                final_joke = self.translate_text(english_joke, language)
            else:
                final_joke = english_joke

            joke_data = {
                'text': final_joke,
                'original_text': english_joke,  # Сохраняем оригинальную английскую шутку
                'category': category,
                'category_label': self.get_category_label(category),
                'language': language,
                'language_label': self.get_language_label(language),
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'date': datetime.now().strftime('%d.%m.%Y'),
                'id': len(self.joke_history) + 1
            }

            # Обновляем статистику
            if language not in self.joke_stats:
                self.joke_stats[language] = {'total': 0, 'by_category': {}}

            self.joke_stats[language]['total'] += 1
            self.joke_stats[language]['by_category'][category] = \
                self.joke_stats[language]['by_category'].get(category, 0) + 1

            self.joke_history.append(joke_data)
            # Ограничиваем историю последними 100 шутками
            if len(self.joke_history) > 100:
                self.joke_history = self.joke_history[-100:]

            return joke_data
        except Exception as e:
            error_text = f'Произошла ошибка: {str(e)}'
            return {
                'text': error_text,
                'original_text': error_text,
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
        for lang in [l['value'] for l in LANGUAGES]:
            self.joke_stats[lang] = {'total': 0, 'by_category': {}}

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
        'total': sum(stats.get('total', 0) for stats in stats_data.values()),
        'by_language': {},
        'by_category': {},
        'last_5_jokes': history_data[:5] if history_data else []
    }

    # Статистика по языкам
    for lang, data in stats_data.items():
        lang_label = joke_gen.get_language_label(lang)
        result['by_language'][lang_label] = {
            'total': data.get('total', 0),
            'categories': {joke_gen.get_category_label(k): v for k, v in data.get('by_category', {}).items()}
        }

    # Общая статистика по категориям
    all_categories = {}
    for lang_data in stats_data.values():
        for cat, count in lang_data.get('by_category', {}).items():
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
        'chuck': 'Шутки про Чака Норриса',
        'twister': 'Английские скороговорки (переводятся)'
    }
    return jsonify(info)


@app.route('/supported_languages')
def supported_languages():
    """Получение списка поддерживаемых языков перевода[citation:1]"""
    try:
        langs = GoogleTranslator().get_supported_languages(as_dict=True)
        return jsonify({'languages': langs})
    except:
        # Возвращаем ручной список в случае ошибки
        basic_langs = {'en': 'English', 'ru': 'Russian', 'es': 'Spanish',
                       'fr': 'French', 'de': 'German', 'it': 'Italian'}
        return jsonify({'languages': basic_langs})


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    print("=" * 50)
    print("Генератор шуток с переводом запущен!")
    print(f"Доступен по адресу: http://{host}:{port}")
    print("Поддерживаемые языки: " + ", ".join([lang['label'] for lang in LANGUAGES]))
    print("Режим работы: Английские шутки → Перевод на выбранный язык")
    print("=" * 50)

    app.run(host=host, port=port, debug=debug)