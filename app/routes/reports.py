"""API маршруты для управления отчетами"""
from flask import request, jsonify
from app.routes import reports_bp
from app.models import db, Report, CouncilMember, Event, Project
from datetime import datetime


@reports_bp.route('/', methods=['GET'])
def get_reports():
    """Получить список всех отчетов"""
    # Фильтры
    report_type = request.args.get('report_type')
    status = request.args.get('status')

    query = Report.query

    if report_type:
        query = query.filter_by(report_type=report_type)
    if status:
        query = query.filter_by(status=status)

    reports = query.order_by(Report.period_end.desc()).all()
    return jsonify([report.to_dict() for report in reports])


@reports_bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """Получить информацию о конкретном отчете"""
    report = Report.query.get_or_404(report_id)
    return jsonify(report.to_dict())


@reports_bp.route('/', methods=['POST'])
def create_report():
    """Создать новый отчет"""
    data = request.get_json()

    try:
        period_start = datetime.strptime(data['period_start'], '%Y-%m-%d').date()
        period_end = datetime.strptime(data['period_end'], '%Y-%m-%d').date()

        report = Report(
            title=data['title'],
            report_type=data.get('report_type'),
            period_start=period_start,
            period_end=period_end,
            total_members=data.get('total_members'),
            new_members=data.get('new_members'),
            active_members=data.get('active_members'),
            total_events=data.get('total_events'),
            events_held=data.get('events_held'),
            total_participants=data.get('total_participants'),
            total_projects=data.get('total_projects'),
            active_projects=data.get('active_projects'),
            completed_projects=data.get('completed_projects'),
            total_budget=data.get('total_budget'),
            budget_spent=data.get('budget_spent'),
            budget_efficiency=data.get('budget_efficiency'),
            summary=data.get('summary'),
            achievements=data.get('achievements'),
            challenges=data.get('challenges'),
            recommendations=data.get('recommendations'),
            author_id=data.get('author_id'),
            status=data.get('status', 'draft'),
            document_id=data.get('document_id')
        )

        db.session.add(report)
        db.session.commit()

        return jsonify(report.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/<int:report_id>', methods=['PUT'])
def update_report(report_id):
    """Обновить информацию об отчете"""
    report = Report.query.get_or_404(report_id)
    data = request.get_json()

    try:
        if 'title' in data:
            report.title = data['title']
        if 'report_type' in data:
            report.report_type = data['report_type']
        if 'period_start' in data:
            report.period_start = datetime.strptime(data['period_start'], '%Y-%m-%d').date()
        if 'period_end' in data:
            report.period_end = datetime.strptime(data['period_end'], '%Y-%m-%d').date()
        if 'total_members' in data:
            report.total_members = data['total_members']
        if 'new_members' in data:
            report.new_members = data['new_members']
        if 'active_members' in data:
            report.active_members = data['active_members']
        if 'total_events' in data:
            report.total_events = data['total_events']
        if 'events_held' in data:
            report.events_held = data['events_held']
        if 'total_participants' in data:
            report.total_participants = data['total_participants']
        if 'total_projects' in data:
            report.total_projects = data['total_projects']
        if 'active_projects' in data:
            report.active_projects = data['active_projects']
        if 'completed_projects' in data:
            report.completed_projects = data['completed_projects']
        if 'total_budget' in data:
            report.total_budget = data['total_budget']
        if 'budget_spent' in data:
            report.budget_spent = data['budget_spent']
        if 'budget_efficiency' in data:
            report.budget_efficiency = data['budget_efficiency']
        if 'summary' in data:
            report.summary = data['summary']
        if 'achievements' in data:
            report.achievements = data['achievements']
        if 'challenges' in data:
            report.challenges = data['challenges']
        if 'recommendations' in data:
            report.recommendations = data['recommendations']
        if 'author_id' in data:
            report.author_id = data['author_id']
        if 'status' in data:
            report.status = data['status']
            if data['status'] == 'submitted':
                report.submitted_at = datetime.utcnow()
            elif data['status'] == 'approved':
                report.approved_at = datetime.utcnow()
        if 'document_id' in data:
            report.document_id = data['document_id']

        db.session.commit()
        return jsonify(report.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Удалить отчет"""
    report = Report.query.get_or_404(report_id)

    try:
        db.session.delete(report)
        db.session.commit()
        return jsonify({'message': 'Report deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/generate', methods=['POST'])
def generate_report():
    """Автоматически сгенерировать отчет за период"""
    data = request.get_json()

    try:
        period_start = datetime.strptime(data['period_start'], '%Y-%m-%d').date()
        period_end = datetime.strptime(data['period_end'], '%Y-%m-%d').date()

        # Подсчет статистики
        total_members = CouncilMember.query.count()
        active_members = CouncilMember.query.filter_by(status='active').count()
        new_members = CouncilMember.query.filter(
            CouncilMember.join_date >= period_start,
            CouncilMember.join_date <= period_end
        ).count()

        total_events = Event.query.filter(
            Event.start_datetime >= datetime.combine(period_start, datetime.min.time()),
            Event.start_datetime <= datetime.combine(period_end, datetime.max.time())
        ).count()

        events_held = Event.query.filter(
            Event.start_datetime >= datetime.combine(period_start, datetime.min.time()),
            Event.start_datetime <= datetime.combine(period_end, datetime.max.time()),
            Event.status == 'completed'
        ).count()

        total_projects = Project.query.filter(
            Project.start_date <= period_end
        ).count()

        active_projects = Project.query.filter(
            Project.start_date <= period_end,
            Project.status == 'active'
        ).count()

        completed_projects = Project.query.filter(
            Project.end_date >= period_start,
            Project.end_date <= period_end,
            Project.status == 'completed'
        ).count()

        # Финансовая статистика
        projects = Project.query.filter(
            Project.start_date <= period_end
        ).all()

        total_budget = sum(p.budget for p in projects if p.budget)
        budget_spent = sum(p.budget_spent for p in projects if p.budget_spent)

        # Создание отчета
        report = Report(
            title=data.get('title', f'Отчет за период {period_start} - {period_end}'),
            report_type=data.get('report_type', 'Автоматический'),
            period_start=period_start,
            period_end=period_end,
            total_members=total_members,
            new_members=new_members,
            active_members=active_members,
            total_events=total_events,
            events_held=events_held,
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            total_budget=total_budget,
            budget_spent=budget_spent,
            author_id=data.get('author_id'),
            status='draft'
        )

        db.session.add(report)
        db.session.commit()

        return jsonify(report.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
