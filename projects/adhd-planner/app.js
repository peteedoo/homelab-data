const STORAGE_KEY = 'focusflow_tasks_v1';
const ENERGY_ORDER = ['high', 'medium', 'low'];
const ENERGY_ICONS = { high: '🔥', medium: '☕', low: '🛋️' };
const PRIORITY_LABELS = { 3: 'High', 2: 'Medium', 1: 'Low' };

let tasks = [];
let currentEnergy = 'medium';
let editingTaskId = null;

// ---------- Helpers ----------
function generateId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function loadTasks() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      tasks = JSON.parse(raw);
      return;
    }
  } catch (e) {
    console.warn('Could not load tasks from localStorage', e);
  }
  tasks = demoTasks();
  saveTasks();
}

function saveTasks() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  } catch (e) {
    console.warn('Could not save tasks to localStorage', e);
  }
}

function demoTasks() {
  return [
    {
      id: generateId(),
      title: 'Drink a glass of water',
      priority: 2,
      energy: 'low',
      duration: 2,
      done: false,
      createdAt: Date.now(),
      subtasks: []
    },
    {
      id: generateId(),
      title: 'Pick one thing to focus on today',
      priority: 3,
      energy: 'medium',
      duration: 5,
      done: false,
      createdAt: Date.now(),
      subtasks: [
        { id: generateId(), title: 'Scan the task list', done: false },
        { id: generateId(), title: 'Choose the most important one', done: false }
      ]
    },
    {
      id: generateId(),
      title: 'Take a 10-minute walk',
      priority: 1,
      energy: 'medium',
      duration: 10,
      done: false,
      createdAt: Date.now(),
      subtasks: []
    }
  ];
}

function pluralize(n, word) {
  return `${n} ${word}${n === 1 ? '' : 's'}`;
}

function encouragement(done, total) {
  if (total === 0) return 'Start with one tiny task.';
  if (done === 0) return 'One step at a time.';
  if (done === total) return 'All done — great work! 🎉';
  if (done / total >= 0.5) return 'More than halfway there!';
  return 'Nice momentum!';
}

// ---------- Rendering ----------
function renderAll() {
  renderStats();
  renderTaskList();
  renderFocus();
  renderEnergy();
}

function renderStats() {
  const total = tasks.length;
  const done = tasks.filter(t => t.done).length;
  const percent = total === 0 ? 0 : Math.round((done / total) * 100);

  document.getElementById('progress-label').textContent = `${pluralize(done, 'task')} done of ${total}`;
  document.getElementById('encouragement').textContent = encouragement(done, total);
  document.getElementById('progress-fill').style.width = `${percent}%`;
}

function renderTaskList() {
  const list = document.getElementById('task-list');
  const filter = document.getElementById('filter-status').value;

  let filtered = tasks.slice().sort((a, b) => b.priority - a.priority || b.createdAt - a.createdAt);
  if (filter === 'active') filtered = filtered.filter(t => !t.done);
  if (filter === 'done') filtered = filtered.filter(t => t.done);

  list.innerHTML = '';

  if (filtered.length === 0) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = filter === 'done' ? 'No completed tasks yet.' : 'No tasks here. Add one above!';
    list.appendChild(empty);
    return;
  }

  for (const task of filtered) {
    list.appendChild(createTaskItem(task));
  }
}

