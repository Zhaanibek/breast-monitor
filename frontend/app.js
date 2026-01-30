// ===== Configuration =====
const CONFIG = {
    apiUrl: localStorage.getItem('apiUrl') || 'http://localhost:8000',
    asymmetryThreshold: parseFloat(localStorage.getItem('asymThreshold')) || 0.5
};

// ===== State =====
let currentMeasurements = {
    leftZones: [36.4, 36.3, 36.5, 36.4],
    rightZones: [37.1, 37.2, 37.3, 37.0]
};

let historyData = [];

// ===== DOM Elements =====
const pages = document.querySelectorAll('.page');
const navLinks = document.querySelectorAll('.nav-link');
const pageTitle = document.querySelector('.page-title');

// ===== Navigation =====
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const pageName = link.dataset.page;
        navigateTo(pageName);
    });
});

function navigateTo(pageName) {
    // Update nav links
    navLinks.forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');
    
    // Update pages
    pages.forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${pageName}`).classList.add('active');
    
    // Update title
    const titles = {
        overview: 'Обзор',
        input: 'Ввод данных',
        upload: 'Загрузка термограммы',
        history: 'История',
        analysis: 'AI Анализ',
        settings: 'Настройки'
    };
    pageTitle.textContent = titles[pageName] || 'Обзор';
}

// ===== Date Display =====
function updateDate() {
    const now = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('currentDate').textContent = now.toLocaleDateString('ru-RU', options);
}
updateDate();

// ===== Temperature Chart =====
let tempChart = null;

function initChart() {
    const ctx = document.getElementById('tempChart').getContext('2d');
    
    // Generate sample data for last 30 days
    const labels = [];
    const leftData = [];
    const rightData = [];
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }));
        leftData.push(36.2 + Math.random() * 0.6);
        rightData.push(36.4 + Math.random() * 0.8);
    }
    
    tempChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Левая грудь',
                    data: leftData,
                    borderColor: '#00d4aa',
                    backgroundColor: 'rgba(0, 212, 170, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Правая грудь',
                    data: rightData,
                    borderColor: '#7c3aed',
                    backgroundColor: 'rgba(124, 58, 237, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#94a3b8',
                        usePointStyle: true,
                        padding: 20
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b' }
                },
                y: {
                    min: 35,
                    max: 39,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#64748b',
                        callback: (value) => value + '°C'
                    }
                }
            }
        }
    });
}

// ===== Analysis Logic =====
function calculateMetrics(leftZones, rightZones) {
    const avgLeft = leftZones.reduce((a, b) => a + b, 0) / leftZones.length;
    const avgRight = rightZones.reduce((a, b) => a + b, 0) / rightZones.length;
    const asymmetry = Math.abs(avgLeft - avgRight);
    const avgTotal = (avgLeft + avgRight) / 2;
    const maxTemp = Math.max(...leftZones, ...rightZones);
    
    let riskLevel = 'normal';
    if (asymmetry >= 1.0 || maxTemp >= 38.0) {
        riskLevel = 'high';
    } else if (asymmetry >= 0.5 || maxTemp >= 37.5) {
        riskLevel = 'elevated';
    }
    
    return { avgLeft, avgRight, asymmetry, avgTotal, maxTemp, riskLevel };
}

function updateDashboard(metrics) {
    // Update temperature values
    document.getElementById('leftTemp').textContent = metrics.avgLeft.toFixed(1) + '°C';
    document.getElementById('rightTemp').textContent = metrics.avgRight.toFixed(1) + '°C';
    document.getElementById('avgTemp').textContent = metrics.avgTotal.toFixed(1) + '°C';
    
    // Update asymmetry
    const asymValue = document.getElementById('asymmetryValue');
    const sign = metrics.avgRight > metrics.avgLeft ? '+' : '-';
    asymValue.textContent = sign + metrics.asymmetry.toFixed(1) + '°C';
    asymValue.className = 'metric-value ' + metrics.riskLevel;
    
    // Update risk indicator
    const riskIndicator = document.getElementById('riskIndicator');
    const riskLabels = {
        normal: '<i class="fas fa-check-circle"></i> НОРМА',
        elevated: '<i class="fas fa-exclamation-triangle"></i> ПОВЫШЕННЫЙ',
        high: '<i class="fas fa-times-circle"></i> ВЫСОКИЙ'
    };
    riskIndicator.innerHTML = riskLabels[metrics.riskLevel];
    riskIndicator.className = 'risk-indicator ' + metrics.riskLevel;
    
    // Update badge
    const badge = document.getElementById('overviewBadge');
    const badgeLabels = { normal: 'Норма', elevated: 'Внимание', high: 'Требует внимания' };
    badge.textContent = badgeLabels[metrics.riskLevel];
    badge.className = 'card-badge badge-' + metrics.riskLevel;
    
    // Update thermal visualization
    updateThermalViz(metrics);
}

function updateThermalViz(metrics) {
    const leftThermal = document.getElementById('leftThermal');
    const rightThermal = document.getElementById('rightThermal');
    
    // Map temperature to color
    function tempToGradient(temp) {
        if (temp >= 38) return 'linear-gradient(180deg, #f59e0b 0%, #ef4444 100%)';
        if (temp >= 37) return 'linear-gradient(180deg, #22c55e 0%, #f59e0b 100%)';
        return 'linear-gradient(180deg, #3b82f6 0%, #22c55e 100%)';
    }
    
    leftThermal.style.background = tempToGradient(metrics.avgLeft);
    rightThermal.style.background = tempToGradient(metrics.avgRight);
}

// ===== Manual Input =====
document.getElementById('submitTemps').addEventListener('click', async () => {
    const zones = [];
    for (let i = 1; i <= 8; i++) {
        const input = document.getElementById(`zone${i}`);
        const value = parseFloat(input.value) || 36.5;
        zones.push(value);
    }
    
    const leftZones = zones.slice(0, 4);
    const rightZones = zones.slice(4, 8);
    
    // Calculate metrics
    const metrics = calculateMetrics(leftZones, rightZones);
    
    // Try to send to API
    try {
        const response = await fetch(`${CONFIG.apiUrl}/api/measurements`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sensor_1: zones[0], sensor_2: zones[1], 
                sensor_3: zones[2], sensor_4: zones[3],
                sensor_5: zones[4], sensor_6: zones[5], 
                sensor_7: zones[6], sensor_8: zones[7],
                source: 'manual'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showAnalysisResult(data);
        }
    } catch (e) {
        console.log('API not available, using local analysis');
    }
    
    // Show local analysis
    showLocalAnalysis(metrics);
    
    // Update dashboard
    currentMeasurements = { leftZones, rightZones };
    updateDashboard(metrics);
    
    // Add to history
    addToHistory(metrics, 'manual');
});

function showLocalAnalysis(metrics) {
    const resultDiv = document.getElementById('manualAnalysisResult');
    const icon = resultDiv.querySelector('.analysis-icon');
    const text = document.getElementById('analysisText');
    
    icon.className = 'analysis-icon ' + metrics.riskLevel;
    
    let message = '';
    if (metrics.riskLevel === 'normal') {
        message = `✅ Все показатели в норме. Средняя температура ${metrics.avgTotal.toFixed(1)}°C, асимметрия ${metrics.asymmetry.toFixed(2)}°C - в пределах допустимых значений.`;
    } else if (metrics.riskLevel === 'elevated') {
        message = `⚠️ Обнаружена незначительная асимметрия температур (${metrics.asymmetry.toFixed(2)}°C). Рекомендуется повторить измерение через 24-48 часов. Средняя температура: ${metrics.avgTotal.toFixed(1)}°C.`;
    } else {
        message = `🔴 Обнаружена значительная температурная асимметрия (${metrics.asymmetry.toFixed(2)}°C) или повышенная температура. Рекомендуется обратиться к специалисту для дополнительного обследования.`;
    }
    
    text.textContent = message;
    resultDiv.style.display = 'block';
}

// ===== Scenario Generators =====
function generateHealthyScenario() {
    // Healthy: symmetric temperatures, low variance, normal range
    const baseTemp = 36.2 + Math.random() * 0.3; // 36.2 - 36.5
    const temps = [];
    for (let i = 0; i < 8; i++) {
        temps.push(+(baseTemp + (Math.random() * 0.3 - 0.15)).toFixed(1));
    }
    return temps;
}

function generateElevatedScenario() {
    // Elevated risk: slight asymmetry (0.5-0.9°C)
    const leftBase = 36.3 + Math.random() * 0.3;
    const rightBase = leftBase + 0.5 + Math.random() * 0.4; // 0.5-0.9°C higher
    const temps = [];
    for (let i = 0; i < 4; i++) {
        temps.push(+(leftBase + (Math.random() * 0.2 - 0.1)).toFixed(1));
    }
    for (let i = 0; i < 4; i++) {
        temps.push(+(rightBase + (Math.random() * 0.2 - 0.1)).toFixed(1));
    }
    return temps;
}

function generateSickScenario() {
    // High risk: significant asymmetry (>1°C) or hot spots
    const leftBase = 36.2 + Math.random() * 0.3;
    const rightBase = leftBase + 1.0 + Math.random() * 0.8; // 1.0-1.8°C higher
    const temps = [];
    for (let i = 0; i < 4; i++) {
        temps.push(+(leftBase + (Math.random() * 0.2 - 0.1)).toFixed(1));
    }
    // Add a hot spot in right breast
    temps.push(+(rightBase + 0.5).toFixed(1)); // Hot spot
    temps.push(+(rightBase + (Math.random() * 0.3)).toFixed(1));
    temps.push(+(rightBase + (Math.random() * 0.3)).toFixed(1));
    temps.push(+(rightBase + (Math.random() * 0.3)).toFixed(1));
    return temps;
}

function generateRandomScenario() {
    // Completely random - could be any scenario
    const scenarios = [generateHealthyScenario, generateElevatedScenario, generateSickScenario];
    const randomPicker = Math.random();
    if (randomPicker < 0.5) return generateHealthyScenario();
    if (randomPicker < 0.8) return generateElevatedScenario();
    return generateSickScenario();
}

function fillTemperatureInputs(temps) {
    for (let i = 0; i < 8; i++) {
        document.getElementById(`zone${i + 1}`).value = temps[i];
    }
    // Visual feedback
    document.querySelectorAll('.temp-input').forEach(input => {
        input.style.animation = 'none';
        input.offsetHeight; // Trigger reflow
        input.style.animation = 'pulse 0.5s ease';
    });
}

// Scenario button handlers
document.getElementById('scenarioHealthy').addEventListener('click', () => {
    const temps = generateHealthyScenario();
    fillTemperatureInputs(temps);
});

document.getElementById('scenarioElevated').addEventListener('click', () => {
    const temps = generateElevatedScenario();
    fillTemperatureInputs(temps);
});

document.getElementById('scenarioSick').addEventListener('click', () => {
    const temps = generateSickScenario();
    fillTemperatureInputs(temps);
});

document.getElementById('scenarioRandom').addEventListener('click', () => {
    const temps = generateRandomScenario();
    fillTemperatureInputs(temps);
});

document.getElementById('clearInputs').addEventListener('click', () => {
    for (let i = 1; i <= 8; i++) {
        document.getElementById(`zone${i}`).value = '';
    }
    document.getElementById('manualAnalysisResult').style.display = 'none';
});

// ===== Image Upload =====
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const uploadPreview = document.getElementById('uploadPreview');
const previewImage = document.getElementById('previewImage');

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleImageUpload(file);
    }
});

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleImageUpload(file);
    }
});

function handleImageUpload(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        uploadZone.style.display = 'none';
        uploadPreview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

document.getElementById('cancelUpload').addEventListener('click', () => {
    uploadZone.style.display = 'block';
    uploadPreview.style.display = 'none';
    document.getElementById('imageAnalysisResult').style.display = 'none';
    fileInput.value = '';
});

document.getElementById('analyzeImage').addEventListener('click', async () => {
    const resultDiv = document.getElementById('imageAnalysisResult');
    const icon = document.getElementById('imageAnalysisIcon');
    const text = document.getElementById('imageAnalysisText');
    
    // Show loading
    text.textContent = 'Анализ изображения...';
    resultDiv.style.display = 'block';
    
    // Simulate analysis (in real app, this would call the API)
    setTimeout(() => {
        // Simulate extracted temperatures from thermal image
        const simulatedTemps = {
            leftZones: [36.2 + Math.random() * 0.5, 36.3 + Math.random() * 0.5, 36.1 + Math.random() * 0.5, 36.4 + Math.random() * 0.5],
            rightZones: [36.5 + Math.random() * 0.8, 36.8 + Math.random() * 0.8, 36.6 + Math.random() * 0.8, 36.7 + Math.random() * 0.8]
        };
        
        const metrics = calculateMetrics(simulatedTemps.leftZones, simulatedTemps.rightZones);
        
        icon.className = 'analysis-icon ' + metrics.riskLevel;
        
        text.innerHTML = `
            <strong>Результаты анализа термограммы:</strong><br><br>
            📊 Извлечённые температуры:<br>
            • Левая грудь (средняя): ${metrics.avgLeft.toFixed(1)}°C<br>
            • Правая грудь (средняя): ${metrics.avgRight.toFixed(1)}°C<br>
            • Асимметрия: ${metrics.asymmetry.toFixed(2)}°C<br><br>
            📋 Заключение: ${metrics.riskLevel === 'normal' ? 'Показатели в пределах нормы.' : 
                            metrics.riskLevel === 'elevated' ? 'Обнаружена незначительная асимметрия. Рекомендуется повторный анализ.' :
                            'Обнаружены значимые отклонения. Рекомендуется консультация специалиста.'}<br><br>
            <em>⚠️ Данный анализ носит информационный характер и не является медицинским диагнозом.</em>
        `;
        
        // Update dashboard
        currentMeasurements = simulatedTemps;
        updateDashboard(metrics);
        addToHistory(metrics, 'image');
        
    }, 2000);
});

// ===== History =====
function addToHistory(metrics, source) {
    const entry = {
        date: new Date().toLocaleString('ru-RU'),
        leftTemp: metrics.avgLeft.toFixed(1),
        rightTemp: metrics.avgRight.toFixed(1),
        asymmetry: metrics.asymmetry.toFixed(2),
        riskLevel: metrics.riskLevel,
        source: source === 'manual' ? 'Ручной ввод' : 'Термограмма'
    };
    
    historyData.unshift(entry);
    localStorage.setItem('historyData', JSON.stringify(historyData));
    renderHistory();
}

function renderHistory() {
    const tbody = document.getElementById('historyTableBody');
    
    if (historyData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Нет данных</td></tr>';
        return;
    }
    
    tbody.innerHTML = historyData.map(entry => `
        <tr>
            <td>${entry.date}</td>
            <td>${entry.leftTemp}°C</td>
            <td>${entry.rightTemp}°C</td>
            <td>${entry.asymmetry}°C</td>
            <td><span class="card-badge badge-${entry.riskLevel}">${
                entry.riskLevel === 'normal' ? 'Норма' : 
                entry.riskLevel === 'elevated' ? 'Повышен' : 'Высокий'
            }</span></td>
            <td>${entry.source}</td>
        </tr>
    `).join('');
}

// Load history from localStorage
try {
    historyData = JSON.parse(localStorage.getItem('historyData')) || [];
} catch {
    historyData = [];
}

// ===== Settings =====
document.getElementById('saveSettings').addEventListener('click', () => {
    const apiUrl = document.getElementById('apiUrl').value;
    const asymThreshold = document.getElementById('asymThreshold').value;
    
    localStorage.setItem('apiUrl', apiUrl);
    localStorage.setItem('asymThreshold', asymThreshold);
    
    CONFIG.apiUrl = apiUrl;
    CONFIG.asymmetryThreshold = parseFloat(asymThreshold);
    
    alert('Настройки сохранены!');
});

// Load settings
document.getElementById('apiUrl').value = CONFIG.apiUrl;
document.getElementById('asymThreshold').value = CONFIG.asymmetryThreshold;

// ===== Tabs =====
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
    });
});

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    renderHistory();
    
    // Initial dashboard update with sample data
    const metrics = calculateMetrics(currentMeasurements.leftZones, currentMeasurements.rightZones);
    updateDashboard(metrics);
});

// Add CSS for active page
const style = document.createElement('style');
style.textContent = `
    .page { display: none; }
    .page.active { display: block; }
`;
document.head.appendChild(style);
