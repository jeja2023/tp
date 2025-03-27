// 全局变量
let currentUser = null;
let currentTask = null;

// 添加API前缀的辅助函数
function apiUrl(url) {
    return url.startsWith('/api') ? url : `/api${url}`;
}

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否已登录
    checkAuthStatus();
    
    // 注册表单提交事件
    setupAuthForms();
    
    // 设置任务相关事件
    setupTaskEvents();
    
    // 设置图片上传相关事件
    setupImageEvents();
    
    // 设置实时预览
    setupPreviewEvents();
});

// 检查认证状态
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    if (token) {
        // 验证token
        fetch(apiUrl('/users/me'), {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                // Token无效，清除并显示登录表单
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                showLoginForm();
                throw new Error('Authentication failed');
            }
        })
        .then(userData => {
            currentUser = userData;
            // 更新localStorage中的username
            localStorage.setItem('username', userData.username);
            showMainApp();
            loadTasks();
        })
        .catch(error => {
            console.error('Auth check error:', error);
            showLoginForm();
        });
    } else {
        // 无token，显示登录表单
        showLoginForm();
    }
}

// 设置认证表单
function setupAuthForms() {
    // 登录表单提交
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            console.log('Attempting login for user:', username);
            
            // 创建表单数据
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            
            // 发送登录请求
            fetch(apiUrl('/token'), {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log('Login response status:', response.status);
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Login failed with status: ' + response.status);
                }
            })
            .then(data => {
                console.log('Login successful, token received');
                // 保存token和用户名
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('username', data.username);
                // 直接跳转到主页
                window.location.href = '/index';
            })
            .catch(error => {
                console.error('Login error:', error);
                alert('登录失败，请检查用户名和密码');
            });
        });
    }
    
    // 注册表单提交
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('register-username').value;
            const password = document.getElementById('register-password').value;
            
            // 发送注册请求
            fetch('/users/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Registration failed');
                }
            })
            .then(data => {
                alert('注册成功，请登录');
                showLoginForm();
            })
            .catch(error => {
                console.error('Registration error:', error);
                alert('注册失败，可能用户名已存在');
            });
        });
    }
    
    // 切换登录/注册表单链接
    const loginLink = document.getElementById('login-link');
    const registerLink = document.getElementById('register-link');
    
    if (loginLink) {
        loginLink.addEventListener('click', function(e) {
            e.preventDefault();
            showLoginForm();
        });
    }
    
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            showRegisterForm();
        });
    }
}

// 设置任务相关事件
function setupTaskEvents() {
    // 创建任务表单
    const createTaskForm = document.getElementById('create-task-form');
    if (createTaskForm) {
        createTaskForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const title = document.getElementById('task-title').value;
            const description = document.getElementById('task-description').value;
            
            createTask(title, description);
        });
    }
    
    // 返回任务列表按钮
    const backToTasksBtn = document.getElementById('back-to-tasks-btn');
    if (backToTasksBtn) {
        backToTasksBtn.addEventListener('click', function() {
            showTasksSection();
        });
    }
}

