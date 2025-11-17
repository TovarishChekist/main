"""Модель для отчетов и статистики"""
from . import db
from datetime import datetime


class Report(db.Model):
    """Отчет о деятельности совета"""
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)

    # Период отчетности
    report_type = db.Column(db.String(50))  # Месячный, квартальный, годовой
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)

    # Статистика по членам
    total_members = db.Column(db.Integer)
    new_members = db.Column(db.Integer)
    active_members = db.Column(db.Integer)

    # Статистика по мероприятиям
    total_events = db.Column(db.Integer)
    events_held = db.Column(db.Integer)
    total_participants = db.Column(db.Integer)

    # Статистика по проектам
    total_projects = db.Column(db.Integer)
    active_projects = db.Column(db.Integer)
    completed_projects = db.Column(db.Integer)

    # Финансовые показатели
    total_budget = db.Column(db.Float)
    budget_spent = db.Column(db.Float)
    budget_efficiency = db.Column(db.Float)  # Эффективность использования бюджета в %

    # Описание и выводы
    summary = db.Column(db.Text)  # Краткое содержание
    achievements = db.Column(db.Text)  # Достижения
    challenges = db.Column(db.Text)  # Проблемы и вызовы
    recommendations = db.Column(db.Text)  # Рекомендации

    # Автор отчета
    author_id = db.Column(db.Integer, db.ForeignKey('council_members.id'))

    # Статус
    status = db.Column(db.String(20), default='draft')  # draft, submitted, approved

    # Документ отчета
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))

    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)

    # Связи
    author = db.relationship('CouncilMember', foreign_keys=[author_id])
    document = db.relationship('Document', foreign_keys=[document_id])

    def __repr__(self):
        return f'<Report {self.title}>'

    @property
    def budget_utilization(self):
        """Процент использования бюджета"""
        if self.total_budget and self.total_budget > 0:
            return round((self.budget_spent / self.total_budget) * 100, 2)
        return 0

    @property
    def project_completion_rate(self):
        """Процент завершенных проектов"""
        if self.total_projects and self.total_projects > 0:
            return round((self.completed_projects / self.total_projects) * 100, 2)
        return 0

    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'title': self.title,
            'report_type': self.report_type,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_members': self.total_members,
            'new_members': self.new_members,
            'active_members': self.active_members,
            'total_events': self.total_events,
            'events_held': self.events_held,
            'total_participants': self.total_participants,
            'total_projects': self.total_projects,
            'active_projects': self.active_projects,
            'completed_projects': self.completed_projects,
            'total_budget': self.total_budget,
            'budget_spent': self.budget_spent,
            'budget_efficiency': self.budget_efficiency,
            'budget_utilization': self.budget_utilization,
            'project_completion_rate': self.project_completion_rate,
            'summary': self.summary,
            'achievements': self.achievements,
            'challenges': self.challenges,
            'recommendations': self.recommendations,
            'author_id': self.author_id,
            'status': self.status,
            'document_id': self.document_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }
