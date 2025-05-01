from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Task, db

# CREATE
@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        task = Task(
            title=data['title'],
            user_id=current_user
        )
        db.session.add(task)
        db.session.commit()
        
        return jsonify({'success': True, 'task': task.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# READ (All)
@app.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        current_user = get_jwt_identity()
        tasks = Task.query.filter_by(user_id=current_user).all()
        return jsonify({
            'success': True,
            'tasks': [task.to_dict() for task in tasks]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# READ (Single)
@app.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    try:
        current_user = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=current_user).first_or_404()
        return jsonify({'success': True, 'task': task.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

# UPDATE
@app.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    try:
        current_user = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=current_user).first_or_404()
        
        data = request.get_json()
        task.title = data.get('title', task.title)
        task.done = data.get('done', task.done)
        
        db.session.commit()
        return jsonify({'success': True, 'task': task.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# DELETE
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    try:
        current_user = get_jwt_identity()
        task = Task.query.filter_by(id=task_id, user_id=current_user).first_or_404()
        
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400