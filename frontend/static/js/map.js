// 地图相关功能

// 全局地图变量
let map = null;
let marker = null;
let pathLayer = null; // 用于存储路径图层
let markersLayer = null; // 用于存储批量导入的标记点
let districtLayer = null; // 用于存储行政区域边界
let trafficLayer = null; // 用于存储交通路况图层
let satelliteLayer = null; // 用于存储卫星图层
let roadNetLayer = null; // 用于存储路网图层
let standardLayer = null; // 用于存储标准矢量图层
let layerControl = null; // 用于存储图层控制面板
let customLayerControl = null; // 自定义图层控制面板
let gpsData = [];

// 监听高德地图API加载完成事件
window.addEventListener('amap-loaded', function() {
    console.log('高德地图API加载完成事件触发');
    setupMapEvents();
    
    // 检查URL中是否有地图相关参数
    if (window.location.search.includes('show_map=true')) {
        console.log('URL参数指定显示地图，准备显示地图');
        setTimeout(function() {
            const mapContainer = document.getElementById('map-container');
            if (mapContainer) {
                mapContainer.style.display = 'block';
                initMap();
            }
        }, 500);
    }
});

// 切换地图容器的显示和隐藏
function toggleMapContainer() {
    // 获取DOM元素
    const mapContainer = document.getElementById('map-container');
    const showMapBtn = document.getElementById('show-map-btn');
    
    if (!mapContainer) {
        console.error('找不到地图容器元素 #map-container');
        return;
    }
    
    // 使用getComputedStyle获取实际计算后的样式
    const computedStyle = window.getComputedStyle(mapContainer);
    const displayStyle = computedStyle.display;
    const isCurrentlyHidden = displayStyle === 'none';
    
    console.log('切换地图显示状态:', 
                '计算样式:', displayStyle, 
                '是否隐藏:', isCurrentlyHidden, 
                '按钮文本:', showMapBtn ? showMapBtn.textContent : 'null');
    
    if (isCurrentlyHidden) {
        // 从隐藏变为显示
        console.log('准备显示地图');
        
        try {
            // 确保显示容器
            mapContainer.style.display = 'block';
            console.log('地图容器设置为显示 block');
            
            // 显示地图时初始化
            if (!map) {
                console.log('地图未初始化，正在初始化...');
                setTimeout(function() {
                    initMap();
                }, 100);
            } else {
                console.log('地图已初始化，刷新大小');
                map.setFitView();
            }
            
            // 更新按钮文本和状态
            if (showMapBtn) {
                showMapBtn.textContent = '隐藏地图';
                // 记录地图可见状态
                showMapBtn.dataset.mapVisible = 'true';
                console.log('按钮文本更新为：隐藏地图，状态设置为可见');
            }
        } catch (error) {
            console.error('显示地图时发生错误:', error);
        }
    } else {
        // 从显示变为隐藏
        try {
            console.log('准备隐藏地图');
            mapContainer.style.display = 'none';
            
            // 更新按钮文本和状态
            if (showMapBtn) {
                showMapBtn.textContent = '显示地图';
                // 记录地图隐藏状态
                showMapBtn.dataset.mapVisible = 'false';
                console.log('按钮文本更新为：显示地图，状态设置为隐藏');
            }
        } catch (error) {
            console.error('隐藏地图时发生错误:', error);
        }
    }
}

// 设置地图相关事件
function setupMapEvents() {
    // 避免重复注册事件
    if (window.mapEventsInitialized) {
        console.log('地图事件已在其他地方初始化，不重复设置');
        return;
    }
    
    // 标记事件已初始化
    window.mapEventsInitialized = true;
    
    // 批量导入GPS按钮
    const importGpsBtn = document.getElementById('import-gps-btn');
    if (importGpsBtn) {
        importGpsBtn.addEventListener('click', function() {
            showGpsImportDialog();
        });
    }
}

