"""API маршруты для управления документами"""
from flask import request, jsonify
from app.routes import documents_bp
from app.models import db, Document
from datetime import datetime


@documents_bp.route('/', methods=['GET'])
def get_documents():
    """Получить список всех документов"""
    # Фильтры
    document_type = request.args.get('document_type')
    category = request.args.get('category')
    status = request.args.get('status')
    access_level = request.args.get('access_level')

    query = Document.query

    if document_type:
        query = query.filter_by(document_type=document_type)
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    if access_level:
        query = query.filter_by(access_level=access_level)

    documents = query.order_by(Document.upload_date.desc()).all()
    return jsonify([doc.to_dict() for doc in documents])


@documents_bp.route('/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Получить информацию о конкретном документе"""
    document = Document.query.get_or_404(document_id)
    return jsonify(document.to_dict())


@documents_bp.route('/', methods=['POST'])
def create_document():
    """Создать новый документ"""
    data = request.get_json()

    try:
        document_date = datetime.strptime(data['document_date'], '%Y-%m-%d').date() if data.get('document_date') else None

        document = Document(
            title=data['title'],
            description=data.get('description'),
            document_type=data.get('document_type'),
            category=data.get('category'),
            file_url=data.get('file_url'),
            file_name=data.get('file_name'),
            file_size=data.get('file_size'),
            file_format=data.get('file_format'),
            document_date=document_date,
            author_id=data.get('author_id'),
            project_id=data.get('project_id'),
            event_id=data.get('event_id'),
            status=data.get('status', 'draft'),
            access_level=data.get('access_level', 'public'),
            tags=data.get('tags'),
            version=data.get('version'),
            notes=data.get('notes')
        )

        db.session.add(document)
        db.session.commit()

        return jsonify(document.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@documents_bp.route('/<int:document_id>', methods=['PUT'])
def update_document(document_id):
    """Обновить информацию о документе"""
    document = Document.query.get_or_404(document_id)
    data = request.get_json()

    try:
        if 'title' in data:
            document.title = data['title']
        if 'description' in data:
            document.description = data['description']
        if 'document_type' in data:
            document.document_type = data['document_type']
        if 'category' in data:
            document.category = data['category']
        if 'file_url' in data:
            document.file_url = data['file_url']
        if 'file_name' in data:
            document.file_name = data['file_name']
        if 'file_size' in data:
            document.file_size = data['file_size']
        if 'file_format' in data:
            document.file_format = data['file_format']
        if 'document_date' in data:
            document.document_date = datetime.strptime(data['document_date'], '%Y-%m-%d').date()
        if 'author_id' in data:
            document.author_id = data['author_id']
        if 'project_id' in data:
            document.project_id = data['project_id']
        if 'event_id' in data:
            document.event_id = data['event_id']
        if 'status' in data:
            document.status = data['status']
        if 'access_level' in data:
            document.access_level = data['access_level']
        if 'tags' in data:
            document.tags = data['tags']
        if 'version' in data:
            document.version = data['version']
        if 'notes' in data:
            document.notes = data['notes']

        db.session.commit()
        return jsonify(document.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@documents_bp.route('/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Удалить документ"""
    document = Document.query.get_or_404(document_id)

    try:
        db.session.delete(document)
        db.session.commit()
        return jsonify({'message': 'Document deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
