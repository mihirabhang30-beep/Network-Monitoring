/**
 * NetGuard — Chart.js Initialization
 */

let protocolChart = null;
let topSourcesChart = null;

const chartColors = {
    TCP: { bg: 'rgba(16, 185, 129, 0.7)', border: '#10b981' },
    UDP: { bg: 'rgba(59, 130, 246, 0.7)', border: '#3b82f6' },
    ICMP: { bg: 'rgba(245, 158, 11, 0.7)', border: '#f59e0b' },
    '-': { bg: 'rgba(148, 163, 184, 0.5)', border: '#94a3b8' }
};

const barPalette = [
    'rgba(59, 130, 246, 0.7)', 'rgba(16, 185, 129, 0.7)',
    'rgba(245, 158, 11, 0.7)', 'rgba(139, 92, 246, 0.7)',
    'rgba(6, 182, 212, 0.7)', 'rgba(236, 72, 153, 0.7)',
    'rgba(239, 68, 68, 0.7)', 'rgba(34, 197, 94, 0.7)',
    'rgba(168, 85, 247, 0.7)', 'rgba(251, 191, 36, 0.7)'
];

function initCharts(protocolData, topSourceData) {
    // Protocol Pie Chart
    const pCtx = document.getElementById('protocolChart');
    if (pCtx) {
        const labels = protocolData.map(function(d) { return d[0]; });
        const values = protocolData.map(function(d) { return d[1]; });
        const bgColors = labels.map(function(l) { return (chartColors[l] || chartColors['-']).bg; });
        const borderColors = labels.map(function(l) { return (chartColors[l] || chartColors['-']).border; });

        protocolChart = new Chart(pCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 2,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#94a3b8', padding: 16, font: { size: 12 } }
                    }
                },
                cutout: '65%'
            }
        });
    }

    // Top Sources Bar Chart
    const sCtx = document.getElementById('topSourcesChart');
    if (sCtx) {
        const labels = topSourceData.map(function(d) { return d[0]; });
        const values = topSourceData.map(function(d) { return d[1]; });

        topSourcesChart = new Chart(sCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Packet Count',
                    data: values,
                    backgroundColor: barPalette.slice(0, labels.length),
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 40
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(148,163,184,0.06)' },
                        ticks: { color: '#64748b', font: { size: 11 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', font: { size: 11 } }
                    }
                }
            }
        });
    }
}

function updateProtocolChart(statsObj) {
    if (!protocolChart) return;
    var labels = Object.keys(statsObj);
    var values = Object.values(statsObj);
    var bgColors = labels.map(function(l) { return (chartColors[l] || chartColors['-']).bg; });
    var borderColors = labels.map(function(l) { return (chartColors[l] || chartColors['-']).border; });

    protocolChart.data.labels = labels;
    protocolChart.data.datasets[0].data = values;
    protocolChart.data.datasets[0].backgroundColor = bgColors;
    protocolChart.data.datasets[0].borderColor = borderColors;
    protocolChart.update('none');
}