// 显示GPS导入对话框
function showGpsImportDialog() {
    // 创建模态对话框
    const modalHtml = `
        <div id="import-gps-modal" class="modal" style="display: flex; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000;">
            <div class="modal-content" style="background-color: white; padding: 20px; border-radius: 5px; width: 80%; max-width: 600px; position: relative;">
                <span class="close-btn" onclick="document.getElementById('import-gps-modal').remove()" style="position: absolute; right: 15px; top: 10px; font-size: 24px; cursor: pointer;">&times;</span>
                <h3>批量导入GPS和时间信息</h3>
                
                <div class="import-tabs" style="display: flex; border-bottom: 1px solid #ddd; margin-bottom: 15px;">
                    <div id="manual-tab" class="import-tab active" style="padding: 10px 15px; cursor: pointer; border-bottom: 2px solid #4a89dc;">手动输入</div>
                    <div id="excel-tab" class="import-tab" style="padding: 10px 15px; cursor: pointer;">Excel导入</div>
                </div>
                
                <div id="manual-input-container">
                    <p>请按照以下格式输入GPS数据，每行一个点：<br>
                    <code>纬度,经度,时间(可选),地点(可选)</code><br>
                    例如: <code>39.915119,116.403963,2023-03-22 14:30:00,天安门</code></p>
                    
                    <textarea id="gps-import-data" rows="10" style="width: 100%; padding: 8px; margin: 10px 0; border-radius: 4px; border: 1px solid #ddd;"></textarea>
                </div>
                
                <div id="excel-input-container" style="display: none;">
                    <p>请上传Excel文件，文件须包含以下字段：<br>
                    <span style="color: red;">纬度、经度</span>(必填)，时间、地点(可选)</p>
                    
                    <div style="margin: 15px 0;">
                        <input type="file" id="excel-file-input" accept=".xlsx, .xls" style="border: 1px solid #ddd; padding: 8px; width: 100%; border-radius: 4px;">
                    </div>
                    
                    <div id="excel-preview" style="margin-top: 10px; max-height: 200px; overflow-y: auto; border: 1px solid #eee; padding: 10px; display: none;">
                        <h4>数据预览</h4>
                        <div id="excel-data-preview"></div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px;">
                    <button id="cancel-import-btn" class="btn" style="padding: 8px 15px; background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;" onclick="document.getElementById('import-gps-modal').remove()">取消</button>
                    <button id="confirm-import-btn" class="btn primary-btn" style="padding: 8px 15px; background-color: #4a89dc; color: white; border: none; border-radius: 4px; cursor: pointer;" onclick="processImportedGps()">导入</button>
                </div>
            </div>
        </div>
    `;
    
    // 确保先移除已存在的模态框
    const existingModal = document.getElementById('import-gps-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加到body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 添加标签切换事件
    const manualTab = document.getElementById('manual-tab');
    const excelTab = document.getElementById('excel-tab');
    const manualInputContainer = document.getElementById('manual-input-container');
    const excelInputContainer = document.getElementById('excel-input-container');
    
    manualTab.addEventListener('click', function() {
        manualTab.classList.add('active');
        excelTab.classList.remove('active');
        manualInputContainer.style.display = 'block';
        excelInputContainer.style.display = 'none';
        
        // 更新样式
        manualTab.style.borderBottom = '2px solid #4a89dc';
        excelTab.style.borderBottom = 'none';
    });
    
    excelTab.addEventListener('click', function() {
        excelTab.classList.add('active');
        manualTab.classList.remove('active');
        excelInputContainer.style.display = 'block';
        manualInputContainer.style.display = 'none';
        
        // 更新样式
        excelTab.style.borderBottom = '2px solid #4a89dc';
        manualTab.style.borderBottom = 'none';
    });
    
    // 添加Excel文件上传事件
    const excelFile = document.getElementById('excel-file-input');
    if (excelFile) {
        excelFile.addEventListener('change', handleExcelUpload);
    }
    
    console.log('GPS导入对话框已显示');
}

// 处理Excel文件上传
async function handleExcelUpload(event) {
    try {
        const file = event.target.files[0];
        if (!file) {
            console.error('未选择文件');
            return;
        }

        console.log('Excel文件上传事件触发');
        console.log('选择的文件:', file.name);

        // 检查XLSX库是否已加载
        if (typeof XLSX === 'undefined') {
            console.log('XLSX库未加载，等待加载完成');
            // 等待XLSX库加载完成
            await new Promise((resolve) => {
                const checkXLSX = setInterval(() => {
                    if (typeof XLSX !== 'undefined') {
                        clearInterval(checkXLSX);
                        resolve();
                    }
                }, 100);
            });
            console.log('XLSX库加载完成，重新处理文件');
            // 重新触发文件处理
            handleExcelUpload(event);
            return;
        }

        console.log('开始读取文件...');
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const firstSheetName = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheetName];
                const jsonData = XLSX.utils.sheet_to_json(worksheet);
                
                console.log('Excel数据读取成功:', jsonData);
                
                // 验证数据格式
                if (!jsonData.length) {
                    alert('Excel文件中没有数据');
                    return;
                }
                
                // 检查必要的字段
                const firstRow = jsonData[0];
                const hasLatitude = 'latitude' in firstRow || '纬度' in firstRow;
                const hasLongitude = 'longitude' in firstRow || '经度' in firstRow;
                
                if (!hasLatitude || !hasLongitude) {
                    alert('Excel文件必须包含"latitude"和"longitude"（或"纬度"和"经度"）列');
                    return;
                }
                
                // 处理数据
                const validData = [];
                const invalidRows = [];
                
                jsonData.forEach((row, index) => {
                    const latitude = parseFloat(row.latitude || row.纬度);
                    const longitude = parseFloat(row.longitude || row.经度);
                    
                    // 验证坐标值
                    if (isNaN(latitude) || isNaN(longitude) || 
                        latitude < -90 || latitude > 90 || 
                        longitude < -180 || longitude > 180) {
                        invalidRows.push({
                            row: index + 1,
                            reason: '无效的GPS坐标',
                            value: `纬度: ${row.latitude || row.纬度}, 经度: ${row.longitude || row.经度}`
                        });
                        return;
                    }
                    
                    validData.push({
                        latitude: latitude,
                        longitude: longitude,
                        time: row.time || row.时间,
                        location: row.location || row.地点,
                        description: row.description || row.描述
                    });
                });
                
                if (invalidRows.length > 0) {
                    const errorMessage = `发现${invalidRows.length}行无效数据：\n` +
                        invalidRows.map(row => `第${row.row}行: ${row.reason} (${row.value})`).join('\n') +
                        '\n\n请检查数据格式是否正确。\n' +
                        '有效的字段名：latitude/longitude 或 纬度/经度\n' +
                        '坐标范围：纬度(-90到90)，经度(-180到180)';
                    
                    alert(errorMessage);
                    return;
                }
                
                // 存储有效数据
                window.importedGpsData = validData;
                
                // 显示预览
                const previewContainer = document.getElementById('gps-preview');
                if (previewContainer) {
                    previewContainer.innerHTML = `
                        <h4>数据预览 (${validData.length}条记录)</h4>
                        <div class="preview-content">
                            ${validData.slice(0, 5).map((item, index) => `
                                <div class="preview-item">
                                    <p>记录 ${index + 1}:</p>
                                    <p>纬度: ${item.latitude}</p>
                                    <p>经度: ${item.longitude}</p>
                                    <p>时间: ${item.time || '未设置'}</p>
                                    <p>地点: ${item.location || '未设置'}</p>
                                </div>
                            `).join('')}
                            ${validData.length > 5 ? `<p>... 还有 ${validData.length - 5} 条记录</p>` : ''}
                        </div>
                    `;
                }
                
                // 启用导入按钮
                const importButton = document.getElementById('import-gps-confirm');
                if (importButton) {
                    importButton.disabled = false;
                }
                
            } catch (error) {
                console.error('处理Excel文件时出错:', error);
                alert('处理Excel文件时出错: ' + error.message);
            }
        };
        
        reader.onerror = function(error) {
            console.error('读取文件时出错:', error);
            alert('读取文件时出错');
        };
        
        reader.readAsArrayBuffer(file);
        
    } catch (error) {
        console.error('处理文件上传时出错:', error);
        alert('处理文件上传时出错: ' + error.message);
    }
}

