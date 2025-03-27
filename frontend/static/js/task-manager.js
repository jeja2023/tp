// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');
    
    // 检查DOM元素是否正确加载
    console.log('用户名元素:', document.getElementById('username') ? '已找到' : '未找到');
    console.log('任务表格:', document.getElementById('task-table-body') ? '已找到' : '未找到');
    console.log('创建任务按钮:', document.getElementById('create-task-btn') ? '已找到' : '未找到');
    console.log('页面内容长度:', document.body.innerHTML.length);
    
    // 注入样式
    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
        .disabled-text {
            color: #999;
            font-style: italic;
            font-size: 0.9em;
        }
    `;
    document.head.appendChild(styleSheet);
    
    // 检查用户是否已登录
    const token = localStorage.getItem('token');
    console.log('Token状态:', token ? '存在' : '不存在');
    if (token) {
        console.log('Token值:', token.substring(0, 20) + '...');
    }
    
    if (!token) {
        console.log('未找到token，重定向到登录页面');
        window.location.href = '/login';
        return;
    }
    
    // 获取并显示用户名
    const username = localStorage.getItem('username');
    console.log('用户名:', username);
    
    if (!username) {
        console.log('未找到用户名，重定向到登录页面');
        window.location.href = '/login';
        return;
    }
    
    try {
        const usernameElement = document.getElementById('username');
        if (usernameElement) {
            usernameElement.textContent = username;
        } else {
            console.error('username元素不存在');
        }
        
        // 加载任务列表
        loadTasks();
    } catch (error) {
        console.error('设置用户名时出错:', error);
    }
    
    // 设置事件监听器
    setupEventListeners();
    
    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', function() {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/login';
    });
});

// 添加API前缀的辅助函数
function apiUrl(url) {
    return url.startsWith('/api') ? url : `/api${url}`;
}

// 加载任务列表
function loadTasks() {
    console.log('开始加载任务列表...');
    const token = localStorage.getItem('token');
    
    fetch(apiUrl('/tasks/'), {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                console.error('授权失败，重定向到登录页面');
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                window.location.href = '/login';
                return;
            }
            throw new Error('加载任务失败');
        }
        return response.json();
    })
    .then(data => {
        console.log('成功获取任务数据:', data);
        renderTasksList(data);
    })
    .catch(error => {
        console.error('加载任务出错:', error);
        showMessage('加载任务失败，请刷新页面重试', 'error');
    });
}

// 渲染任务列表
function renderTasksList(tasks) {
    console.log('渲染任务列表，任务数量:', tasks.length);
    const taskTableBody = document.getElementById('task-table-body');
    const currentUsername = localStorage.getItem('username');
    
    if (!taskTableBody) {
        console.error('找不到任务表格元素');
        return;
    }
    
    taskTableBody.innerHTML = '';
    
    if (tasks.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="no-tasks">没有任务</td>';
        taskTableBody.appendChild(row);
        return;
    }
    
    // 确保任务按创建时间降序排序
    const sortedTasks = [...tasks].sort((a, b) => {
        return new Date(b.created_at) - new Date(a.created_at);
    });
    
    // 先创建所有行并保持正确顺序
    const rows = sortedTasks.map(task => {
        const row = document.createElement('tr');
        const createdAt = new Date(task.created_at).toLocaleString();
        
        // 先设置基本信息，添加创建人字段
        row.innerHTML = `
            <td>${task.id}</td>
            <td>${task.title}</td>
            <td>${task.description || '无描述'}</td>
            <td>${task.owner ? task.owner.username : '未知'}</td>
            <td>${createdAt}</td>
            <td class="actions">
                <span class="loading-permissions">加载权限中...</span>
            </td>
        `;
        
        // 给行添加数据属性，方便后续更新
        row.dataset.taskId = task.id;
        row.dataset.taskTitle = task.title;
        
        return row;
    });
    
    // 先将所有行按顺序添加到表格中
    rows.forEach(row => {
        taskTableBody.appendChild(row);
    });
    
    // 再异步加载每个任务的权限
    sortedTasks.forEach((task, index) => {
        const row = rows[index];
        const token = localStorage.getItem('token');
        
        // 获取用户对当前任务的权限
        fetch(apiUrl(`/tasks/${task.id}/user-permission`), {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                console.error(`获取任务 ${task.id} 权限失败:`, response.status);
                return { can_view: true, can_edit: false, can_share: false, is_owner: false };
            }
            return response.json();
        })
        .then(permission => {
            console.log(`任务 ${task.id} 权限:`, permission);
            console.log(`任务 ${task.id} 权限JSON字符串:`, JSON.stringify(permission));
            console.log(`任务 ${task.id} permission_type:`, permission.permission_type);
            console.log(`is_owner: ${permission.is_owner}, can_manage: ${permission.can_manage}, can_share: ${permission.can_share}`);
            
            // 构建按钮HTML，只包含用户有权限的按钮
            let buttonsHtml = `<button class="btn view-btn" data-id="${task.id}">查看</button>`;
            
            // 只有拥有编辑权限才显示编辑按钮
            if (permission.can_edit || permission.is_owner) {
                buttonsHtml += ` <button class="btn edit-btn" data-id="${task.id}">编辑</button>`;
            }
            
            // 任务创建者或有管理员权限的用户可以分享任务
            if (permission.is_owner || permission.can_manage) {
                console.log(`显示任务 ${task.id} 的分享按钮`);
                buttonsHtml += ` <button class="btn share-btn" data-id="${task.id}" data-title="${task.title}">分享</button>`;
                // 添加管理权限按钮
                buttonsHtml += ` <button class="btn manage-btn manage-permissions-btn" data-id="${task.id}" data-title="${task.title}">管理权限</button>`;
            } else {
                console.log(`不显示任务 ${task.id} 的分享按钮，权限不足。is_owner=${permission.is_owner}, can_manage=${permission.can_manage}, can_share=${permission.can_share}`);
            }
            
            // 只有任务创建者可以删除任务
            if (permission.is_owner) {
                buttonsHtml += ` <button class="btn delete-btn danger-btn" data-id="${task.id}" data-title="${task.title}">删除</button>`;
            }
            
            // 更新行中的操作列
            const actionsCell = row.querySelector('.actions');
            if (actionsCell) {
                actionsCell.innerHTML = buttonsHtml;
                console.log(`已更新任务 ${task.id} 的操作按钮:`, buttonsHtml);
            } else {
                console.error(`找不到任务 ${task.id} 的操作列`);
            }
            
            // 为这个任务的按钮添加事件监听器
            addTaskButtonListenersForRow(row);
        })
        .catch(error => {
            console.error(`处理任务 ${task.id} 时出错:`, error);
            // 发生错误时仍然显示查看按钮
            const actionsCell = row.querySelector('.actions');
            if (actionsCell) {
                actionsCell.innerHTML = `<button class="btn view-btn" data-id="${task.id}">查看</button>`;
                addTaskButtonListenersForRow(row);
            }
        });
    });
}

// 为单行任务按钮添加事件监听器
function addTaskButtonListenersForRow(row) {
    // 查看任务按钮
    row.querySelectorAll('.view-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.dataset.id;
            console.log('查看任务:', taskId);
            // 跳转到任务详情页
            window.location.href = `/image?task_id=${taskId}`;
        });
    });
    
    // 编辑任务按钮
    row.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.dataset.id;
            console.log('编辑任务:', taskId);
            openEditTaskModal(taskId);
        });
    });
    
    // 分享任务按钮
    row.querySelectorAll('.share-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.dataset.id;
            const taskTitle = this.dataset.title;
            console.log('分享任务:', taskId, taskTitle);
            openShareTaskModal(taskId, taskTitle);
        });
    });

    // 管理权限按钮
    row.querySelectorAll('.manage-permissions-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.dataset.id;
            const taskTitle = this.dataset.title;
            console.log('管理权限:', taskId, taskTitle);
            openManagePermissionsModal(taskId, taskTitle);
        });
    });
    
    // 删除任务按钮
    row.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.dataset.id;
            const taskTitle = this.dataset.title;
            console.log('删除任务:', taskId, taskTitle);
            confirmDeleteTask(taskId, taskTitle);
        });
    });
}

// 设置事件监听器
function setupEventListeners() {
    console.log('设置事件监听器');
    
    // 创建任务按钮
    const createTaskBtn = document.getElementById('create-task-btn');
    if (createTaskBtn) {
        createTaskBtn.addEventListener('click', openCreateTaskModal);
    }
    
    // 关闭模态窗口按钮
    document.querySelectorAll('.close-btn').forEach(button => {
        button.addEventListener('click', function() {
            console.log('点击关闭按钮');
            closeAllModals();
        });
    });
    
    // 点击模态窗口外部关闭
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(event) {
            if (event.target === this) {
                console.log('点击模态窗口外部');
                closeAllModals();
            }
        });
    });
    
    // 创建任务表单提交
    const createTaskForm = document.getElementById('create-task-form');
    if (createTaskForm) {
        createTaskForm.addEventListener('submit', function(event) {
            event.preventDefault();
            console.log('提交创建任务表单');
            createTask();
        });
    }
    
    // 编辑任务表单提交
    const editTaskForm = document.getElementById('edit-task-form');
    if (editTaskForm) {
        editTaskForm.addEventListener('submit', function(event) {
            event.preventDefault();
            console.log('提交编辑任务表单');
            updateTask();
        });
    }
    
    // 分享任务表单提交
    const shareTaskForm = document.getElementById('share-task-form');
    if (shareTaskForm) {
        shareTaskForm.addEventListener('submit', function(event) {
            event.preventDefault();
            console.log('提交分享任务表单');
            shareTask();
        });
    }

    // 为每个任务的按钮添加事件监听
    document.getElementById('task-table-body').addEventListener('click', function(e) {
        const target = e.target;
        const taskId = target.dataset.id;
        
        if (target.classList.contains('view-btn')) {
            window.location.href = `/image?task_id=${taskId}`;
        } else if (target.classList.contains('edit-btn')) {
            openEditTaskModal(taskId);
        } else if (target.classList.contains('share-btn')) {
            openShareTaskModal(taskId, target.dataset.title);
        } else if (target.classList.contains('manage-permissions-btn')) {
            openManagePermissionsModal(taskId, target.dataset.title);
        }
    });
}

// 打开创建任务模态窗口
function openCreateTaskModal() {
    console.log('打开创建任务模态窗口');
    const modal = document.getElementById('create-task-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('create-task-form').reset();
    } else {
        console.error('找不到创建任务模态窗口');
    }
}

// 打开编辑任务模态窗口
function openEditTaskModal(taskId) {
    console.log('打开编辑任务模态窗口，任务ID:', taskId);
    const token = localStorage.getItem('token');
    
    fetch(apiUrl(`/tasks/${taskId}`), {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取任务详情失败');
        }
        return response.json();
    })
    .then(task => {
        document.getElementById('edit-task-id').value = task.id;
        document.getElementById('edit-task-title').value = task.title;
        document.getElementById('edit-task-description').value = task.description || '';
        
        const modal = document.getElementById('edit-task-modal');
        if (modal) {
            modal.style.display = 'flex';
        } else {
            console.error('找不到编辑任务模态窗口');
        }
    })
    .catch(error => {
        console.error('获取任务详情出错:', error);
        showMessage('获取任务详情失败', 'error');
    });
}

// 打开分享任务模态窗口
function openShareTaskModal(taskId, taskTitle) {
    console.log('打开分享任务模态窗口');
    const modal = document.getElementById('share-task-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('share-task-id').value = taskId;
        document.getElementById('share-task-title').textContent = taskTitle;
        document.getElementById('share-task-form').reset();
    } else {
        console.error('找不到分享任务模态窗口');
    }
}

// 打开管理权限模态窗口
function openManagePermissionsModal(taskId, taskTitle) {
    console.log('打开管理权限模态窗口');
    const modal = document.getElementById('manage-permissions-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('manage-permissions-title').textContent = taskTitle;
        
        // 加载任务权限列表
        loadTaskPermissions(taskId);
    } else {
        console.error('找不到管理权限模态窗口');
    }
}

// 加载任务权限列表
function loadTaskPermissions(taskId) {
    console.log('开始加载任务权限列表...');
    const token = localStorage.getItem('token');
    const tableBody = document.getElementById('permissions-table-body');
    
    if (!tableBody) {
        console.error('找不到权限表格元素');
        return;
    }
    
    tableBody.innerHTML = '<tr><td colspan="4" class="loading-text">加载中...</td></tr>';
    
    fetch(apiUrl(`/tasks/${taskId}/permissions`), {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 403) {
                return response.json().then(data => {
                    throw new Error(data.detail || '没有权限查看权限列表');
                });
            }
            throw new Error('加载权限列表失败');
        }
        return response.json();
    })
    .then(permissions => {
        console.log('成功获取权限数据:', permissions);
        renderPermissionsList(permissions, taskId);
        
        // 添加提示信息
        const currentUsername = localStorage.getItem('username');
        const isTaskCreator = permissions.some(p => 
            p.shared_by && p.shared_by.is_creator && p.shared_by.username === currentUsername
        );
    })
    .catch(error => {
        console.error('加载权限出错:', error);
        tableBody.innerHTML = `<tr><td colspan="4" class="error-text">${error.message || '加载权限列表失败，请重试'}</td></tr>`;
    });
}

// 渲染权限列表
function renderPermissionsList(permissions, taskId) {
    const tableBody = document.getElementById('permissions-table-body');
    const currentUsername = localStorage.getItem('username');
    
    if (!tableBody) {
        console.error('找不到权限表格元素');
        return;
    }
    
    if (permissions.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="no-data">暂无分享记录</td></tr>';
        return;
    }
    
    // 查找任务创建者
    let isTaskCreator = false;
    permissions.forEach(permission => {
        if (permission.shared_by && permission.shared_by.is_creator && permission.shared_by.username === currentUsername) {
            isTaskCreator = true;
        }
    });
    
    tableBody.innerHTML = '';
    permissions.forEach(permission => {
        // 不展示当前用户自己的权限
        if (permission.username === currentUsername) {
            return;
        }
        
        const row = document.createElement('tr');
        
        let permissionTypeText = '只读';
        if (permission.permission_type === 'admin') {
            permissionTypeText = '管理员';
        } else if (permission.permission_type === 'edit') {
            permissionTypeText = '编辑';
        }
        
        // 构建分享者信息
        let sharedByText = '';
        let canRevoke = false;
        
        if (permission.shared_by) {
            sharedByText = permission.shared_by.username;
            if (permission.shared_by.is_creator) {
                sharedByText += ' (创建者)';
            }
            
            // 判断是否可以取消分享：如果是任务创建者或是自己分享的
            canRevoke = isTaskCreator || permission.shared_by.username === currentUsername;
        }
        
        row.innerHTML = `
            <td>${permission.username}</td>
            <td>${permissionTypeText}</td>
            <td>${sharedByText}</td>
            <td>
                ${canRevoke ? 
                    `<button class="btn danger-btn revoke-permission-btn" 
                            style="background-color: #ff4d4f; color: white;"
                            data-task-id="${taskId}" 
                            data-username="${permission.username}">取消分享</button>` : 
                    `<span class="disabled-text" title="只有任务创建者或分享者可以取消">无法取消</span>`
                }
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // 添加取消分享按钮的事件监听
    addRevokePermissionListeners();
}

