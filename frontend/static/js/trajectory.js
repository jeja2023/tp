// 显示消息提示的全局函数
window.showMessage = function(message, type = 'info') {
    // 检查是否已存在消息容器
    let messageContainer = document.querySelector('.message-container');
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.className = 'message-container';
        messageContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(messageContainer);
    }

    // 创建消息元素
    const messageElement = document.createElement('div');
    messageElement.className = `message message-${type}`;
    messageElement.style.cssText = `
        padding: 10px 20px;
        margin-bottom: 10px;
        border-radius: 4px;
        color: white;
        background-color: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease-out;
    `;
    messageElement.textContent = message;

    // 添加消息到容器
    messageContainer.appendChild(messageElement);

    // 8秒后自动移除消息
    setTimeout(() => {
        messageElement.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => messageContainer.removeChild(messageElement), 300);
    }, 8000);
};

// 生成轨迹Excel文件
window.generateTrack = async function() {
    try {
        window.showMessage('正在生成轨迹表...', 'info');
        
        // 获取当前任务ID
        const taskId = new URLSearchParams(window.location.search).get('id');
        if (!taskId) {
            throw new Error('未找到任务ID');
        }
        
        console.log(`正在为任务ID ${taskId} 生成轨迹表`);
        const response = await authenticatedFetch(`/api/trajectory/excel/${taskId}`, {
            method: 'GET'
        });

        if (!response.ok) {
            console.error(`生成轨迹表接口返回错误: ${response.status}`);
            const errorText = await response.text();
            console.error(`错误详情: ${errorText}`);
            throw new Error('生成轨迹表失败');
        }

        const result = await response.json();
        console.log('生成轨迹表结果:', result);
        
        if (result.filename) {
            // 使用filename字段
            const filename = result.filename;
            console.log(`生成的文件名: ${filename}`);
            
            // 构建正确的预览和下载URL
            const previewUrl = `/api/trajectory/preview/${encodeURIComponent(filename)}`;
            const downloadUrl = `/api/trajectory/download-file/${encodeURIComponent(filename)}`;
            
            console.log(`预览URL: ${previewUrl}`);
            console.log(`下载URL: ${downloadUrl}`);
            
            // 添加文件链接到页面
            addFileLink(filename, previewUrl, downloadUrl, 'excel');
            
            // 保存文件信息到本地存储，以便页面刷新后恢复
            saveFileToLocalStorage(taskId, filename, previewUrl, downloadUrl, 'excel');
            
            window.showMessage('轨迹表已生成', 'success');
        } else {
            throw new Error('未获取到文件名');
        }
    } catch (error) {
        console.error('生成轨迹表失败:', error);
        window.showMessage('生成轨迹表失败: ' + error.message, 'error');
    }
};

// 生成轨迹报告
window.generateReport = async function() {
    try {
        window.showMessage('正在生成轨迹报告...', 'info');
        
        // 获取当前任务ID
        const taskId = new URLSearchParams(window.location.search).get('id');
        if (!taskId) {
            throw new Error('未找到任务ID');
        }
        
        console.log(`正在为任务ID ${taskId} 生成轨迹报告`);
        const response = await authenticatedFetch(`/api/trajectory/report/${taskId}`, {
            method: 'GET'
        });

        if (!response.ok) {
            console.error(`生成轨迹报告接口返回错误: ${response.status}`);
            const errorText = await response.text();
            console.error(`错误详情: ${errorText}`);
            throw new Error('生成轨迹报告失败');
        }

        const result = await response.json();
        console.log('生成轨迹报告结果:', result);
        
        if (result.filename) {
            // 使用filename字段
            const filename = result.filename;
            console.log(`生成的文件名: ${filename}`);
            
            // 构建正确的预览和下载URL
            const previewUrl = `/api/trajectory/preview/${encodeURIComponent(filename)}`;
            const downloadUrl = `/api/trajectory/download-file/${encodeURIComponent(filename)}`;
            
            console.log(`预览URL: ${previewUrl}`);
            console.log(`下载URL: ${downloadUrl}`);
            
            // 添加文件链接到页面
            addFileLink(filename, previewUrl, downloadUrl, 'report');
            
            // 保存文件信息到本地存储，以便页面刷新后恢复
            saveFileToLocalStorage(taskId, filename, previewUrl, downloadUrl, 'report');
            
            window.showMessage('轨迹报告已生成', 'success');
        } else {
            throw new Error('未获取到文件名');
        }
    } catch (error) {
        console.error('生成轨迹报告失败:', error);
        window.showMessage('生成轨迹报告失败: ' + error.message, 'error');
    }
};

