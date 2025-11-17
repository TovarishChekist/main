"""Модель для проектов и инициатив"""
from . import db
from datetime import datetime


# Связующая таблица для участников проектов
project_members = db.Table('project_members',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('member_id', db.Integer, db.ForeignKey('council_members.id'), primary_key=True),
    db.Column('role', db.String(50)),  # Руководитель, участник, координатор и т.д.
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)


class Project(db.Model):
    """Проект или инициатива совета"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Классификация
    project_type = db.Column(db.String(50))  # Социальный, образовательный, культурный и т.д.
    category = db.Column(db.String(50))

    # Сроки
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    planned_duration_months = db.Column(db.Integer)

    # Статус
    status = db.Column(db.String(20), default='planning')  # planning, active, paused, completed, cancelled

    # Цели и задачи
    goals = db.Column(db.Text)  # Цели проекта
    tasks = db.Column(db.Text)  # Задачи проекта
    target_audience = db.Column(db.String(200))  # Целевая аудитория

    # Ресурсы
    budget = db.Column(db.Float)
    budget_spent = db.Column(db.Float, default=0)
    funding_source = db.Column(db.String(200))

    # Результаты
    expected_results = db.Column(db.Text)  # Ожидаемые результаты
    actual_results = db.Column(db.Text)  # Фактические результаты
    beneficiaries_count = db.Column(db.Integer)  # Количество благополучателей

    # Прогресс
    progress_percentage = db.Column(db.Integer, default=0)  # 0-100%

    # Руководство
    leader_id = db.Column(db.Integer, db.ForeignKey('council_members.id'))

    # Документы
    documents_url = db.Column(db.String(300))  # Ссылка на документы проекта
    report_url = db.Column(db.String(300))  # Ссылка на отчет

    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    members = db.relationship('CouncilMember', secondary='project_members', back_populates='projects')
    leader = db.relationship('CouncilMember', foreign_keys=[leader_id])

    def __repr__(self):
        return f'<Project {self.title}>'

    @property
    def is_active(self):
        """Проверка, является ли проект активным"""
        return self.status == 'active'

    @property
    def budget_remaining(self):
        """Остаток бюджета"""
        if self.budget:
            return self.budget - (self.budget_spent or 0)
        return None

    @property
    def is_overdue(self):
        """Проверка, просрочен ли проект"""
        if self.end_date and self.status in ['planning', 'active']:
            return datetime.utcnow().date() > self.end_date
        return False

    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'project_type': self.project_type,
            'category': self.category,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'planned_duration_months': self.planned_duration_months,
            'status': self.status,
            'goals': self.goals,
            'tasks': self.tasks,
            'target_audience': self.target_audience,
            'budget': self.budget,
            'budget_spent': self.budget_spent,
            'budget_remaining': self.budget_remaining,
            'funding_source': self.funding_source,
            'expected_results': self.expected_results,
            'actual_results': self.actual_results,
            'beneficiaries_count': self.beneficiaries_count,
            'progress_percentage': self.progress_percentage,
            'leader_id': self.leader_id,
            'documents_url': self.documents_url,
            'report_url': self.report_url,
            'is_active': self.is_active,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
