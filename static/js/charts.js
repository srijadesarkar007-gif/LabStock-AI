/**
 * LabStock AI - Chart.js Visualizations
 * Academic navy-blue and slate visual themes
 */

document.addEventListener('DOMContentLoaded', () => {
    initDemandForecastChart();
    initDepartmentDistributionChart();
});

/**
 * Initializes the Predictive Demand Forecast Line Chart
 */
function initDemandForecastChart() {
    const ctx = document.getElementById('demandForecastChart');
    if (!ctx) return;

    fetch('/api/forecast/chart')
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Historical Actual Consumption',
                            data: data.actual,
                            borderColor: '#0f2b48',
                            backgroundColor: 'rgba(15, 43, 72, 0.08)',
                            fill: true,
                            tension: 0.3,
                            borderWidth: 2.5,
                            pointRadius: 4,
                            pointBackgroundColor: '#0f2b48'
                        },
                        {
                            label: 'AI Predictive Forecast',
                            data: data.predicted,
                            borderColor: '#2563eb',
                            backgroundColor: 'rgba(37, 99, 235, 0.08)',
                            borderDash: [6, 6],
                            fill: true,
                            tension: 0.3,
                            borderWidth: 2.5,
                            pointRadius: 5,
                            pointBackgroundColor: '#2563eb'
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
                                font: { family: '-apple-system, Segoe UI, Roboto', size: 12 },
                                color: '#334155',
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            backgroundColor: '#0a1c36',
                            titleFont: { size: 13, weight: 'bold' },
                            bodyFont: { size: 12 },
                            padding: 10
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: '#f1f5f9' },
                            ticks: { color: '#64748b', font: { size: 11 } }
                        },
                        y: {
                            beginAtZero: true,
                            grid: { color: '#e2e8f0' },
                            ticks: { color: '#64748b', font: { size: 11 } }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error("Failed to load forecast chart data:", err);
        });
}

/**
 * Initializes the Department Inventory Distribution Chart
 */
function initDepartmentDistributionChart() {
    const ctx = document.getElementById('deptDistributionChart');
    if (!ctx) return;

    fetch('/api/department-distribution')
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.counts,
                        backgroundColor: [
                            '#0f2b48',
                            '#2563eb',
                            '#38bdf8',
                            '#94a3b8'
                        ],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                padding: 14,
                                font: { size: 11 },
                                color: '#334155'
                            }
                        }
                    },
                    cutout: '65%'
                }
            });
        })
        .catch(err => {
            console.error("Failed to load department distribution data:", err);
        });
}
