from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Настройка для работы за прокси
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/onboarding.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max-limit

db = SQLAlchemy(app)

# Создаем папку uploads если её нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.String(50), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_surname = db.Column(db.String(100), nullable=False)
    emp_position = db.Column(db.String(100), nullable=False)
    user_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    checkin_at = db.Column(db.DateTime, default=datetime.utcnow)

# Обработка ошибок
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f"404 Error: {request.url}")
    return render_template('error.html', message="Страница не найдена. Проверьте URL и попробуйте снова."), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 Error: {str(error)}")
    db.session.rollback()
    return render_template('error.html', message="Внутренняя ошибка сервера. Попробуйте позже."), 500

# Маршруты
@app.route('/')
def root():
    app.logger.info(f"Root request received. Path: {request.path}")
    app.logger.info(f"Full URL: {request.url}")
    app.logger.info(f"Headers: {dict(request.headers)}")
    app.logger.info(f"Args: {dict(request.args)}")
    
    place_id = request.args.get('place_id')
    if place_id:
        return redirect(url_for('index', place_id=place_id))
    return render_template('error.html', message="Необходим параметр place_id в URL. Пример: /?place_id=your_place_id"), 400

@app.route('/onboarding/')
def index():
    app.logger.info(f"Request received. Path: {request.path}")
    app.logger.info(f"Full URL: {request.url}")
    app.logger.info(f"Headers: {dict(request.headers)}")
    app.logger.info(f"Args: {dict(request.args)}")
    
    place_id = request.args.get('place_id')
    app.logger.info(f'Accessing onboarding page with place_id: {place_id}')
    
    if not place_id:
        app.logger.warning('No place_id provided in request')
        return render_template('error.html', message="Необходим параметр place_id в URL. Пример: /onboarding/?place_id=your_place_id"), 400
    
    return render_template('index.html', place_id=place_id)

# API endpoints
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
            filename = secure_filename(f"{place_id}_{user_surname}_{user_name}.jpg")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            app.logger.info(f'Saved image to {filepath}')

            new_user = User(
                place_id=place_id,
                user_name=user_name,
                user_surname=user_surname,
                emp_position=emp_position,
                user_image=filename,
                checkin_at=datetime.utcnow()
            )
            
            db.session.add(new_user)
            db.session.commit()
            app.logger.info(f'Successfully saved user data to database')

            return jsonify({
                'status': 'success',
                'message': 'Данные успешно сохранены',
                'data': {
                    'id': new_user.id,
                    'place_id': new_user.place_id,
                    'user_name': new_user.user_name,
                    'user_surname': new_user.user_surname,
                    'emp_position': new_user.emp_position,
                    'user_image': new_user.user_image,
                    'created_at': new_user.created_at.isoformat(),
                    'checkin_at': new_user.checkin_at.isoformat()
                }
            }), 200

    except Exception as e:
        app.logger.error(f'Error processing submission: {str(e)}')
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/onboarding/api/users/<place_id>')
def get_users(place_id):
    app.logger.info(f"Getting users for place_id: {place_id}")
    users = User.query.filter_by(place_id=place_id).all()
    return jsonify([{
        'id': user.id,
        'place_id': user.place_id,
        'user_name': user.user_name,
        'user_surname': user.user_surname,
        'emp_position': user.emp_position,
        'user_image': user.user_image,
        'created_at': user.created_at.isoformat(),
        'checkin_at': user.checkin_at.isoformat()
    } for user in users])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001)