function createTaskItem(task) {
  const li = document.createElement('li');
  li.className = `task-item ${task.done ? 'done' : ''}`;
  li.dataset.id = task.id;

  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.className = 'task-checkbox';
  checkbox.checked = task.done;
  checkbox.setAttribute('aria-label', `Mark ${task.title} as ${task.done ? 'not done' : 'done'}`);
  checkbox.addEventListener('change', () => toggleTaskDone(task.id));

  const body = document.createElement('div');
  body.className = 'task-body';

  const title = document.createElement('div');
  title.className = 'task-title';
  title.textContent = task.title;
  body.appendChild(title);

  const meta = document.createElement('div');
  meta.className = 'task-meta';
  meta.innerHTML = `
    <span class="badge badge-priority-${PRIORITY_LABELS[task.priority].toLowerCase()}">${PRIORITY_LABELS[task.priority]}</span>
    <span class="badge badge-energy-${task.energy}">${ENERGY_ICONS[task.energy]} ${capitalize(task.energy)}</span>
    ${task.duration ? `<span>⏱ ${task.duration} min</span>` : ''}
    ${task.subtasks.length ? `<span>☑ ${task.subtasks.filter(s => s.done).length}/${task.subtasks.length}</span>` : ''}
  `;
  body.appendChild(meta);

  if (task.subtasks.length > 0 && !task.done) {
    const subList = document.createElement('ul');
    subList.className = 'subtasks-preview';
    for (const sub of task.subtasks) {
      const sli = document.createElement('li');
      const sCheck = document.createElement('input');
      sCheck.type = 'checkbox';
      sCheck.checked = sub.done;
      sCheck.addEventListener('change', () => toggleSubtask(task.id, sub.id));
      const sSpan = document.createElement('span');
      sSpan.className = sub.done ? 'done' : '';
      sSpan.textContent = sub.title;
      sli.appendChild(sCheck);
      sli.appendChild(sSpan);
      subList.appendChild(sli);
    }
    body.appendChild(subList);
  }

  const actions = document.createElement('div');
  actions.className = 'task-actions';

  const editBtn = document.createElement('button');
  editBtn.className = 'icon-btn';
  editBtn.setAttribute('aria-label', 'Edit task');
  editBtn.textContent = '✎';
  editBtn.addEventListener('click', () => openEditModal(task.id));

  actions.appendChild(editBtn);

  li.appendChild(checkbox);
  li.appendChild(body);
  li.appendChild(actions);

  return li;
}

function renderFocus() {
  const container = document.getElementById('focus-content');
  const active = tasks.filter(t => !t.done);

  if (active.length === 0) {
    container.innerHTML = '<p class="empty">No active tasks. Add one in the Plan view.</p>';
    return;
  }

  // Pick task: highest priority, then matching current energy, then shortest duration
  const scored = active.map(t => {
    const energyMatch = t.energy === currentEnergy ? 2 : ENERGY_ORDER.indexOf(t.energy) === ENERGY_ORDER.indexOf(currentEnergy) ? 1 : 0;
    return { task: t, score: t.priority * 10 + energyMatch * 3 - (t.duration || 0) / 60 };
  });
  scored.sort((a, b) => b.score - a.score);
  const task = scored[0].task;

  const remainingSubtasks = task.subtasks.filter(s => !s.done);
  const nextSub = remainingSubtasks.length > 0 ? remainingSubtasks[0] : null;

  container.innerHTML = `
    <div class="focus-task">
      <div class="task-title">${escapeHtml(task.title)}</div>
      <div class="task-meta">
        <span class="badge badge-priority-${PRIORITY_LABELS[task.priority].toLowerCase()}">${PRIORITY_LABELS[task.priority]}</span>
        <span class="badge badge-energy-${task.energy}">${ENERGY_ICONS[task.energy]} ${capitalize(task.energy)}</span>
        ${task.duration ? `<span>⏱ ${task.duration} min</span>` : ''}
      </div>
      ${nextSub ? `<p style="margin-top:14px; color: var(--text-muted);">Next tiny step: <strong>${escapeHtml(nextSub.title)}</strong></p>` : ''}
      <div class="focus-actions">
        <button class="btn btn-primary" id="focus-done">Done ✓</button>
        <button class="btn btn-secondary" id="focus-edit">Edit / Break down</button>
        <button class="btn btn-ghost" id="focus-skip">Skip for now</button>
      </div>
    </div>
  `;

  document.getElementById('focus-done').addEventListener('click', () => {
    if (nextSub) {
      toggleSubtask(task.id, nextSub.id);
    } else {
      toggleTaskDone(task.id);
    }
    renderAll();
  });

  document.getElementById('focus-edit').addEventListener('click', () => openEditModal(task.id));

  document.getElementById('focus-skip').addEventListener('click', () => {
    // Move task to end of active list by updating createdAt so it doesn't resurface immediately
    task.createdAt = Date.now();
    saveTasks();
    renderAll();
  });
}

