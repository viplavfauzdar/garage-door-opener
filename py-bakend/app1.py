from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource, reqparse
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
api = Api(app)

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    done = db.Column(db.Boolean, default=False)

# API Resource
task_parser = reqparse.RequestParser()
task_parser.add_argument('title', type=str, required=True)
task_parser.add_argument('done', type=bool, default=False)

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

api.add_resource(TaskResource, '/tasks', '/tasks/<int:task_id>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