// 显示Excel数据预览
function showExcelPreview(data) {
    console.log('显示Excel数据预览');
    const previewContainer = document.getElementById('excel-data-preview');
    const previewDiv = document.getElementById('excel-preview');
    
    if (!previewContainer || !previewDiv) {
        console.error('预览容器元素不存在');
        return;
    }
    
    if (!data || data.length === 0) {
        previewContainer.innerHTML = '<p style="color: #666; font-style: italic;">无数据</p>';
        previewDiv.style.display = 'none';
        console.log('没有数据可预览');
        return;
    }
    
    try {
        console.log(`将显示${Math.min(5, data.length)}行数据预览`);
        
        // 只显示前5行数据作为预览
        const previewData = data.slice(0, 5);
        
        // 创建表格
        let tableHtml = '<div style="overflow-x: auto;">'; // 添加水平滚动容器
        tableHtml += '<table style="width: 100%; border-collapse: collapse; margin-top: 10px; min-width: 500px;">'; // 设置最小宽度
        
        // 表头
        tableHtml += '<thead><tr style="background-color: #f8f9fa;">';
        const headers = Object.keys(previewData[0]);
        headers.forEach(header => {
            tableHtml += `<th style="border: 1px solid #ddd; padding: 8px; text-align: left; white-space: nowrap;">${header}</th>`;
        });
        tableHtml += '</tr></thead>';
        
        // 表体
        tableHtml += '<tbody>';
        previewData.forEach((row, index) => {
            tableHtml += `<tr style="background-color: ${index % 2 === 0 ? 'white' : '#f9f9f9'}">`;
            headers.forEach(header => {
                const cellValue = row[header] !== undefined ? row[header] : '';
                tableHtml += `<td style="border: 1px solid #ddd; padding: 8px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${cellValue}</td>`;
            });
            tableHtml += '</tr>';
        });
        tableHtml += '</tbody></table></div>';
        
        // 显示总行数和字段信息
        if (data.length > 5) {
            tableHtml += `
                <div style="margin-top: 10px; color: #666; font-style: italic;">
                    共${data.length}行数据，仅显示前5行
                    <br>
                    <small>包含字段：${headers.join(', ')}</small>
                </div>
            `;
        }
        
        // 显示预览
        previewContainer.innerHTML = tableHtml;
        previewDiv.style.display = 'block';
        
        console.log('Excel数据预览显示完成');
    } catch (error) {
        console.error('生成预览表格失败:', error);
        previewContainer.innerHTML = `
            <div style="color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px;">
                <strong>错误：</strong> 生成预览失败 - ${error.message}
            </div>
        `;
    }
}

// 格式化时间函数
function formatDateTime(timeStr) {
    if (!timeStr) return '';
    try {
        const date = new Date(timeStr);
        if (isNaN(date.getTime())) return timeStr; // 如果转换失败，返回原始字符串
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    } catch (error) {
        console.error('时间格式化失败:', error);
        return timeStr; // 出错时返回原始字符串
    }
}

