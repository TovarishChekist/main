"""Модель для документов и отчетов"""
from . import db
from datetime import datetime


class Document(db.Model):
    """Документ или отчет"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Тип документа
    document_type = db.Column(db.String(50))  # Отчет, протокол, положение, письмо и т.д.
    category = db.Column(db.String(50))

    # Файл
    file_url = db.Column(db.String(300))  # Ссылка на файл
    file_name = db.Column(db.String(200))
    file_size = db.Column(db.Integer)  # Размер в байтах
    file_format = db.Column(db.String(20))  # PDF, DOCX и т.д.

    # Даты
    document_date = db.Column(db.Date)  # Дата документа
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    author_id = db.Column(db.Integer, db.ForeignKey('council_members.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))

    # Статус
    status = db.Column(db.String(20), default='draft')  # draft, approved, archived

    # Доступ
    access_level = db.Column(db.String(20), default='public')  # public, internal, restricted

    # Метаданные
    tags = db.Column(db.String(300))  # Теги через запятую
    version = db.Column(db.String(20))
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    author = db.relationship('CouncilMember', foreign_keys=[author_id])
    project = db.relationship('Project', foreign_keys=[project_id])
    event = db.relationship('Event', foreign_keys=[event_id])

    def __repr__(self):
        return f'<Document {self.title}>'

    @property
    def file_size_mb(self):
        """Размер файла в МБ"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None

    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'document_type': self.document_type,
            'category': self.category,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_size_mb': self.file_size_mb,
            'file_format': self.file_format,
            'document_date': self.document_date.isoformat() if self.document_date else None,
            'upload_date': self.upload_date.isoformat(),
            'author_id': self.author_id,
            'project_id': self.project_id,
            'event_id': self.event_id,
            'status': self.status,
            'access_level': self.access_level,
            'tags': self.tags,
            'version': self.version,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
