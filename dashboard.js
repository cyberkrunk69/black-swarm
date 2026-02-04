```javascript
// ... existing code ...

// Render model distribution chart
const modelDistributionChart = document.getElementById('model-distribution-chart').getContext('2d');
const chart = new Chart(modelDistributionChart, {
  type: 'bar',
  data: {
    labels: ['Claude', 'Groq'],
    datasets: [{
      label: 'Model Distribution',
      data: [claudeModels, groqModels],
      backgroundColor: [
        'rgba(255, 99, 132, 0.2)',
        'rgba(54, 162, 235, 0.2)'
      ],
      borderColor: [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)'
      ],
      borderWidth: 1
    }]
  },
  options: {
    scales: {
      yAxes: [{
        ticks: {
          beginAtZero: true
        }
      }]
    }
  }
});
```