// 设置图片上传相关事件
function setupImageEvents() {
    const uploadForm = document.getElementById('upload-form');
    const showMapBtn = document.getElementById('show-map-btn');
    
    if (uploadForm) {
        console.log('找到上传表单，设置提交事件');
        
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('上传表单提交触发');
            
            // 检查当前任务
            if (!currentTask || !currentTask.id) {
                console.error('上传失败：无效的当前任务', currentTask);
                alert('请先选择一个任务');
                return;
            }
            
            // 获取文件
            const fileInput = document.getElementById('file');
            if (!fileInput.files.length) {
                console.error('上传失败：未选择文件');
                alert('请选择文件');
                return;
            }
            
            console.log('准备上传文件:', fileInput.files[0].name);
            
            try {
                // 创建表单数据
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('task_id', currentTask.id);
                
                // 添加图片信息 - 使用正确的字段ID
                const time = document.getElementById('time').value;
                const location = document.getElementById('location').value;
                const transportation = document.getElementById('transportation').value;
                
                if (!time || !location || !transportation) {
                    console.error('上传失败：缺少必填信息', { time, location, transportation });
                    alert('请填写所有必填信息（时间、地点、交通方式）');
                    return;
                }
                
                formData.append('time', time);
                formData.append('location', location);
                formData.append('transportation', transportation);
                
                // 添加GPS信息
                const latitude = document.getElementById('gps-latitude').value;
                const longitude = document.getElementById('gps-longitude').value;
                
                if (latitude && longitude) {
                    formData.append('gps_latitude', latitude);
                    formData.append('gps_longitude', longitude);
                }
                
                // 添加人员信息
                const peopleContainer = document.getElementById('people-container');
                if (peopleContainer) {
                    const personForms = peopleContainer.querySelectorAll('.person-form');
                    
                    const people = [];
                    personForms.forEach(function(form) {
                        const name = form.querySelector('.person-name').value;
                        const id = form.querySelector('.person-id').value;
                        const household = form.querySelector('.person-household').value;
                        
                        if (name || id || household) {
                            people.push({
                                name: name,
                                id_number: id,
                                household_registration: household
                            });
                        }
                    });
                    
                    if (people.length > 0) {
                        formData.append('people_involved', JSON.stringify(people));
                    }
                }
                
                // 确保formData有效后再上传图片
                if (formData) {
                    console.log('调用uploadImage函数，传递formData');
                    uploadImage(formData);
                } else {
                    throw new Error('表单数据创建失败');
                }
            } catch (error) {
                console.error('准备上传数据时出错:', error);
                alert('准备上传数据时出错: ' + error.message);
            }
        });
    }
    
    // 添加显示/隐藏地图的事件处理
    if (showMapBtn) {
        showMapBtn.addEventListener('click', function() {
            console.log('显示/隐藏地图按钮点击');
            
            if (typeof toggleMapContainer === 'function') {
                console.log('使用 toggleMapContainer 函数');
                toggleMapContainer();
            } else if (window.mapUtils && typeof window.mapUtils.toggleMapContainer === 'function') {
                console.log('使用 window.mapUtils.toggleMapContainer 函数');
                window.mapUtils.toggleMapContainer();
            } else {
                console.log('使用内置切换逻辑');
                const mapContainer = document.getElementById('map-container');
                if (mapContainer) {
                    if (mapContainer.style.display === 'none' || mapContainer.style.display === '') {
                        console.log('地图从隐藏变为显示');
                        mapContainer.style.display = 'block';
                        // 如果地图未初始化，初始化地图
                        if (typeof initMap === 'function') {
                            console.log('使用 initMap 函数');
                            initMap();
                        } else if (window.initMap) {
                            console.log('使用 window.initMap 函数');
                            window.initMap();
                        }
                        // 更新按钮文本
                        showMapBtn.textContent = '隐藏地图';
                        console.log('按钮文本更新为：隐藏地图');
                    } else {
                        console.log('地图从显示变为隐藏');
                        mapContainer.style.display = 'none';
                        // 更新按钮文本
                        showMapBtn.textContent = '显示地图';
                        console.log('按钮文本更新为：显示地图');
                    }
                } else {
                    console.error('找不到地图容器 #map-container');
                }
            }
        });
    }
    
    // 获取当前位置按钮
    const getLocationBtn = document.getElementById('get-location-btn');
    if (getLocationBtn) {
        getLocationBtn.addEventListener('click', function() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const latitude = position.coords.latitude;
                        const longitude = position.coords.longitude;
                        
                        // 更新输入框
                        document.getElementById('gps-latitude').value = latitude;
                        document.getElementById('gps-longitude').value = longitude;
                        
                        // 更新预览
                        updatePreview();
                        
                        // 如果有地图功能，在地图上标记位置
                        if (typeof markLocationOnMap === 'function') {
                            // 显示地图
                            document.getElementById('map-container').style.display = 'block';
                            // 初始化并标记
                            if (typeof initMap === 'function') initMap();
                            markLocationOnMap(longitude, latitude);
                        }
                        
                        // 尝试获取地址
                        if (typeof getAddressByCoords === 'function') {
                            getAddressByCoords(longitude, latitude);
                        }
                    },
                    function(error) {
                        console.error('获取位置信息失败:', error);
                        alert('获取位置信息失败，请手动输入坐标');
                    }
                );
            } else {
                alert('您的浏览器不支持地理定位');
            }
        });
    }
}

// 设置实时预览事件
function setupPreviewEvents() {
    // 监听图片信息输入的变化
    const infoInputs = document.querySelectorAll('.info-column input, .info-column textarea');
    infoInputs.forEach(input => {
        input.addEventListener('input', updatePreview);
    });
}