// 保存文件信息到localStorage
function saveFileToLocalStorage(taskId, filename, previewUrl, downloadUrl, type) {
    try {
        // 获取当前任务的已生成文件列表
        const storageKey = `task_${taskId}_files`;
        let taskFiles = JSON.parse(localStorage.getItem(storageKey) || '[]');
        
        // 检查文件是否已存在
        const existingFileIndex = taskFiles.findIndex(file => file.filename === filename);
        
        // 如果存在，更新文件信息；否则添加新文件
        const fileInfo = {
            filename,
            previewUrl,
            downloadUrl,
            type,
            createdAt: new Date().toISOString()
        };
        
        if (existingFileIndex >= 0) {
            taskFiles[existingFileIndex] = fileInfo;
        } else {
            taskFiles.push(fileInfo);
        }
        
        // 保存更新后的文件列表
        localStorage.setItem(storageKey, JSON.stringify(taskFiles));
        console.log(`已保存文件信息到本地存储: ${filename}`);
    } catch (error) {
        console.error('保存文件信息到本地存储失败:', error);
    }
}

// 从localStorage加载文件列表并显示
window.loadFilesFromLocalStorage = function() {
    try {
        // 获取当前任务ID
        const taskId = new URLSearchParams(window.location.search).get('id');
        if (!taskId) return;
        
        // 获取当前任务的已生成文件列表
        const storageKey = `task_${taskId}_files`;
        const taskFiles = JSON.parse(localStorage.getItem(storageKey) || '[]');
        
        if (taskFiles.length === 0) {
            console.log('本地存储中没有找到文件信息');
            return;
        }
        
        console.log(`从本地存储加载了 ${taskFiles.length} 个文件`);
        
        // 显示所有文件
        taskFiles.forEach(file => {
            addFileLink(file.filename, file.previewUrl, file.downloadUrl, file.type);
        });
    } catch (error) {
        console.error('从本地存储加载文件信息失败:', error);
    }
};

