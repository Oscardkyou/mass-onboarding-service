import os
from flask import Flask, request, jsonify, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import base64
import logging

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Настраиваем базовый путь
app.config['APPLICATION_ROOT'] = '/onboarding'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///onboarding.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
db = SQLAlchemy(app)

# load the uploads folder if it does not exist
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

@app.route('/onboarding/')
def index():
    place_id = request.args.get('place_id')
    app.logger.info(f"Received request with place_id: {place_id}")
    if not place_id:
        app.logger.warning("No place_id provided")
        return render_template('error.html', message="Необходим параметр place_id в URL. Пример: /?place_id=your_place_id"), 400
    app.logger.info(f"Rendering template for place_id: {place_id}")
    return render_template('index.html', place_id=place_id)

@app.route('/onboarding/api/submit', methods=['POST'])
def submit():
    app.logger.info("Received form submission")
    try:
        place_id = request.form.get('place_id')
        user_name = request.form.get('user_name')
        user_surname = request.form.get('user_surname')
        emp_position = request.form.get('emp_position')
        user_image = request.files.get('user_image')

        app.logger.info(f"Processing submission for place_id: {place_id}")

        if not all([place_id, user_name, user_surname, emp_position, user_image]):
            app.logger.warning("Missing required fields")
            return jsonify({'error': 'Все поля обязательны для заполнения'}), 400

        # Save the image
        filename = secure_filename(f"{place_id}_{user_surname}_{user_name}.jpg")
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        user_image.save(image_path)
        app.logger.info(f"Saved image to: {image_path}")

        # Create new user
        new_user = User(
            place_id=place_id,
            user_name=user_name,
            user_surname=user_surname,
            emp_position=emp_position,
            user_image=filename
        )
        db.session.add(new_user)
        db.session.commit()
        app.logger.info("Successfully saved user to database")

        return jsonify({'message': 'Данные успешно сохранены'}), 200

    except Exception as e:
        app.logger.error(f"Error processing submission: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/onboarding/api/users/<place_id>')
def get_users(place_id):
    app.logger.info(f"Received request for users with place_id: {place_id}")
    users = User.query.filter_by(place_id=place_id).all()
    app.logger.info(f"Found {len(users)} users with place_id: {place_id}")
    return jsonify([{
        'user_name': user.user_name,
        'user_surname': user.user_surname,
        'emp_position': user.emp_position,
        'created_at': user.created_at.isoformat()
    } for user in users])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with app.app_context():
        db.create_all()
    app.debug = True
    app.run(host='0.0.0.0', port=5001)
