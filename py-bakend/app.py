import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, create_refresh_token,
    get_jwt
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, supports_credentials=True)  

# Configuration
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///app.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'fallback-secret-key'),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
    PROPAGATE_EXCEPTIONS=True,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB upload limit
)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(','),
        "supports_credentials": True
    }
})

# Configure logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

# Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')

    def __init__(self, username=None, email=None, password=None, **kwargs):
        super(User, self).__init__(**kwargs)
        if username:
            self.username = username
        if email:
            self.email = email
        if password:
            self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    priority = db.Column(db.Integer, default=3)  # 1-5 priority scale
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }

# JWT Callbacks
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    # Here you would check if the token is revoked (e.g., in redis)
    return False

# Error Handlers
@app.errorhandler(400)
def handle_bad_request(error):
    return jsonify({
        'success': False,
        'error': 'bad_request',
        'message': str(error) or 'Invalid request parameters'
    }), 400

@app.errorhandler(401)
def handle_unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'unauthorized',
        'message': str(error) or 'Authentication required'
    }), 401

@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({
        'success': False,
        'error': 'not_found',
        'message': str(error) or 'Resource not found'
    }), 404

@app.errorhandler(500)
def handle_server_error(error):
    app.logger.error(f'Server error: {str(error)}')
    return jsonify({
        'success': False,
        'error': 'server_error',
        'message': 'An unexpected error occurred'
    }), 500

# Auth Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return handle_bad_request('Missing required fields')

    try:
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=user)
        refresh_token = create_refresh_token(identity=user)
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        if 'username' in str(e):
            return handle_bad_request('Username already exists')
        elif 'email' in str(e):
            return handle_bad_request('Email already exists')
        return handle_bad_request('Database integrity error')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Registration error: {str(e)}')
        return handle_server_error(e)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if 'email' not in data or 'password' not in data:
        return handle_bad_request('Email and password required')

    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return handle_unauthorized('Invalid credentials')

    if not user.is_active:
        return handle_unauthorized('Account disabled')

    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200

@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({
        'success': True,
        'access_token': new_token
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    # In production, you would add the token to a blocklist here
    return jsonify({'success': True}), 200

# Task Routes
@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    current_user = get_jwt_identity()
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    
    tasks = query.order_by(
        Task.priority.asc(),
        Task.due_date.asc()
    ).all()
    
    return jsonify({
        'success': True,
        'tasks': [task.to_dict() for task in tasks]
    }), 200

@app.route('/api/tasks', methods=['POST'])
@jwt_required()
def create_task():
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if 'title' not in data:
        return handle_bad_request('Title is required')
    
    try:
        task = Task(
            title=data['title'],
            description=data.get('description'),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 3),
            due_date=datetime.fromisoformat(data['due_date']) if 'due_date' in data else None,
            user_id=current_user.id
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        }), 201
    except ValueError as e:
        return handle_bad_request('Invalid date format')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Task creation error: {str(e)}')
        return handle_server_error(e)

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    current_user = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    
    if not task:
        return handle_not_found('Task not found')
    
    return jsonify({
        'success': True,
        'task': task.to_dict()
    }), 200

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    current_user = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    
    if not task:
        return handle_not_found('Task not found')
    
    data = request.get_json()
    
    try:
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'priority' in data:
            task.priority = data['priority']
        if 'due_date' in data:
            task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        }), 200
    except ValueError as e:
        return handle_bad_request('Invalid date format')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Task update error: {str(e)}')
        return handle_server_error(e)

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    current_user = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    
    if not task:
        return handle_not_found('Task not found')
    
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Task deletion error: {str(e)}')
        return handle_server_error(e)

# User Profile
@app.route('/api/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user = get_jwt_identity()
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200

# Health Check
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        app.logger.error(f'Health check failed: {str(e)}')
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

# Initialize database
def initialize_database():
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com'
            )
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Created admin user')

if __name__ == '__main__':
    initialize_database()
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )