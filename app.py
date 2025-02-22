from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import logging

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///onboarding.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

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

@app.route('/')
def root():
    place_id = request.args.get('place_id')
    if place_id:
        return redirect(url_for('index', place_id=place_id))
    return render_template('error.html', message="Необходим параметр place_id в URL. Пример: /?place_id=your_place_id"), 400

@app.route('/onboarding')
@app.route('/onboarding/')
def index():
    place_id = request.args.get('place_id')
    if not place_id:
        return render_template('error.html', message="Необходим параметр place_id в URL. Пример: /onboarding/?place_id=your_place_id"), 400
    return render_template('index.html', place_id=place_id)

@app.route('/api/submit', methods=['POST'])
@app.route('/onboarding/api/submit', methods=['POST'])
def submit():
    try:
        place_id = request.form.get('place_id')
        user_name = request.form.get('user_name')
        user_surname = request.form.get('user_surname')
        emp_position = request.form.get('emp_position')
        user_image = request.files.get('user_image')

        if not all([place_id, user_name, user_surname, emp_position, user_image]):
            return jsonify({
                'status': 'error',
                'message': 'Все поля обязательны для заполнения'
            }), 400

        # Сохраняем изображение
        filename = secure_filename(f"{place_id}_{user_surname}_{user_name}.jpg")
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        user_image.save(image_path)

        # Создаем пользователя
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/users/<place_id>')
@app.route('/onboarding/api/users/<place_id>')
def get_users(place_id):
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
    logging.basicConfig(level=logging.INFO)
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001)
