import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import base64
import logging

app = Flask(__name__)
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

@app.route('/')
def index():
    place_id = request.args.get('place_id')
    app.logger.info(f"Received request with place_id: {place_id}")
    if not place_id:
        app.logger.warning("No place_id provided")
        return render_template('error.html', message="Необходим параметр place_id в URL. Пример: /?place_id=your_place_id"), 400
    app.logger.info(f"Rendering template for place_id: {place_id}")
    return render_template('index.html', place_id=place_id)

@app.route('/api/submit', methods=['POST'])
def submit():
    try:
        data = request.form
        place_id = data.get('place_id')
        user_name = data.get('user_name')
        user_surname = data.get('user_surname')
        emp_position = data.get('emp_position')

        if not all([place_id, user_name, user_surname, emp_position]):
            app.logger.warning("Not all fields are provided")
            return jsonify({'error': 'All fields are required'}), 400

        image_file = request.files.get('user_image')
        image_path = None

        if image_file:
            filename = secure_filename(f"{place_id}_{datetime.utcnow().timestamp()}.jpg")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_path = filepath
            app.logger.info(f"Image saved to {image_path}")

        user = User(
            place_id=place_id,
            user_name=user_name,
            user_surname=user_surname,
            emp_position=emp_position,
            user_image=image_path
        )

        db.session.add(user)
        db.session.commit()
        app.logger.info(f"User created with place_id: {place_id}")

        return jsonify({
            'status': 'success',
            'message': 'Data saved successfully'
        })

    except Exception as e:
        app.logger.error(f"Error occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<place_id>')
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
