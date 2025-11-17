// API базовый URL
const API_URL = '/api';

// Переключение между секциями
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const section = btn.dataset.section;

        // Обновление активной кнопки
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Обновление активной секции
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        document.getElementById(section).classList.add('active');

        // Загрузка данных для секции
        loadSectionData(section);
    });
});

// Загрузка данных при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

// Загрузка данных для секции
function loadSectionData(section) {
    switch(section) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'members':
            loadMembers();
            break;
        case 'events':
            loadEvents();
            break;
        case 'projects':
            loadProjects();
            break;
        case 'documents':
            loadDocuments();
            break;
        case 'reports':
            loadReports();
            break;
    }
}

// ========== ПАНЕЛЬ УПРАВЛЕНИЯ ==========
async function loadDashboard() {
    try {
        // Загрузка статистики членов
        const membersStats = await fetch(`${API_URL}/members/stats`).then(r => r.json());
        document.getElementById('stat-members').textContent = membersStats.active_members || 0;

        // Загрузка статистики мероприятий
        const eventsStats = await fetch(`${API_URL}/events/stats`).then(r => r.json());
        document.getElementById('stat-events').textContent = eventsStats.total_events || 0;

        // Загрузка статистики проектов
        const projectsStats = await fetch(`${API_URL}/projects/stats`).then(r => r.json());
        document.getElementById('stat-projects').textContent = projectsStats.active_projects || 0;
        document.getElementById('stat-budget').textContent =
            `${(projectsStats.total_budget || 0).toLocaleString('ru-RU')} ₽`;

        // Загрузка предстоящих мероприятий
        const upcomingEvents = await fetch(`${API_URL}/events?upcoming=true`).then(r => r.json());
        displayUpcomingEvents(upcomingEvents);

        // Загрузка активных проектов
        const activeProjects = await fetch(`${API_URL}/projects?status=active`).then(r => r.json());
        displayActiveProjects(activeProjects);
    } catch (error) {
        console.error('Ошибка загрузки панели управления:', error);
    }
}

function displayUpcomingEvents(events) {
    const container = document.getElementById('upcoming-events');
    if (events.length === 0) {
        container.innerHTML = '<p class="empty-message">Нет предстоящих мероприятий</p>';
        return;
    }

    container.innerHTML = events.slice(0, 5).map(event => `
        <div style="padding: 15px; border-bottom: 1px solid #e9ecef;">
            <strong>${event.title}</strong><br>
            <small>${new Date(event.start_datetime).toLocaleDateString('ru-RU')}</small>
        </div>
    `).join('');
}

function displayActiveProjects(projects) {
    const container = document.getElementById('active-projects');
    if (projects.length === 0) {
        container.innerHTML = '<p class="empty-message">Нет активных проектов</p>';
        return;
    }

    container.innerHTML = projects.slice(0, 5).map(project => `
        <div style="padding: 15px; border-bottom: 1px solid #e9ecef;">
            <strong>${project.title}</strong><br>
            <small>Прогресс: ${project.progress_percentage}%</small>
        </div>
    `).join('');
}

// ========== ЧЛЕНЫ СОВЕТА ==========
async function loadMembers() {
    try {
        const status = document.getElementById('member-status-filter')?.value || '';
        const councilType = document.getElementById('member-council-filter')?.value || '';

        let url = `${API_URL}/members?`;
        if (status) url += `status=${status}&`;
        if (councilType) url += `council_type=${councilType}&`;

        const members = await fetch(url).then(r => r.json());
        displayMembers(members);
    } catch (error) {
        console.error('Ошибка загрузки членов совета:', error);
    }
}

