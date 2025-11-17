# Примеры использования API

Этот документ содержит примеры запросов к API системы управления советом.

## Базовый URL

```
http://localhost:5000/api
```

## Члены совета

### Получить список всех членов

```bash
curl http://localhost:5000/api/members/
```

### Получить только активных членов детского совета

```bash
curl "http://localhost:5000/api/members/?status=active&council_type=Детский"
```

### Добавить нового члена совета

```bash
curl -X POST http://localhost:5000/api/members/ \
  -H "Content-Type: application/json" \
  -d '{
    "last_name": "Иванов",
    "first_name": "Иван",
    "middle_name": "Иванович",
    "birth_date": "2010-05-15",
    "email": "ivanov@example.com",
    "phone": "+79001234567",
    "council_type": "Детский",
    "position": "Член совета",
    "interests": "Спорт, образование, волонтерство"
  }'
```

### Обновить информацию о члене

```bash
curl -X PUT http://localhost:5000/api/members/1 \
  -H "Content-Type: application/json" \
  -d '{
    "position": "Заместитель председателя",
    "status": "active"
  }'
```

### Получить статистику по членам

```bash
curl http://localhost:5000/api/members/stats
```

## Мероприятия

### Получить все предстоящие мероприятия

```bash
curl "http://localhost:5000/api/events/?upcoming=true"
```

### Создать новое мероприятие

```bash
curl -X POST http://localhost:5000/api/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Заседание совета",
    "description": "Ежемесячное заседание молодёжного совета",
    "event_type": "Заседание",
    "category": "Организационное",
    "start_datetime": "2024-02-15T14:00:00",
    "end_datetime": "2024-02-15T16:00:00",
    "location": "Офис Уполномоченного",
    "address": "г. Благовещенск, ул. Ленина, 1",
    "status": "planned",
    "organizer_id": 1,
    "max_participants": 30
  }'
```

### Добавить участника к мероприятию

```bash
curl -X POST http://localhost:5000/api/events/1/participants \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": 2
  }'
```

### Обновить статус мероприятия

```bash
curl -X PUT http://localhost:5000/api/events/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "attendance_count": 25,
    "outcome": "Обсуждены планы на следующий квартал, приняты решения по 3 проектам"
  }'
```

## Проекты

### Получить список активных проектов

```bash
curl "http://localhost:5000/api/projects/?status=active"
```

### Создать новый проект

```bash
curl -X POST http://localhost:5000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Помощь детским домам",
    "description": "Благотворительный проект по поддержке детских домов области",
    "project_type": "Социальный",
    "category": "Благотворительность",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "planned_duration_months": 12,
    "status": "active",
    "goals": "Собрать и передать помощь для 5 детских домов",
    "tasks": "1. Сбор средств\n2. Закупка необходимых товаров\n3. Организация доставки",
    "target_audience": "Дети из детских домов Амурской области",
    "budget": 500000.0,
    "funding_source": "Благотворительные взносы",
    "expected_results": "Оказана помощь 200+ детям",
    "leader_id": 1,
    "progress_percentage": 35
  }'
```

### Обновить прогресс проекта

```bash
curl -X PUT http://localhost:5000/api/projects/1 \
  -H "Content-Type: application/json" \
  -d '{
    "progress_percentage": 50,
    "budget_spent": 250000.0,
    "actual_results": "Оказана помощь 3 детским домам, 120 детей"
  }'
```

### Добавить участника к проекту

```bash
curl -X POST http://localhost:5000/api/projects/1/members \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": 3
  }'
```

## Документы

### Получить список всех документов

```bash
curl http://localhost:5000/api/documents/
```

### Создать новый документ

```bash
curl -X POST http://localhost:5000/api/documents/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Протокол заседания №1",
    "description": "Протокол первого заседания совета в 2024 году",
    "document_type": "Протокол",
    "category": "Организационное",
    "file_url": "/uploads/protocol_01_2024.pdf",
    "file_name": "protocol_01_2024.pdf",
    "file_size": 524288,
    "file_format": "PDF",
    "document_date": "2024-01-15",
    "author_id": 1,
    "event_id": 1,
    "status": "approved",
    "access_level": "internal",
    "tags": "протокол, заседание, 2024"
  }'
```

## Отчеты

### Получить список отчетов

```bash
curl http://localhost:5000/api/reports/
```

### Создать отчет вручную

```bash
curl -X POST http://localhost:5000/api/reports/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Квартальный отчет за Q1 2024",
    "report_type": "Квартальный",
    "period_start": "2024-01-01",
    "period_end": "2024-03-31",
    "total_members": 45,
    "new_members": 5,
    "active_members": 42,
    "total_events": 12,
    "events_held": 10,
    "total_participants": 380,
    "total_projects": 8,
    "active_projects": 5,
    "completed_projects": 3,
    "total_budget": 2000000.0,
    "budget_spent": 1500000.0,
    "summary": "Успешный квартал с высокой активностью",
    "achievements": "Завершены 3 крупных проекта, привлечены 5 новых членов",
    "challenges": "Недостаток финансирования для некоторых инициатив",
    "recommendations": "Усилить работу по привлечению спонсоров",
    "author_id": 1,
    "status": "draft"
  }'
```

### Автоматически сгенерировать отчет за период

```bash
curl -X POST http://localhost:5000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Автоматический отчет за январь 2024",
    "report_type": "Месячный",
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "author_id": 1
  }'
```

### Утвердить отчет

```bash
curl -X PUT http://localhost:5000/api/reports/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved"
  }'
```

## Примеры использования в JavaScript

### Получить список членов

```javascript
fetch('/api/members/')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Ошибка:', error));
```

### Создать новое мероприятие

```javascript
const eventData = {
  title: "Семинар по правам детей",
  description: "Образовательный семинар для членов совета",
  event_type: "Семинар",
  start_datetime: "2024-03-20T10:00:00",
  end_datetime: "2024-03-20T14:00:00",
  location: "Конференц-зал",
  status: "planned"
};

fetch('/api/events/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(eventData)
})
  .then(response => response.json())
  .then(data => console.log('Мероприятие создано:', data))
  .catch(error => console.error('Ошибка:', error));
```

### Обновить прогресс проекта

```javascript
const updateData = {
  progress_percentage: 75,
  budget_spent: 375000
};

fetch('/api/projects/1', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(updateData)
})
  .then(response => response.json())
  .then(data => console.log('Проект обновлен:', data))
  .catch(error => console.error('Ошибка:', error));
```

## Коды ответов

- `200 OK` - Успешный запрос
- `201 Created` - Ресурс успешно создан
- `400 Bad Request` - Неверный запрос (отсутствуют обязательные поля)
- `404 Not Found` - Ресурс не найден
- `500 Internal Server Error` - Внутренняя ошибка сервера

## Формат ошибок

При ошибке API возвращает JSON с описанием:

```json
{
  "error": "Missing required field: last_name"
}
```
