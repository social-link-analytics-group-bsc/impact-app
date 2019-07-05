// Set new default font family and font color to mimic Bootstrap's default styling
//import ChartDataLabels from 'chartjs-plugin-datalabels';
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';
Chart.plugins.unregister(ChartDataLabels);

// Line chart
function drawLineChart(domElementId, data, showLegend, showDataPointLabels){
    var ctx = document.getElementById(domElementId);
    var myLineChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: [],
      },
      options: {
        maintainAspectRatio: false,
        layout: {
          padding: {
            left: 10,
            right: 25,
            top: 25,
            bottom: 0
          }
        },
        scales: {
          xAxes: [{
            time: {
              unit: 'date'
            },
            gridLines: {
              display: false,
              drawBorder: false
            },
            ticks: {
              maxTicksLimit: 7,
              autoSkip: false
            }
          }],
          yAxes: [{
            ticks: {
              maxTicksLimit: 5,
              padding: 10
            },
            gridLines: {
              color: "rgb(234, 236, 244)",
              zeroLineColor: "rgb(234, 236, 244)",
              drawBorder: false,
              borderDash: [2],
              zeroLineBorderDash: [2]
            }
          }],
        },
        legend: {
          display: showLegend
        },
        tooltips: {
          backgroundColor: "rgb(255,255,255)",
          bodyFontColor: "#858796",
          titleMarginBottom: 10,
          titleFontColor: '#6e707e',
          titleFontSize: 14,
          borderColor: '#dddfeb',
          borderWidth: 1,
          xPadding: 15,
          yPadding: 15,
          displayColors: false,
          intersect: false,
          mode: 'index',
          caretPadding: 10,
          callbacks: {
            label: function(tooltipItem, chart) {
              var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
              return datasetLabel + ': ' + tooltipItem.yLabel;
            }
          }
        }
      }
    });
    for (index = 0; index < data.datasets.length; ++index) {
        dataset = data.datasets[index]
        myLineChart.data.datasets.push({
            label: dataset.label,
            fill: dataset.fill,
            lineTension: 0.1,
            //backgroundColor: "rgba(0, 0, 0, 0.1)",
            borderColor: dataset.color,  // line color
            pointRadius: 3,
            pointBackgroundColor: dataset.color,
            pointBorderColor: dataset.color,
            pointHoverRadius: 3,
            pointHoverBackgroundColor: dataset.color,
            pointHoverBorderColor: dataset.color,
            pointHitRadius: 10,
            pointBorderWidth: 2,
            data: dataset.data,
            borderDash: dataset.lineType
        });
    }
    myLineChart.update();
}