// 处理导入的GPS数据
function processImportedGps() {
    try {
        // 确保地图已初始化
        if (!map) {
            console.log('地图未初始化，尝试初始化地图');
            const mapContainer = document.getElementById('map-container');
            if (mapContainer) {
                // 确保地图容器可见
                if (mapContainer.style.display === 'none') {
                    mapContainer.style.display = 'block';
                }
                
                // 初始化地图
                initMap().then(mapInstance => {
                    map = mapInstance;
                    // 等待地图初始化完成后再处理数据
                    setTimeout(() => {
                        processGpsData();
                    }, 500);
                });
                return;
            } else {
                throw new Error('找不到地图容器');
            }
        }
        
        // 如果地图已初始化，直接处理数据
        processGpsData();
        
        // 将数据处理逻辑移到独立函数中
        function processGpsData() {
            let points = [];
            let pointsInfo = [];
            
            // 检查当前激活的是哪个导入方式
            const isExcelActive = document.getElementById('excel-tab').classList.contains('active');
            
            if (isExcelActive) {
                // 处理Excel导入的数据
                if (!window.importedGpsData || window.importedGpsData.length === 0) {
                    alert('请先上传并解析Excel文件');
                    return;
                }
                
                // 解析Excel数据
                window.importedGpsData.forEach((row, index) => {
                    // 获取纬度和经度
                    let lat = row.latitude;
                    let lng = row.longitude;
                    
                    // 添加到数组
                    points.push([lng, lat]); // 高德地图使用[lng, lat]顺序
                    pointsInfo.push({
                        lat: lat,
                        lng: lng,
                        time: row.time,
                        location: row.location,
                        description: row.description,
                        index: index + 1
                    });
                });
            } else {
                // 获取文本框中的数据
                const importText = document.getElementById('gps-import-data').value.trim();
                if (!importText) {
                    alert('请输入GPS数据');
                    return;
                }
                
                // 分析每行数据
                const lines = importText.split('\n');
                
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;
                    
                    const parts = line.split(',');
                    if (parts.length < 2) {
                        throw new Error(`第${i+1}行数据格式不正确，至少需要纬度和经度`);
                    }
                    
                    const lat = parseFloat(parts[0]);
                    const lng = parseFloat(parts[1]);
                    
                    if (isNaN(lat) || isNaN(lng)) {
                        throw new Error(`第${i+1}行包含无效的坐标数据`);
                    }
                    
                    // 收集点位信息
                    let time = '';
                    let location = '';
                    
                    if (parts.length >= 3) {
                        time = parts[2].trim();
                    }
                    
                    if (parts.length >= 4) {
                        location = parts[3].trim();
                    }
                    
                    // 添加到数组
                    points.push([lng, lat]); // 高德地图使用[lng, lat]顺序
                    pointsInfo.push({
                        lat: lat,
                        lng: lng,
                        time: time,
                        location: location,
                        description: '',
                        index: i + 1
                    });
                }
            }
            
            if (points.length === 0) {
                throw new Error('没有有效的GPS数据');
            }
            
            // 清除旧的点
            if (markersLayer) {
                markersLayer.forEach(marker => map.remove(marker));
                markersLayer = [];
            } else {
                markersLayer = []; // 确保markersLayer被初始化
            }
            
            if (pathLayer) {
                map.remove(pathLayer);
                pathLayer = null;
            }
            
            // 添加所有点到地图
            pointsInfo.forEach(point => {
                // 创建标记，使用自定义样式的数字图标
                const marker = new AMap.Marker({
                    position: [point.lng, point.lat],
                    map: map,
                    content: `<div style="width: 32px; height: 32px; background-color: #3388ff; color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 16px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">${point.index}</div>`,
                    offset: new AMap.Pixel(-16, -16) // 调整偏移以使标记位于正确位置
                });
                
                // 添加点击事件，显示信息窗体
                marker.on('click', function() {
                    const formattedTime = formatDateTime(point.time);
                    const infoWindow = new AMap.InfoWindow({
                        content: `
                            <div style="padding: 15px; min-width: 200px;">
                                <h4 style="margin: 0 0 10px 0; color: #333;">点位：${point.index}</h4>
                                <div style="border-top: 1px solid #eee; padding-top: 10px;">
                                    ${formattedTime ? `<p style="margin: 5px 0;"><strong>时间：</strong>${formattedTime}</p>` : ''}
                                    ${point.location ? `<p style="margin: 5px 0;"><strong>地点：</strong>${point.location}</p>` : ''}
                                    <p style="margin: 5px 0;"><strong>GPS：</strong>${point.lat.toFixed(6)}, ${point.lng.toFixed(6)}</p>
                                </div>
                            </div>
                        `,
                        offset: new AMap.Pixel(0, -30),
                        closeWhenClickMap: true // 点击地图其他区域时关闭信息窗体
                    });
                    infoWindow.open(map, [point.lng, point.lat]);
                });
                
                markersLayer.push(marker);
            });
            
            // 创建路径线
            pathLayer = new AMap.Polyline({
                path: points,
                strokeColor: '#e74c3c',
                strokeWeight: 4,
                strokeOpacity: 0.7,
                strokeStyle: 'dashed',
                lineJoin: 'round'
            });
            map.add(pathLayer);
            
            // 调整地图视图以显示所有点
            map.setFitView([...markersLayer, pathLayer]);
            
            // 关闭对话框
            const modal = document.getElementById('import-gps-modal');
            if (modal) {
                modal.remove();
            }
            
            // 显示成功消息
            alert(`成功导入了 ${points.length} 个GPS点位`);
        }
    } catch (error) {
        console.error('处理GPS导入数据失败:', error);
        alert('处理GPS导入数据失败: ' + error.message);
    }
}

// 根据地址搜索位置
function searchLocation(address) {
    if (!map || typeof AMap === 'undefined') {
        console.error('地图未初始化或API未加载');
        return;
    }
    
    AMap.plugin('AMap.Geocoder', function() {
        const geocoder = new AMap.Geocoder();
        
        geocoder.getLocation(address, function(status, result) {
            if (status === 'complete' && result.info === 'OK') {
                const location = result.geocodes[0].location;
                
                // 更新输入框
                document.getElementById('gps-latitude').value = location.lat;
                document.getElementById('gps-longitude').value = location.lng;
                
                // 在地图上标记位置
                markLocationOnMap(location.lng, location.lat);
            } else {
                console.error('搜索位置失败');
                alert('搜索位置失败，请检查地址是否正确');
            }
        });
    });
}

