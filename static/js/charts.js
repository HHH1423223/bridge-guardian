/* ============================================================================
   charts.js —— ECharts 统一取色与换肤脚手架（规范 4.4.1 / 4.5 / 7.7）
   ----------------------------------------------------------------------------
   为什么需要它：ECharts 与 Three.js 都拿不到 CSS 变量，规范要求它们
   【运行时读取根元素的计算样式取得同名变量值】，禁止在 JS 里另抄一份色值。
   本文件是全站唯一的取色入口：任何图表配置里的颜色、字号、字体都必须来自
   window.BGCharts.tokens()，不得出现色值字面量。

   换肤：主题切换时 _shell.html 广播 document 上的 `bg:themechange` 事件，
   图表用 BGCharts.onThemeChange(fn) 订阅后重新 setOption（完整替换，不销毁实例）。
   ========================================================================== */
(function () {
  'use strict';

  /* CSS 变量名 → 返回对象里的键名。只登记规范 2.1.6 与第四章用到的变量。 */
  var NAMES = {
    seriesPrimary: '--chart-series-primary',
    seriesSecondary: '--chart-series-secondary',
    seriesTertiary: '--chart-series-tertiary',
    area: '--chart-area',
    grid: '--chart-grid',
    axis: '--chart-axis',
    label: '--chart-label',
    crosshair: '--chart-crosshair',
    threshold: '--chart-threshold',

    textPrimary: '--text-primary',
    textSecondary: '--text-secondary',
    textTertiary: '--text-tertiary',
    textInverse: '--text-inverse',
    bgSurface: '--bg-surface',
    bgSubtle: '--bg-subtle',
    bgSunken: '--bg-sunken',
    bgRaised: '--bg-raised',
    borderDefault: '--border-default',
    borderStrong: '--border-strong',
    accentDefault: '--accent-default',
    accentSoft: '--accent-soft',
    accentBorder: '--accent-border',

    riskNormal: '--risk-normal-main',
    riskWarn: '--risk-warn-main',
    riskAlarm: '--risk-alarm-main',
    riskCrit: '--risk-crit-main',
    riskAlarmText: '--risk-alarm-text',

    fs2xs: '--fs-2xs',
    fsXs: '--fs-xs',
    fsSm: '--fs-sm',
    fontData: '--font-data',
    fontUi: '--font-ui',
  };

  /* 读取失败时的兜底：与 tokens.css 浅色取值完全一致（规范 7.2 第 2 条同样的约定） */
  var FALLBACK = {
    seriesPrimary: '#2b3038', seriesSecondary: '#8f959e', seriesTertiary: '#c8ccd2',
    area: 'rgba(43,48,56,0.06)', grid: '#eef0f2', axis: '#c8ccd2', label: '#6b717a',
    crosshair: '#8f959e', threshold: '#c25a16',
    textPrimary: '#16181d', textSecondary: '#4b515a', textTertiary: '#6b717a', textInverse: '#ffffff',
    bgSurface: '#ffffff', bgSubtle: '#f9fafb', bgSunken: '#edeff2', bgRaised: '#ffffff',
    borderDefault: '#dcdfe3', borderStrong: '#c8ccd2',
    accentDefault: '#3a68ad', accentSoft: '#ebf1fa', accentBorder: '#a9c0e3',
    riskNormal: '#2f855a', riskWarn: '#b7791f', riskAlarm: '#c25a16', riskCrit: '#c8353b',
    riskAlarmText: '#a6450d',
    fs2xs: '11px', fsXs: '12px', fsSm: '13px',
    fontData: 'Inter, "PingFang SC", "Microsoft YaHei", sans-serif',
    fontUi: 'Inter, "PingFang SC", "Microsoft YaHei", sans-serif',
  };

  function px(v, fallback) {
    var n = parseFloat(v);
    return isFinite(n) ? n : fallback;
  }

  function tokens() {
    var cs = getComputedStyle(document.documentElement);
    var out = {};
    Object.keys(NAMES).forEach(function (key) {
      var raw = cs.getPropertyValue(NAMES[key]).trim();
      out[key] = raw || FALLBACK[key];
    });
    /* 字号要转成数值：ECharts 只接受 number */
    out.fs2xsPx = px(out.fs2xs, 11);
    out.fsXsPx = px(out.fsXs, 12);
    out.fsSmPx = px(out.fsSm, 13);
    /* 去掉字体栈里的引号，避免 canvas 解析异常 */
    out.fontDataName = String(out.fontData).split(',')[0].replace(/["']/g, '').trim() || 'sans-serif';
    return out;
  }

  /* 主题切换订阅：回调收到新 token 快照 */
  function onThemeChange(fn) {
    document.addEventListener('bg:themechange', function () {
      var t = tokens();
      /* 让回调在下一帧执行：确保新的 CSS 变量已经生效（同一帧内 getComputedStyle 已刷新，
         这里只是为了不与切换本身抢帧） */
      if (window.requestAnimationFrame) window.requestAnimationFrame(function () { fn(t); });
      else window.setTimeout(function () { fn(t); }, 0);
    });
  }

  /* 悬浮提示（tooltip）的统一外观：浅色主题深底反色，深色主题浮层底 + 描边（4.12.6） */
  function tooltipStyle(t) {
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      backgroundColor: dark ? t.bgRaised : t.textPrimary,
      borderColor: dark ? t.borderStrong : 'transparent',
      borderWidth: dark ? 1 : 0,
      padding: [4, 8],
      textStyle: { color: dark ? t.textPrimary : t.textInverse, fontSize: t.fsXsPx, fontFamily: t.fontDataName },
      extraCssText: 'border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,.18);',
    };
  }

  window.BGCharts = {
    tokens: tokens,
    onThemeChange: onThemeChange,
    tooltipStyle: tooltipStyle,
    /* 风险等级 → 图形色 / 文字色（与 data-risk 五态一一对应） */
    riskMain: function (t, key) {
      return { normal: t.riskNormal, warn: t.riskWarn, alarm: t.riskAlarm, crit: t.riskCrit }[key] || t.seriesPrimary;
    },
  };
})();
