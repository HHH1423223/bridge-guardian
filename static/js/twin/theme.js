/* ============================================================================
 * 主题系统（theme.js）—— 浅色 / 深色两套「工程可视化」主题
 * ----------------------------------------------------------------------------
 * 本文件是 P2「3D 浅色渲染」的唯一主题真相（契约 §3.1）：
 *   · 浅色/深色 descriptor（clear / 雾 / 光照 / 环境贴图渐变 / 地形·水面·雾气 /
 *     环境反射强度 / 线框参数）
 *   · 程序化环境贴图（canvas 画 equirect 渐变 → PMREM，不依赖任何外部 HDR 文件）
 *   · 场景级主题应用（clearColor / FogExp2 / 光照组 / 环境贴图，并 dispose 旧资源）
 *   · 材质主题（材质配方 + 风险五色派生，供 materials.js 与场景克隆材质共用）
 *   · 线框（结构透视）主题参数
 *
 * 依赖方向：theme.js **不 import 任何本项目模块**（避免循环依赖）；
 *          materials.js / canyon.js → theme.js 是单向依赖。
 *          THREE 一律由调用方传入（契约 §3.1 的签名就是这么定的）。
 *
 * ----------------------------------------------------------------------------
 * 【浅色主题下，桥体靠什么保持可辨？】
 * 白/浅灰底上没有「深色峡谷剪影」可借，可辨性必须由**明度关系**造出来，
 * 而不是靠背景。本主题的四层明度阶梯（数值为 sRGB 反照率，白底 WCAG 对比度实算）：
 *   ① 深灰钢构 = 对比主体：桁架杆件 #5b646c（对 #f2f5f7 约 5.4:1）、
 *      索夹 #5a6067、沥青桥面 #44474a —— 全场最暗的一层，桥的「骨架」由此读出。
 *   ② 中性灰混凝土：桥塔/锚碇/承台 #878d91（对白底 3.07:1）—— 大块体量，
 *      靠「受光面浅、背光面灰」的自身明暗差读出体积，不靠背景反差。
 *   ③ 金属高光/边缘描边：主缆与吊索 #7e878e（金属度 0.42、粗糙度 0.30）——
 *      细长构件不追求大面积对比，靠环境贴图里那团太阳的**镜面高光**勾出线形，
 *      再叠加玻璃/混凝土/桁架的 accent 描边（风险色，opacity 0.55~0.9）。
 *   ④ 风险色测点：测点球/光环/吊索着色用风险五色（浅色专版，白底 4.5~6.3:1），
 *      是全场饱和度最高、最容易被眼睛抓到的元素 —— 数据信息永远压过美术。
 * 另外：环境贴图从「近黑石墨 + 香槟金地平线」换成「淡蓝灰天顶 + 亮地平线 +
 * 中灰地面」，金属/玻璃才有可信的浅色反射；雾色改成浅灰白 #dfe6ea，远景
 * 收到雾色而不是收到黑，625m 纵深仍然读得出来（雾因子 = 1-exp(-(d·ρ)²)）。
 * ==========================================================================*/

/* ---------------------------------------------------------------- 主题名 */
export const THEME_NAMES = ['light', 'dark'];
export const DEFAULT_THEME = 'light';

/**
 * 风险等级 → 主题色（浅色专版）。
 * 规范 7.2 / 2.1.4：这四个值必须与 CSS 变量 --risk-*-main 完全一致，
 * 运行时由 syncFromCss() 从根元素计算样式覆盖；这里的字面量只是读不到 CSS 时的兜底。
 */
export const RISK_COLORS_LIGHT = {
  normal: '#2f855a',
  warn: '#b7791f',
  alarm: '#c25a16',
  crit: '#c8353b',
  offline: '#8a9099',
};

/**
 * 深色专版（规范 7.2）。**不再是香槟金**：深色主题的正常色原为 #e0b97b，
 * 与浅色主题强调色冲突是同一个问题在 3D 里的翻版（0.3 第 1 条）。
 */
export const RISK_COLORS_DARK = {
  normal: '#4cb782',
  warn: '#e0a82e',
  alarm: '#e87a3a',
  crit: '#ef5a5f',
  offline: '#6b7079',
};

/** #rrggbb → 0xrrggbb（读 CSS 变量用） */
function hexToInt(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(hex || '').trim());
  return m ? parseInt(m[1], 16) : null;
}

/**
 * 规范 7.2：CSS token 是唯一真相。
 * 在挂载时以及每次主题切换后，从根元素计算样式读取本表列出的变量，
 * 覆盖 theme.js 里的兜底字面量（对象是原地修改的，所以调用方不需要改签名）。
 * 读不到（例如在没有 DOM 的自测环境里）就保持字面量不动。
 */
