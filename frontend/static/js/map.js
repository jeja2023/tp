// 地图相关功能

// 全局地图变量
let map = null;
let marker = null;
let pathLayer = null; // 用于存储路径图层
let markersLayer = null; // 用于存储批量导入的标记点
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

// 初始化地图
function initMap() {
    return new Promise((resolve, reject) => {
        if (window.map) {
            console.log('地图已经初始化');
            resolve(window.map);
            return;
        }
        
        try {
            console.log('开始初始化地图');
            const mapContainer = document.getElementById('map-container');
            
            if (!mapContainer) {
                console.error('找不到地图容器元素');
                reject(new Error('找不到地图容器元素'));
                return;
            }
            
            if (!window.AMap) {
                console.error('高德地图API尚未加载完成');
                reject(new Error('地图组件尚未完成加载，请稍后再试'));
                return;
            }
            
            // 创建地图实例
            window.map = new window.AMap.Map(mapContainer, {
                viewMode: '2D',  // 使用2D视图
                zoom: 11,  // 设置默认缩放级别为11
                center: [120.301663, 31.574729],  // 无锡市中心坐标
                resizeEnable: true,
                isHotspot: false,  // 禁用热点和标注
                defaultCursor: 'default',  // 设置默认光标样式
                showBuildingBlock: false,  // 不显示3D建筑物
                layers: [],  // 先不设置图层，由setupMapLayers控制
                offline: true,  // 启用离线模式
                zooms: [1, 12],  // 限制缩放级别
                features: ['bg', 'building'],  // 只显示基础图层
                showRoad: false,  // 不显示道路
                showTraffic: false,  // 不显示交通
                showPOI: false,  // 不显示兴趣点
                showBuilding: false,  // 不显示建筑物
                showIndoorMap: false,  // 不显示室内地图
                showLabel: false  // 不显示标签
            });
            
            // 添加图层控制
            setupMapLayers();
            
            console.log('地图初始化完成');
            
            // 触发resize事件，确保地图完全渲染
            setTimeout(() => {
                if (window.map) {
                    window.map.resize();
                    resolve(window.map);
                }
            }, 200);
        } catch (error) {
            console.error('初始化地图出错:', error);
            reject(error);
        }
    });
}

// 设置地图图层
function setupMapLayers() {
    if (!window.map) return;
    
    try {
        // 创建标准矢量图层
        window.vectorLayer = new window.AMap.TileLayer({
            zIndex: 0,
            visible: true
        });               
        
        // 添加标准矢量图层并设置为可见
        window.vectorLayer.setMap(window.map);           
        console.log('地图图层设置完成，包括矢量图层');

        // 重写AMap.TileLayer.prototype.getTileUrl方法
        if (window.AMap.TileLayer) {
            window.AMap.TileLayer.prototype.getTileUrl = function(x, y, z) {
                if (z > 12) z = 12;
                return `/frontend/static/js/MAP_zxy/${z}/${x}/${y}.png`;
            };
        }
    } catch (error) {
        console.error('设置地图图层出错:', error);
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
                    // 创建标记，使用自定义HTML内容的数字图标
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
    processImportedGps: processImportedGps
};

// 导出独立函数，确保能直接调用
window.showGpsImportDialog = showGpsImportDialog;
window.plotImagesOnMap = plotImagesOnMap;

// 导出地图初始化函数
window.initMap = initMap;

// 导出更新预览函数
window.updatePreview = updatePreview; 