function renderEnergy() {
  document.querySelectorAll('.energy-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.energy === currentEnergy);
  });

  const list = document.getElementById('energy-task-list');
  const filtered = tasks
    .filter(t => !t.done && t.energy === currentEnergy)
    .sort((a, b) => b.priority - a.priority || a.duration - b.duration);

  document.getElementById('energy-summary').textContent =
    filtered.length === 0
      ? `No ${currentEnergy}-energy tasks. Add one or switch energy levels.`
      : `Showing ${pluralize(filtered.length, 'task')} that fit ${currentEnergy} energy.`;

  list.innerHTML = '';

  if (filtered.length === 0) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = 'Nothing here. Try a different energy level or add a task.';
    list.appendChild(empty);
    return;
  }

  for (const task of filtered) {
    list.appendChild(createTaskItem(task));
  }
}

// ---------- Actions ----------
function addTask(title, priority, energy, duration) {
  tasks.push({
    id: generateId(),
    title: title.trim(),
    priority: parseInt(priority, 10),
    energy,
    duration: parseInt(duration, 10) || 0,
    done: false,
    createdAt: Date.now(),
    subtasks: []
  });
  saveTasks();
  renderAll();
}

function toggleTaskDone(id) {
  const task = tasks.find(t => t.id === id);
  if (task) {
    task.done = !task.done;
    saveTasks();
    renderAll();
  }
}

function toggleSubtask(taskId, subId) {
  const task = tasks.find(t => t.id === taskId);
  if (!task) return;
  const sub = task.subtasks.find(s => s.id === subId);
  if (sub) {
    sub.done = !sub.done;
    // Auto-complete parent when all subtasks are done
    if (task.subtasks.length > 0 && task.subtasks.every(s => s.done)) {
      task.done = true;
    }
    saveTasks();
    renderAll();
  }
}

function deleteTask(id) {
  tasks = tasks.filter(t => t.id !== id);
  saveTasks();
  renderAll();
  closeModal();
}

function clearDone() {
  tasks = tasks.filter(t => !t.done);
  saveTasks();
  renderAll();
}

// ---------- Modal ----------
const modal = document.getElementById('task-modal');

function openEditModal(id) {
  editingTaskId = id;
  const task = tasks.find(t => t.id === id);
  if (!task) return;

  document.getElementById('edit-title').value = task.title;
  document.getElementById('edit-priority').value = task.priority;
  document.getElementById('edit-energy').value = task.energy;
  document.getElementById('edit-duration').value = task.duration || '';
  renderEditSubtasks(task);

  modal.showModal();
}

function renderEditSubtasks(task) {
  const list = document.getElementById('edit-subtasks');
  list.innerHTML = '';
  for (const sub of task.subtasks) {
    const li = document.createElement('li');
    const check = document.createElement('input');
    check.type = 'checkbox';
    check.checked = sub.done;
    check.addEventListener('change', () => {
      sub.done = !sub.done;
      renderEditSubtasks(task);
    });
    const span = document.createElement('span');
    span.className = sub.done ? 'done' : '';
    span.textContent = sub.title;
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'remove-subtask';
    remove.setAttribute('aria-label', 'Remove subtask');
    remove.textContent = '×';
    remove.addEventListener('click', () => {
      task.subtasks = task.subtasks.filter(s => s.id !== sub.id);
      renderEditSubtasks(task);
    });
    li.appendChild(check);
    li.appendChild(span);
    li.appendChild(remove);
    list.appendChild(li);
  }
}