// 添加取消分享按钮的事件监听
function addRevokePermissionListeners() {
    document.querySelectorAll('.revoke-permission-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.dataset.taskId;
            const username = this.dataset.username;
            
            if (confirm(`确定要取消与用户 ${username} 的分享吗？`)) {
                revokePermission(taskId, username);
            }
        });
    });
}

// 取消分享
function revokePermission(taskId, username) {
    console.log('取消分享:', taskId, username);
    const token = localStorage.getItem('token');
    
    fetch(apiUrl(`/tasks/${taskId}/permissions/${username}`), {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            // 处理不同的错误状态
            if (response.status === 403) {
                return response.json().then(data => {
                    throw new Error(data.detail || '没有权限执行此操作');
                });
            }
            throw new Error('取消分享失败');
        }
        return response.json();
    })
    .then(data => {
        console.log('取消分享成功:', data);
        // 重新加载权限列表
        loadTaskPermissions(taskId);
        showMessage(`已取消与用户 ${username} 的分享`, 'success');
        // 触发页面刷新事件
        document.dispatchEvent(new Event('taskOperationComplete'));
    })
    .catch(error => {
        console.error('取消分享出错:', error);
        showMessage(error.message || '取消分享失败', 'error');
    });
}

// 关闭所有模态窗口
function closeAllModals() {
    console.log('关闭所有模态窗口');
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// 创建任务
function createTask() {
    console.log('创建新任务');
    const title = document.getElementById('create-task-title').value;
    const description = document.getElementById('create-task-description').value;
    const token = localStorage.getItem('token');
    
    fetch(apiUrl('/tasks/'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            title: title,
            description: description
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('创建任务失败');
        }
        return response.json();
    })
    .then(data => {
        console.log('任务创建成功:', data);
        closeAllModals();
        loadTasks();
        showMessage('任务创建成功', 'success');
    })
    .catch(error => {
        console.error('创建任务出错:', error);
        showMessage('创建任务失败', 'error');
    });
}