// 显示登录表单
function showLoginForm() {
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('register-section').style.display = 'none';
    document.getElementById('main-app').style.display = 'none';
}

// 显示注册表单
function showRegisterForm() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('register-section').style.display = 'block';
    document.getElementById('main-app').style.display = 'none';
}

// 显示主应用
function showMainApp() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('register-section').style.display = 'none';
    document.getElementById('main-app').style.display = 'block';
    
    // 默认显示任务列表
    showTasksSection();
    
    // 显示用户名
    const userDisplay = document.getElementById('user-display');
    if (userDisplay && currentUser) {
        userDisplay.textContent = currentUser.username;
    }
}

// 显示任务列表部分
function showTasksSection() {
    document.getElementById('tasks-section').style.display = 'block';
    document.getElementById('task-detail-section').style.display = 'none';
    
    // 重置当前任务
    currentTask = null;
}

// 显示任务详情部分
function showTaskDetailSection(task) {
    if (!task || !task.id) {
        console.error('无法显示任务详情：无效的任务对象', task);
        alert('无效的任务，请重新选择');
        return;
    }
    
    console.log('显示任务详情', task);
    
    document.getElementById('tasks-section').style.display = 'none';
    document.getElementById('task-detail-section').style.display = 'block';
    
    // 设置当前任务
    currentTask = task;
    
    // 显示任务信息
    document.getElementById('current-task-title').textContent = task.title;
    document.getElementById('current-task-description').textContent = task.description || '无描述';
    
    // 加载任务图片
    loadImages(task.id);
    
    // 设置当前日期时间为默认值
    const now = new Date();
    const timeInput = document.getElementById('time');
    if (timeInput) {
        now.setMilliseconds(0); // 去掉毫秒
        timeInput.value = now.toISOString().slice(0, 19);
    }
}

// 加载用户任务
function loadTasks() {
    const token = localStorage.getItem('token');
    const taskList = document.getElementById('task-list');
    
    if (!token) {
        console.error('No token found, redirecting to login');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1000);
        return;
    }
    
    // 显示加载消息
    taskList.innerHTML = '<tr><td colspan="4" class="loading">加载中...</td></tr>';
    
    fetch(apiUrl('/tasks/'), {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Failed to load tasks');
        }
    })
    .then(tasks => {
        // 更新任务列表
        taskList.innerHTML = '';
        
        if (tasks.length === 0) {
            taskList.innerHTML = '<p>您还没有任务，请创建新任务</p>';
            return;
        }
        
        tasks.forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.className = 'task-card';
            taskItem.innerHTML = `
                <h3>${task.title}</h3>
                <p>${task.description || '无描述'}</p>
                <p>创建时间: ${new Date(task.created_at).toLocaleString()}</p>
                <button class="view-task-btn" data-id="${task.id}">进入任务</button>
            `;
            taskList.appendChild(taskItem);
            
            // 添加查看任务按钮事件
            const viewBtn = taskItem.querySelector('.view-task-btn');
            if (viewBtn) {
                viewBtn.addEventListener('click', function() {
                    const taskId = parseInt(this.getAttribute('data-id'));
                    
                    // 获取完整任务信息
                    fetch(apiUrl(`/tasks/${taskId}`), {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    })
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        } else {
                            throw new Error('Failed to load task details');
                        }
                    })
                    .then(taskDetails => {
                        showTaskDetailSection(taskDetails);
                    })
                    .catch(error => {
                        console.error('Load task details error:', error);
                        alert('获取任务详情失败');
                    });
                });
            }
        });
    })
    .catch(error => {
        console.error('Load tasks error:', error);
    });
}

// 创建新任务
function createTask(title, description) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    fetch('/tasks/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: title,
            description: description
        })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Failed to create task');
        }
    })
    .then(task => {
        // 清空表单
        document.getElementById('task-title').value = '';
        document.getElementById('task-description').value = '';
        
        alert('任务创建成功');
        
        // 重新加载任务列表
        loadTasks();
    })
    .catch(error => {
        console.error('Create task error:', error);
        alert('创建任务失败');
    });
}

