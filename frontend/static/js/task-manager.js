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
        localStorage.removeItem('user_id');
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
    
    // 确保任务按ID降序排序
    const sortedTasks = [...tasks].sort((a, b) => b.id - a.id);
    
    // 先创建所有行并保持正确顺序
    const rows = sortedTasks.map(task => {
        const row = document.createElement('tr');
        // 直接使用数据库中的时间
        const createdAt = new Date(task.created_at);
        const formattedDate = createdAt.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        
        // 先设置基本信息，添加创建人字段
        row.innerHTML = `
            <td>${task.id}</td>
            <td>${task.title}</td>
            <td>${task.description || '无描述'}</td>
            <td>${task.owner ? task.owner.username : '未知'}</td>
            <td>${formattedDate}</td>
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
    console.log('打开分享任务模态窗口，任务ID:', taskId, '任务标题:', taskTitle);
    const modal = document.getElementById('share-task-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('share-task-id').value = taskId;
        document.getElementById('share-task-title').value = taskTitle;
    } else {
        console.error('找不到分享任务模态窗口');
    }
}

// 打开管理权限模态窗口
function openManagePermissionsModal(taskId, taskTitle) {
    console.log('打开管理权限模态窗口，任务ID:', taskId, '任务标题:', taskTitle);
    const modal = document.getElementById('manage-permissions-modal');
    if (modal) {
        modal.style.display = 'flex';
        // 更新模态窗口标题
        const titleElement = document.getElementById('manage-permissions-title');
        if (titleElement) {
            titleElement.textContent = taskTitle;
        }
        // 加载任务权限列表
        loadTaskPermissions(taskId);
    } else {
        console.error('找不到管理权限模态窗口');
    }
}

// 确认删除任务
function confirmDeleteTask(taskId, taskTitle) {
    console.log('确认删除任务，任务ID:', taskId, '任务标题:', taskTitle);
    const confirmation = confirm('您确定要删除这个任务吗？');
    if (confirmation) {
        deleteTask(taskId);
    }
}

// 删除任务
function deleteTask(taskId) {
    console.log('删除任务，任务ID:', taskId);
    const token = localStorage.getItem('token');
    
    fetch(apiUrl(`/tasks/${taskId}`), {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            console.error('删除任务失败:', response.status);
            showMessage('删除任务失败，请刷新页面重试', 'error');
            return;
        }
        showMessage('任务删除成功', 'success');
        loadTasks();
    })
    .catch(error => {
        console.error('删除任务出错:', error);
        showMessage('删除任务失败，请刷新页面重试', 'error');
    });
}

// 显示消息
function showMessage(message, type) {
    // 创建消息容器
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${type}`;
    
    // 创建消息内容
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = message;
    
    // 创建关闭按钮
    const closeButton = document.createElement('button');
    closeButton.className = 'message-close';
    closeButton.innerHTML = '&times;';
    closeButton.onclick = () => messageContainer.remove();
    
    // 组装消息
    messageContent.appendChild(closeButton);
    messageContainer.appendChild(messageContent);
    
    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        .message-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 9999;
            min-width: 300px;
            max-width: 80%;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: messageFadeIn 0.3s ease;
        }
        
        .message-content {
            position: relative;
            padding-right: 30px;
            font-size: 16px;
            line-height: 1.5;
        }
        
        .message-close {
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: #666;
            padding: 0 5px;
        }
        
        .message-close:hover {
            color: #333;
        }
        
        .success {
            background-color: #f0f9eb;
            border: 1px solid #e1f3d8;
            color: #67c23a;
        }
        
        .error {
            background-color: #fef0f0;
            border: 1px solid #fde2e2;
            color: #f56c6c;
        }
        
        @keyframes messageFadeIn {
            from {
                opacity: 0;
                transform: translate(-50%, -60%);
            }
            to {
                opacity: 1;
                transform: translate(-50%, -50%);
            }
        }
    `;
    
    // 添加样式到页面
    if (!document.getElementById('message-style')) {
        style.id = 'message-style';
        document.head.appendChild(style);
    }
    
    // 添加到页面
    document.body.appendChild(messageContainer);
    
    // 3秒后自动关闭
    setTimeout(() => {
        messageContainer.style.animation = 'messageFadeOut 0.3s ease';
        setTimeout(() => messageContainer.remove(), 300);
    }, 3000);
}

// 关闭所有模态窗口
function closeAllModals() {
    console.log('关闭所有模态窗口');
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.style.display = 'none';
    });
}

// 创建任务
function createTask() {
    console.log('创建新任务');
    const title = document.getElementById('create-task-title').value;
    const description = document.getElementById('create-task-description').value;
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('user_id');
    
    if (!userId) {
        showMessage('用户ID不存在，请重新登录', 'error');
        return;
    }
    
    const requestData = {
        title: title,
        description: description,
        user_id: parseInt(userId)
    };
    
    console.log('发送创建任务请求:', requestData);
    
    fetch(apiUrl('/tasks/'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || '创建任务失败');
            });
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
        showMessage(error.message || '创建任务失败', 'error');
    });
}

// 更新任务
function updateTask() {
    console.log('更新任务');
    const taskId = document.getElementById('edit-task-id').value;
    const title = document.getElementById('edit-task-title').value;
    const description = document.getElementById('edit-task-description').value;
    const token = localStorage.getItem('token');
    
    const requestData = {
        title: title,
        description: description
    };
    
    console.log('发送的请求数据:', requestData);
    
    fetch(apiUrl(`/tasks/${taskId}`), {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            // 尝试解析错误响应为 JSON
            return response.text().then(text => {
                try {
                    const errorData = JSON.parse(text);
                    throw new Error(errorData.detail || '更新任务失败');
                } catch (e) {
                    // 如果不是 JSON 格式，使用状态文本
                    throw new Error(`更新任务失败: ${response.statusText}`);
                }
            });
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
        showMessage(error.message || '更新任务失败', 'error');
    });
}

// 加载任务权限列表
function loadTaskPermissions(taskId) {
    console.log('加载任务权限列表，任务ID:', taskId);
    const token = localStorage.getItem('token');
    const permissionsTableBody = document.getElementById('permissions-table-body');
    
    if (!permissionsTableBody) {
        console.error('找不到权限表格元素');
        return;
    }
    
    // 显示加载中
    permissionsTableBody.innerHTML = '<tr><td colspan="4" class="loading-text">加载中...</td></tr>';
    
    // 获取任务权限列表
    fetch(apiUrl(`/tasks/${taskId}/permissions`), {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('获取权限列表失败');
        }
        return response.json();
    })
    .then(permissions => {
        console.log('获取到权限列表:', permissions);
        
        if (!permissions || permissions.length === 0) {
            permissionsTableBody.innerHTML = '<tr><td colspan="4" class="no-data">暂无权限记录</td></tr>';
            return;
        }
        
        // 清空表格
        permissionsTableBody.innerHTML = '';
        
        // 添加权限记录
        permissions.forEach(permission => {
            const row = document.createElement('tr');
            
            // 获取分享来源信息
            let sharedByText = '-';
            if (permission.shared_by) {
                sharedByText = permission.shared_by.is_creator ? 
                    `${permission.shared_by.username} (创建者)` : 
                    permission.shared_by.username;
            }
            
            row.innerHTML = `
                <td>${permission.username}</td>
                <td>${getPermissionTypeText(permission.permission_type)}</td>
                <td>${sharedByText}</td>
                <td>
                    <button class="btn danger-btn remove-permission-btn" 
                            data-username="${permission.username}" 
                            data-task-id="${taskId}">
                        删除权限
                    </button>
                </td>
            `;
            
            permissionsTableBody.appendChild(row);
        });
        
        // 添加删除权限按钮的事件监听
        addRemovePermissionButtonListeners();
    })
    .catch(error => {
        console.error('加载权限列表失败:', error);
        permissionsTableBody.innerHTML = '<tr><td colspan="4" class="error-text">加载失败，请刷新页面重试</td></tr>';
    });
}

// 获取权限类型的显示文本
function getPermissionTypeText(type) {
    switch (type) {
        case 'view':
            return '查看';
        case 'edit':
            return '编辑';
        case 'admin':
            return '管理员';
        default:
            return type;
    }
}

// 添加删除权限按钮的事件监听
function addRemovePermissionButtonListeners() {
    document.querySelectorAll('.remove-permission-btn').forEach(button => {
        button.addEventListener('click', function() {
            const username = this.dataset.username;
            const taskId = this.dataset.taskId;
            
            if (confirm(`确定要删除用户 "${username}" 的权限吗？`)) {
                removeTaskPermission(taskId, username);
            }
        });
    });
}

// 删除任务权限
function removeTaskPermission(taskId, username) {
    console.log('删除任务权限，任务ID:', taskId, '用户名:', username);
    const token = localStorage.getItem('token');
    
    fetch(apiUrl(`/tasks/${taskId}/permissions/${username}`), {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || '删除权限失败');
            });
        }
        return response.json();
    })
    .then(() => {
        console.log('权限删除成功');
        showMessage('权限删除成功', 'success');
        // 重新加载权限列表
        loadTaskPermissions(taskId);
    })
    .catch(error => {
        console.error('删除权限失败:', error);
        showMessage(error.message || '删除权限失败', 'error');
    });
}

// 分享任务
function shareTask() {
    console.log('分享任务');
    const taskId = document.getElementById('share-task-id').value;
    const username = document.getElementById('share-task-username').value;
    const permissionType = document.getElementById('share-task-permission').value;
    const token = localStorage.getItem('token');
    
    if (!username) {
        showMessage('请输入用户名', 'error');
        return;
    }
    
    const requestData = {
        username: username,
        permission_type: permissionType
    };
    
    console.log('发送分享任务请求:', requestData);
    
    fetch(apiUrl(`/tasks/${taskId}/permissions/`), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || '分享任务失败');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('任务分享成功:', data);
        closeAllModals();
        showMessage('任务分享成功', 'success');
    })
    .catch(error => {
        console.error('分享任务出错:', error);
        showMessage(error.message || '分享任务失败', 'error');
    });
}