// 在地图上标记位置并连线
async function plotImagesOnMap() {
    // 添加标志位，防止重复调用
    if (window.isPlottingInProgress) {
        console.log('已有打点操作正在进行中，忽略重复调用');
        return;
    }
    
    window.isPlottingInProgress = true;
    
    try {
        console.log('执行打点上图...');
        
        if (!map) {
            console.log('地图未初始化，尝试初始化地图');
            
            // 获取显示/隐藏地图按钮，提前设置按钮状态
            const showMapBtn = document.getElementById('show-map-btn');
            if (showMapBtn) {
                showMapBtn.textContent = '隐藏地图';
                showMapBtn.dataset.mapVisible = 'true';
                console.log('首次初始化：提前设置按钮状态为visible=true');
            }
            
            // 尝试初始化地图
            const mapContainer = document.getElementById('map-container');
            if (mapContainer) {
                // 使用getComputedStyle检查地图容器是否真的隐藏
                const computedStyle = window.getComputedStyle(mapContainer);
                const isCurrentlyHidden = computedStyle.display === 'none';
                
                // 确保地图显示
                if (isCurrentlyHidden) {
                    console.log('地图容器隐藏，显示地图');
                    mapContainer.style.display = 'block';
                }
                
                // 使用then而不是await
                initMap().then(mapInstance => {
                    map = mapInstance;
                    // 等待地图初始化完成
                    setTimeout(() => {
                        // 地图完全初始化后再次确认按钮状态
                        if (showMapBtn) {
                            showMapBtn.textContent = '隐藏地图';
                            showMapBtn.dataset.mapVisible = 'true';
                            console.log('地图初始化完成后再次确认按钮状态为visible=true');
                        }
                        continueMapPlotting();
                    }, 500);
                });
                
                return;
            } else {
                console.error('找不到地图容器');
                alert('找不到地图容器，无法执行打点上图');
                window.isPlottingInProgress = false;
                return;
            }
        } else {
            // 地图已初始化，直接继续
            continueMapPlotting();
        }
        
        // 将地图打点的后续操作移到独立函数中
        async function continueMapPlotting() {
            try {
                console.log('获取任务图片GPS信息...');
            
                // 使用authenticatedFetch获取当前任务的所有图片
                const taskId = window.taskId || new URLSearchParams(window.location.search).get('id');
                if (!taskId) {
                    console.error('未找到任务ID');
                    alert('未找到任务ID');
                    window.isPlottingInProgress = false;
                    return;
                }
                
                // 清除已有的路径图层和标记
                if (pathLayer) {
                    map.remove(pathLayer);
                    pathLayer = null;
                }
                
                // 清除已有的标记图层
                if (markersLayer) {
                    markersLayer.forEach(marker => {
                        map.remove(marker);
                    });
                    markersLayer = null;
                }
                
                // 创建新的标记数组
                markersLayer = [];
                
                // 获取任务下的所有图片
                const response = await window.authenticatedFetch(`/tasks/${taskId}/images`);
                if (!response.ok) {
                    throw new Error('获取图片列表失败');
                }
                
                const images = await response.json();
                console.log(`获取到${images.length}张图片`);
                
                // 筛选出有GPS信息的图片，并按时间排序
                const gpsImages = images
                    .filter(img => img.gps_latitude && img.gps_longitude)
                    .sort((a, b) => new Date(a.time) - new Date(b.time));
                
                console.log(`其中有${gpsImages.length}张图片包含GPS信息`);
                
                if (gpsImages.length === 0) {
                    console.warn('没有找到包含GPS信息的图片');
                    alert('没有找到包含GPS信息的图片');
                    window.isPlottingInProgress = false;
                    return;
                }
                
                // 收集所有点的坐标 - 注意高德地图使用[lng, lat]顺序
                const points = gpsImages.map(img => [img.gps_longitude, img.gps_latitude]);
                
                // 创建标记点和连线
                points.forEach((point, index) => {
                    // 创建标记，使用数字图标
                    const marker = new AMap.Marker({
                        position: point,
                        map: map,
                        content: `<div style="width: 32px; height: 32px; background-color: #3388ff; color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 16px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">${index + 1}</div>`,
                        offset: new AMap.Pixel(-16, -16) // 调整偏移以使标记位于正确位置
                    });
                    
                    // 添加点击事件，显示图片信息
                    const img = gpsImages[index];
                    const formattedTime = new Date(img.time).toLocaleString();
                    marker.on('click', function() {
                        const infoWindow = new AMap.InfoWindow({
                            content: `
                                <div style="text-align: center;">
                                    <h4>图片 #${index + 1}</h4>
                                    <p>时间: ${formattedTime}</p>
                                    <p>地点: ${img.location || '未知'}</p>
                                    <p>GPS: ${img.gps_latitude.toFixed(6)}, ${img.gps_longitude.toFixed(6)}</p>
                                    <button onclick="window.showImageDetail(${img.id})" style="padding: 5px 10px; background: #3388ff; color: white; border: none; border-radius: 4px; cursor: pointer;">查看详情</button>
                                </div>
                            `,
                            offset: new AMap.Pixel(0, -30)
                        });
                        infoWindow.open(map, point);
                    });
                    
                    markersLayer.push(marker);
                });
                
                // 创建路径线
                pathLayer = new AMap.Polyline({
                    path: points,
                    strokeColor: '#3388ff',
                    strokeWeight: 4,
                    strokeOpacity: 0.7,
                    strokeStyle: 'dashed',
                    lineJoin: 'round'
                });
                map.add(pathLayer);
                
                // 调整地图视图以显示所有点
                if (points.length > 0) {
                    try {
                        // 计算所有点的中心点
                        let centerLng = 0;
                        let centerLat = 0;
                        points.forEach(point => {
                            centerLng += point[0];
                            centerLat += point[1];
                        });
                        centerLng = centerLng / points.length;
                        centerLat = centerLat / points.length;
                        
                        // 直接移动到中心点，不进行缩放
                        map.setCenter([centerLng, centerLat], {
                            duration: 1000,
                            noAnimation: false
                        });
                        
                        console.log('地图已移动到点位中心位置');
                    } catch (error) {
                        console.error('设置地图位置时出错:', error);
                        // 发生错误时，尝试使用第一个点作为中心点
                        if (points.length > 0) {
                            const center = points[0];
                            map.setCenter(center, {
                                duration: 1000,
                                noAnimation: false
                            });
                        }
                    }
                }
                
                console.log('已成功在地图上标记所有点并连线');
            } catch (error) {
                console.error('打点上图失败:', error);
                alert('打点上图失败: ' + error.message);
            } finally {
                // 重置进行中标志
                window.isPlottingInProgress = false;
            }
        }
    } catch (error) {
        console.error('打点上图失败:', error);
        alert('打点上图失败: ' + error.message);
        window.isPlottingInProgress = false;
    }
}

