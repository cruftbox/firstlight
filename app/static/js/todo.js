document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('newTodoInput');
  const addBtn = document.getElementById('addTodoBtn');
  const list = document.getElementById('todoList');

  function addTodo() {
    const text = input.value.trim();
    if (!text) return;
    fetch('/api/todos', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text}),
    })
    .then(r => r.json())
    .then(todo => {
      list.appendChild(makeTodoItem(todo));
      input.value = '';
    })
    .catch(() => {
      alert('Failed to save todo. Please try again.');
    });
  }

  function makeTodoItem(todo) {
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    li.dataset.id = todo.id;
    const span = document.createElement('span');
    span.className = 'todo-text';
    span.textContent = todo.text;
    const btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-outline-danger delete-btn';
    btn.textContent = '×';
    li.appendChild(span);
    li.appendChild(btn);
    return li;
  }

  addBtn.addEventListener('click', addTodo);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') addTodo();
  });

  list.addEventListener('click', function (e) {
    if (e.target.classList.contains('delete-btn')) {
      const li = e.target.closest('li');
      fetch('/api/todos', {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: li.dataset.id}),
      }).then(r => {
        if (r.ok) li.remove();
      });
    }
  });
});