// 更新任务
function updateTask() {
    console.log('更新任务');
    const taskId = document.getElementById('edit-task-id').value;
    const title = document.getElementById('edit-task-title').value;
    const description = document.getElementById('edit-task-description').value;
    const token = localStorage.getItem('token');
    
    fetch(apiUrl(`/tasks/${taskId}`), {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            title: title,
            description: description
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('更新任务失败');
        }
        return response.json();
    })
    .then(data => {
        console.log('任务更新成功:', data);
        closeAllModals();
        loadTasks();
        showMessage('任务更新成功', 'success');
        // 触发页面刷新事件
        document.dispatchEvent(new Event('taskOperationComplete'));
    })
    .catch(error => {
        console.error('更新任务出错:', error);
        showMessage('更新任务失败', 'error');
    });
}

// 分享任务
function shareTask() {
    console.log('分享任务');
    const taskId = document.getElementById('share-task-id').value;
    const username = document.getElementById('share-task-username').value;
    const permission = document.getElementById('share-task-permission').value;
    const token = localStorage.getItem('token');
    
    fetch(apiUrl(`/tasks/${taskId}/permissions/`), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            username: username,
            permission_type: permission
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('分享任务失败');
        }
        return response.json();
    })
    .then(data => {
        console.log('任务分享成功:', data);
        closeAllModals();
        showMessage(`已成功分享任务给 ${username}`, 'success');
        // 触发页面刷新事件
        document.dispatchEvent(new Event('taskOperationComplete'));
    })
    .catch(error => {
        console.error('分享任务出错:', error);
        showMessage('分享任务失败', 'error');
    });
}