// 加载任务图片
function loadImages(taskId) {
    const token = localStorage.getItem('token');
    const imageContainer = document.getElementById('task-images');
    
    if (!token || !imageContainer) return;
    
    imageContainer.innerHTML = '<p class="loading">加载图片中...</p>';
    
    fetch(apiUrl(`/tasks/${taskId}/images`), {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Failed to load images');
        }
    })
    .then(images => {
        // 更新图片列表
        const imageList = document.getElementById('image-list');
        if (imageList) {
            imageList.innerHTML = '';
            
            if (images.length === 0) {
                imageList.innerHTML = '<p>此任务暂无图片</p>';
                return;
            }
            
            images.forEach(image => {
                const imageItem = document.createElement('div');
                imageItem.className = 'image-card';
                imageItem.innerHTML = `
                    <img src="/uploads/${currentTask.id}/${image.file_path}" alt="图片">
                    <p>序号: ${image.sequence_number}</p>
                    <p>时间: ${new Date(image.time).toLocaleString()}</p>
                    <p>地点: ${image.location}</p>
                    <p>交通方式: ${image.transportation}</p>
                    <button class="view-image-btn" data-id="${image.id}">查看详情</button>
                `;
                imageList.appendChild(imageItem);
                
                // 添加查看图片详情按钮事件
                const viewBtn = imageItem.querySelector('.view-image-btn');
                if (viewBtn) {
                    viewBtn.addEventListener('click', function() {
                        const imageId = parseInt(this.getAttribute('data-id'));
                        showImageDetails(imageId);
                    });
                }
            });
        }
    })
    .catch(error => {
        console.error('Load images error:', error);
    });
}

// 上传图片
function uploadImage(formData) {
    const token = localStorage.getItem('token');
    if (!token) {
        console.error('上传失败：用户未登录');
        alert('请先登录');
        return;
    }
    
    if (!formData || typeof formData.get !== 'function') {
        console.error('上传失败：无效的表单数据', formData);
        alert('表单数据无效');
        return;
    }
    
    const taskId = formData.get('task_id');
    if (!taskId) {
        console.error('上传失败：无效的任务ID');
        alert('无效的任务ID，请重新进入任务');
        return;
    }
    
    // 检查必填字段
    const time = formData.get('time');
    const location = formData.get('location');
    const transportation = formData.get('transportation');
    
    if (!time || !location || !transportation) {
        console.error('上传失败：缺少必填信息', { time, location, transportation });
        alert('请填写所有必填信息（时间、地点、交通方式）');
        return;
    }
    
    // 显示上传中提示
    const uploadButton = document.querySelector('#upload-form button[type="submit"]');
    const originalText = uploadButton.textContent;
    uploadButton.textContent = '上传中...';
    uploadButton.disabled = true;
    
    console.log('开始上传图片，任务ID:', taskId);
    
    fetch(apiUrl(`/images/${taskId}`), {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    })
    .then(response => {
        console.log('Upload response status:', response.status);
        if (response.ok) {
            return response.json();
        } else {
            return response.text().then(text => {
                throw new Error(`Failed to upload image: ${response.status} ${text}`);
            });
        }
    })
    .then(image => {
        console.log('Upload successful:', image);
        // 重新加载图片列表
        loadImages(currentTask.id);
        
        // 清空表单和预览
        document.getElementById('upload-form').reset();
        document.getElementById('image-preview').style.display = 'none';
        document.getElementById('info-preview').innerHTML = '<p>请上传图片并填写信息</p>';
        
        // 清空人员信息
        const peopleContainer = document.getElementById('people-container');
        if (peopleContainer) {
            // 保留第一个表单但清空其内容
            const firstForm = peopleContainer.querySelector('.person-form');
            if (firstForm) {
                const inputs = firstForm.querySelectorAll('input');
                inputs.forEach(input => {
                    input.value = '';
                });
                
                // 删除其他表单
                while (peopleContainer.children.length > 1) {
                    peopleContainer.removeChild(peopleContainer.lastChild);
                }
            }
        }
        
        alert('图片上传成功');
    })
    .catch(error => {
        console.error('Upload image error:', error);
        alert('图片上传失败: ' + error.message);
    })
    .finally(() => {
        // 恢复上传按钮的文本和状态
        uploadButton.textContent = originalText;
        uploadButton.disabled = false;
    });
}

