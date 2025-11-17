"""API маршруты для управления проектами"""
from flask import request, jsonify
from app.routes import projects_bp
from app.models import db, Project, CouncilMember
from datetime import datetime


@projects_bp.route('/', methods=['GET'])
def get_projects():
    """Получить список всех проектов"""
    # Фильтры
    status = request.args.get('status')
    project_type = request.args.get('project_type')
    category = request.args.get('category')

    query = Project.query

    if status:
        query = query.filter_by(status=status)
    if project_type:
        query = query.filter_by(project_type=project_type)
    if category:
        query = query.filter_by(category=category)

    projects = query.order_by(Project.start_date.desc()).all()
    return jsonify([project.to_dict() for project in projects])


@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Получить информацию о конкретном проекте"""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())


@projects_bp.route('/', methods=['POST'])
def create_project():
    """Создать новый проект"""
    data = request.get_json()

    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None

        project = Project(
            title=data['title'],
            description=data.get('description'),
            project_type=data.get('project_type'),
            category=data.get('category'),
            start_date=start_date,
            end_date=end_date,
            planned_duration_months=data.get('planned_duration_months'),
            status=data.get('status', 'planning'),
            goals=data.get('goals'),
            tasks=data.get('tasks'),
            target_audience=data.get('target_audience'),
            budget=data.get('budget'),
            budget_spent=data.get('budget_spent', 0),
            funding_source=data.get('funding_source'),
            expected_results=data.get('expected_results'),
            actual_results=data.get('actual_results'),
            beneficiaries_count=data.get('beneficiaries_count'),
            progress_percentage=data.get('progress_percentage', 0),
            leader_id=data.get('leader_id'),
            documents_url=data.get('documents_url'),
            report_url=data.get('report_url')
        )

        db.session.add(project)
        db.session.commit()

        return jsonify(project.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Обновить информацию о проекте"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    try:
        if 'title' in data:
            project.title = data['title']
        if 'description' in data:
            project.description = data['description']
        if 'project_type' in data:
            project.project_type = data['project_type']
        if 'category' in data:
            project.category = data['category']
        if 'start_date' in data:
            project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            project.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'planned_duration_months' in data:
            project.planned_duration_months = data['planned_duration_months']
        if 'status' in data:
            project.status = data['status']
        if 'goals' in data:
            project.goals = data['goals']
        if 'tasks' in data:
            project.tasks = data['tasks']
        if 'target_audience' in data:
            project.target_audience = data['target_audience']
        if 'budget' in data:
            project.budget = data['budget']
        if 'budget_spent' in data:
            project.budget_spent = data['budget_spent']
        if 'funding_source' in data:
            project.funding_source = data['funding_source']
        if 'expected_results' in data:
            project.expected_results = data['expected_results']
        if 'actual_results' in data:
            project.actual_results = data['actual_results']
        if 'beneficiaries_count' in data:
            project.beneficiaries_count = data['beneficiaries_count']
        if 'progress_percentage' in data:
            project.progress_percentage = data['progress_percentage']
        if 'leader_id' in data:
            project.leader_id = data['leader_id']
        if 'documents_url' in data:
            project.documents_url = data['documents_url']
        if 'report_url' in data:
            project.report_url = data['report_url']

        db.session.commit()
        return jsonify(project.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Удалить проект"""
    project = Project.query.get_or_404(project_id)

    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({'message': 'Project deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/<int:project_id>/members', methods=['POST'])
def add_member(project_id):
    """Добавить участника к проекту"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    try:
        member = CouncilMember.query.get_or_404(data['member_id'])
        if member not in project.members:
            project.members.append(member)
            db.session.commit()
            return jsonify({'message': 'Member added successfully'}), 200
        else:
            return jsonify({'message': 'Member is already in the project'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/stats', methods=['GET'])
def get_stats():
    """Получить статистику по проектам"""
    total = Project.query.count()
    active = Project.query.filter_by(status='active').count()
    completed = Project.query.filter_by(status='completed').count()
    planning = Project.query.filter_by(status='planning').count()

    # Общий бюджет и затраты
    projects = Project.query.all()
    total_budget = sum(p.budget for p in projects if p.budget)
    total_spent = sum(p.budget_spent for p in projects if p.budget_spent)

    return jsonify({
        'total_projects': total,
        'active_projects': active,
        'completed_projects': completed,
        'planning_projects': planning,
        'total_budget': total_budget,
        'total_spent': total_spent
    })
