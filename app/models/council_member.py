"""Модель для членов совета"""
from . import db
from datetime import datetime


class CouncilMember(db.Model):
    """Член Детского и Молодёжного Общественного Совета"""
    __tablename__ = 'council_members'

    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    birth_date = db.Column(db.Date, nullable=False)

    # Контактная информация
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

    # Образование и деятельность
    education = db.Column(db.String(200))
    occupation = db.Column(db.String(200))
    school_university = db.Column(db.String(200))

    # Статус в совете
    position = db.Column(db.String(100))  # Председатель, заместитель, член и т.д.
    council_type = db.Column(db.String(50))  # "Детский" или "Молодёжный"
    join_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, inactive, alumni

    # Интересы и компетенции
    interests = db.Column(db.Text)
    skills = db.Column(db.Text)
    achievements = db.Column(db.Text)

    # Фотография
    photo_url = db.Column(db.String(200))

    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    projects = db.relationship('Project', secondary='project_members', back_populates='members')
    events = db.relationship('Event', secondary='event_participants', back_populates='participants')

    def __repr__(self):
        return f'<CouncilMember {self.last_name} {self.first_name}>'

    @property
    def full_name(self):
        """Полное имя"""
        if self.middle_name:
            return f'{self.last_name} {self.first_name} {self.middle_name}'
        return f'{self.last_name} {self.first_name}'

    @property
    def age(self):
        """Возраст члена совета"""
        today = datetime.today().date()
        age = today.year - self.birth_date.year
        if today.month < self.birth_date.month or (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        return age

    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'birth_date': self.birth_date.isoformat(),
            'age': self.age,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'education': self.education,
            'occupation': self.occupation,
            'school_university': self.school_university,
            'position': self.position,
            'council_type': self.council_type,
            'join_date': self.join_date.isoformat(),
            'status': self.status,
            'interests': self.interests,
            'skills': self.skills,
            'achievements': self.achievements,
            'photo_url': self.photo_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