// 备用的Excel数据预览函数
function updatePreview(data) {
    console.log('使用备用预览函数显示Excel数据');
    const previewContainer = document.getElementById('excel-data-preview');
    const previewDiv = document.getElementById('excel-preview');
    
    if (!previewContainer || !previewDiv) {
        console.error('找不到预览容器元素');
        return;
    }
    
    if (!data || !Array.isArray(data) || data.length === 0) {
        previewContainer.innerHTML = '<p style="color: #666; font-style: italic;">无数据</p>';
        previewDiv.style.display = 'none';
        console.log('没有数据可预览');
        return;
    }
    
    try {
        // 限制预览行数
        const maxPreviewRows = 5;
        const previewData = data.slice(0, maxPreviewRows);
        console.log(`将显示${Math.min(maxPreviewRows, data.length)}行数据预览`);
        
        // 创建表格
        let html = '<div style="overflow-x: auto;">'; // 添加水平滚动容器
        html += '<table style="width: 100%; border-collapse: collapse; margin-top: 10px; min-width: 500px;">'; // 设置最小宽度
        
        // 表头
        html += '<thead><tr style="background-color: #f8f9fa;">';
        const headers = Object.keys(previewData[0]);
        headers.forEach(header => {
            html += `<th style="border: 1px solid #ddd; padding: 8px; text-align: left; white-space: nowrap;">${header}</th>`;
        });
        html += '</tr></thead>';
        
        // 表体
        html += '<tbody>';
        previewData.forEach((row, index) => {
            html += `<tr style="background-color: ${index % 2 === 0 ? 'white' : '#f9f9f9'}">`;
            headers.forEach(header => {
                const value = row[header];
                const displayValue = value !== undefined && value !== null ? value.toString() : '';
                html += `<td style="border: 1px solid #ddd; padding: 8px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${displayValue}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table></div>';
        
        // 添加数据统计信息
        if (data.length > maxPreviewRows) {
            html += `<div style="margin-top: 10px; color: #666; font-style: italic;">
                共${data.length}行数据，仅显示前${maxPreviewRows}行
                <br>
                <small>包含字段：${headers.join(', ')}</small>
            </div>`;
        }
        
        // 显示预览
        previewContainer.innerHTML = html;
        previewDiv.style.display = 'block';
        
        console.log('Excel数据预览更新完成');
        
        // 验证必要字段
        const requiredFields = ['纬度', 'latitude', 'lat', '经度', 'longitude', 'lng'];
        const hasRequiredFields = requiredFields.some(field => headers.includes(field));
        
        if (!hasRequiredFields) {
            previewContainer.insertAdjacentHTML('afterbegin', `
                <div style="margin-bottom: 10px; padding: 8px; background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 4px; color: #856404;">
                    <strong>警告：</strong> 未检测到必要的GPS字段（纬度/latitude/lat 和 经度/longitude/lng）
                </div>
            `);
        }
    } catch (error) {
        console.error('更新预览时出错:', error);
        previewContainer.innerHTML = `
            <div style="padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;">
                <strong>错误：</strong> 处理数据时出错: ${error.message}
            </div>
        `;
    }
}

// 导出函数供其他模块使用
window.mapUtils = {
    plotImagesOnMap: plotImagesOnMap,
    showGpsImportDialog: showGpsImportDialog,
    handleExcelUpload: handleExcelUpload,
    showExcelPreview: showExcelPreview,
    processImportedGps: processImportedGps,
    toggleMapContainer: toggleMapContainer,
    toggleLayerControl: toggleLayerControl
};

// 导出独立函数，确保能直接调用
window.showGpsImportDialog = showGpsImportDialog;
window.plotImagesOnMap = plotImagesOnMap;
window.toggleMapContainer = toggleMapContainer;
window.toggleLayerControl = toggleLayerControl;

// 导出地图初始化函数
window.initMap = initMap;

// 导出更新预览函数
window.updatePreview = updatePreview;

// 创建自定义图层控制面板
function createLayerControl() {
    if (customLayerControl) {
        return; // 已经创建过了
    }

    console.log('创建自定义图层控制面板...');

    // 创建控制面板容器 - 调整位置和样式
    customLayerControl = document.createElement('div');
    customLayerControl.className = 'layer-control';
    customLayerControl.style.cssText = 'position: absolute; top: 80px; right: 10px; background: rgba(255, 255, 255, 0.95); border-radius: 8px; padding: 12px; z-index: 100; color: #333; font-size: 13px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); border: 1px solid rgba(0,0,0,0.1); backdrop-filter: blur(4px); min-width: 180px;';

    // 创建标题
    const title = document.createElement('div');
    title.innerHTML = '<i class="fas fa-layer-group" style="margin-right: 6px;"></i>图层控制';
    title.style.cssText = 'font-weight: bold; margin-bottom: 10px; font-size: 15px; color: #333; text-align: center; padding-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); letter-spacing: 1px;';
    customLayerControl.appendChild(title);

    // 添加图层分组标题
    const baseLayersTitle = document.createElement('div');
    baseLayersTitle.innerHTML = '基础图层';
    baseLayersTitle.style.cssText = 'font-size: 12px; color: #666; margin: 10px 0 5px 0; font-weight: bold;';
    customLayerControl.appendChild(baseLayersTitle);

    // 添加基础图层选项（单选）
    const baseLayersGroup = document.createElement('div');
    baseLayersGroup.style.cssText = 'margin-bottom: 10px; padding-left: 5px;';
    customLayerControl.appendChild(baseLayersGroup);

    // 添加标准地图图层（默认选中）
    addRadioOption(baseLayersGroup, 'standard-layer', '标准地图', true, function(checked) {
        if (checked) {
            toggleStandardLayer(true);
            toggleSatelliteLayer(false);
        }
    });

    // 添加卫星图层
    addRadioOption(baseLayersGroup, 'satellite-layer', '卫星影像', false, function(checked) {
        if (checked) {
            toggleStandardLayer(false);
            toggleSatelliteLayer(true);
        }
    });

    // 添加覆盖图层标题
    const overlaysTitle = document.createElement('div');
    overlaysTitle.innerHTML = '覆盖图层';
    overlaysTitle.style.cssText = 'font-size: 12px; color: #aaa; margin: 10px 0 5px 0; font-weight: bold;';
    customLayerControl.appendChild(overlaysTitle);

    // 添加覆盖图层选项（复选）
    const overlaysGroup = document.createElement('div');
    overlaysGroup.style.cssText = 'padding-left: 5px;';
    customLayerControl.appendChild(overlaysGroup);

    // 添加路网图层选项
    addCheckboxOption(overlaysGroup, 'road-net-layer', '路网图层', false, function(checked) {
        toggleRoadNetLayer(checked);
    });

    // 添加交通路况图层选项
    addCheckboxOption(overlaysGroup, 'traffic-layer', '交通路况', false, function(checked) {
        toggleTrafficLayer(checked);
    });

    // 添加行政区域图层选项
    addCheckboxOption(overlaysGroup, 'district-layer', '行政区域', false, function(checked) {
        toggleDistrictLayer(checked);
    });

    // 添加控制按钮容器
    const buttonsContainer = document.createElement('div');
    buttonsContainer.style.cssText = 'display: flex; justify-content: space-between; margin-top: 15px;';
    customLayerControl.appendChild(buttonsContainer);

    // 添加关闭按钮
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '关闭';
    closeBtn.style.cssText = 'text-align: center; padding: 6px 12px; border-radius: 4px; background: #e74c3c; cursor: pointer; font-weight: bold; font-size: 12px; border: none; color: white; flex: 1; margin-right: 5px; transition: all 0.2s;';
    closeBtn.onmouseover = function() { this.style.backgroundColor = '#c0392b'; };
    closeBtn.onmouseout = function() { this.style.backgroundColor = '#e74c3c'; };
    closeBtn.onclick = function() {
        customLayerControl.style.display = 'none';
    };
    buttonsContainer.appendChild(closeBtn);

    // 添加重置按钮
    const resetBtn = document.createElement('button');
    resetBtn.innerHTML = '重置';
    resetBtn.style.cssText = 'text-align: center; padding: 6px 12px; border-radius: 4px; background: #3498db; cursor: pointer; font-weight: bold; font-size: 12px; border: none; color: white; flex: 1; margin-left: 5px; transition: all 0.2s;';
    resetBtn.onmouseover = function() { this.style.backgroundColor = '#2980b9'; };
    resetBtn.onmouseout = function() { this.style.backgroundColor = '#3498db'; };
    resetBtn.onclick = function() {
        resetAllLayers();
    };
    buttonsContainer.appendChild(resetBtn);

    // 将控制面板添加到地图容器中
    const mapContainer = document.getElementById('map-container');
    if (mapContainer) {
        mapContainer.appendChild(customLayerControl);
    }

    // 辅助函数：添加复选框选项
    function addCheckboxOption(container, id, text, initialState, callback) {
        const item = document.createElement('div');
        item.style.cssText = 'margin: 8px 0; display: flex; align-items: center;';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = id;
        checkbox.checked = initialState;
        checkbox.style.cssText = 'margin-right: 8px; cursor: pointer; width: 16px; height: 16px;';
        checkbox.onchange = function() {
            callback(this.checked);
        };

        const label = document.createElement('label');
        label.htmlFor = id;
        label.textContent = text;
        label.style.cssText = 'cursor: pointer; flex: 1; font-size: 13px;';

        item.appendChild(checkbox);
        item.appendChild(label);
        container.appendChild(item);
    }

    // 辅助函数：添加单选按钮选项
    function addRadioOption(container, id, text, initialState, callback) {
        const item = document.createElement('div');
        item.style.cssText = 'margin: 8px 0; display: flex; align-items: center;';

        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.id = id;
        radio.name = 'base-layer';
        radio.checked = initialState;
        radio.style.cssText = 'margin-right: 8px; cursor: pointer; width: 16px; height: 16px;';
        radio.onchange = function() {
            callback(this.checked);
        };

        const label = document.createElement('label');
        label.htmlFor = id;
        label.textContent = text;
        label.style.cssText = 'cursor: pointer; flex: 1; font-size: 13px;';

        item.appendChild(radio);
        item.appendChild(label);
        container.appendChild(item);
    }
}

// 重置所有图层到默认状态
function resetAllLayers() {
    // 重置基础图层
    toggleStandardLayer(true);
    toggleSatelliteLayer(false);
    
    // 重置覆盖图层
    toggleRoadNetLayer(false);
    toggleTrafficLayer(false);
    toggleDistrictLayer(false);
    
    // 更新图层控制面板中的复选框状态
    if (customLayerControl) {
        const standardRadio = document.getElementById('standard-layer');
        if (standardRadio) standardRadio.checked = true;
        
        const satelliteRadio = document.getElementById('satellite-layer');
        if (satelliteRadio) satelliteRadio.checked = false;
        
        const roadNetCheckbox = document.getElementById('road-net-layer');
        if (roadNetCheckbox) roadNetCheckbox.checked = false;
        
        const trafficCheckbox = document.getElementById('traffic-layer');
        if (trafficCheckbox) trafficCheckbox.checked = false;
        
        const districtCheckbox = document.getElementById('district-layer');
        if (districtCheckbox) districtCheckbox.checked = false;
    }
}

// 显示/隐藏图层控制面板
function toggleLayerControl() {
    if (!customLayerControl) {
        createLayerControl();
    } else {
        customLayerControl.style.display = customLayerControl.style.display === 'none' ? 'block' : 'none';
    }
}

// 切换标准矢量地图图层
function toggleStandardLayer(visible) {
    if (!map) return;

    try {
        if (visible) {
            // 切换到标准矢量地图样式
            map.setMapStyle('amap://styles/normal');
            console.log('切换到标准矢量地图图层');
        } else {
            // 如果关闭标准图层但卫星图层未开启，保持标准图层显示
            if (!satelliteLayer) {
                map.setMapStyle('amap://styles/normal');
            }
        }
    } catch (error) {
        console.error('切换标准矢量地图图层时出错:', error);
    }
}

// 切换卫星图层
function toggleSatelliteLayer(visible) {
    if (!map) return;

    try {
        if (visible) {
            if (!satelliteLayer) {
                satelliteLayer = new AMap.TileLayer.Satellite();
                map.add(satelliteLayer);
                // 切换到卫星地图样式
                map.setMapStyle('amap://styles/dark');
                console.log('添加卫星图层');
            }
        } else {
            if (satelliteLayer) {
                map.remove(satelliteLayer);
                satelliteLayer = null;
                // 重置为标准地图样式
                map.setMapStyle('amap://styles/normal');
                console.log('移除卫星图层');
            }
        }
    } catch (error) {
        console.error('切换卫星图层时出错:', error);
    }
}

// 切换交通路况图层
function toggleTrafficLayer(visible) {
    if (!map) return;

    try {
        if (visible) {
            if (!trafficLayer) {
                trafficLayer = new AMap.TileLayer.Traffic();
                map.add(trafficLayer);
                console.log('添加交通路况图层');
            }
        } else {
            if (trafficLayer) {
                map.remove(trafficLayer);
                trafficLayer = null;
                console.log('移除交通路况图层');
            }
        }
    } catch (error) {
        console.error('切换交通路况图层时出错:', error);
    }
}

// 切换路网图层
function toggleRoadNetLayer(visible) {
    if (!map) return;

    try {
        if (visible) {
            if (!roadNetLayer) {
                roadNetLayer = new AMap.TileLayer.RoadNet();
                map.add(roadNetLayer);
                console.log('添加路网图层');
            }
        } else {
            if (roadNetLayer) {
                map.remove(roadNetLayer);
                roadNetLayer = null;
                console.log('移除路网图层');
            }
        }
    } catch (error) {
        console.error('切换路网图层时出错:', error);
    }
}

// 切换行政区域边界图层
function toggleDistrictLayer(visible) {
    if (!map) return;

    try {
        if (visible) {
            if (!districtLayer) {
                // 加载行政区域插件
                AMap.plugin('AMap.DistrictSearch', function() {
                    const districtSearch = new AMap.DistrictSearch({
                        level: 'district',
                        showbiz: false,
                        extensions: 'all'
                    });
                    
                    // 默认显示全国
                    districtSearch.search('中国', function(status, result) {
                        if (status === 'complete') {
                            const boundaries = result.districtList[0].boundaries;
                            if (boundaries) {
                                districtLayer = new AMap.PolygonLayer({
                                    strokeWeight: 1,
                                    strokeColor: '#0091ea',
                                    strokeOpacity: 0.5,
                                    fillColor: '#1791fc',
                                    fillOpacity: 0.1
                                });
                                
                                const polygons = [];
                                for (let i = 0; i < boundaries.length; i++) {
                                    const polygon = new AMap.Polygon({
                                        path: boundaries[i],
                                        strokeColor: '#0091ea',
                                        strokeWeight: 1,
                                        strokeOpacity: 0.5,
                                        fillColor: '#1791fc',
                                        fillOpacity: 0.1
                                    });
                                    polygons.push(polygon);
                                }
                                
                                map.add(polygons);
                                console.log('添加行政区域边界图层');
                            }
                        } else {
                            console.error('获取行政区域边界失败');
                        }
                    });
                });
            }
        } else {
            if (districtLayer) {
                map.remove(districtLayer);
                districtLayer = null;
                console.log('移除行政区域边界图层');
            }
        }
    } catch (error) {
        console.error('切换行政区域边界图层时出错:', error);
    }
}

// 初始化地图
async function initMap() {
    console.log('开始初始化地图...');
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) {
        console.error('找不到地图容器元素');
        return;
    }

    // 创建地图实例
    map = new AMap.Map('map-container', {
        zoom: 12,
        center: [116.397428, 39.90923], // 北京天安门坐标
        viewMode: '2D',
        resizeEnable: true,
        mapStyle: 'amap://styles/normal',
        features: ['bg', 'road', 'building', 'point', 'boundary'],
        showIndoorMap: false,
        defaultCursor: 'pointer',
        zooms: [3, 20],
        jogEnable: true,
        animateEnable: true,
        dragEnable: true,
        zoomEnable: true,
        doubleClickZoom: true,
        keyboardEnable: false,
        jogEnable: true,
        scrollWheel: true,
        touchZoom: true,
        showBuildingBlock: true,
        showIndoorMap: false,
        expandZoomRange: true,
        zooms: [3, 20],
        layers: [
            new AMap.TileLayer({
                zIndex: 1,
                opacity: 1,
                getTileUrl: function(x, y, z) {
                    return 'https://webst01.is.autonavi.com/appmaptile?style=7&x=' + x + '&y=' + y + '&z=' + z;
                }
            })
        ]
    });

    // 添加地图控件
    map.addControl(new AMap.Scale({
        position: 'LB',
        theme: 'dark'
    }));
    
    map.addControl(new AMap.ControlBar({
        position: {
            right: '10px',
            bottom: '10px'
        },
        theme: 'dark'
    }));

    console.log('地图初始化完成');
}

// 修改图层控制按钮位置
function addLayerControlButton() {
    try {
        if (!map) return;
        
        // 创建自定义控件 - 调整位置
        const layerControlBtn = document.createElement('div');
        layerControlBtn.className = 'amap-control-item layer-control-btn';
        layerControlBtn.style.cssText = 'width: 38px; height: 38px; background: rgba(31, 31, 31, 0.9); border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); cursor: pointer; display: flex; justify-content: center; align-items: center; margin: 10px; color: white; font-size: 16px; position: absolute; top: 80px; right: 12px; z-index: 90; transition: all 0.3s ease;';
        layerControlBtn.innerHTML = '<i style="font-size: 18px;" class="fas fa-layer-group"></i>';
        layerControlBtn.title = '图层控制';
        
        // 添加交互效果
        layerControlBtn.onmouseover = function() {
            this.style.backgroundColor = 'rgba(40, 40, 40, 0.95)';
            this.style.transform = 'scale(1.05)';
        };
        
        layerControlBtn.onmouseout = function() {
            this.style.backgroundColor = 'rgba(31, 31, 31, 0.9)';
            this.style.transform = 'scale(1)';
        };
        
        // 添加点击事件
        layerControlBtn.onclick = function() {
            toggleLayerControl();
        };
        
        // 将按钮添加到地图容器
        const mapContainer = document.getElementById('map-container');
        if (mapContainer) {
            mapContainer.appendChild(layerControlBtn);
        }
        
        // 初始化图层控制面板
        createLayerControl();
        
    } catch (error) {
        console.error('添加图层控制按钮时出错:', error);
    }
} 