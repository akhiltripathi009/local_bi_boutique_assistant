/**
 * Mishika Fashion Luxury Boutique - ApexCharts Engine
 * High-performance, luxury-styled financial charts
 */

const ChartsManager = {
  hourlyChart: null,
  categoryChart: null,

  initHourlySalesChart(containerId, seriesData) {
    const el = document.getElementById(containerId);
    if (!el || !seriesData || seriesData.length === 0) return;
    if (typeof ApexCharts === 'undefined') {
      console.warn('ApexCharts library is loading or offline.');
      el.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-muted); font-size:12px;">📊 Hourly Sales data loaded. ApexCharts rendering engine connecting...</div>';
      return;
    }

    const hours = seriesData.map(d => d.hour);
    const revenue = seriesData.map(d => d.revenue);
    const profit = seriesData.map(d => d.profit);

    const options = {
      series: [
        { name: 'Total Revenue ($)', data: revenue },
        { name: 'Gross Profit ($)', data: profit }
      ],
      chart: {
        type: 'area',
        height: 280,
        toolbar: { show: false },
        background: 'transparent',
        fontFamily: 'Inter, sans-serif'
      },
      colors: ['#d4af37', '#10b981'],
      fill: {
        type: 'gradient',
        gradient: {
          shadeIntensity: 1,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [0, 95, 100]
        }
      },
      stroke: {
        curve: 'smooth',
        width: 2.5
      },
      dataLabels: { enabled: false },
      xaxis: {
        categories: hours,
        labels: { style: { colors: '#94a3b8', fontSize: '11px' } },
        axisBorder: { show: false },
        axisTicks: { show: false }
      },
      yaxis: {
        labels: {
          style: { colors: '#94a3b8', fontSize: '11px' },
          formatter: (val) => `$${val.toLocaleString()}`
        }
      },
      grid: {
        borderColor: 'rgba(255, 255, 255, 0.06)',
        strokeDashArray: 4
      },
      tooltip: {
        theme: 'dark',
        y: { formatter: (val) => `$${val.toFixed(2)}` }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'right',
        labels: { colors: '#f8fafc' },
        markers: { radius: 12 }
      }
    };

    if (ChartsManager.hourlyChart) {
      ChartsManager.hourlyChart.updateOptions(options);
    } else {
      ChartsManager.hourlyChart = new ApexCharts(el, options);
      ChartsManager.hourlyChart.render();
    }
  },

  initCategoryChart(containerId, categoryData) {
    const el = document.getElementById(containerId);
    if (!el || !categoryData || categoryData.length === 0) return;
    if (typeof ApexCharts === 'undefined') {
      el.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-muted); font-size:12px;">📊 Category data loaded. ApexCharts rendering engine connecting...</div>';
      return;
    }

    const categories = categoryData.map(c => c.category);
    const revenues = categoryData.map(c => c.revenue);

    const options = {
      series: [{ name: 'Revenue', data: revenues }],
      chart: {
        type: 'bar',
        height: 280,
        toolbar: { show: false },
        background: 'transparent',
        fontFamily: 'Inter, sans-serif'
      },
      plotOptions: {
        bar: {
          borderRadius: 6,
          horizontal: true,
          barHeight: '55%',
          distributed: true
        }
      },
      colors: ['#d4af37', '#38bdf8', '#a855f7', '#f43f5e', '#10b981'],
      dataLabels: {
        enabled: true,
        formatter: (val) => `$${val.toLocaleString()}`,
        style: { fontSize: '11px', colors: ['#ffffff'] }
      },
      xaxis: {
        categories: categories,
        labels: {
          style: { colors: '#94a3b8', fontSize: '10px' },
          formatter: (val) => `$${val}`
        },
        axisBorder: { show: false }
      },
      yaxis: {
        labels: { style: { colors: '#f8fafc', fontSize: '12px', fontWeight: 600 } }
      },
      grid: {
        borderColor: 'rgba(255, 255, 255, 0.06)',
        strokeDashArray: 4
      },
      tooltip: {
        theme: 'dark',
        y: { formatter: (val) => `$${val.toFixed(2)}` }
      },
      legend: { show: false }
    };

    if (ChartsManager.categoryChart) {
      ChartsManager.categoryChart.updateOptions(options);
    } else {
      ChartsManager.categoryChart = new ApexCharts(el, options);
      ChartsManager.categoryChart.render();
    }
  },

  liveStockChart: null,

  initLiveOpsStockChart(containerId, items) {
    const el = document.getElementById(containerId);
    if (!el || !items || items.length === 0) return;
    if (typeof ApexCharts === 'undefined') {
      el.innerHTML = '<div style="padding:30px; text-align:center; color:var(--text-muted); font-size:12px;">📊 Stock chart connecting...</div>';
      return;
    }

    const categories = items.map(i => i.product_name);
    const seriesData = items.map(i => i.stock);
    const colors = items.map(i => i.color);

    const options = {
      series: [{ name: 'Units On Hand', data: seriesData }],
      chart: {
        type: 'bar',
        height: 220,
        toolbar: { show: false },
        background: 'transparent',
        fontFamily: 'Inter, sans-serif',
        animations: {
          enabled: true,
          easing: 'easeinout',
          speed: 250,
          dynamicAnimation: { enabled: true, speed: 250 }
        }
      },
      plotOptions: {
        bar: {
          borderRadius: 4,
          columnWidth: '65%',
          distributed: true,
          dataLabels: { position: 'top' }
        }
      },
      colors: colors,
      dataLabels: {
        enabled: true,
        formatter: (val) => val,
        offsetY: -18,
        style: { fontSize: '10px', colors: ['#94a3b8'], fontWeight: 700 }
      },
      xaxis: {
        categories: categories,
        labels: {
          rotate: -45,
          rotateAlways: true,
          trim: true,
          maxHeight: 70,
          style: { colors: '#94a3b8', fontSize: '9.5px', fontFamily: 'Inter' }
        },
        axisBorder: { color: '#334155' },
        axisTicks: { show: false }
      },
      yaxis: {
        min: 0,
        max: Math.max(...seriesData, 100) + 15,
        labels: {
          style: { colors: '#94a3b8', fontSize: '10px' },
          formatter: (val) => Math.round(val)
        },
        title: {
          text: 'Units On Hand',
          style: { color: '#64748b', fontSize: '11px', fontWeight: 600 }
        }
      },
      grid: {
        borderColor: 'rgba(255, 255, 255, 0.05)',
        strokeDashArray: 3
      },
      tooltip: {
        theme: 'dark',
        y: {
          formatter: (val, opts) => {
            const item = items[opts.dataPointIndex];
            return `${val} units (${item ? item.tag : ''})`;
          }
        }
      },
      legend: { show: false }
    };

    if (ChartsManager.liveStockChart) {
      ChartsManager.liveStockChart.updateOptions(options, true, true);
    } else {
      ChartsManager.liveStockChart = new ApexCharts(el, options);
      ChartsManager.liveStockChart.render();
    }
  },

  updateTheme(mode = 'dark') {
    const isLight = mode === 'light';
    const tooltipTheme = isLight ? 'light' : 'dark';
    const textColor = isLight ? '#475569' : '#94a3b8';
    const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.05)';

    const commonUpdate = {
      theme: { mode: tooltipTheme },
      tooltip: { theme: tooltipTheme },
      grid: { borderColor: gridColor }
    };

    if (this.hourlyChart) {
      try {
        this.hourlyChart.updateOptions({
          ...commonUpdate,
          xaxis: { labels: { style: { colors: textColor } } },
          yaxis: { labels: { style: { colors: textColor } } }
        }, false, true);
      } catch (e) {}
    }
    if (this.categoryChart) {
      try {
        this.categoryChart.updateOptions({
          ...commonUpdate,
          legend: { labels: { colors: textColor } }
        }, false, true);
      } catch (e) {}
    }
    if (this.liveStockChart) {
      try {
        this.liveStockChart.updateOptions({
          ...commonUpdate,
          xaxis: { labels: { style: { colors: textColor } } },
          yaxis: { labels: { style: { colors: textColor } } }
        }, false, true);
      } catch (e) {}
    }
  }
};