export function syncFromCss(doc) {
  const d = doc || (typeof document !== 'undefined' ? document : null);
  if (!d || !d.documentElement || !d.defaultView) return false;
  let cs;
  try { cs = d.defaultView.getComputedStyle(d.documentElement); } catch (e) { return false; }
  if (!cs) return false;
  const themed = d.documentElement.getAttribute('data-theme') === 'dark';
  const read = (name) => {
    try { return String(cs.getPropertyValue(name) || '').trim(); } catch (e) { return ''; }
  };
  const riskTarget = themed ? RISK_COLORS_DARK : RISK_COLORS_LIGHT;
  const map = {
    normal: '--risk-normal-main',
    warn: '--risk-warn-main',
    alarm: '--risk-alarm-main',
    crit: '--risk-crit-main',
    offline: '--trust-unknown-main',
  };
  Object.keys(map).forEach((key) => {
    const v = read(map[key]);
    if (/^#[0-9a-f]{6}$/i.test(v)) riskTarget[key] = v.toLowerCase();
  });
  const t = themed ? THEME_DARK : THEME_LIGHT;
  const clearHex = read('--twin-clear');
  const clearInt = hexToInt(clearHex);
  if (clearInt !== null) {
    /* 雾色必须等于清屏色（7.2）：否则画布远端会出现一条可见的地平线色带 */
    t.clear = clearInt;
    t.fog.color = clearInt;
  }
  const wireHex = read('--text-secondary');
  if (/^#[0-9a-f]{6}$/i.test(wireHex)) t.wire.color = wireHex.toLowerCase();
  const mutedHex = read('--text-tertiary');
  if (/^#[0-9a-f]{6}$/i.test(mutedHex)) t._muted = mutedHex.toLowerCase();
  return true;
}

/* ------------------------------------------------- WCAG 对比度（校验用） */
/**
 * 相对亮度（WCAG 2.x：sRGB → 线性 → 0.2126R+0.7152G+0.0722B）。
 * 产品渲染不依赖它；它存在的意义是「代码里能复算报告里的对比度数字」，
 * 自测脚本 import 本函数即可证明报告不是手写编的。
 */
export function relativeLuminance(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(hex || ''));
  if (!m) return 0;
  const n = parseInt(m[1], 16);
  const ch = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => {
    const s = v / 255;
    return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
}

/** WCAG 对比度比值 (L1+0.05)/(L2+0.05)，1~21。 */
export function contrastRatio(hexA, hexB) {
  const a = relativeLuminance(hexA);
  const b = relativeLuminance(hexB);
  const hi = Math.max(a, b), lo = Math.min(a, b);
  return (hi + 0.05) / (lo + 0.05);
}

/* ---------------------------------------------------------------- 描述符 */
/**
 * 浅色主题（默认）。取值理由集中在字段注释里，改任何一个都要给出对比度依据。
 */
const THEME_LIGHT = {
  name: 'light',
  /* 渲染器 clearColor。规范 7.2：必须等于 CSS 变量 --twin-clear（= --bg-canvas），
     否则画布与页面底色之间会出现可见的色差接缝。运行时由 syncFromCss() 覆盖。 */
  clear: 0xf4f5f7,
  /* ACES 色调映射曝光。浅色场景不靠加大曝光提亮（会把高光顶到纯白），
     靠环境贴图与反照率本身；所以保持 1.0。 */
  exposure: 1.0,
  /* 雾色 == 清屏色（7.2）：远景自然溶解进页面背景，3D 场景与页面没有边界。 */
  fog: { color: 0xf4f5f7, density: 0.00016, mistOffDensityScale: 1.75 },
  lights: {
    /* 半球光：天空淡蓝白 / 地面中灰。ground 不能太暗，否则背光面会掉成剪影 */
    hemi: { sky: 0xe8f0f6, ground: 0x9aa2a8, intensity: 0.70 },
    /* 主光：暖白、斜上方，负责「受光面浅」 */
    key: { color: 0xfffaf2, intensity: 1.32, pos: [-900, 1500, -1200] },
    /* 补光：冷白、反向低角度，只做填充，不给暖色调（暖色天光是深色主题的签名） */
    rim: { color: 0xeef4f8, intensity: 0.32, pos: [1200, 400, 900] },
    amb: { color: 0xffffff, intensity: 0.16 },
  },
  env: {
    /* equirect 渐变（offset 自上而下 = 天顶→谷底）。太阳位于 (76,64)：
       与主光方向一致（azimuth≈0.15, elevation≈31°），金属高光才「有来处」。 */
    stops: [
      [0.00, '#b9c8d6'],   // 天顶：淡蓝灰
      [0.30, '#d7e0e7'],
      [0.46, '#eef3f6'],   // 地平线：亮带（金属/水面的高光来源）
      [0.53, '#dfe6ea'],
      [0.66, '#a8b0b5'],   // 远山灰
      [1.00, '#8b9298'],   // 谷底中灰：朝下法线也能拿到 ~0.26 环境光，不成死黑
    ],
    sun: {
      x: 76, y: 64, r: 130,
      stops: [
        [0.00, 'rgba(255,255,255,0.72)'],
        [0.34, 'rgba(236,244,250,0.22)'],
        [1.00, 'rgba(255,255,255,0)'],
      ],
    },
  },
  terrain: {
    /* 反照率阶梯：谷底湿岩 → 谷壁 → 台地 → 山脊受光面 → 岩层暖夹层。
       浅色主题下 cTop 必须**亮**（山脊被光照到接近雾色，远景自然消隐），
       cLow 只比 cMid 暗一档（湿岩），不能像深色主题那样一压到底。 */
    cLow: '#767c81', cMid: '#98a0a5', cHigh: '#b6bbbe', cTop: '#d3d7d9', cWarm: '#bfa184',
    nearWaterDarken: 0.18,      // 近水压暗（深色主题 0.35 → 浅色减半，避免谷底发黑）
    metalness: 0.05, roughness: 0.95, flatShading: true,
    envIntensity: 0.95,         // 岩石几乎全接受天光 → 背光面落在「中性灰」而不是黑
  },
  water: {
    /* 浅色反光：不再用深黑金属水面，改成中灰蓝 + 低粗糙度，主要映天空亮带 */
    color: 0x84929b, metalness: 0.30, roughness: 0.15,
    emissive: 0x2b3a42, opacity: 0.94, envIntensity: 1.05,
  },
  mist: {
    /* 白色半透明（NormalBlending）。emissive 让面片「自亮」，不受光照方向影响，
       否则水平面片被主光照到才亮、背光面会发灰，在白底上看起来像脏雾。 */
    color: 0xffffff, opacityScale: 1.6, blending: 'normal',
    emissive: 0xffffff, emissiveIntensity: 0.5,
  },
  /* 环境反射强度（契约字段）：金属结构要够（有高光），玻璃/混凝土压住（防过曝） */
  envIntensity: {
    steel: 0.95, cable: 1.0, deckPlate: 0.95, clamp: 0.9, concrete: 0.8,
    /* 玻璃 1.2 → 0.55：浅色环境贴图平均亮度 ~0.7 线性（深色版只有 ~0.1），
       反射项按比例线性放大，不压就会变成一块白玻璃。 */
    glass: 0.55,
  },
  /* 线框主题（结构透视）：白底上加法混合等于消失，必须 NormalBlending + 不透明深色描边 */
  wire: {
    color: '#334155',      // 石板灰，白底 9.5:1
    opacity: 1.0,
    transparent: false,    // 不透明：半透明描边会被浅背景拉浅，只剩 ~2:1
    blending: 'normal',
    depthWrite: false,
    depthTest: true,
    renderOrder: 2,
  },
  /* 主题色派生系数：浅底上「更亮」等于更看不见，所以 bright 与 accent 同值，
     dim 只用于需要弱化的边线。 */
  tint: { lighten: 1.0, darken: 0.70 },
};

/**
 * 深色主题：规范 7.3 / 7.4 的「中性冷灰」配方。
 * 原先是 P1 的「黑曜石 + 香槟金」——香槟金轮廓光、金色地平线亮带、暖米色玻璃，
 * 会让整座桥呈现黑金质感，属于 6.3 第 10 条禁止的装饰性配色。现在全部改为中性灰，
 * 只保留「帮助轮廓从深色背景里分离」这一功能。
 */
const THEME_DARK = {
  name: 'dark',
  /* 规范 7.2：等于 --bg-canvas 深色取值 #0B0C0E */
  clear: 0x0b0c0e,
  exposure: 1.0,
  fog: { color: 0x0b0c0e, density: 0.00019, mistOffDensityScale: 1.75 },
  lights: {
    hemi: { sky: 0xb4bac2, ground: 0x101113, intensity: 0.55 },
    key: { color: 0xf2f4f7, intensity: 1.12, pos: [-900, 1500, -1200] },
    /* 轮廓光：原香槟金 #e0b97b / 0.75 → 中性冷灰 / 0.45（只做轮廓分离，不做氛围） */
    rim: { color: 0xc8ced6, intensity: 0.45, pos: [1200, 400, 900] },
    amb: { color: 0x1c1e22, intensity: 0.30 },
  },
  env: {
    /* 规范 7.3.3：地平线的金色亮带 #7a5f3c → 中性灰 #4E545C。
       这是 6.3 第 2 条「禁止渐变」的唯一例外：环境贴图渐变是渲染物理需要，
       用户看不到渐变本身，只看到它在金属材质上的反射。 */
    stops: [
      [0.00, '#08090b'],
      [0.38, '#14161a'],
      [0.50, '#4e545c'],
      [0.57, '#121418'],
      [1.00, '#060708'],
    ],
    sun: {
      x: 150, y: 84, r: 120,
      stops: [
        [0.00, 'rgba(242,244,247,0.55)'],
        [0.34, 'rgba(180,186,194,0.14)'],
        [1.00, 'rgba(0,0,0,0)'],
      ],
    },
  },
  terrain: {
    /* 规范 7.4.3：地形渐变去暖调。cWarm 保留极轻微暖调（模拟向阳岩壁），
       饱和度降到「人眼仅能察觉它不是纯灰」的程度。 */
    cLow: '#1e2023', cMid: '#2a2d31', cHigh: '#373a3f', cTop: '#44484e', cWarm: '#4c4b48',
    nearWaterDarken: 0.35,
    metalness: 0.16, roughness: 0.97, flatShading: true, envIntensity: 1.0,
  },
  water: {
    color: 0x0f1114, metalness: 0.50, roughness: 0.28,
    emissive: 0x16181b, opacity: 0.92, envIntensity: 1.0,
  },
  mist: {
    /* 规范 7.3.4：暖米色 + 叠加混合 → 中性灰 + 普通混合。
       叠加混合会让雾层在深色背景上发光，属于 6.3 第 4 条禁止的发光效果。 */
    color: 0x9aa1a9, opacityScale: 1.0, blending: 'normal',
    emissive: 0x000000, emissiveIntensity: 1.0,
  },
  envIntensity: {
    steel: 0.9, cable: 1.0, deckPlate: 0.9, clamp: 0.8, concrete: 0.15, glass: 0.8,
  },
  wire: {
    /* 规范 7.4.4：线框不随风险变色，用 --text-secondary（深色主题 #B4B8BF） */
    color: '#b4b8bf', opacity: 0.9, transparent: false,
    blending: 'normal', depthWrite: false, depthTest: true, renderOrder: 2,
  },
  tint: { lighten: 1.45, darken: 0.55 },
};

const THEMES = { light: THEME_LIGHT, dark: THEME_DARK };

/* ------------------------------------------------------------ 材质配方表 */
/**
 * 每套主题一份材质配方。键名 = material.userData.recipe（见 materials.js）；
 * 只有出现在表里的字段才会被写进材质。约定：
 *   · 带 tintRole 的材质**不在这里给 color/emissive** —— 它们由风险五色派生
 *     （applyTintToMaterial），这里只管透明度/混合模式等结构性参数。
 *   · envMapIntensity 不在这张表里的键（steel/cable/deckPlate/clamp/concrete/glass）
 *     统一走 descriptor.envIntensity，避免两处口径打架。
 *   · emissiveScale 是「发光强度 = 风险色 × 系数」里的系数；浅色主题整体调小
 *     （发光是深色主题的语言，白底上只会把结构冲淡）。
 */
export const MATERIAL_THEMES = {
  light: {
    steel: { color: '#5b646c', metalness: 0.18, roughness: 0.48, emissiveScale: 0.05 },
    edge: { color: '#4d555c', opacity: 0.90 },
    deckPlate: { color: '#727980', metalness: 0.22, roughness: 0.55, emissiveScale: 0.05 },
    road: { color: '#44474a', metalness: 0.05, roughness: 0.95 },
    laneMark: { color: '#f7f7f4', opacity: 0.90 },
    /* 7.4.4：车道/栏杆「发光条」改为非发光的中性材质（浅色 #C8CCD2）。
       tintRole 为 none 的情况下这里给的就是最终色；带 tintRole 的材质由风险色派生，
       是否让它随风险变色由 scene.js 的构件清单决定。 */
    laneGlow: { color: '#c8ccd2', opacity: 0.45 },
    railGlow: { color: '#c8ccd2', opacity: 0.90 },
    cable: { color: '#7e878e', metalness: 0.42, roughness: 0.30, emissiveScale: 0.05 },
    /* 主缆流光：规范 7.4.4 要求删除（流动光带是典型赛博装饰，且不对应任何物理量） */
    cableFlow: { opacity: 0.0, blending: 'normal', depthWrite: false, visible: false },
    clamp: { color: '#5a6067', metalness: 0.70, roughness: 0.35, emissiveScale: 0.05 },
    concrete: { color: '#878d91', metalness: 0.02, roughness: 0.90 },
    concreteEdge: { color: '#737a7d', opacity: 0.60 },
    /* 玻璃（7.4.2）：#cdd8de → #D5DAE0、不透明度 0.34 → 0.30（去掉残留的蓝偏） */
    glass: { color: '#d5dae0', metalness: 0.0, roughness: 0.14, opacity: 0.30, emissiveScale: 0.05, envMapIntensity: 0.55 },
    glassEdge: { color: '#b5babe', opacity: 0.65 },
    sensor: { opacity: 0.98 },
    /* 测点光晕：两套主题都用普通混合，不透明度 0.20（7.5.1） */
    sensorHalo: { opacity: 0.20, blending: 'normal', depthWrite: false },
    rock: { color: '#8a8f92', metalness: 0.04, roughness: 0.98, flatShading: true },
    rockEdge: { color: '#757a7c', opacity: 0.12 },
    water: { color: '#84929b', metalness: 0.30, roughness: 0.15, emissive: '#2b3a42', opacity: 0.94, envMapIntensity: 1.05 },
    mist: { color: '#ffffff', opacity: 0.06, blending: 'normal', emissive: '#ffffff', emissiveIntensity: 0.5 },
    /* 塔顶信号灯：中性，不发光不闪烁（红色会与严重报警混淆，7.4.4） */
    beacon: { color: '#6b717a', opacity: 1.0 },
  },
  dark: {
    /* 规范 7.4.3：结构材质全部去暖调，改为中性冷灰；
       桥塔明度明显降一级，避免它成为全场最亮的物体（测点才应该是）。 */
    steel: { color: '#a9aeb4', metalness: 0.25, roughness: 0.42, emissiveScale: 0.10 },
    edge: { color: '#909599', opacity: 0.90 },
    deckPlate: { color: '#6a6f75', metalness: 0.30, roughness: 0.50, emissiveScale: 0.10 },
    road: { color: '#16181b', metalness: 0.25, roughness: 0.90 },
    laneMark: { color: '#f0efee', opacity: 0.85 },
    laneGlow: { color: '#4e525a', opacity: 0.35 },
    railGlow: { color: '#4e525a', opacity: 0.90 },
    cable: { color: '#c4c9cf', metalness: 0.35, roughness: 0.30, emissiveScale: 0.10 },
    cableFlow: { opacity: 0.0, blending: 'normal', depthWrite: false, visible: false },
    clamp: { color: '#3a3d42', metalness: 0.90, roughness: 0.30, emissiveScale: 0.10 },
    concrete: { color: '#9da2a8', metalness: 0.02, roughness: 0.95 },
    concreteEdge: { color: '#868b90', opacity: 0.60 },
    glass: { color: '#b8c0c8', metalness: 0.0, roughness: 0.08, opacity: 0.28, emissiveScale: 0.10, envMapIntensity: 0.8 },
    glassEdge: { color: '#9ca4ab', opacity: 0.55 },
    sensor: { opacity: 0.95 },
    sensorHalo: { opacity: 0.20, blending: 'normal', depthWrite: false },
    rock: { color: '#2c2f33', metalness: 0.12, roughness: 1.00, flatShading: true },
    rockEdge: { color: '#25282b', opacity: 0.10 },
    water: { color: '#0f1114', metalness: 0.90, roughness: 0.12, emissive: '#16181b', opacity: 0.95, envMapIntensity: 1.0 },
    mist: { color: '#9aa1a9', opacity: 0.05, blending: 'normal', emissive: '#000000', emissiveIntensity: 1.0 },
    beacon: { color: '#80858d', opacity: 1.0 },
  },
};

/* -------------------------------------------------------- 主题查询与归一 */
/** 非法主题名 → DEFAULT_THEME（localStorage 脏值不能把场景搞崩，契约 §1.3）。 */
export function normalizeThemeName(name) {
  return THEME_NAMES.indexOf(name) >= 0 ? name : DEFAULT_THEME;
}

/** 主题名 → descriptor（冻结字段名，只读使用）。非法值回落浅色。 */
export function getTheme(name) {
  return THEMES[normalizeThemeName(name)];
}

/** 主题名 → 风险五色（返回副本，调用方改它不会污染主题表）。 */
export function riskColors(name) {
  const src = normalizeThemeName(name) === 'dark' ? RISK_COLORS_DARK : RISK_COLORS_LIGHT;
  return { normal: src.normal, warn: src.warn, alarm: src.alarm, crit: src.crit, offline: src.offline };
}

/** 允许传主题名或 descriptor 本身（canyon.js 内部用，省得到处写 getTheme）。 */
export function resolveTheme(nameOrDescriptor) {
  if (nameOrDescriptor && typeof nameOrDescriptor === 'object' && nameOrDescriptor.name) {
    return THEMES[normalizeThemeName(nameOrDescriptor.name)];
  }
  return getTheme(nameOrDescriptor);
}

/* --------------------------------------------------- 主题色（风险五色派生） */
/**
 * 「当前风险等级」由 materials.js 在 setPalette() 时登记。
 * 用途：切换主题时同步场景里**克隆出来**的材质（bridge.js 的测点环
 * `mats.sensorHalo.clone()`）—— 它们不会跟着源材质自动变色，而 theme.js 的
 * 场景同步需要一个「当前是哪个风险色」的口径。默认 normal。
 */
let _activeRisk = 'normal';
export function setActiveRisk(key) {
  const known = !!(RISK_COLORS_LIGHT[key] || RISK_COLORS_DARK[key]);
  _activeRisk = known ? key : 'normal';
  return _activeRisk;
}
export function getActiveRisk() {
  return _activeRisk;
}

/**
 * 风险等级 + 主题 → 三个派生色（accent / bright / dim）。
 * 与 P1 的语义完全一致（bright = accent×1.45、dim = accent×0.55），
 * 只是系数与色值都改成按主题给（浅色主题 bright 不再提亮，见 descriptor.tint）。
 */
export function derivePalette(THREE, name, riskKey) {
  const t = getTheme(name);
  const rc = riskColors(t.name);
  const hex = rc[riskKey] || rc.normal;
  const f = t.tint || { lighten: 1.45, darken: 0.55 };
  return {
    accent: new THREE.Color(hex),
    bright: new THREE.Color(hex).multiplyScalar(f.lighten),
    dim: new THREE.Color(hex).multiplyScalar(f.darken),
    hex,
  };
}

/**
 * 按 tintRole 把主题色写进材质（**原地修改**，不换对象引用）。
 *   · role 'color'    → material.color = accent（userData.bright 时用 bright）
 *   · role 'emissive' → material.emissive = accent × userData.emissiveScale（缺省 0.10）
 * 这条逻辑与 P1 materials.js 的 applyPalette 等价（这里抽出成公共函数，
 * 是为了让「场景里克隆出来的材质」能用同一套口径同步，避免两份实现漂移）。
 */
export function applyTintToMaterial(material, palette) {
  if (!material || !material.userData || !palette) return false;
  const role = material.userData.tintRole;
  if (!role) return false;
  if (role === 'color' && material.color) {
    material.color.copy(material.userData.bright ? palette.bright : palette.accent);
  } else if (role === 'emissive' && material.emissive) {
    material.emissive.copy(palette.accent).multiplyScalar(material.userData.emissiveScale || 0.10);
  }
  return true;
}

/**
 * 按 userData.recipe 把主题配方写进材质（原地）。只写配方里出现过的字段，
 * 所以 tintRole 材质的颜色不会被这里覆盖。
 * blending/transparent/flatShading 会进 three 的 program cache key，变了要 needsUpdate。
 */
export function applyRecipeToMaterial(material, name, THREE) {
  if (!material || !material.userData) return false;
  const t = getTheme(name);
  const key = material.userData.recipe;
  const r = key ? MATERIAL_THEMES[t.name][key] : null;
  if (!r) return false;
  let recompile = false;
  if (r.color !== undefined && material.color) material.color.set(r.color);
  if (r.metalness !== undefined && 'metalness' in material) material.metalness = r.metalness;
  if (r.roughness !== undefined && 'roughness' in material) material.roughness = r.roughness;
  if (r.opacity !== undefined) material.opacity = r.opacity;
  if (r.transparent !== undefined && material.transparent !== r.transparent) {
    material.transparent = r.transparent; recompile = true;
  }
  if (r.flatShading !== undefined && 'flatShading' in material && material.flatShading !== r.flatShading) {
    material.flatShading = r.flatShading; recompile = true;
  }
  if (r.emissive !== undefined && material.emissive) material.emissive.set(r.emissive);
  if (r.emissiveIntensity !== undefined) material.emissiveIntensity = r.emissiveIntensity;
  if (r.emissiveScale !== undefined) material.userData.emissiveScale = r.emissiveScale;
  if (r.depthWrite !== undefined) material.depthWrite = r.depthWrite;
  if (r.depthTest !== undefined) material.depthTest = r.depthTest;
  if (r.side !== undefined) material.side = r.side;
  /* visible：规范 7.4.4 要求直接删除主缆流光（流动光带是装饰），
     保留几何但整块不参与渲染，几何与调用方都不需要改。 */
  if (r.visible !== undefined) material.visible = r.visible;
  if (r.blending !== undefined && THREE) {
    const b = r.blending === 'additive' ? THREE.AdditiveBlending : THREE.NormalBlending;
    if (material.blending !== b) { material.blending = b; recompile = true; }
  }
  // 环境反射强度：材质自身优先，其次 descriptor.envIntensity[recipe]，否则不动
  let envI = r.envMapIntensity;
  if (envI === undefined && t.envIntensity && t.envIntensity[key] !== undefined) envI = t.envIntensity[key];
  if (envI !== undefined && 'envMapIntensity' in material) material.envMapIntensity = envI;
  if (recompile) material.needsUpdate = true;
  return true;
}

/* ------------------------------------------------------------ 环境贴图 */
/**
 * 程序化环境贴图：canvas 画一张（512×256）equirect 渐变 → PMREM 预滤波。
 * 完全离线，不依赖任何 HDR 文件（P1 的成功经验，浅色版只是换了渐变色值）。
 * @returns {{texture:object, renderTarget:object, source:[number,number], dispose:Function}}
 */
export function buildEnvironment(THREE, renderer, name) {
  const t = getTheme(name);
  const W = 512, H = 256;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const g = canvas.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, H);
  for (let i = 0; i < t.env.stops.length; i++) grad.addColorStop(t.env.stops[i][0], t.env.stops[i][1]);
  g.fillStyle = grad;
  g.fillRect(0, 0, W, H);
  // 一团柔和「日光」：给金属面/水面提供高光来源（位置与主光方向一致）
  const s = t.env.sun;
  const sun = g.createRadialGradient(s.x, s.y, Math.max(2, s.r * 0.04), s.x, s.y, s.r);
  for (let i = 0; i < s.stops.length; i++) sun.addColorStop(s.stops[i][0], s.stops[i][1]);
  g.fillStyle = sun;
  g.fillRect(0, 0, W, H);

  const tex = new THREE.Texture(canvas);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  if ('colorSpace' in tex) tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;

  const pmrem = new THREE.PMREMGenerator(renderer);
  let rt = null;
  try {
    rt = pmrem.fromEquirectangular(tex);
  } finally {
    pmrem.dispose();     // PMREM 只借用 renderer 的临时资源，用完即放
    tex.dispose();       // 源 canvas 贴图不能留：RT 已经烘好，留着白占一份 GPU 显存
  }
  return {
    texture: rt.texture,
    renderTarget: rt,
    source: [W, H],
    /** 释放旧环境贴图 RT（切主题时必须调用，否则每切一次泄漏一张 cubeUV 贴图） */
    dispose() { rt.dispose(); },
  };
}

/**
 * 释放 scene.userData.twinEnv 记录的环境贴图 RT，并把 scene.environment 清掉。
 * 供 scene.js 的 api.dispose() 调用。
 */
export function disposeEnvironment(scene) {
  if (!scene || !scene.userData) return false;
  const rec = scene.userData.twinEnv;
  if (!rec) return false;
  if (scene.environment === rec.texture) scene.environment = null;
  if (typeof rec.dispose === 'function') rec.dispose();
  scene.userData.twinEnv = null;
  return true;
}

/* ------------------------------------------------------------ 场景级主题 */
const LIGHTS_NAME = 'theme-lights';

function buildLights(THREE, t) {
  const g = new THREE.Group();
  g.name = LIGHTS_NAME;
  const L = t.lights;
  const hemi = new THREE.HemisphereLight(L.hemi.sky, L.hemi.ground, L.hemi.intensity);
  hemi.name = 'theme-hemi';
  const key = new THREE.DirectionalLight(L.key.color, L.key.intensity);
  key.name = 'theme-key';
  key.position.set(L.key.pos[0], L.key.pos[1], L.key.pos[2]);
  const rim = new THREE.DirectionalLight(L.rim.color, L.rim.intensity);
  rim.name = 'theme-rim';
  rim.position.set(L.rim.pos[0], L.rim.pos[1], L.rim.pos[2]);
  const amb = new THREE.AmbientLight(L.amb.color, L.amb.intensity);
  amb.name = 'theme-amb';
  g.add(hemi, key, rim, amb);
  g.userData.themeName = t.name;
  return g;
}

/** 释放旧光照组：DirectionalLight.dispose() 会释放 shadow RT（本项目未开阴影，仍照做） */
function disposeLights(group) {
  let n = 0;
  group.traverse((o) => {
    if (o.isLight && typeof o.dispose === 'function') { o.dispose(); n++; }
    if (o.isDirectionalLight && o.target && o.target.parent) o.target.parent.remove(o.target);
  });
  if (typeof group.clear === 'function') group.clear();
  return n;
}

/**
 * 雾：FogExp2 深度雾。mist=false（低画质档关掉 4 层雾气面片）时把 density 乘上
 * descriptor.fog.mistOffDensityScale，用更浓的深度雾补回纵深 —— 见 canyon.js
 * createMist 的说明：面片雾是「水平悬空白纱 + 缓慢漂移」，深度雾是「随距离整体
 * 退向雾色」，两者不等价，补偿只能近似。
 */
export function applyFog(THREE, scene, name, opts) {
  const t = getTheme(name);
  if (!scene) return null;
  const mistOn = !(opts && opts.mist === false);
  const density = t.fog.density * (mistOn ? 1 : (t.fog.mistOffDensityScale || 1.75));
  if (!scene.fog || scene.fog.isFogExp2 !== true) {
    scene.fog = new THREE.FogExp2(t.fog.color, density);
  } else {
    scene.fog.color.set(t.fog.color);
    scene.fog.density = density;
  }
  if (!scene.userData) scene.userData = {};
  scene.userData.twinMistOn = mistOn;
  scene.userData.twinFogDensity = density;
  return scene.fog;
}

/** 把主题下发给所有挂了 userData.applyTheme 的对象（canyon/river/mist）。 */
function applyWorldTheme(scene, name) {
  let n = 0;
  const t = getTheme(name);
  scene.traverse((obj) => {
    const fn = obj.userData && obj.userData.applyTheme;
    if (typeof fn !== 'function') return;
    try { fn(t); n++; } catch (err) {
      if (typeof console !== 'undefined' && console.warn) {
        console.warn('[theme] ' + (obj.name || obj.type) + ' 应用主题失败：' + ((err && err.message) || err));
      }
    }
  });
  return n;
}

/**
 * 同步场景里所有带 recipe / tintRole 的材质（含 bridge.js 里 clone 出来的测点环）。
 * 原地修改，不换引用 —— scene.js 的 wireMat 之类外部引用不会失效。
 * 传了 matCtl 时会把克隆材质**认领**进受控调色板（幂等），这样它们从此也能跟着
 * 风险等级换色（修掉 P1 里克隆材质永远停在初始色的问题）；没传就只按当前主题刷一遍。
 */
function syncSceneMaterials(scene, name, THREE, matCtl) {
  const seen = [];
  let n = 0;
  let palette = null;
  scene.traverse((o) => {
    const m = o.material;
    if (!m) return;
    const list = Array.isArray(m) ? m : [m];
    for (let i = 0; i < list.length; i++) {
      const mat = list[i];
      if (!mat || !mat.userData || seen.indexOf(mat) >= 0) continue;
      seen.push(mat);
      if (matCtl && typeof matCtl.adopt === 'function' && mat.userData.tintRole) matCtl.adopt(mat);
      if (mat.userData.recipe && applyRecipeToMaterial(mat, name, THREE)) n++;
      if (mat.userData.tintRole) {
        if (!palette) palette = derivePalette(THREE, name, _activeRisk);
        if (applyTintToMaterial(mat, palette)) n++;
      }
    }
  });
  return n;
}

/** 没有 matCtl 时的兜底：至少把配方（颜色/粗糙度/混合/环境强度）刷对。 */
function applyRecipesInScene(scene, name, THREE) {
  let n = 0;
  scene.traverse((o) => {
    const m = o.material;
    if (!m) return;
    const list = Array.isArray(m) ? m : [m];
    for (let i = 0; i < list.length; i++) {
      if (list[i] && list[i].userData && list[i].userData.recipe
          && applyRecipeToMaterial(list[i], name, THREE)) n++;
    }
  });
  return n;
}

/**
 * 场景级主题：clearColor / 曝光 / 雾 / 光照组 / 环境贴图 / 世界材质 / 材质主题。
 *
 * 契约 §3.1 的签名是 `applySceneTheme({THREE, scene, renderer, name})`，
 * 这里额外接受两个**可选**参数（不传也完全可用）：
 *   · matCtl —— materials.js 的控制器。强烈建议传：只有它能同步 bridge.js 里
 *     `mats.sensorHalo.clone()` 出来的测点环材质，并让风险色在同一帧对齐。
 *   · mist   —— 当前画质档是否启用雾气面片（profile.mist）；false 时用更浓的
 *     深度雾补偿（参见 applyFog）。
 *
 * ⚠ 切主题的硬性要求（用户需求 11）：不重建任何几何、不闪黑屏、旧资源必须 dispose。
 *   实现上：几何一律不动（地形顶点色原地重算见 canyon.js applyCanyonTheme）；
 *   环境贴图**先建新的、成功后**才 dispose 旧的，失败就保留旧贴图继续渲染。
 *
 * @returns {object} 新的光照 Group（契约：调用方可用于调试/挂载）
 */
export function applySceneTheme(opts) {
  const o = opts || {};
  const THREE = o.THREE, scene = o.scene, renderer = o.renderer;
  /* 规范 7.2：CSS token 是唯一真相 —— 应用主题前先从根元素计算样式同步一次，
     让画布底色、雾色、风险五色、线框色与页面 CSS 完全一致。
     读不到 DOM（自测环境）时保持本文件的字面量兜底。 */
  if (o.syncCss !== false) syncFromCss(o.doc);
  const t = getTheme(o.name);
  if (!scene) return null;
  if (!scene.userData) scene.userData = {};

  const report = { name: t.name, lights: 4, env: false, fog: null, world: 0, materials: 0, disposedLights: 0 };

  // ① 底色与曝光：画布底色必须等于页面 CSS 变量 --twin-clear（规范 7.2）
  if (renderer) {
    renderer.setClearColor(t.clear, 1);
    if ('toneMappingExposure' in renderer) renderer.toneMappingExposure = t.exposure;
  }

  // ② 雾
  const fog = applyFog(THREE, scene, t.name, { mist: o.mist });
  report.fog = fog ? { color: '#' + fog.color.getHexString(), density: fog.density } : null;

  // ③ 环境贴图：新的建好之前不动旧的（失败保留旧贴图 = 不黑屏）
  if (renderer) {
    let next = null;
    try {
      next = buildEnvironment(THREE, renderer, t.name);
    } catch (err) {
      if (typeof console !== 'undefined' && console.warn) {
        console.warn('[theme] 环境贴图构建失败，保留旧贴图：' + ((err && err.message) || err));
      }
    }
    if (next) {
      const prev = scene.userData.twinEnv;
      scene.environment = next.texture;
      scene.userData.twinEnv = next;
      if (prev && prev !== next && typeof prev.dispose === 'function') prev.dispose();
      report.env = true;
    }
  }

  // ④ 光照组：换新并 dispose 旧的（不 dispose 会每次切主题泄漏一组光照 + shadow RT）
  const old = scene.getObjectByName(LIGHTS_NAME);
  if (old) {
    report.disposedLights = disposeLights(old);
    scene.remove(old);
  }
  const lights = buildLights(THREE, t);
  scene.add(lights);
  scene.userData.twinLights = lights;

  // ⑤ 世界（地形/水面/雾气）：原地刷顶点色与材质参数，不重建几何
  report.world = applyWorldTheme(scene, t.name);

  // ⑥ 材质主题
  if (o.matCtl && typeof o.matCtl.setTheme === 'function') {
    matCtlSetTheme(o.matCtl, t.name);
    report.materials = syncSceneMaterials(scene, t.name, o.matCtl.THREE || THREE, o.matCtl);
    report.viaMatCtl = true;
  } else {
    // 兜底：没有控制器时至少按配方刷一遍（风险色只有 matCtl 能给出，会保持旧值）
    report.materials = applyRecipesInScene(scene, t.name, THREE);
    report.viaMatCtl = false;
  }

  scene.userData.twinTheme = t.name;
  lights.userData.themeReport = report;
  return lights;
}

/** 内部转调（matCtl.setTheme 由 materials.js 提供；缺失时不抛错，只在控制台说明）。 */
function matCtlSetTheme(matCtl, name) {
  try {
    return matCtl.setTheme(name);
  } catch (err) {
    if (typeof console !== 'undefined' && console.warn) {
      console.warn('[theme] matCtl.setTheme 失败：' + ((err && err.message) || err));
    }
    return null;
  }
}

/**
 * 材质级主题（契约 §3.1）。
 * @param {object} matCtl materials.js 的控制器（必需）
 * @param {string} name   'light' | 'dark'
 * @param {object} [scene] 传了才会同步场景里克隆出来的材质（bridge.js 的测点环）；
 *                         契约签名是两参，第三个参数是可选的向后兼容扩展。
 * @returns {{name:string, materialsUpdated:number}}
 */
export function applyMaterialTheme(matCtl, name, scene) {
  const t = getTheme(name);
  let n = 0;
  if (matCtl && typeof matCtl.setTheme === 'function') {
    matCtlSetTheme(matCtl, t.name);
    n++;
  }
  if (scene) {
    const THREE = (matCtl && matCtl.THREE) || null;
    n += syncSceneMaterials(scene, t.name, THREE, matCtl);
  }
  return { name: t.name, materialsUpdated: n };
}

/* ------------------------------------------------------------ 线框主题 */
/**
 * 线框（结构透视）主题参数 —— 供 scene.js 的 wireMat 接线（本文件不含任何
 * scene.js 代码，只提供参数）。
 *
 * 【为什么浅色必须换掉 AdditiveBlending？】
 *   加法混合输出 out = src×α + dst。白底被照亮后 dst≈0.91（线性），
 *   任何一点加法都容易把通道推过 1.0 被钳到纯白 —— 1px 的杆件棱线与背景同色，
 *   等于「点了线框没反应」（P1 用户就是这么反馈的）。WebGL 的 linewidth 在多数
 *   驱动上被钳成 1px，无法靠加粗补偿。
 * 【浅色方案】NormalBlending + **不透明**深色描边：
 *   out = mix(dst, src, α)，α=1 时 out 恒等于 src，与背景亮度无关。
 *   #334155 在 #f2f5f7 上对比度 9.5:1（远超 3:1 的图形元素要求）；
 *   若调用方按风险等级覆盖为风险色，浅色五色在白底是 4.5~6.3:1，同样清晰。
 *   反例（用来解释为什么不能给半透明）：opacity 0.62 时 #334155 与白底混合后的
 *   有效对比度只剩 ~2.2:1，白底上就是一条若有若无的灰影。
 * 【depthWrite 策略】depthWrite=false：线框只做描边叠加，不写深度，避免后续
 *   半透明件（玻璃/雾气面片）被 1px 棱线切出细缝；depthTest=true：仍被实体
 *   杆件正确遮挡，不会「穿透」桥体画到前面来。renderOrder=2 保证画在其它
 *   半透明件之后。
 */
export function wireframeTheme(THREE, name) {
  const t = getTheme(name);
  const w = t.wire;
  return {
    color: new THREE.Color(w.color),
    opacity: w.opacity,
    transparent: w.transparent,
    blending: w.blending === 'additive' ? THREE.AdditiveBlending : THREE.NormalBlending,
    depthWrite: w.depthWrite,
    depthTest: w.depthTest,
    renderOrder: w.renderOrder,
  };
}

/** 当前主题下、给定风险等级的线框颜色（perf-core 的 wireMat 直接 set 这个 hex）。 */
export function wireColor(name, riskKey) {
  const rc = riskColors(name);
  return rc[riskKey] || rc.normal;
}
