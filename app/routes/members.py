"""API маршруты для управления членами совета"""
from flask import request, jsonify
from app.routes import members_bp
from app.models import db, CouncilMember
from datetime import datetime


@members_bp.route('/', methods=['GET'])
def get_members():
    """Получить список всех членов совета"""
    # Фильтры
    status = request.args.get('status')
    council_type = request.args.get('council_type')
    position = request.args.get('position')

    query = CouncilMember.query

    if status:
        query = query.filter_by(status=status)
    if council_type:
        query = query.filter_by(council_type=council_type)
    if position:
        query = query.filter_by(position=position)

    members = query.order_by(CouncilMember.last_name).all()
    return jsonify([member.to_dict() for member in members])


@members_bp.route('/<int:member_id>', methods=['GET'])
def get_member(member_id):
    """Получить информацию о конкретном члене совета"""
    member = CouncilMember.query.get_or_404(member_id)
    return jsonify(member.to_dict())


@members_bp.route('/', methods=['POST'])
def create_member():
    """Добавить нового члена совета"""
    data = request.get_json()

    try:
        # Преобразование строк дат в объекты date
        birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        join_date = datetime.strptime(data.get('join_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()

        member = CouncilMember(
            last_name=data['last_name'],
            first_name=data['first_name'],
            middle_name=data.get('middle_name'),
            birth_date=birth_date,
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            education=data.get('education'),
            occupation=data.get('occupation'),
            school_university=data.get('school_university'),
            position=data.get('position'),
            council_type=data.get('council_type'),
            join_date=join_date,
            status=data.get('status', 'active'),
            interests=data.get('interests'),
            skills=data.get('skills'),
            achievements=data.get('achievements'),
            photo_url=data.get('photo_url')
        )

        db.session.add(member)
        db.session.commit()

        return jsonify(member.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@members_bp.route('/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    """Обновить информацию о члене совета"""
    member = CouncilMember.query.get_or_404(member_id)
    data = request.get_json()

    try:
        # Обновление полей
        if 'last_name' in data:
            member.last_name = data['last_name']
        if 'first_name' in data:
            member.first_name = data['first_name']
        if 'middle_name' in data:
            member.middle_name = data['middle_name']
        if 'birth_date' in data:
            member.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if 'email' in data:
            member.email = data['email']
        if 'phone' in data:
            member.phone = data['phone']
        if 'address' in data:
            member.address = data['address']
        if 'education' in data:
            member.education = data['education']
        if 'occupation' in data:
            member.occupation = data['occupation']
        if 'school_university' in data:
            member.school_university = data['school_university']
        if 'position' in data:
            member.position = data['position']
        if 'council_type' in data:
            member.council_type = data['council_type']
        if 'status' in data:
            member.status = data['status']
        if 'interests' in data:
            member.interests = data['interests']
        if 'skills' in data:
            member.skills = data['skills']
        if 'achievements' in data:
            member.achievements = data['achievements']
        if 'photo_url' in data:
            member.photo_url = data['photo_url']

        db.session.commit()
        return jsonify(member.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@members_bp.route('/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    """Удалить члена совета"""
    member = CouncilMember.query.get_or_404(member_id)

    try:
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': 'Member deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@members_bp.route('/stats', methods=['GET'])
def get_stats():
    """Получить статистику по членам совета"""
    total = CouncilMember.query.count()
    active = CouncilMember.query.filter_by(status='active').count()
    children = CouncilMember.query.filter_by(council_type='Детский').count()
    youth = CouncilMember.query.filter_by(council_type='Молодёжный').count()

    return jsonify({
        'total_members': total,
        'active_members': active,
        'children_council': children,
        'youth_council': youth,
        'inactive_members': total - active
    })
