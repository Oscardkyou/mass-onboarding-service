from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# Конфигурация
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max-limit

# Создаем папку для загрузок если её нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def root():
    place_id = request.args.get('place_id')
    if place_id:
        return redirect(f'/onboarding/?place_id={place_id}')
    return render_template('error.html', message="Необходим параметр place_id в URL")

@app.route('/onboarding/')
def index():
    place_id = request.args.get('place_id')
    app.logger.info(f'Accessing onboarding page with place_id: {place_id}')
    
    if not place_id:
        app.logger.warning('No place_id provided in request')
        return render_template('error.html', message="Необходим параметр place_id в URL. Пример: /onboarding/?place_id=your_place_id"), 400
    
    return render_template('index.html', place_id=place_id)

@app.route('/onboarding/api/submit', methods=['POST'])
def submit():
    app.logger.info('Received submission request')
    try:
        if 'user_image' not in request.files:
            app.logger.error('No user_image in request')
            return jsonify({'status': 'error', 'message': 'Фото не найдено'}), 400

        user_name = request.form.get('user_name')
        user_surname = request.form.get('user_surname')
        emp_position = request.form.get('emp_position')
        place_id = request.form.get('place_id')

        app.logger.info(f'Processing submission for {user_name} {user_surname} at {place_id}')

        if not all([user_name, user_surname, emp_position, place_id]):
            app.logger.error('Missing required fields in submission')
            return jsonify({'status': 'error', 'message': 'Все поля обязательны для заполнения'}), 400

        file = request.files['user_image']
        if file.filename == '':
            app.logger.error('Empty filename in user_image')
            return jsonify({'status': 'error', 'message': 'Файл не выбран'}), 400

        if file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = secure_filename(f"{place_id}_{user_surname}_{user_name}_{timestamp}.jpg")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            app.logger.info(f'Saved image to {filepath}')

            return jsonify({
                'status': 'success',
                'message': 'Данные успешно сохранены',
                'data': {
                    'place_id': place_id,
                    'user_name': user_name,
                    'user_surname': user_surname,
                    'emp_position': emp_position,
                    'image_path': filename,
                    'timestamp': timestamp
                }
            })

    except Exception as e:
        app.logger.error(f'Error processing submission: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
