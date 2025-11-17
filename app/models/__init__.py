"""Модели базы данных для системы управления Детским и Молодёжным Общественным Советом"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Импорт всех моделей
from .council_member import CouncilMember
from .event import Event, event_participants
from .project import Project, project_members
from .document import Document
from .report import Report

__all__ = ['db', 'CouncilMember', 'Event', 'Project', 'Document', 'Report',
           'event_participants', 'project_members']