// 确认删除任务
function confirmDeleteTask(taskId, taskTitle) {
    if (confirm(`确定要删除任务"${taskTitle}"吗？此操作将删除该任务下的所有图片和权限，且不可恢复。`)) {
        deleteTask(taskId);
    }
}

// 删除任务
function deleteTask(taskId) {
    console.log('执行删除任务:', taskId);
    const token = localStorage.getItem('token');
    
    fetch(apiUrl(`/tasks/${taskId}`), {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('删除任务失败');
        }
        return response.json();
    })
    .then(data => {
        console.log('任务删除成功:', data);
        showMessage('任务删除成功', 'success');
        // 触发页面刷新事件
        document.dispatchEvent(new Event('taskOperationComplete'));
    })
    .catch(error => {
        console.error('删除任务出错:', error);
        showMessage('删除任务失败', 'error');
    });
}

// 显示消息提示
function showMessage(message, type) {
    console.log('显示消息:', message, '类型:', type);
    
    // 检查是否已存在消息元素
    let messageElement = document.querySelector('.message');
    
    // 如果不存在，创建一个新的
    if (!messageElement) {
        messageElement = document.createElement('div');
        messageElement.className = 'message';
        document.body.appendChild(messageElement);
    }
    
    // 设置消息内容和样式
    messageElement.textContent = message;
    messageElement.className = `message ${type}`;
}