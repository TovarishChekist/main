"""Модель для мероприятий"""
from . import db
from datetime import datetime


# Связующая таблица для участников мероприятий
event_participants = db.Table('event_participants',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('member_id', db.Integer, db.ForeignKey('council_members.id'), primary_key=True),
    db.Column('role', db.String(50)),  # Организатор, участник, спикер и т.д.
    db.Column('attendance', db.Boolean, default=False)  # Отметка о присутствии
)


class Event(db.Model):
    """Мероприятие совета"""
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Тип и категория
    event_type = db.Column(db.String(50))  # Заседание, конференция, семинар, акция и т.д.
    category = db.Column(db.String(50))  # Образование, спорт, культура, социальное и т.д.

    # Дата и время
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime)

    # Место проведения
    location = db.Column(db.String(200))
    address = db.Column(db.String(300))
    online_link = db.Column(db.String(300))  # Ссылка на онлайн-мероприятие

    # Статус
    status = db.Column(db.String(20), default='planned')  # planned, ongoing, completed, cancelled

    # Организационные детали
    organizer_id = db.Column(db.Integer, db.ForeignKey('council_members.id'))
    max_participants = db.Column(db.Integer)
    budget = db.Column(db.Float)

    # Результаты
    outcome = db.Column(db.Text)  # Результаты мероприятия
    attendance_count = db.Column(db.Integer)

    # Документы и материалы
    materials_url = db.Column(db.String(300))  # Ссылка на материалы
    photos_url = db.Column(db.String(300))  # Ссылка на фотографии

    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    participants = db.relationship('CouncilMember', secondary='event_participants', back_populates='events')
    organizer = db.relationship('CouncilMember', foreign_keys=[organizer_id])

    def __repr__(self):
        return f'<Event {self.title}>'

    @property
    def is_upcoming(self):
        """Проверка, является ли мероприятие предстоящим"""
        return self.start_datetime > datetime.utcnow() and self.status == 'planned'

    @property
    def duration_hours(self):
        """Длительность мероприятия в часах"""
        if self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return delta.total_seconds() / 3600
        return None

    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'event_type': self.event_type,
            'category': self.category,
            'start_datetime': self.start_datetime.isoformat(),
            'end_datetime': self.end_datetime.isoformat() if self.end_datetime else None,
            'location': self.location,
            'address': self.address,
            'online_link': self.online_link,
            'status': self.status,
            'organizer_id': self.organizer_id,
            'max_participants': self.max_participants,
            'budget': self.budget,
            'outcome': self.outcome,
            'attendance_count': self.attendance_count,
            'materials_url': self.materials_url,
            'photos_url': self.photos_url,
            'is_upcoming': self.is_upcoming,
            'duration_hours': self.duration_hours,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
