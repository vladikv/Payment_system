document.addEventListener('DOMContentLoaded', () => {
    const ctx = document.getElementById('transactionChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: CHART_LABELS,
            datasets: [
                {
                    label: 'Income',
                    data: CHART_INCOME,
                    backgroundColor: 'rgba(34, 197, 94, 0.5)',
                    borderColor: 'rgba(34, 197, 94, 1)',
                    borderWidth: 1,
                    borderRadius: 6,
                },
                {
                    label: 'Expenses',
                    data: CHART_EXPENSE,
                    backgroundColor: 'rgba(239, 68, 68, 0.5)',
                    borderColor: 'rgba(239, 68, 68, 1)',
                    borderWidth: 1,
                    borderRadius: 6,
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: '#e8e9f0' }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#7b7f96' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y: {
                    ticks: { color: '#7b7f96' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        }
    });
});