function displayMembers(members) {
    const container = document.getElementById('members-list');
    if (members.length === 0) {
        container.innerHTML = '<p class="empty-message">Нет членов совета</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>ФИО</th>
                    <th>Возраст</th>
                    <th>Совет</th>
                    <th>Должность</th>
                    <th>Контакты</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                ${members.map(member => `
                    <tr>
                        <td>${member.full_name}</td>
                        <td>${member.age}</td>
                        <td>${member.council_type || 'Не указан'}</td>
                        <td>${member.position || 'Не указана'}</td>
                        <td>${member.email || member.phone || 'Нет данных'}</td>
                        <td><span class="badge badge-${member.status}">${member.status}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function showMemberForm() {
    document.getElementById('member-form').style.display = 'flex';
}

function closeMemberForm() {
    document.getElementById('member-form').style.display = 'none';
}

// Обработка формы добавления члена
document.getElementById('member-form-data')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
        last_name: document.getElementById('member-last-name').value,
        first_name: document.getElementById('member-first-name').value,
        middle_name: document.getElementById('member-middle-name').value,
        birth_date: document.getElementById('member-birth-date').value,
        email: document.getElementById('member-email').value,
        phone: document.getElementById('member-phone').value,
        council_type: document.getElementById('member-council-type').value,
        position: document.getElementById('member-position').value,
        interests: document.getElementById('member-interests').value
    };

    try {
        await fetch(`${API_URL}/members/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        closeMemberForm();
        loadMembers();
        alert('Член совета успешно добавлен!');
    } catch (error) {
        console.error('Ошибка добавления члена совета:', error);
        alert('Ошибка при добавлении члена совета');
    }
});

// ========== МЕРОПРИЯТИЯ ==========
async function loadEvents() {
    try {
        const status = document.getElementById('event-status-filter')?.value || '';
        const upcoming = document.getElementById('event-upcoming-filter')?.checked || false;

        let url = `${API_URL}/events?`;
        if (status) url += `status=${status}&`;
        if (upcoming) url += `upcoming=true&`;

        const events = await fetch(url).then(r => r.json());
        displayEvents(events);
    } catch (error) {
        console.error('Ошибка загрузки мероприятий:', error);
    }
}

function displayEvents(events) {
    const container = document.getElementById('events-list');
    if (events.length === 0) {
        container.innerHTML = '<p class="empty-message">Нет мероприятий</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Название</th>
                    <th>Тип</th>
                    <th>Дата начала</th>
                    <th>Место</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                ${events.map(event => `
                    <tr>
                        <td><strong>${event.title}</strong></td>
                        <td>${event.event_type || 'Не указан'}</td>
                        <td>${new Date(event.start_datetime).toLocaleDateString('ru-RU')}</td>
                        <td>${event.location || event.address || 'Онлайн'}</td>
                        <td><span class="badge badge-${event.status}">${event.status}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function showEventForm() {
    alert('Форма создания мероприятия будет доступна в следующей версии');
}

// ========== ПРОЕКТЫ ==========
async function loadProjects() {
    try {
        const status = document.getElementById('project-status-filter')?.value || '';

        let url = `${API_URL}/projects?`;
        if (status) url += `status=${status}&`;

        const projects = await fetch(url).then(r => r.json());
        displayProjects(projects);
    } catch (error) {
        console.error('Ошибка загрузки проектов:', error);
    }
}

function displayProjects(projects) {
    const container = document.getElementById('projects-list');
    if (projects.length === 0) {
        container.innerHTML = '<p class="empty-message">Нет проектов</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Название</th>
                    <th>Тип</th>
                    <th>Дата начала</th>
                    <th>Прогресс</th>
                    <th>Бюджет</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                ${projects.map(project => `
                    <tr>
                        <td><strong>${project.title}</strong></td>
                        <td>${project.project_type || 'Не указан'}</td>
                        <td>${new Date(project.start_date).toLocaleDateString('ru-RU')}</td>
                        <td>${project.progress_percentage}%</td>
                        <td>${(project.budget || 0).toLocaleString('ru-RU')} ₽</td>
                        <td><span class="badge badge-${project.status}">${project.status}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function showProjectForm() {
    alert('Форма создания проекта будет доступна в следующей версии');
}

// ========== ДОКУМЕНТЫ ==========
async function loadDocuments() {
    try {
        const documents = await fetch(`${API_URL}/documents/`).then(r => r.json());
        displayDocuments(documents);
    } catch (error) {
        console.error('Ошибка загрузки документов:', error);
    }
}

function displayDocuments(documents) {
    const container = document.getElementById('documents-list');
    if (documents.length === 0) {
        container.innerHTML = '<p class="empty-message">Нет документов</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Название</th>
                    <th>Тип</th>
                    <th>Дата</th>
                    <th>Формат</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                ${documents.map(doc => `
                    <tr>
                        <td><strong>${doc.title}</strong></td>
                        <td>${doc.document_type || 'Не указан'}</td>
                        <td>${doc.document_date ? new Date(doc.document_date).toLocaleDateString('ru-RU') : 'Нет данных'}</td>
                        <td>${doc.file_format || 'Не указан'}</td>
                        <td><span class="badge badge-${doc.status}">${doc.status}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function showDocumentForm() {
    alert('Форма добавления документа будет доступна в следующей версии');
}

// ========== ОТЧЕТЫ ==========
async function loadReports() {
    try {
        const reports = await fetch(`${API_URL}/reports/`).then(r => r.json());
        displayReports(reports);
    } catch (error) {
        console.error('Ошибка загрузки отчетов:', error);
    }
}

function displayReports(reports) {
    const container = document.getElementById('reports-list');
    if (reports.length === 0) {
        container.innerHTML = '<p class="empty-message">Нет отчетов</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Название</th>
                    <th>Тип</th>
                    <th>Период</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                ${reports.map(report => `
                    <tr>
                        <td><strong>${report.title}</strong></td>
                        <td>${report.report_type || 'Не указан'}</td>
                        <td>${new Date(report.period_start).toLocaleDateString('ru-RU')} - ${new Date(report.period_end).toLocaleDateString('ru-RU')}</td>
                        <td><span class="badge badge-${report.status}">${report.status}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function showReportForm() {
    alert('Форма создания отчета будет доступна в следующей версии');
}