function saveEditedTask() {
  const task = tasks.find(t => t.id === editingTaskId);
  if (!task) return;

  task.title = document.getElementById('edit-title').value.trim();
  task.priority = parseInt(document.getElementById('edit-priority').value, 10);
  task.energy = document.getElementById('edit-energy').value;
  const duration = parseInt(document.getElementById('edit-duration').value, 10);
  task.duration = isNaN(duration) ? 0 : duration;

  saveTasks();
  renderAll();
}

function closeModal() {
  modal.close();
  editingTaskId = null;
}

// ---------- Export / Import ----------
function exportData() {
  const blob = new Blob([JSON.stringify(tasks, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `focusflow-backup-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function importData(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      if (Array.isArray(data)) {
        tasks = data;
        saveTasks();
        renderAll();
        alert('Data imported successfully.');
      } else {
        alert('Invalid file format.');
      }
    } catch (e) {
      alert('Could not read file.');
    }
  };
  reader.readAsText(file);
}

// ---------- Tabs ----------
function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(`${name}-view`).classList.add('active');

  document.querySelectorAll('.tab').forEach(t => {
    const active = t.dataset.view === name;
    t.classList.toggle('active', active);
    t.setAttribute('aria-selected', active);
  });

  if (name === 'focus') renderFocus();
  if (name === 'energy') renderEnergy();
}

// ---------- Utilities ----------
function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ---------- Event listeners ----------
document.addEventListener('DOMContentLoaded', () => {
  loadTasks();
  renderAll();

  // Tabs
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => showView(tab.dataset.view));
  });

  // Add task
  document.getElementById('add-form').addEventListener('submit', e => {
    e.preventDefault();
    const title = document.getElementById('new-task-title').value;
    const priority = document.getElementById('new-task-priority').value;
    const energy = document.getElementById('new-task-energy').value;
    const duration = document.getElementById('new-task-duration').value;
    if (!title.trim()) return;
    addTask(title, priority, energy, duration);
    document.getElementById('add-form').reset();
    document.getElementById('new-task-duration').value = 15;
    document.getElementById('new-task-priority').value = '2';
    document.getElementById('new-task-energy').value = 'medium';
    document.getElementById('new-task-title').focus();
  });

  // Filter
  document.getElementById('filter-status').addEventListener('change', renderTaskList);

  // Clear done
  document.getElementById('clear-done').addEventListener('click', () => {
    if (confirm('Clear all completed tasks?')) clearDone();
  });

  // Energy buttons
  document.querySelectorAll('.energy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      currentEnergy = btn.dataset.energy;
      renderEnergy();
    });
  });

  // Modal form
  modal.addEventListener('close', () => {
    editingTaskId = null;
  });

  document.querySelector('.modal-form').addEventListener('submit', e => {
    e.preventDefault();
    saveEditedTask();
    closeModal();
  });

  document.getElementById('cancel-edit').addEventListener('click', closeModal);

  document.getElementById('delete-task').addEventListener('click', () => {
    if (confirm('Delete this task?')) deleteTask(editingTaskId);
  });

  document.getElementById('add-subtask-btn').addEventListener('click', () => {
    const input = document.getElementById('new-subtask');
    const title = input.value.trim();
    if (!title || !editingTaskId) return;
    const task = tasks.find(t => t.id === editingTaskId);
    task.subtasks.push({ id: generateId(), title, done: false });
    renderEditSubtasks(task);
    input.value = '';
    input.focus();
  });

  document.getElementById('new-subtask').addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('add-subtask-btn').click();
    }
  });

  // Export / Import
  document.getElementById('export-btn').addEventListener('click', exportData);
  document.getElementById('import-btn').addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) importData(file);
    e.target.value = '';
  });

  // Keyboard shortcut: / focuses add input
  document.addEventListener('keydown', e => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA' && document.activeElement.tagName !== 'SELECT' && !modal.open) {
      e.preventDefault();
      document.getElementById('new-task-title').focus();
    }
  });
});
