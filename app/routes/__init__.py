"""API маршруты для системы управления советом"""
from flask import Blueprint

# Создание blueprints
members_bp = Blueprint('members', __name__, url_prefix='/api/members')
events_bp = Blueprint('events', __name__, url_prefix='/api/events')
projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')
documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

# Импорт маршрутов
from . import members, events, projects, documents, reports

__all__ = ['members_bp', 'events_bp', 'projects_bp', 'documents_bp', 'reports_bp']
