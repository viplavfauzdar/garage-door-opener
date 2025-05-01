from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS for all routes and origins
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Add this import 
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

# Configure Database (SQLite example)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here'  # Change this in production!

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

jwt = JWTManager(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Task Model (from previous example)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create tables (run once)
with app.app_context():
    db.drop_all()
    db.create_all()

# Auth Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "User already exists"}), 400

    user = User(username=data['username'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

# Protected Route Example
#@app.route('/tasks', methods=['GET'])
#@jwt_required()
#def get_tasks():
#    current_user_id = get_jwt_identity()
#    tasks = Task.query.filter_by(user_id=current_user_id).all()
#    return jsonify([{"id": t.id, "title": t.title} for t in tasks]), 200

@jwt_required()
class TaskResource(Resource):
    def get(self, task_id=None):
        if task_id:
            task = Task.query.get_or_404(task_id)
            return {"id": task.id, "title": task.title, "done": task.done}
        else:
            tasks = Task.query.all()
            return [{"id": t.id, "title": t.title, "done": t.done} for t in tasks]

    def post(self):
        args = task_parser.parse_args()
        task = Task(title=args['title'], done=args['done'])
        db.session.add(task)
        db.session.commit()
        return {"message": "Task created", "id": task.id}, 201

    def put(self, task_id):
        task = Task.query.get_or_404(task_id)
        args = task_parser.parse_args()
        task.title = args['title']
        task.done = args['done']
        db.session.commit()
        return {"message": "Task updated"}

    def delete(self, task_id):
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return {"message": "Task deleted"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