// 添加文件链接到页面
function addFileLink(filename, previewUrl, downloadUrl, type) {
    // 显示文件链接容器
    const container = document.getElementById('generated-files-container');
    container.style.display = 'block';
    
    const filesList = document.getElementById('generated-files-list');
    
    // 检查是否已经存在相同的文件链接
    const existingItems = filesList.querySelectorAll('.file-item');
    let fileExists = false;
    
    existingItems.forEach(item => {
        const linkElement = item.querySelector('a');
        if (linkElement && linkElement.textContent === filename) {
            fileExists = true;
            // 闪烁效果提示用户该文件已经存在
            item.style.animation = 'flash 0.5s';
            setTimeout(() => {
                item.style.animation = '';
            }, 500);
        }
    });
    
    if (fileExists) {
        return; // 如果文件已存在，不再添加
    }
    
    // 创建文件项容器
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.style.cssText = `
        display: flex;
        align-items: center;
        margin: 10px 0;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    `;
    
    // 文件图标
    const icon = document.createElement('i');
    icon.className = type === 'excel' ? 'fas fa-table' : 'fas fa-file-word';
    icon.style.cssText = `
        font-size: 18px;
        margin-right: 10px;
        color: ${type === 'excel' ? '#217346' : '#2b579a'};
    `;
    
    // 创建预览链接
    const link = document.createElement('a');
    link.href = '#'; // 使用JavaScript控制预览打开方式，而不是直接跳转
    link.textContent = filename;
    link.title = '点击预览文件';
    link.style.cssText = `
        flex: 1;
        color: #0366d6;
        text-decoration: none;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        cursor: pointer;
    `;
    
    // 使用点击事件来控制预览
    link.onclick = function(e) {
        e.preventDefault(); // 阻止默认行为
        // 在新标签页中打开预览链接
        const previewWin = window.open(previewUrl, '_blank');
        
        // 检查是否成功打开了窗口
        if (!previewWin || previewWin.closed || typeof previewWin.closed == 'undefined') {
            console.error('预览窗口被浏览器拦截或无法打开');
            window.showMessage('预览窗口被浏览器拦截，请允许弹出窗口或直接下载文件查看', 'error');
            
            // 作为备选方案，可以尝试通过临时的iframe预览
            try {
                const iframe = document.createElement('iframe');
                iframe.style.display = 'none';
                iframe.src = previewUrl;
                document.body.appendChild(iframe);
                
                // 稍后移除iframe
                setTimeout(() => {
                    document.body.removeChild(iframe);
                }, 5000);
            } catch(err) {
                console.error('通过iframe预览也失败了:', err);
            }
        } else {
            console.log(`正在打开预览链接: ${previewUrl}`);
        }
    };
    
    // 创建下载按钮
    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'btn secondary-btn';
    downloadBtn.innerHTML = '<i class="fas fa-download"></i> 下载';
    downloadBtn.title = '下载文件';
    downloadBtn.style.cssText = `
        margin-left: 10px;
        padding: 5px 10px;
        font-size: 14px;
    `;
    
    // 使用下载API端点
    downloadBtn.onclick = function(e) {
        e.preventDefault(); // 防止点击事件冒泡
        console.log(`开始下载文件: ${downloadUrl}`);
        
        // 使用a标签触发下载
        try {
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename; // 设置下载文件名
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            
            // 延迟后移除a标签
            setTimeout(() => {
                document.body.removeChild(a);
            }, 1000);
            
            window.showMessage('开始下载文件...', 'info');
        } catch (error) {
            console.error('下载文件时出错:', error);
            window.showMessage('下载失败，请重试或联系管理员', 'error');
            
            // 作为备选方案，尝试直接在新窗口打开下载链接
            window.open(downloadUrl, '_blank');
        }
    };
    
    // 创建移除按钮
    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn secondary-btn';
    removeBtn.innerHTML = '<i class="fas fa-times"></i>';
    removeBtn.title = '从列表中移除';
    removeBtn.style.cssText = `
        margin-left: 5px;
        padding: 5px 8px;
        font-size: 14px;
        background-color: #dc3545;
    `;
    removeBtn.onclick = function(e) {
        e.preventDefault(); // 防止点击事件冒泡
        filesList.removeChild(fileItem);
        
        // 如果没有文件了，隐藏容器
        if (filesList.children.length === 0) {
            container.style.display = 'none';
            // 移除清除所有按钮
            const clearAllBtn = document.getElementById('clear-files-btn');
            if (clearAllBtn) {
                clearAllBtn.remove();
            }
        }
    };
    
    // 添加到文件项
    fileItem.appendChild(icon);
    fileItem.appendChild(link);
    fileItem.appendChild(downloadBtn);
    fileItem.appendChild(removeBtn);
    
    // 添加到文件列表
    filesList.appendChild(fileItem);
    
    // 如果这是第一个文件且没有清除所有按钮，添加清除所有按钮
    if (filesList.children.length > 0 && !document.getElementById('clear-files-btn')) {
        const clearAllBtn = document.createElement('button');
        clearAllBtn.id = 'clear-files-btn';
        clearAllBtn.className = 'btn secondary-btn';
        clearAllBtn.innerHTML = '<i class="fas fa-trash"></i> 清除所有';
        clearAllBtn.style.cssText = `
            margin-top: 10px;
            padding: 5px 10px;
            font-size: 14px;
            background-color: #6c757d;
            float: right;
        `;
        clearAllBtn.onclick = function() {
            filesList.innerHTML = '';
            container.style.display = 'none';
            clearAllBtn.remove();
        };
        
        container.appendChild(clearAllBtn);
    }
}

// 添加API前缀的辅助函数
function apiUrl(url) {
    return url.startsWith('/api') ? url : `/api${url}`;
}

window.downloadFile = async function(filename) {
    try {
        const response = await fetch(apiUrl(`/download/${filename}`), {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        if (!response.ok) {
            throw new Error('下载文件失败');
        }
        
        // 创建一个临时链接来下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        window.showMessage('下载文件失败：' + error.message, 'error');
    }
};

window.previewFile = function(filename) {
    // 在新窗口中打开文件
    window.open(apiUrl(`/download/${filename}`), '_blank');
};

function showError(message) {
    showMessage(message, 'error');
}

function showLoading(message) {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingIndicator';
    loadingDiv.className = 'alert alert-info text-center';
    loadingDiv.innerHTML = `
        <div class="spinner-border spinner-border-sm" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <span class="ms-2">${message}</span>
    `;
    document.body.insertBefore(loadingDiv, document.body.firstChild);
}

function hideLoading() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    @keyframes flash {
        0% { background-color: #f8f9fa; }
        50% { background-color: #ffc107; }
        100% { background-color: #f8f9fa; }
    }
`;
document.head.appendChild(style); 