// 更新预览
function updatePreview() {
    const preview = document.getElementById('info-preview');
    const imagePreview = document.getElementById('image-preview');
    
    if (!preview) return;
    
    // 获取表单数据
    const time = document.getElementById('time').value;
    const location = document.getElementById('location').value;
    const transportation = document.getElementById('transportation').value;
    const gpsLat = document.getElementById('gps-latitude').value;
    const gpsLng = document.getElementById('gps-longitude').value;
    
    // 构建预览HTML
    let previewHTML = '';
    
    // 添加基本信息
    if (time) {
        const timeDate = new Date(time);
        previewHTML += '<div class="preview-item"><strong>时间:</strong> ' + timeDate.toLocaleString() + '</div>';
    }
    
    if (location) {
        previewHTML += '<div class="preview-item"><strong>地点:</strong> ' + location + '</div>';
    }
    
    if (transportation) {
        previewHTML += '<div class="preview-item"><strong>交通方式:</strong> ' + transportation + '</div>';
    }
    
    // 添加GPS信息
    if (gpsLat && gpsLng) {
        previewHTML += '<div class="preview-item"><strong>GPS坐标:</strong> ' + gpsLat + ', ' + gpsLng + '</div>';
    }
    
    // 添加人员信息
    const personForms = document.querySelectorAll('.person-form');
    if (personForms.length > 0) {
        let hasPersonInfo = false;
        let personHTML = '<div class="preview-item"><strong>相关人员:</strong><ul>';
        
        personForms.forEach(form => {
            const name = form.querySelector('.person-name').value;
            const idNumber = form.querySelector('.person-id').value;
            const household = form.querySelector('.person-household').value;
            
            if (name || idNumber || household) {
                hasPersonInfo = true;
                personHTML += '<li>' + 
                    (name ? '姓名: ' + name + ' ' : '') +
                    (idNumber ? '身份证: ' + idNumber + ' ' : '') +
                    (household ? '户籍: ' + household : '') +
                    '</li>';
            }
        });
        
        personHTML += '</ul></div>';
        
        if (hasPersonInfo) {
            previewHTML += personHTML;
        }
    }
    
    // 更新预览区域
    if (previewHTML) {
        preview.innerHTML = previewHTML;
    } else {
        preview.innerHTML = '<p>请上传图片并填写信息</p>';
    }
}

// 图片预览
function previewImage(event) {
    const preview = document.getElementById('image-preview');
    const file = event.target.files[0];
    
    if (file) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            updatePreview();
        }
        
        reader.readAsDataURL(file);
    } else {
        preview.src = '#';
        preview.style.display = 'none';
        updatePreview();
    }
}

// 显示图片详情
function showImageDetails(imageId) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const modalContent = document.querySelector('#image-modal .modal-content');
    if (!modalContent) return;
    
    modalContent.innerHTML = '<p class="loading">加载中...</p>';
    document.getElementById('image-modal').style.display = 'block';
    
    fetch(apiUrl(`/images/${imageId}`), {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Failed to load image details');
        }
    })
    .then(image => {
        // 创建模态框显示图片详情
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close">&times;</span>
                <h2>图片详情</h2>
                <img src="/uploads/${currentTask.id}/${image.file_path}" alt="图片" style="max-width:100%;">
                <p>序号: ${image.sequence_number}</p>
                <p>时间: ${new Date(image.time).toLocaleString()}</p>
                <p>地点: ${image.location}</p>
                <p>交通方式: ${image.transportation}</p>
                ${image.gps_latitude && image.gps_longitude ? 
                    `<p>GPS坐标: ${image.gps_latitude}, ${image.gps_longitude}</p>` : ''}
                
                ${image.people_involved && image.people_involved.length > 0 ? `
                <h3>相关人员</h3>
                <ul>
                    ${image.people_involved.map(person => `
                        <li>
                            <p>姓名: ${person.name}</p>
                            <p>身份证号: ${person.id_number}</p>
                            <p>户籍地: ${person.household_registration}</p>
                        </li>
                    `).join('')}
                </ul>
                ` : ''}
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 关闭按钮事件
        const closeBtn = modal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                document.body.removeChild(modal);
            });
        }
        
        // 点击模态框外部关闭
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                document.body.removeChild(modal);
            }
        });
    })
    .catch(error => {
        console.error('Load image details error:', error);
    });
}

// 退出登录
function logout() {
    localStorage.removeItem('token');
    currentUser = null;
    currentTask = null;
    showLoginForm();
} 