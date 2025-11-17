"""API маршруты для управления мероприятиями"""
from flask import request, jsonify
from app.routes import events_bp
from app.models import db, Event, CouncilMember
from datetime import datetime


@events_bp.route('/', methods=['GET'])
def get_events():
    """Получить список всех мероприятий"""
    # Фильтры
    status = request.args.get('status')
    event_type = request.args.get('event_type')
    category = request.args.get('category')
    upcoming = request.args.get('upcoming', 'false').lower() == 'true'

    query = Event.query

    if status:
        query = query.filter_by(status=status)
    if event_type:
        query = query.filter_by(event_type=event_type)
    if category:
        query = query.filter_by(category=category)
    if upcoming:
        query = query.filter(Event.start_datetime > datetime.utcnow(), Event.status == 'planned')

    events = query.order_by(Event.start_datetime.desc()).all()
    return jsonify([event.to_dict() for event in events])


@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Получить информацию о конкретном мероприятии"""
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict())


@events_bp.route('/', methods=['POST'])
def create_event():
    """Создать новое мероприятие"""
    data = request.get_json()

    try:
        start_datetime = datetime.fromisoformat(data['start_datetime'])
        end_datetime = datetime.fromisoformat(data['end_datetime']) if data.get('end_datetime') else None

        event = Event(
            title=data['title'],
            description=data.get('description'),
            event_type=data.get('event_type'),
            category=data.get('category'),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location=data.get('location'),
            address=data.get('address'),
            online_link=data.get('online_link'),
            status=data.get('status', 'planned'),
            organizer_id=data.get('organizer_id'),
            max_participants=data.get('max_participants'),
            budget=data.get('budget'),
            outcome=data.get('outcome'),
            materials_url=data.get('materials_url'),
            photos_url=data.get('photos_url')
        )

        db.session.add(event)
        db.session.commit()

        return jsonify(event.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@events_bp.route('/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """Обновить информацию о мероприятии"""
    event = Event.query.get_or_404(event_id)
    data = request.get_json()

    try:
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'event_type' in data:
            event.event_type = data['event_type']
        if 'category' in data:
            event.category = data['category']
        if 'start_datetime' in data:
            event.start_datetime = datetime.fromisoformat(data['start_datetime'])
        if 'end_datetime' in data:
            event.end_datetime = datetime.fromisoformat(data['end_datetime'])
        if 'location' in data:
            event.location = data['location']
        if 'address' in data:
            event.address = data['address']
        if 'online_link' in data:
            event.online_link = data['online_link']
        if 'status' in data:
            event.status = data['status']
        if 'organizer_id' in data:
            event.organizer_id = data['organizer_id']
        if 'max_participants' in data:
            event.max_participants = data['max_participants']
        if 'budget' in data:
            event.budget = data['budget']
        if 'outcome' in data:
            event.outcome = data['outcome']
        if 'attendance_count' in data:
            event.attendance_count = data['attendance_count']
        if 'materials_url' in data:
            event.materials_url = data['materials_url']
        if 'photos_url' in data:
            event.photos_url = data['photos_url']

        db.session.commit()
        return jsonify(event.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@events_bp.route('/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Удалить мероприятие"""
    event = Event.query.get_or_404(event_id)

    try:
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@events_bp.route('/<int:event_id>/participants', methods=['POST'])
def add_participant(event_id):
    """Добавить участника к мероприятию"""
    event = Event.query.get_or_404(event_id)
    data = request.get_json()

    try:
        member = CouncilMember.query.get_or_404(data['member_id'])
        if member not in event.participants:
            event.participants.append(member)
            db.session.commit()
            return jsonify({'message': 'Participant added successfully'}), 200
        else:
            return jsonify({'message': 'Member is already a participant'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@events_bp.route('/stats', methods=['GET'])
def get_stats():
    """Получить статистику по мероприятиям"""
    total = Event.query.count()
    upcoming = Event.query.filter(Event.start_datetime > datetime.utcnow(), Event.status == 'planned').count()
    completed = Event.query.filter_by(status='completed').count()
    ongoing = Event.query.filter_by(status='ongoing').count()

    return jsonify({
        'total_events': total,
        'upcoming_events': upcoming,
        'completed_events': completed,
        'ongoing_events': ongoing
    })
