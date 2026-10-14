# FACTCHECK —— 「桥体卫士」答辩 PPT v2 全量事实核验报告

| 项 | 值 |
|---|---|
| 被核验文件 | `桥体卫士答辩PPT_v2/桥体卫士答辩PPT_12分钟版.pptx` |
| **SHA256（本人自算，核验前后各算一次，一致）** | `69E3294A9F668C4084792D0C17F96D924055B86B5D859B2E96BB1D0C9E8B8352` |
| 字节数 / 页数 | 91,761 bytes / 15 页 |
| 冻结基准（Lead 下发） | `69E3294A9F668C4084792D0C17F96D924055B86B5D859B2E96BB1D0C9E8B8352` → **一致 ✅**（旧指纹 `669A2432…BC4CDF` 已在核验中途作废，本报告全部结论基于新指纹，已弃用旧数据重跑） |
| 核验时间 | 2026-10-09 19:40 – 19:58（本机） |
| 文件 mtime / 核验期间是否被改动 | 2026-10-09 19:39:58；核验开始与结束两次 SHA256 相同 → **核验期间未被改动** |
| 派生规格 | `_spec/SPEC_content.json`、`_spec/SPEC_diagrams.json`、`_spec/BUILD_SPEC.md`（§7 事实口径） |
| 构建器 | `桥体卫士答辩PPT_v2/build_deck.py` |
| 全文提取物（本人重新生成，未采信现成文件） | `桥体卫士答辩PPT_v2/_work/pptx_text_final.txt`（1,356 行；形状文本 + 表格单元格 + notes + **独立 raw-XML `<a:t>` 全量扫描**双通道交叉） |
| 临时脚本 | `_work/fc_extract.py`、`_work/fc_consistency.py` |
| 证据附件 | `_work/pytest_out.txt`、`_work/flake_repro.txt`、`_work/flake_detail.txt`、`_work/fc_consistency_final.txt` |

### 实跑命令（全部为本机真实执行，原始输出见上列附件）

```powershell
# ① 指纹
Get-FileHash -Algorithm SHA256 "桥体卫士答辩PPT_v2\桥体卫士答辩PPT_12分钟版.pptx"

# ② 全文提取（bundled python 3.14 + python-pptx 1.0.2）
& $py -X utf8 "桥体卫士答辩PPT_v2\_work\fc_extract.py" `
     "桥体卫士答辩PPT_v2\桥体卫士答辩PPT_12分钟版.pptx" `
     "桥体卫士答辩PPT_v2\_work\pptx_text_final.txt"

# ③ 测试实跑（系统 Python 3.14.7 + pytest 9.1.1）—— 共 9 次全量 + 8 次分文件 + 12 次单用例重试
& "C:\Users\CX\AppData\Local\Programs\Python\Python314\python.exe" -m pytest tests/ -q
& "C:\Users\CX\AppData\Local\Programs\Python\Python314\python.exe" -m pytest tests/ --collect-only -q

# ④ 规格逐字一致性 + 红线扫描
& $py -X utf8 "桥体卫士答辩PPT_v2\_work\fc_consistency.py" `
     "...\桥体卫士答辩PPT_v2" "...\桥体卫士答辩PPT_v2\桥体卫士答辩PPT_12分钟版.pptx"
```

> 已遵守 `_work/PREVIEW_NOTES.md`：本报告**不做** `render --input x.pptx` 几何判定，全部结论来自 XML/源码/实跑，不依赖该失真的光栅化通道。

---

## 一、✅ 通过项

### 1.1 规模与路由数字

| # | PPT 声明（页） | 结论 | 证据 |
|---|---|---|---|
| 1 | 「Flask 19 条路由」/「19 条后端路由」（p3） | ✅ | `app.py` 内 `@app.route` 共 19 处（正则计数输出 `@app.route count in app.py = 19`）。逐条：`/`(356) `/login`(361) `/logout`(374) `/dashboard`(380) `/settings`(397) `/history`(406) `/trend`(417) `/alarms`(425) `/device`(433) `/api/data`(443) `/api/audit`(469) `/api/clear_alarms`(476) `/api/clear_data`(484) `/api/settings`(492) `/api/acknowledge_alarm/<int>`(514) `/api/scenario`(523) `/api/history_alarms`(545) `/api/history_data`(553) `/api/export/<record_type>`(561) |
| 2 | 「6 个 Python 模块 · 约 1500 行」（p3、p11） | ✅ | 6 个核心模块 = `app.py` 582 + `config.py` 84 + `datasource.py` 277 + `db.py` 216 + `rules.py` 137 + `firmware/main.py` 237 = **1,533 行 ≈ 约 1500 ✅**；模块数 = 6 ✅。口径与 `BUILD_SPEC.md:138` 一致。**口径说明**：不含 `tests/`（11 文件）与 `scripts/`（3 文件 393 行）；若按全仓 `*.py` 计则是 9+ 个，答辩被追问时须答「6 个核心模块」 |
| 3 | 「11 个测试文件（10 个 test_*.py + conftest.py）」（p12、p11 notes） | ✅ | `tests/` 实测：10 个 `test_*.py`（test_api/test_auth/test_csrf/test_db/test_device/test_mobile_layout/test_mobile_no_3d/test_rules/test_serial_flow/test_shell）+ `conftest.py` = 11 ✅（另有 `browser_harness.py`、`check_pages_fill.py` 非 `test_*`，不计） |
| 4 | 「101 项用例」（p11、p12） | ✅ | `pytest tests/ --collect-only -q` → **`101 tests collected in 0.02s`**。分文件：test_shell 41 / test_mobile_layout 12 / test_mobile_no_3d 11 / test_api 9 / test_rules 8 / test_auth 5 / test_serial_flow 5 / test_csrf 4 / test_db 3 / test_device 3 = **101** ✅ |
| 5 | 「1 秒采样周期，曲线保留最近 60 点」（p13、p7） | ✅ | `config.py:55` `SAMPLE_INTERVAL = float(_env("SAMPLE_INTERVAL", "1"))`；`app.py:42` `HISTORY_LIMIT = 60  # 实时曲线保留点数`，`app.py:248` `if len(self.latest["history"]) > HISTORY_LIMIT: pop(0)`；`db.py:115` `recent_samples(self, limit=60)` |
| 6 | 采样周期范围 0.1–60s | ✅ | `config.py:80` `if not 0.1 <= cls.SAMPLE_INTERVAL <= 60`；`app.py:507-508` 同区间并回 400「采集周期范围为 0.1-60 秒。」 |
| 7 | 测试耗时 15.38s | ✅（区间内） | 9 次全量实跑耗时：15.19 / 15.22 / 15.30 / 15.32 / 15.34 / 15.35 / 15.37 / 15.43 / 15.43 s → **区间 15.19–15.43s，15.38s 落在区间内**。⚠️ 但这是单次快照、非常量，详见 ⚠️-5、❌-1 |
| 8 | 「0 skipped」 | ✅ | 9 次全量运行中**从未出现 skip**（无 `-rs` 提示、无 `skipped` 计数） |

### 1.2 规则引擎默认参数（`rules.py`）

| PPT 声明 | 结论 | 证据 |
|---|---|---|
| threshold = 120.0 | ✅ | `rules.py:18` `def __init__(self, threshold=120.0, ...)`；`config.py:54` `THRESHOLD = float(_env("THRESHOLD", "120"))` |
| rate_limit = 10.0 | ✅ | `rules.py:18` `rate_limit=10.0`；判定 `rules.py:73` `if abs(delta) >= self.rate_limit` |
| duration_points = 5 | ✅ | `rules.py:18` `duration_points=5`；判定 `rules.py:81` `if self._over_count >= self.duration_points and not self._duration_fired` |
| baseline_window = 30 | ✅ | `rules.py:20` `baseline_window=30` |
| drift_limit = 20.0 | ✅ | `rules.py:20` `drift_limit=20.0`；判定 `rules.py:115` `if abs(drift) >= self.drift_limit` |
| 短时波动「近 10 点峰谷差 ≥ 30.0」 | ✅ | `rules.py:19` `volatility_window=10, volatility_limit=30.0`；`rules.py:94-95` `recent = values[-self.volatility_window:]; span = max(recent)-min(recent)` / `if span >= self.volatility_limit` |
| 设备离线 offline_after = 10 | ✅（数字对，位置见 ⚠️-3） | `datasource.py:137` `def __init__(self, port, baud=115200, read_timeout=0.5, offline_after=10)`；`datasource.py:250,257` `if self.timeout_count >= self.offline_after` |
| 分级 1.1× = 132 / 1.2× = 144 | ✅ | 阈值 120 × 1.1 = **132**、× 1.2 = **144**；`rules.py:42-46` `if value >= threshold*1.2: return "严重报警"` / `if value >= threshold*1.1: return "报警"`。p7 波段 `≤120 / >120 / ≥132 / ≥144` 与 `rules.py` 的 `>`、`>=` 语义**逐字吻合** ✅ |
| 四级配色语义 green/amber/orange/red | ✅ | `SPEC_diagrams.json` 中 `s07_risk` → `rl_chart.bands` = `{60–120 green α.08} {120–132 amber α.1} {132–144 orange α.1} {144–180 red α.1}`；执行器 `build_deck.py:806-817` 按 band 逐条绘制 |

### 1.3 能力声明

| # | PPT 声明（页） | 结论 | 证据 |
|---|---|---|---|
| 9 | 「6 类可解释规则」= 阈值超限/变化率突变/持续超限/短时波动/基线偏移/设备离线（p3、p8、p12） | ✅ | `rules.py:5-10` 文档列出 5 类采样值规则（阈值超限 / 变化率突变 / 持续超限 / 短时波动 / 基线偏移），`rules.py:5` 明写「另「设备离线」事件规则在采集层 app.py 实现」；`app.py:210` `self._record_device_event("设备离线", "严重报警", ...)` = 第 6 类。名称逐字一致 |
| 10 | 边沿触发 + 滞回（找标志位实现） | ✅ | 边沿：`rules.py:31` `self._over = False`、`rules.py:55-57` `if value > self.threshold: if not self._over: self._over = True; alarms.append(...)`、`rules.py:65-68` 回落重置。滞回标志位：`rules.py:33` `_duration_fired`、`:34` `_vol_fired`、`:35` `_drift_fired`；解除条件 `rules.py:103` `elif span < self.volatility_limit * 0.5`、`rules.py:123` `elif abs(drift) < self.drift_limit * 0.5`（回落到阈值一半才可再报，正是「滞回」） |
| 11 | 每条报警 = 触发规则 + 触发值 + 原因 | ✅ | `rules.py:58-62` 每个 alarm dict 带 `rule`/`level`/`reason`，reason 用 `%.2f` 内插触发值与阈值：`"应变指标 %.2f 超过阈值 %.2f（相对应变指标，无量纲）"`；`app.py:257-260` 落库 `(level, rule, reason)`；`db.py:36-37` 列 `rule TEXT NOT NULL` / `reason TEXT NOT NULL` |
| 12 | 「未做工程级标定」为否定句、reason 自带「无量纲」口径 | ✅ | `rules.py:61` reason 尾缀「（相对应变指标，无量纲）」（另外 4 条 reason 均为「（相对应变指标）」）；`config.py:52-53` 注释「不声称微应变(με)精度」；`datasource.py:30` `UNIT = "相对应变指标"` |
| 13 | 双模式环境变量 `DATA_SOURCE=sim|serial` 一键切换 | ✅ | `config.py:47` `DATA_SOURCE = _env("DATA_SOURCE", "sim").strip().lower()  # sim | serial`；`config.py:76-77` 校验非法值报错；`app.py:148-150` `_build_source()` 按 `Config.DATA_SOURCE == "serial"` 二选一；`.env.example:20` `DATA_SOURCE=sim` |
| 14 | 模拟 6 场景（正常/预警/报警/严重/离线/恢复） | ✅ | `datasource.py:80` `valid = {"normal","warn","alarm","critical","offline","recover"}` = 6；`app.py:46` `SCENARIOS = ("normal","warn","alarm","critical","offline","recover")`；`app.py:47-50` 中文标签 `正常运行/预警/报警/严重报警/设备离线/设备恢复`；`/api/scenario` GET 返回全部 6 项（`app.py:534`）。**口径提示**：`datasource.py:86-87` `if name == "recover": self.scenario = "normal"` —— 「恢复」是合法 API 入参但落地即归并为 normal（过渡态语义），场景数按「可切换项」计为 6 ✅ |
| 15 | 「围绕 80 波动，始终在线」（p4 sim 卡） | ✅ | `datasource.py:74` `self.value = 80.0`；`:96-97` `self.value += random.uniform(-3, 3)` / `round(max(50, min(110, self.value)), 2)`；`:112-117` `health()` 在 normal 下恒 `"state": "online"` |
| 16 | 心跳 / 连续超时计数 / 最近错误原因 三要素 | ✅ | `datasource.py:148-150` `last_heartbeat / timeout_count / last_error`；`:254-269` `health()` 返回 `last_heartbeat / timeout_count / last_error`；`:198-199` 收到数据即 `last_heartbeat = now_str()`；`:195` 超时 `timeout_count += 1`；`:169/176/190` 写入 `last_error` |
| 17 | 「三态：未连接/在线/离线」 | ✅ | `datasource.py:247-252` `status_text()` 三分支 `设备未连接` / `设备离线` / `设备在线`；`:255-260` `health()` 同口径（`设备未连接` → `state="offline"`, `text="设备未连接"`） |
| 18 | 「断线如实离线、不伪造数据、不沿用旧值」（p4） | ✅ | `datasource.py:93-94` `if s == "offline": return None  # 设备离线：无新数据`；`app.py:195-196` sim 模式直接 return，不造假心跳；`app.py:208-211` 离线边沿 `reason = health.get("last_error") or "心跳超时"` → 写入 `"设备离线"/"严重报警"` |
| 19 | 「连续超时计数 ≥ 10 → 离线」（p4、p8） | ✅ | `datasource.py:250,257` `if self.timeout_count >= self.offline_after`（`offline_after=10`） |
| 20 | 「真实硬件链路已实现，本次按软件模式演示」（p4，唯一硬件口径句） | ✅ | `datasource.py:124-277` 完整 `SerialSource`（读线程 / JSON 新旧双协议 `_parse` / 心跳 / 超时 / 关闭）；`firmware/main.py` 237 行；`app.py:149` `SerialSource(Config.SERIAL_PORT, Config.SERIAL_BAUD)` 真实接线 |
| 21 | 未登录 API → 401 | ✅ | `app.py:100-102` `if "user" not in session: if request.path.startswith("/api/"): return jsonify({...}), 401`；`tests/test_auth.py:5-9` 实测 4 个 API `== 401`；`:12-15` 页面 302 → `/login` |
| 22 | CSRF 防护 | ✅ | `app.py:70-93` `@app.before_request csrf_protect()`：POST/PUT/PATCH/DELETE 强制校验、`secrets.compare_digest` 常量时间比对、失败 403（API 返回 JSON）；`app.py:43-44` `CSRF_TOKEN_NAME="csrf_token"` / `CSRF_HEADER="X-CSRF-Token"`；`tests/test_csrf.py:5-24` 无 token→403、错 token→403、对 token→200、`/login` 豁免 |
| 23 | 密钥走 .env、不进仓库 | ✅ | `config.py:15-19` `load_dotenv()`；`config.py:31` `SECRET_KEY = _env("SECRET_KEY","") or secrets.token_hex(32)`（不硬编码）；`.env.example` 全量键值模板；`.gitignore` 含 `.env`（Environments 段）；实盘 `.env` 不存在（`Test-Path .env` → `False`），仓库仅有 `.env.example` |
| 24 | 「统一鉴权」 | ✅ | `app.py:96-105` `login_required` 装饰器，覆盖 8 个页面路由（除 `/login`、`/logout`）与全部 10 个 `/api/*`；`app.py:381,398,408,418,426,434,444,470,477,485,493,515,524,546,554,562` 逐处挂载 |
| 25 | 密码哈希（能力存在） | ✅ | `config.py:37` `PASSWORD_HASH = _env("APP_PASSWORD_HASH","")`；`config.py:66-69` `hmac.compare_digest(hashlib.sha256(password).hexdigest(), PASSWORD_HASH.lower())`。⚠️ 但「只存哈希」不成立，见 ❌-2 |

### 1.4 SQLite 五表 —— 表名 / 字段名 / 索引名（逐字符核对）

来源：`db.py:17-66`（`SCHEMA`，`CREATE TABLE IF NOT EXISTS` 原文）

| PPT 第 10 页声明 | 结论 | `db.py` 原文 |
|---|---|---|
| `samples` | ✅ | `db.py:18` `CREATE TABLE IF NOT EXISTS samples (` |
| `alarms` | ✅ | `db.py:28` `CREATE TABLE IF NOT EXISTS alarms (` |
| `settings` | ✅ | `db.py:43` `CREATE TABLE IF NOT EXISTS settings (` |
| `audit` | ✅ | `db.py:50` `CREATE TABLE IF NOT EXISTS audit (` |
| `device_heartbeat` | ✅ | `db.py:58` `CREATE TABLE IF NOT EXISTS device_heartbeat (` —— 精确，非 `heartbeats`；亦无 `audit_log`（`db.py:50` 为 `audit`） |
| `ts · device_id · value · seq`（samples） | ✅ | `db.py:20,21,23,24` `ts TEXT` / `device_id TEXT` / `value REAL` / `seq INTEGER`（另有 `source TEXT`，PPT 未列不错） |
| `threshold · interval`（settings） | ✅ | `db.py:46,47` `threshold REAL NOT NULL` / `interval REAL NOT NULL` |
| `actor · action · detail`（audit） | ✅ | `db.py:53,54,55` `actor TEXT NOT NULL` / `action TEXT NOT NULL` / `detail TEXT` |
| `level · rule · reason · status`（alarms） | ✅ | `db.py:35,36,37,38` `level TEXT NOT NULL` / `rule TEXT NOT NULL` / `reason TEXT NOT NULL` / `status TEXT NOT NULL DEFAULT '未处理'` |
| `event = beat / offline / online` | ✅ | `db.py:63` `event TEXT NOT NULL  -- beat(心跳) / offline(离线) / online(恢复)`；写入侧 `app.py:201,217` 仅用 `"beat"`/`"offline"`/`"online"` |
| 「3 个时间索引」 | ✅ | `db.py:26` `idx_samples_ts ON samples(ts)`；`:41` `idx_alarms_ts ON alarms(ts)`；`:65` `idx_heartbeat_ts ON device_heartbeat(ts)` → 索引名与目标表逐字符一致，共 3 个 |
| 「历史查询按时间走索引，不全表加载」 | ✅ | `db.py:119-129` `query_samples` / `:150-160` `query_alarms` 按 `ts >= ? AND ts <= ?` 过滤；索引 `idx_samples_ts`/`idx_alarms_ts` 正对 `ts` |
| 「时间筛选、统计摘要与 CSV 导出」（p10） | ✅ | 时间筛选 `app.py:545-558`（`start`/`end` 透传 `query_alarms`/`query_samples`）；CSV 导出 `app.py:561-577` `_csv_response`（带 BOM，`alarms_history.csv`/`data_history.csv`）；统计摘要见 `/api/data` 的 `sample_count`/`uptime`（`app.py:455,464`） |

### 1.5 业务闭环（p9）

| PPT 声明 | 结论 | 证据 |
|---|---|---|
| 「确认处理后，状态从「未处理」转为「已处理」」 | ✅ | `db.py:38` `status TEXT NOT NULL DEFAULT '未处理'`；`db.py:168` `UPDATE alarms SET status='已处理', acknowledged_at=? WHERE id=?`；`app.py:313` 内存同步 `alarm["status"] = "已处理"`；`tests/…`；页面 `未处理 → 已处理` 口径一致 |
| 「离线触发严重报警」 | ✅ | `app.py:210` `self._record_device_event("设备离线", "严重报警", f"设备失去连接：{reason}", "未处理")` |
| 「恢复自动记录设备恢复」 | ✅ | `app.py:206` `self._record_device_event("设备恢复", "预警", "设备已恢复在线", "已恢复")`；`app.py:216-217` 同时写 `device_heartbeat` 的 `online` 事件 |
| 「谁在何时改了什么，审计表一查便知」 | ✅ | `app.py:302-303` `add_audit(actor,"update_settings",f"阈值={...}，周期={...} 秒")`；`app.py:169,285,293,315` 场景/清数据/清报警/确认处置均写审计；`/api/audit`（`app.py:469-473`）供设置页展示 |
| 「7 步闭环」（p9 左栏 7 张卡） | ✅ | PPT 可见 7 个环节文本：报警产生 / 分级着色 / 确认处置 / 状态变更 / 设备恢复记录 / 历史可查 / 审计留痕 —— 与上表证据一一对应 |
| 「数据、阈值、历史三端用同一生效参数」（p12） | ✅ | 单一真源 `simulator.latest["threshold"]`：`app.py:393,412,421,429,437`（5 个页面模板）+ `app.py:451`（`/api/data`）+ `app.py:498`（`/api/settings` GET）；写入路径 `app.py:295-303` 同时更新 `latest`、`engine.set_threshold`、`settings` 表、`audit` 表；重启后 `app.py:122-124` 从 `db.latest_setting()` 恢复 |

### 1.6 三维场景 / 离线可用 / 手机端

| # | PPT 声明（页） | 结论 | 证据 |
|---|---|---|---|
| 26 | three.js **r160** 本地化 | ✅ | **实测**：`node --input-type=module -e "import('…/three.module.min.js')"` → `REVISION = 160`、`WebGLRenderer = function`。`static/vendor/README.md:11` 记 `three.js 0.160.0（r160；MIT License）`；`:18` 记 sha256 `3e690ac7…f69ba6`、字节 670681 —— **本人自算 `Get-FileHash` 结果与文档逐字符一致** ✅ |
| 27 | OrbitControls 本地化 | ✅ | `static/vendor/OrbitControls.js` 存在（29,868 bytes），**自算 sha256 = `5a44a9e86a2a0fb11933eed69bc2cd33c76a496854c1aed6ed776efa87d7b064`**，与 `README.md:19` 记录一致；`README.md:74` 记录 `orbitcontrols-construct ok`；`README.md:133-134` 说明裸导入 `from 'three'` 由 `three-boot.js` 的 importmap 解析 |
| 28 | 5 个预设视角 | ✅ | `static/js/twin/scene.js:81-89` `viewPresets()` **恰好返回 5 项**：`full 全桥` / `span 主跨` / `tower 桥塔` / `canyon 峡谷` / `deck 桥面`（各带 label+note）；`:431` `const presets = viewPresets()`；`:474-476` 按 key 切换 |
| 29 | 旋转 / 缩放 / 平移 / 双击聚焦 | ✅ | `static/js/twin/scene.js:6` 头注释「双击任意位置 = 以该点为中心平滑飞行（聚焦）」；`:707` `add('dblclick', …)`、`:709-727` 双击测点→聚焦该点，双击其它位置→射线与桥面平面交点为中心；`:698-704` 单击选中与双击互斥（260ms）。HUD 明示 `static/js/twin/hud.js:100` `'拖拽旋转 · 滚轮缩放 · 右键平移 · 双击聚焦'` |
| 30 | 结构线框与测点标注可开关 | ✅ | `static/js/twin/hud.js:76-79` `toggle('结构线框', false, (v)=>{…setMode(on ? '线框' : '实体')})`；`:82-85` `toggle('测点标注', true …)` 三态文案 `['测点标注','仅跨中','标注关闭']`；实现 `scene.js:273-305`（`wireRoot` 层 + 按当前风险色 `applyWireTheme`）、`scene.js:821-837` 由杆件矩阵生成 12 棱线段 |
| 31 | 颜色与涟漪随风险等级联动 | ✅ | 大屏分级 → 场景：`templates/dashboard.html:623-628` `riskOf()` 返回 `key ∈ normal/warn/alarm/crit/offline`，注释 `:621-622` 明写「用于 #scene 的 sev-* 类与 TwinScene.setData({riskKey})，两者必须一致」；`scene.js:1390` `setRisk(state.risk)` + `:768` `applyWireTheme()`；涟漪：`static/app.css:539`「跨中传感器测点：三层扩散涟漪 + 呼吸光环（currentColor 联动风险等级）」、`:557`「风险等级 → 测点颜色 + 涟漪节奏（等级越高越急促）」 |
| 32 | WebGL 不可用降级二维 | ✅ | `static/js/twin/mount.js:37-47` `webglOk()` 探测 `webgl2/webgl/experimental-webgl`，失败即 `showFallback('当前浏览器/显卡未启用 WebGL')`；`:25-32` `showFallback()` 显示 `#sceneFallback`、隐藏 canvas、置 `window.TWIN_3D_READY=false` 并写明原因（不静默）；`:8-9` 头注释「回退到原有的 2D 桥梁示意图」；降级容器 `templates/dashboard.html:492` `<div class="scene-fallback" id="sceneFallback" hidden>`（`:475` 注明另有跨中标签同层）；`:274-293` 另处理 `webglcontextlost/restored` |
| 33 | 手机端 ≤768px + 服务端 User-Agent 302 → `/trend` | ✅ | **服务端**：`app.py:345` `MOBILE_BREAKPOINT_PX = 768`、`:346-347` `MOBILE_UA_RE = Mobile|Mobi|Android|iPhone|iPod|iPad|IEMobile|Opera Mini|Windows Phone`、`:350-352` `_is_mobile_request()`、`:390-391` `@login_required` 之后 `if _is_mobile_request(): return redirect("/trend")`（注释 `:386-387` 说明鉴权优先，未登录仍是 302 → `/login`）。**客户端兜底**：`static/js/mobile-redirect.js:32` `MOBILE_BREAKPOINT_PX = 768`、`:37` `if (window.innerWidth > MOBILE_BREAKPOINT_PX) return;`、`:39` `location.replace('/trend')`；`:25-26` 注释三处断点同值。测试覆盖 `tests/test_mobile_no_3d.py`（11 例）、`tests/test_mobile_layout.py`（12 例） |
| 34 | 主跨 1420m 双塔单跨钢桁梁悬索桥（按公开设计参数） | ✅ | `static/js/twin/spec.js:30` `main: 1420`；`:31` `total: 2160 // 245+1420+495`；`:163-177` `FACT_SHEET` 首两项 `['桥型','双塔单跨钢桁梁悬索桥']`、`['主跨','1420 m']`；`:180-183` `FIDELITY_NOTE` 明写「主跨/缆跨/垂跨比/桁高桁宽/节段长度/桥面宽度/桥高为公开设计参数；塔柱截面收坡、横梁道数、承台、锚碇体量、峡谷具体地形为…示意模型，**不作为工程测量依据**」✅；`:1-19` 头注释给出参数来源（《桥梁》杂志 2024 年第 6 期）|
| 35 | 「杆件与缆索按公开参数生成，点选测点看说明」（p5） | ✅ | `spec.js:145-160` `HOTSPOTS` 7 个可点选热点（跨中/四分点/两塔/主缆跨中/两锚碇），各带 `label`+`code`+`note`（如 `SG-01` 跨中测点）；`scene.js:580-727` 射线拾取 + 单击选中 + 详情面板（`hud.js:106` 空态文案「点击场景中的测点标记查看该部位说明」） |
| 36 | 「断网可用」（p5 卡片标题） | ✅（主路径） | 全部关键资产本地路径、无外部 `<script src>`：`templates/dashboard.html:17,20,923` → `/static/js/mobile-redirect.js`、`/static/js/three-boot.js`、`/static/js/twin/mount.js`（module）；`templates/trend.html:186`、`alarms.html:254`、`history.html:12` → `/static/js/echarts.min.js`（本地 1,024,740 bytes）；样式 `/static/app.css`。`static/vendor/README.md:80-93` 记录 headless Edge + `--host-resolver-rules` 断网实测 `source:"local"`、`fallbackUsed:false`。⚠️ 仍存 CDN 兜底代码，见 ⚠️-1 |
| 37 | ECharts 本地化 | ✅ | `static/echarts.min.js`（1,024,740 bytes）经 Flask 静态目录本地加载；引用处均有「本地」注释，如 `templates/alarms.html:253`「本地 ECharts（离线可用，不依赖 CDN）」；全仓 `templates/` 与 `static/*.js` **未发现任何 CDN 直连 ECharts** |
| 38 | 模拟模式水印（p4「大屏常显模拟演示水印」） | ✅ | `templates/dashboard.html:550-552` `<div class="demo-banner" id="demoBanner">` + `<span class="wm-text">模拟演示 · 非真实硬件数据 · 缩尺模型受载变化模拟</span>`；`:547` 由 `/api/data` 的 `is_simulated`/`source` 驱动，`app.py:460` `"is_simulated": simulator.source == "sim"`；`:759` serial 模式整条隐藏 |

### 1.7 一致性：PPT 可见文本 vs 规格（逐字）／notes／页序

| # | 检查 | 结论 | 证据 |
|---|---|---|---|
| 39 | 页序与 slide_id 对应 | ✅ | `fc_consistency_final.txt` A 节：`PPTX slides = 15 ; SPEC slides = 15 ; equal = True`；逐页 `p1 s01_cover` … `p15 s15_thanks`，与 `BUILD_SPEC.md:111-127` 页面清单顺序、`chrome` 取值（s01/s15 = `none`，其余 `standard`）**15/15 一致** |
| 40 | 可见文本逐字（形状+表格+图形内文字） | ✅ | B 节：`TOTAL missing = 1 ; TOTAL extra = 0`。**唯一差异已定位为非缺陷**：`SPEC_diagrams.json` 中 `s07_risk` 的 `rl_chart.series[0].name = "示意波形"` 未出现在 PPT —— 原因是 `build_deck.py:950-952` 图例仅在 `if len(legend) > 1` 时绘制，单序列图按设计**不画图例**，故该字段无渲染路径；该曲线的「示意」限定词已由同一图表的 `x_label = "采样点（1 s 周期，示意）"` 在 PPT 中如实呈现（见 `pptx_text_final.txt:432`）。**结论：0 处文本不一致** |
| 41 | notes 逐字 | ✅ | C 节：`notes mismatched slides = 0 / 15` —— 15 页演讲者备注与 `SPEC_content.json` 的 `notes` 字段全等 |
| 42 | 构建期覆盖是否改动文案 | ✅ | `build_deck.py:988-994` `NO_CHROME_TITLE`（仅新增 s01/s15 的页标题文本，取自 `s["title"]`）、`:997` `TEXT_Y_OFFSET = {"s15_thanks": 300000}`（仅 y 位移）、`:1001-1003` `TEXT_COLOR_OVERRIDE = {"s15_thanks": {"white": "navy"}}`（仅颜色）。**三者均不动文案与坐标语义**，故 40/41 项的逐字结论成立 |

### 1.8 口径红线（**按 Lead 2026-10-09 收口后的判据**）

扫描对象 = PPT 15 页全部可见文本 + 15 页 notes（双通道：python-pptx 形状遍历 + 独立 raw-XML `<a:t>` 全量扫描，结果一致）。原始输出见 `_work/fc_consistency_final.txt` D/D2/D3 节。

| 判据 | 结论 | 证据 |
|---|---|---|
| 禁词：数字孪生 / 机器学习 / 人工智能 / 大数据 / 微应变 / 高精度 / 工程级精度 / 真实桥梁应变监测 / 我们 / 团队 / 领先 / 革命性 / AI / 预测 / 深度学习 / 智能算法 | ✅ **全部 0 命中** | D 节 16 行全部输出 `clean:` —— 逐条扫描后无任何命中（含 notes） |
| 「工程级」**只允许**出现在 s13 否定句「未做工程级标定与量值溯源」 | ✅ | D2 节：全文 `工程级` 出现 **1 次**，位于 `pptx_text_final.txt:881` `p0: '未做工程级标定与量值溯源'`（第 13 页），`disallowed = 0`。Lead 所指 s02 旧句「依赖工程级标定」已改为 `pptx_text_final.txt:58` `p0: '依赖专业标定'` ✅ |
| 「3D」只允许在 `three.js`/`WebGL` 等技术名或代码标识中；叙述文字统一「三维」 | ✅ | D3 节：全文 `3D` 出现 **0 次**（`total '3D' occurrences = 0 ; narrative(disallowed) = 0`）。Lead 所指 s03 旧句「3D 场景」已改为 `pptx_text_final.txt:143` `p0: '三维场景 + 大屏 + 手机趋势页'` ✅。叙述统一用「三维」（p1:35、p3:143、p5:318、p15:970） |
| 禁用「AI」子串 | ✅ | D 节 `clean: 'AI'`（无任何大小写形态命中） |
| 「压力传感器」只允许在第 3 页硬件层 | ✅ | E 节：`压力传感器` **全文 0 次**；`ESP32` 出现 **1 次**，位于 `pptx_text_final.txt:133` `p0: 'ESP32 + 传感器（现场不接实物）'` = 第 3 页硬件层，且自带「现场不接实物」限定 ✅。第 4 页硬件口径为 `pptx_text_final.txt:227` `p0: '真实硬件链路已实现，本次按软件模式演示。'` ✅ |
| 「硬件」出现位置 | ✅ 合理 | 仅 p2「低成本，无需硬件」、p3「硬件层」、p4「真实硬件链路已实现…」、p6「无硬件实物」——均在「本次不用硬件/现场只跑软件」的口径内，与 `BUILD_SPEC.md:7,151` 一致 |

### 1.9 孤证排查（除下述 ❌-4 外）

对 PPT 全部 15 页逐条做「仓库可溯性」反查：**其余每一条可见文本与 notes 均在仓库中找到直接依据**，明细已并入 1.1–1.8 各表的「证据」列（共 42 项通过）。特别复核了 6 类规则示例 reason 文案、桥型参数、五表字段、测试数字四个高风险点。

---

## 二、⚠️ 存疑 / 口径需注意（不阻断答辩，但被追问时需有说法）

### ⚠️-1（中）`static/js/three-boot.js` 仍保留 unpkg CDN 兜底代码

PPT p5「断网可用」、p11「three.js / ECharts 已本地化」在**主路径上成立**（本地两级加载 + README 断网实测），但仓库里确实存在 CDN 直连残留：

- `static/js/three-boot.js:37`：`var CDN_ROOT = 'https://unpkg.com/three@' + VERSION + '/';`
- `static/js/three-boot.js:185`：`/** CDN 兜底策略 2：不依赖 importmap 的文本重写导入（需要外网 + CORS，unpkg 允许）。 */`
- `static/vendor/README.md:6-7` 自述：「只有本地两级加载（importmap → Blob 改写）全部失败时才会回退 `unpkg.com`，回退时 `window.BridgeThree.fallbackUsed === true`」
- **未发现** `<script src="https://…">` 形式的模板直连（`templates/*.html` 全部静态引用均为 `/static/…`）；ECharts 无任何 CDN 残留

**影响**：断网现场走的是本地路径（README 已实测 `fallbackUsed:false`），不影响「断网可用」成立；但「无外网依赖」若被逐字追问，需承认存在**最后一级 CDN 兜底分支**。

### ⚠️-2（中）分级边界在「规则引擎」与「大屏」之间不一致，而 PPT 声明「同一套分级」

- 引擎：`rules.py:42-44` 用 `>=` —— `value >= threshold*1.2` → 严重报警；`value >= threshold*1.1` → 报警（阈值 120 时：**132 判「报警」、144 判「严重报警」**）
- 大屏：`templates/dashboard.html:626-628` 用 `<=` —— `strain <= threshold*1.1` → 预警；`strain <= threshold*1.2` → 报警（**132 显示「预警」、144 显示「报警」**）

即：**恰好等于 132 或 144 时，报警行写「报警/严重报警」，而大屏风险卡显示「预警/报警」**。区间内部（如 130、140）两者一致。

PPT 第 7 页声明「大屏、仪表、报警行同一套分级」（`pptx_text_final.txt:460`）、「等级 → 颜色 → 处置优先级（同一份数据）」（`:453`），其波段标签 `≤120 / >120 / ≥132 / ≥144` 与 `rules.py` 的 `>`/`>=` **逐字吻合** ✅ —— 即**库表侧（引擎）是 PPT 的依据**，不一致的是大屏显示侧的边界含入。`datasource.py:60-62` 的注释声称两者「统一口径」，但在 132/144 两点上并不严格成立。

### ⚠️-3（低）「参数集中在 rules.py」不含第 6 类规则的参数

`pptx_text_final.txt:551`（第 8 页脚注）：「边沿触发 + 滞回：持续超限只报一次，回落后才能再报；**参数集中在 rules.py**。」

- `rules.py:18-20` 集中了前 5 类采样值规则的全部参数（threshold / rate_limit / duration_points / volatility_window / volatility_limit / baseline_window / drift_limit）✅
- 但第 6 类「设备离线」的判据参数 `offline_after=10` 在 **`datasource.py:137`**（构造函数默认值），`app.py:149` 调用 `SerialSource(Config.SERIAL_PORT, Config.SERIAL_BAUD)` **未显式传入、也未来自 `Config`** —— 全仓 `offline_after` 仅出现于 `datasource.py:137,141,250,257`

**影响**：同一页正文列了「串口连续超时 ≥ 10 次」（`:535`），该 10 不在 `rules.py`。被追问「参数都集中在 rules.py 吗」时需答「5 类采样值规则在 rules.py，设备离线的 offline_after 在 datasource.py」。

### ⚠️-4（低）第 5 页同一数字两种排版：「主跨 1420 m」与「主跨 1420m」

同一页（p5）并存两种写法，仅差一个半角空格：

- `pptx_text_final.txt:295` `p0: '主跨 1420 m'`（桥体尺寸标注）
- `pptx_text_final.txt:300` `p0: '主跨 1420m'`（右侧卡片标题）

数字口径无误（均为 1420），属排版一致性瑕疵；`spec.js:165` `FACT_SHEET` 的规范写法是 `'1420 m'`（带空格）。

### ⚠️-5（低）「15.38s」是单次运行快照，不是可复现常量

9 次全量实跑耗时落在 **15.19–15.43s**（15.38 在区间内 ✅），但每次数值都不同，同一台机器上**无法复现出 15.38 这个定值**。PPT 将其写为「实跑：101 passed in 15.38s」并附「0 failed / 0 skipped」的确定性断言，属把**单次快照**表述为**稳定结果**。建议口头讲解时说「约 15 秒」；真正的问题不在秒数，而在 ❌-1。

### ⚠️-6（低 · 非缺陷）规格字段 `示意波形` 无渲染路径

`SPEC_diagrams.json` → `s07_risk` → `rl_chart.series[0].name = "示意波形"`，因 `build_deck.py:950-952` 图例仅在序列数 > 1 时绘制，该字符串不会出现在 PPT 中。**不构成事实错误**（同一图表 `x_label = "采样点（1 s 周期，示意）"` 已承载「示意」限定，见 `pptx_text_final.txt:432`），仅说明该规格字段冗余，可删。

---

## 三、❌ 必须修

### ❌-1（高）「101 passed in 15.38s（0 failed / 0 skipped）」不可稳定复现 —— 测试套件是 flaky 的

**PPT 原句**（4 处正文 + 2 处 notes）：
- `pptx_text_final.txt:759`（p11）`p0: '实跑：101 passed in 15.38s（0 failed / 0 skipped）'`
- `pptx_text_final.txt:790`（p12）`p0: '101 passed in 15.38s'`
- `pptx_text_final.txt:792`（p12）`p0: '0 failed / 0 skipped · 11 个测试文件（10 个 test_*.py + conftest.py）'`
- `pptx_text_final.txt:773`（p11 notes）「…零失败、零跳过…」/ `:859`（p12 notes）「零失败零跳过」

**实跑反证**（原始输出：`_work/pytest_out.txt`、`_work/flake_repro.txt`、`_work/flake_detail.txt`）

全量 `python -m pytest tests/ -q` 共跑 9 次，**2 次失败**（≈22%）：

```
run  1 (pwsh-102) : 101 passed in 15.30s
run  2 (pwsh-107) : FAILED tests/test_mobile_layout.py::test_device_mobile_no_text_overlap[viewport0]
                    1 failed, 100 passed in 15.37s
run  3 (pwsh-107) : 101 passed in 15.43s
run  4..8 (pwsh-114): 101 passed in 15.32 / 15.35 / 15.34 / 15.22 / 15.19s
run  9 (pwsh-114) : FAILED tests/test_mobile_layout.py::test_device_mobile_no_text_overlap[viewport0]
                    1 failed, 100 passed in 15.43s
```

分文件 `pytest tests/test_mobile_layout.py -q` 跑 8 次，**3 次失败**（37.5%）：

```
focus 1 : 12 passed in 13.69s      focus 5 : 12 passed in 13.78s
focus 2 : 1 failed, 11 passed      focus 6 : 1 failed, 11 passed
focus 3 : 1 failed, 11 passed      focus 7 : 12 passed in 13.84s
focus 4 : 12 passed in 13.69s      focus 8 : 12 passed in 13.72s
```

单用例重试到失败时的完整 traceback：

```
FAILED on attempt 2
F......                                                                  [100%]
________________ test_device_mobile_no_text_overlap[viewport0] ________________
browser = <browser_harness.Harness object at 0x…>
viewport = (320, 568)
    def test_device_mobile_no_text_overlap(browser, viewport):
        _open(browser, "/device", viewport)
        spill = browser.page.eval_js(CARD_SPILL_JS)
>       assert not spill.get("missing"), "页面缺失 .dv-3col"
E       AssertionError: 页面缺失 .dv-3col
E       assert not True
tests\test_mobile_layout.py:180: AssertionError
```

**排除随机化插件**：`pytest --version` → `pytest 9.1.1`，环境仅 `pluggy 1.6.0`，**未安装 pytest-randomly / pytest-xdist 等顺序或并发插件**，故非用例顺序随机导致，是真实竞态（`browser_harness` 在 320×568 视口下 DOM 尚未就绪即被采样）。

**影响**：这是答辩要当场亮的一页（p12「可度量成果 —— 测试全绿」），评委若要求现场复跑，约 1/5 概率看到红字，与幻灯片上的「0 failed」直接冲突，属最高风险项。

**最小修复建议**（改哪一处）
1. **首选（治本）**：`tests/test_mobile_layout.py:180` 所在的 `test_device_mobile_no_text_overlap`，在 `_open(browser, "/device", viewport)` 之后、`eval_js(CARD_SPILL_JS)` 之前加**显式等待**（轮询 `.dv-3col` 出现，带超时；项目内 `tests/browser_harness.py` 已有就绪等待设施可复用），再断言。修完重跑 ≥10 次全量确认 0 失败。
2. **若答辩前无时间改代码**：把 p12 标题「可度量成果 —— 测试全绿」与正文「0 failed / 0 skipped」的**确定性断言降级**为可复述的口径（例如「101 项用例，最近一次实跑全通过」），并**在讲稿里预先给出兜底话术**；同时删掉「15.38s」这个定值。
3. **修好后同步改规格**：`SPEC_content.json` → `s12_evidence` 与 `s11_security` 的相关元素与 `notes`；改完必须重新走 `build_deck.py` 重建（本报告已核验的 SHA256 将失效，需重新冻结并重核）。

### ❌-2（中）「口令只存哈希，不存明文」与仓库实现不符

**PPT 原句**：`pptx_text_final.txt:741`（p11 第 4 行说明）`p0: '表单带令牌；口令只存哈希，不存明文'`

**反证**：
- `config.py:34` 注释原文：「存储：`PASSWORD_HASH` 为 SHA-256 十六进制摘要（**可选**，见下），**否则回退到明文 `PASSWORD`**。」
- `config.py:36` `PASSWORD = _env("APP_PASSWORD", "123456")` —— 默认值就是明文口令
- `config.py:37` `PASSWORD_HASH = _env("APP_PASSWORD_HASH", "")` —— 默认**空字符串**
- `config.py:66-70` `verify_password`：`if cls.PASSWORD_HASH:` 走哈希比对，**`else: return hmac.compare_digest(password, cls.PASSWORD)`** —— 明文比较分支
- `.env.example:11` `APP_PASSWORD=123456`（明文，未注释）；`.env.example:15` `# APP_PASSWORD_HASH=`（**被注释掉、未启用**）
- 实盘 `Test-Path .env` → `False`：本次交付**既没有 .env，也没有启用哈希**，运行时走的就是 `config.py:36` 的明文默认分支

**影响**：这是安全项的实质夸大。同一页的同义表述其实有两处口径一强一弱——p11 notes（`:773`）写的是「密码**支持**哈希存储」（✅ 准确），而 p11 正文（`:741`）写「**只**存哈希，**不**存明文」（❌ 不实）。两者并存本身也会被追问。

**最小修复建议**：改 `SPEC_content.json` → `s11_security` 中 `id` 对应 `'表单带令牌；口令只存哈希，不存明文'` 的元素文本，改为与 notes 一致的「表单带令牌；密码支持哈希存储」或「表单带令牌；支持 SHA-256 口令摘要」。若要保留强表述，则必须先改代码：在 `config.py` 强制要求 `PASSWORD_HASH`（无则拒绝启动）、并同步改 `.env.example:11,15`。

### ❌-3（中）四级风险名称「安全 / 严重」与代码实际字符串「正常 / 严重报警」不符

**PPT 原句**：
- `pptx_text_final.txt` 第 437 / 439 / 441 / 443 行（p7 四张等级卡，逐行原文）`p0: '安全'` / `p0: '预警'` / `p0: '报警'` / `p0: '严重'`
- `pptx_text_final.txt:464`（p7 左栏）`p0: '超过阈值 1.2 倍判严重，'`
- `pptx_text_final.txt:482`（p7 notes）「风险分四级：**安全**、预警、报警、**严重**，对应绿、黄、橙、红。分级口径统一：超过阈值 1.2 倍判**严重**，1.1 倍判报警，其余是预警。」

**反证（代码里的实际字符串，逐字符）**：

| 层级 | PPT 写的 | 仓库实际字符串 | 出处 |
|---|---|---|---|
| 最高档 | `严重` | **`严重报警`** | `rules.py:43` `return "严重报警"`；`rules.py:76` `"严重报警" if abs(delta) >= self.rate_limit * 2 else "报警"`；`rules.py:85` `"level": "严重报警"`；`app.py:49` `"critical": "严重报警"`；`app.py:210` 设备离线 level `"严重报警"`；`db.py:35` 注释 `-- 预警 / 报警 / 严重报警`；`templates/dashboard.html:617` `label: '严重报警'`；`templates/dashboard.html:628` `return { sev: 3, key: 'crit', label: '严重报警', … }` |
| 最低档 | `安全` | **`正常`** | `templates/dashboard.html:614` `0: { key: 'normal', color: '#15803d', label: '正常', icon: '●' }`；`templates/dashboard.html:625` `if (strain <= threshold) return { sev: 0, key: 'normal', label: '正常', … }` |
| 中间两档 | `预警` / `报警` | `预警` / `报警` ✅ | `rules.py:45,46`；`dashboard.html:615,616` |

即 4 个名称中 **2 个与代码/大屏界面字符串不一致**。注意第 9 页同页的表述反而是**正确**的：`pptx_text_final.txt:614` `p0: '离线触发严重报警，恢复自动记录设备恢复。'` —— 全文只有第 7 页用了简称。溯源：`BUILD_SPEC.md:141` 写的是「安全 / 预警 / 报警 / 严重」，规格本身即与代码脱节，PPT 忠实照抄了规格。

**影响**：评委在 PPT 上看到四级叫「安全…严重」，切到大屏却看到「正常…严重报警」，属可被当场指出的口径不一致；且 task 判据明确要求核对「四级风险名称」。

**最小修复建议**（两处，都在规格；改完需重建）
1. `SPEC_diagrams.json` → `figures[for_slide="s07_risk"]`（`fig_id: risk_link`）→ `rl_c1n.text`：`"安全"` → `"正常"`；`rl_c4n.text`：`"严重"` → `"严重报警"`
2. `SPEC_content.json` → `s07_risk` → 左栏「分级口径」元素 `'超过阈值 1.2 倍判严重，'` → `'超过阈值 1.2 倍判严重报警，'`；以及 `s07_risk.notes` 中「风险分四级：安全、预警、报警、严重」→「正常、预警、报警、严重报警」、「1.2 倍判严重」→「1.2 倍判严重报警」
3. 顺带修 `_spec/BUILD_SPEC.md:141` 的口径描述，避免下次再传抄

### ❌-4（中）第 8 页 6 条报警 reason 示例中，有 2 条与 `rules.py` / `app.py` 的实际输出文案不符（孤证）

第 8 页每张规则卡下方展示一条「原因」样例。逐条与代码中的 reason 格式串比对：

| # | PPT 第 8 页原句（`pptx_text_final.txt` 行号） | 代码实际格式串 | 结论 |
|---|---|---|---|
| 1 | `:537` `'应变指标 132.40 超过阈值 120.00（相对应变指标，无量纲）'` | `rules.py:61` `"应变指标 %.2f 超过阈值 %.2f（相对应变指标，无量纲）"` | ✅ 逐字吻合 |
| 2 | `:539` `'单周期变化 +12.35，超过变化率阈值 ±10.00（相对应变指标）'` | `rules.py:77` `"单周期变化 %+.2f，超过变化率阈值 ±%.2f（相对应变指标）"` | ✅ |
| 3 | `:541` `'连续 5 个采样点超过阈值 120.00（相对应变指标）'` | `rules.py:86` `"连续 %d 个采样点超过阈值 %.2f（相对应变指标）"` | ✅ |
| 4 | `:543` `'近 10 点峰谷差 41.20，超过波动阈值 30.00（相对应变指标）'` | `rules.py:100-101` `"近 %d 点峰谷差 %.2f，超过波动阈值 %.2f（相对应变指标）"` | ✅ |
| 5 | `:545` `'近期均值 118.60 相对基线 96.10 偏移 +22.50（相对应变指标）'` | `rules.py:120-121` `"近期均值 %.2f 相对基线 %.2f 偏移 %+.2f，**超过阈值 %.2f**（相对应变指标）"` | ❌ **漏掉了「，超过阈值 20.00」整段**；实际输出必为 `近期均值 118.60 相对基线 96.10 偏移 +22.50，超过阈值 20.00（相对应变指标）` |
| 6 | `:547` `'设备失去连接：串口连续超时计数达 10 次'` | `app.py:209-210` `reason = health.get("last_error") or "心跳超时"` → `f"设备失去连接：{reason}"` | ❌ 后半句**无代码路径可产出**。串口超时但无异常时 `last_error` 为空（`datasource.py:150` `self.last_error = ""`，仅在 `:169,176,190` 三类异常下被赋值），因此真实文案是 `设备失去连接：心跳超时`；仅当发生 `串口打开失败：…` / `串口读取失败：…` / `未安装 pyserial…` 时才会带具体错误 |

**影响**：这两条是本页唯一「直接引用系统输出」的内容，属 task 判据第 7 条「PPT 里出现但仓库找不到依据的表述 → ❌」。风险中等：评委若现场触发一次真实报警并对照页面文字，会发现格式与文案不同。

**最小修复建议**：改 `SPEC_diagrams.json` → `for_slide="s08_rules"` 图中对应两个元素文本：
- 第 5 条补回阈值子句 → `'近期均值 118.60 相对基线 96.10 偏移 +22.50（相对应变指标）'` 改为 `'近期均值 118.60 相对基线 96.10 偏移 +22.50，超过阈值 20.00（相对应变指标）'`（若卡片宽度放不下，可缩短为 `'近期均值偏移 +22.50，超过阈值 20.00（相对应变指标）'`，但须保持与 `rules.py:120` 同一句式）
- 第 6 条改为代码真实可产出的文案 → `'设备失去连接：心跳超时'`（或 `'设备失去连接：心跳超时（串口连续超时计数达 10 次）'`，括号内为解释性补充，不与代码格式串冲突）

---

## 四、总体结论

### **不能直接拿去答辩 —— 需先修 4 条 ❌。**

技术主体（19 条路由、6 个核心模块约 1500 行、五表五字段三索引、6 类规则与全部默认参数、双模式与 6 场景、401/CSRF/.env、three.js r160 与 OrbitControls 本地化及 sha256、5 个预设视角、交互/线框/标注/涟漪/二维降级、UA 302 与 ≤768px 兜底、ECharts 本地化）**逐条经代码与实跑核实，证据充分、口径正确**；全文 15 页可见文本与 notes 与 `SPEC_content.json`/`SPEC_diagrams.json` **逐字一致（0 处不一致）**，红线扫描 **16 个禁词 0 命中、「工程级」仅 1 处且为 s13 允许的否定句、「3D」0 处**，硬件口径仅出现在允许位置——这些都是可以放心讲的。

阻断项集中在 **4 处「说法比实现更强」**，且**全部可用改文案的方式解决，不需要改产品代码**（唯 ❌-1 建议连测试一起治本）：

| ❌ | 一句话 | 最小修复位置 | 改代码? |
|---|---|---|---|
| ❌-1 | 「0 failed / 0 skipped」不稳定，测试套件 flaky（9 次全量跑 2 次红，均由 `test_device_mobile_no_text_overlap[viewport0]` 竞态引起） | `tests/test_mobile_layout.py:180` 前加就绪等待；无时间则降级 p11/p12 的确定性断言 | 是（测试） |
| ❌-2 | 「口令只存哈希，不存明文」不实（默认明文 `APP_PASSWORD=123456`，哈希为可选且未启用） | `SPEC_content.json` → `s11_security` 该行文本 | 否 |
| ❌-3 | 四级名称「安全/严重」≠ 代码/大屏的「正常/严重报警」 | `SPEC_diagrams.json` `s07_risk` 的 `rl_c1n`/`rl_c4n` + `SPEC_content.json` `s07_risk` 文案与 notes + `BUILD_SPEC.md:141` | 否 |
| ❌-4 | 第 8 页 2/6 条 reason 示例与 `rules.py:120` / `app.py:210` 实际输出不符 | `SPEC_diagrams.json` → `s08_rules` 两个元素文本 | 否 |

⚠️ 6 条中，**⚠️-1（three-boot.js 的 unpkg 兜底）与 ⚠️-2（132/144 两点引擎与大屏边界含入不一致）** 建议准备口头答法；⚠️-3/4/5/6 为低危口径与排版提示。

**改完后必须重建并重新冻结**：本报告的全部结论绑定 SHA256 `69E3294A9F668C4084792D0C17F96D924055B86B5D859B2E96BB1D0C9E8B8352`；一旦 `build_deck.py` 重跑，该指纹失效，需重新计算指纹并至少复跑「章节 1.7 一致性 + 1.8 红线 + ❌-1 的 10 次全量测试」。

---

*核验员：fact-checker ｜ 报告生成于 2026-10-09 19:58（本机）｜ 全部结论均可用本文列出的「文件:行号」或「命令 + 原始输出」复核，无一处基于推测。*

---
---

# 附：收口后复验（第二轮）

## 0. 被核验文件 / 指纹 / 时间

| 项 | 值 |
|---|---|
| **被核验文件名** | `桥体卫士答辩PPT_v2/桥体卫士答辩PPT_12分钟版.pptx`（**交付名，修正版已写入该名**） |
| **自算 SHA256（核验前）** | `8C0BC84D9766DC5B5D1FDFDACEBC5E6456FEA69DD085339BE3708CD03849064D` |
| **自算 SHA256（核验后，一字未变）** | `8C0BC84D9766DC5B5D1FDFDACEBC5E6456FEA69DD085339BE3708CD03849064D` → **核验期间未被改动 ✅** |
| 字节数 / 页数 | 91,663 bytes / 15 页 |
| 文件 mtime | 2026-10-09 19:52:32 |
| 复验时间 | 2026-10-09 19:52 – 19:57（本机） |
| 与 Lead 下发指纹是否一致 | `MATCH = True`（Lead 下发 `8C0BC84D…49064D`） |
| 本轮文本提取物（本人重新生成） | `_work/pptx_text_r4.txt`（1,356 行，python-pptx + 独立 raw-XML `<a:t>` 双通道） |

### 指纹变更史（本人实测，共 5 个版本；此前 4 个均已作废）

| 版本 | SHA256 | bytes | mtime | 处置 |
|---|---|---:|---|---|
| R1（第一轮冻结） | `69E3294A…BC4CDF` | 91,761 | 19:39:58 | 第一至四节全量核验基准 |
| 中间版 ① | `BD97178C…EAA91C0` | 91,778 | 19:48:58 | 曾短暂位于交付名 |
| 中间版 ② | `4E0C5F5C…ABDB26C` | 91,705 | 19:50:34 | `_work/…CORRECTED.pptx` |
| R2 | `634761E5…3481866E` | 91,705 | 19:50:51 | 复验中被 R3 取代 |
| R3 | `24921A15…AE75223C` | 91,665 | 19:51:54 | 复验中被 R4 取代 |
| **R4（本复验节基准）** | **`8C0BC84D…49064D`** | **91,663** | **19:52:32** | **最终交付版** |

> 补充实测：中间版 ① `BD97178C`、中间版 ② `4E0C5F5C`、R2 `634761E5` 三者**可见文本与 notes 完全相同**（逐行 diff 仅差异 dump 头部路径行 1 行，`differing lines = 1`），字节差异来自 ZIP 内嵌时间戳，非内容差异。故前三次改动在内容层面是一次性生效的，后续指纹变化均为重建噪声。

### 本轮实跑命令

```powershell
# ① 指纹（核验前后各一次）
Get-FileHash -Algorithm SHA256 "桥体卫士答辩PPT_v2\桥体卫士答辩PPT_12分钟版.pptx"

# ② 干净提取
& $py -X utf8 "桥体卫士答辩PPT_v2\_work\fc_extract.py" `
     "桥体卫士答辩PPT_v2\桥体卫士答辩PPT_12分钟版.pptx" `
     "桥体卫士答辩PPT_v2\_work\pptx_text_r4.txt"

# ③ 规格逐字一致性 + 红线扫描
& $py -X utf8 "桥体卫士答辩PPT_v2\_work\fc_consistency.py" "...\桥体卫士答辩PPT_v2" `
     "...\桥体卫士答辩PPT_v2\桥体卫士答辩PPT_12分钟版.pptx"

# ④ 三个校验器
& $py -X utf8 "桥体卫士答辩PPT_v2\check_spec.py"
& $py -X utf8 "桥体卫士答辩PPT_v2\build_deck.py" --check
& $py -X utf8 "桥体卫士答辩PPT_v2\verify_deck.py"
```

---

## 1. 点一：9 类收口改动是否真实落到 PPTX

### 1.1 ✅ 已完全落地（7 类）

| # | 改动 | 结论 | 证据（R4 可见文本行号 / SPEC 元素） |
|---|---|---|---|
| 1 | **❌-2 口令说法** | ✅ **完全落地（正文+notes）** | `pptx_text_r4.txt:741`（p11 正文）`p0: '表单带令牌；口令支持哈希校验存储'`（原「口令只存哈希，不存明文」）；`:733` `p0: 'CSRF 防护 + 口令哈希'`（原「CSRF 防护 + 密码哈希」）；`:773`（notes）「口令支持哈希校验，可用环境变量切换」。扫描 `只存哈希` / `明文` / `密码哈希` → **全文 0 命中**。SPEC 侧：`SPEC_diagrams.json` `figures[10] security_8` → `se_d4r`、`se_d4n` |
| 2 | **❌-4 基线偏移 reason** | ✅ 落地 | `:545`（p8）`p0: '近期均值 118.60 相对基线 96.10 偏移 +22.50，超过阈值 20.00'` —— 已补回 `rules.py:120-121` 的「，超过阈值 %.2f」子句 |
| 3 | **❌-4 设备离线 reason** | ✅ 落地 | `:547`（p8）`p0: '设备失去连接：心跳超时'` —— 与 `app.py:209-210`（`reason = health.get("last_error") or "心跳超时"`）的真实产出逐字一致；原「串口连续超时计数达 10 次」无代码路径 |
| 4 | **❌-4 离线判据条件** | ✅ 落地 | `:535`（p8）`p0: '连续心跳超时 ≥ 10 次：如实判离线'`；扫描 `串口连续超时` → **0 命中** |
| 5 | **⚠️-2 删「同一份数据」** | ✅ 落地 | `:453`（p7）`p0: '等级 → 颜色 → 处置优先级'`（原「…（同一份数据）」）；`:460` `p0: '大屏、仪表、报警行同一套颜色语言。'`（原「同一套分级。」）；`:482` notes「共用同一套颜色语言」。扫描 `同一份数据` → **0 命中** |
| 6 | **R3 三处同源遗漏** | ✅ 落地 | `se_d4r`→`:741`、`se_d4n`→`:733`、`td_kpi_s`→`:792`（p12）`p0: '101 项用例 · 11 个测试文件（10 个 test_*.py + conftest.py）'`（SPEC 原文见 `SPEC_diagrams.json:3983`）、`se_m1r`→`:751`（p11）`p0: '项测试用例 · 11 个测试文件'` |
| 7 | **R4 s12 标题** | ✅ 落地 | `:851`（p12）`p0: '可度量成果 —— 测试覆盖'`（原「可度量成果 —— 测试全绿」）；SPEC 侧 `SPEC_content.json` `slides[11].title`。扫描 `测试全绿` → **全文 0 命中** |

### 1.2 ❌ 未完全落地（1 类，1 处残留）

| # | 改动 | 结论 | 证据 |
|---|---|---|---|
| 8 | **❌-3 四级名称** | ⚠️ **部分落地 → 仍留 1 处 ❌** | 已改：`:437` `p0: '正常'`（原「安全」）、`:443` `p0: '严重报警'`（原「严重」）、`:482` notes「正常、预警、报警、严重报警…1.2 倍判严重报警」**全部正确** ✅<br>**未改：`:464`（p7 正文左栏）`p0: '超过阈值 1.2 倍判严重，'` —— 裸用「严重」作等级名** ❌<br>SPEC 位置：`SPEC_content.json` `slides[6]`（`slide_id: s07_risk`）`elements[5].id = "e4"` 的 `.text`<br>**该处与同页 notes 直接矛盾**：notes 已写「1.2 倍判严重报警」，正文仍写「判严重」。同页两处口径打架，比改动前更易被追问 |

---

## 2. 点二：「0 failed / 0 skipped」是否已从全 PPT 与 notes 中彻底消失

### 2.1 ✅ 目标字符串及其全部同义形态——已彻底消失

对 15 页可见文本 + 15 页 notes（含 raw-XML 镜像）逐一扫描，**全部为 0 命中**：

| 扫描串 | 命中数 |
|---|---|
| `0 failed` | **0** |
| `0 skipped` | **0** |
| `0 失败`（中文形态） | **0** |
| `0 跳过`（中文形态） | **0** |
| `零失败` | **0** |
| `零跳过` | **0** |
| `全部通过` | **0** |
| `测试全绿` | **0** |

对应 3 处原句均已改写：`:759`（p11）→「实跑：101 项用例 · 覆盖规则、数据、鉴权、串口与页面壳」；`:751`（p11 KPI 副标题）→「项测试用例 · 11 个测试文件」；`:792`（p12）→「101 项用例 · 11 个测试文件（10 个 test_*.py + conftest.py）」；notes `:773` / `:859` →「测试套件一共 101 个用例、11 个测试文件」。

### 2.2 ❌ 但**同类「确定性全绿」断言仍残留 1 处**

| 位置 | 原文 | 问题 |
|---|---|---|
| `pptx_text_r4.txt:790`（**第 12 页正文，可见**） | `p0: '101 passed in 15.38s'` | 同时断言两件不可保证的事：**(a) 全部通过**（pytest 只在 0 失败时才输出 `101 passed`）、**(b) 固定耗时 15.38s**。这正是第一轮 ❌-1 的同一缺陷类别，只是换了字符串 |
| SPEC 位置 | `SPEC_diagrams.json` `figures[11]`（`fig_id: tests_dist`，`for_slide: s12_evidence`）`elements[1].id = "td_kpi_v"` 的 `.text` | — |

**反证（第一轮实测，证据见 `_work/flake_repro.txt` / `_work/flake_detail.txt`）**：套件为 **flaky** ——
- 全量 `pytest tests/ -q` **9 次运行 2 次红**（`1 failed, 100 passed in 15.37s` / `15.43s`），失败固定为 `tests/test_mobile_layout.py::test_device_mobile_no_text_overlap[viewport0]`（320×568，`AssertionError: 页面缺失 .dv-3col`）
- 分文件 `pytest tests/test_mobile_layout.py -q` **8 次运行 3 次红**
- 耗时实测区间 **15.19–15.43s**，`15.38s` 是其中一次的快照，非可复现常量

**影响**：该 KPI 大字是第 12 页视觉焦点，评委若要求现场复跑 `pytest tests/ -q`，仍有约 1/5 概率出现红字，与屏幕上的「101 passed」直接冲突。Lead 已治本一半（`_open()` 加就绪等待，复现率 38%→12%），但未根治，**因此不宜在页面上保留确定性「passed」断言**。

---

## 3. 点三：四级名称是否全文统一为「正常 / 预警 / 报警 / 严重报警」

### 3.1 ✅ 等级名（图内 + notes）：已统一

| 位置 | R4 原文 | 判定 |
|---|---|---|
| `:437`（p7 等级卡 1） | `p0: '正常'` | ✅ |
| `:439`（p7 等级卡 2） | `p0: '预警'` | ✅ |
| `:441`（p7 等级卡 3） | `p0: '报警'` | ✅ |
| `:443`（p7 等级卡 4） | `p0: '严重报警'` | ✅ |
| `:482`（p7 notes） | 「风险分四级：**正常、预警、报警、严重报警**，对应绿、黄、橙、红。分级口径统一：超过阈值 1.2 倍判**严重报警**，1.1 倍判报警，其余是预警。」 | ✅ |

### 3.2 ❌ 仍存在 1 处裸用「严重」作等级名

- `pptx_text_r4.txt:464`（**第 7 页正文左栏，可见**）`p0: '超过阈值 1.2 倍判严重，'`
- SPEC 位置：`SPEC_content.json` `slides[6]`（`s07_risk`）`elements[5].id = "e4"` 的 `.text`
- **同页 notes（`:482`）已写「判严重报警」** → 同页正文与讲稿口径不一致

### 3.3 ⚠️ 边界情形 1 处（非等级名，但严格判据会命中）

- `pptx_text_r4.txt:198`（第 4 页，模拟 6 场景枚举）`p0: '正常/预警/报警/严重/离线/恢复'`
- 代码口径 `app.py:47-50` `SCENARIO_LABELS` = `正常运行 / 预警 / 报警 / **严重报警** / 设备离线 / 设备恢复`
- 判定：这是**场景标签的缩写**（对应 `critical`），不是风险等级名；按「不得出现裸用『严重』作为等级名」的字面判据不违规，但若要求「全文任何位置的『严重』都必须带『报警』尾缀」，则此处也算命中。SPEC 位置：`SPEC_diagrams.json` `figures[3]`（`fig_id: source_switch`）`elements[10].id = "ss_l2"`

### 3.4 ✅ 非违规的「安全」出现位置（正确保留，不构成 ❌）

| 行号 | 原文 | 说明 |
|---|---|---|
| `:765`（p11 标题） | `'安全与工程化 —— 能交付的程度'` | 「安全」= security 主题词，非等级名 |
| `:773`（p11 notes） | 「**安全**上，密钥走环境变量、不硬编码…」 | 同上 |
| `:102`（p2 notes） | 「结构健康关乎**安全**」 | 一般语义 |
| `:563`（p8 notes） | 「回到**安全**区才允许再报」 | 一般语义（safe zone） |

---

## 4. 点四：SHA256（核验前后各一次）

```
核验前：8C0BC84D9766DC5B5D1FDFDACEBC5E6456FEA69DD085339BE3708CD03849064D   91,663 bytes
核验后：8C0BC84D9766DC5B5D1FDFDACEBC5E6456FEA69DD085339BE3708CD03849064D   91,663 bytes
结论  ：一致 → 复验期间该文件未被改动 ✅
```

**若 Lead 之后再次替换该文件**，本复验节的全部结论即失效，须以新指纹重跑「§2.2 残留断言扫描 + §3.2 等级名扫描 + 三个校验器」。

---

## 5. 复验节附加核验（本轮新做）

| 检查 | 结论 | 原始输出 |
|---|---|---|
| `check_spec.py` | ✅ `校验结果: 0 error / 0 warn` ＋ `结论: 通过 ✅` | 实跑 |
| `build_deck.py --check`（构建器自带坐标/重叠/字号校验） | ✅ `校验结果: 0 error / 0 warn` | 实跑 |
| `verify_deck.py` | ✅ `结构复核通过 ✅（页数/尺寸/零位图/字号/字体/备注一致性）`；`位图数量: 0（要求 0）`；字体仅 `Segoe UI` 299 处 | 实跑 |
| PPT 可见文本 vs 两份 SPEC（逐字，双向） | ✅ `TOTAL missing = 1 ; TOTAL extra = 0` —— 唯一差异为 `s07_risk` 的 `rl_chart.series[0].name = "示意波形"`，因 `build_deck.py:950-952` 图例仅在序列数 > 1 时绘制，单序列图无渲染路径（**非缺陷**，见第一轮 ⚠️-6） | `_work/fc_consistency_r4.txt` |
| notes vs SPEC notes（逐字） | ✅ `notes mismatched slides = 0 / 15` | 同上 |
| 红线禁词 16 项 | ✅ 全部 `clean`（0 命中） | 同上 |
| 「工程级」限定 | ✅ 全文 1 次，位于 p13 `'未做工程级标定与量值溯源'`（允许），`disallowed = 0` | 同上 |
| 「3D」限定 | ✅ 全文 0 次，`narrative(disallowed) = 0` | 同上 |
| 「压力传感器」/「ESP32」位置 | ✅ `压力传感器` 0 次；`ESP32` 仅 p3「ESP32 + 传感器（现场不接实物）」 | 同上 |

---

## 6. 复验后剩余问题汇总

### ❌ 剩余 **2** 条（均为「改一处文案」即可，不涉及代码）

| ❌ | 一句话 | 精确修改位置（请 Lead 改，我不动规格） |
|---|---|---|
| **❌-A** | 第 12 页仍断言「101 passed in 15.38s」——套件 flaky 时会被现场复跑打脸，且 15.38s 是快照非常量 | `SPEC_diagrams.json` → `figures[11]`（`fig_id: tests_dist`，`for_slide: s12_evidence`）→ `elements[1].id = "td_kpi_v"` 的 `text`。建议改为可稳定复现的量，如 `'101 项用例'` 或 `'101 项用例 · 11 个测试文件'`（与本页已改好的 `td_kpi_s`、左栏 `101 项用例 · 11 个文件` 同口径） |
| **❌-B** | 第 7 页正文仍裸用「严重」作等级名，与同页 notes 的「严重报警」自相矛盾 | `SPEC_content.json` → `slides[6]`（`s07_risk`）→ `elements[5].id = "e4"` 的 `text`：`'超过阈值 1.2 倍判严重，'` → `'超过阈值 1.2 倍判严重报警，'` |

> ❌-A 已确认为**唯一**未收口的测试类断言（`0 failed` / `0 skipped` / `零失败` / `零跳过` / `全部通过` / `测试全绿` 六个形态全部 0 命中，Lead 的收口在这六个上是彻底的）。

### ⚠️ 剩余 **7** 条

**沿用第一轮、Lead 已记录不改（4 条）**：

| ⚠️ | 摘要 | 证据 |
|---|---|---|
| ⚠️-1 | `static/js/three-boot.js` 仍保留 unpkg CDN 兜底代码 | `three-boot.js:37` `var CDN_ROOT = 'https://unpkg.com/three@' + VERSION + '/';`、`:38-39` CDN_THREE/CDN_ORBIT、`:185` 「CDN 兜底策略 2」（主路径本地化、README 断网实测 `fallbackUsed:false`） |
| ⚠️-3 | 「参数集中在 rules.py」不含设备离线参数 `offline_after=10` | `pptx_text_r4.txt:551`（p8）原句仍在；`offline_after` 仅见 `datasource.py:137,141,250,257`（p8 卡片条件已改为「连续心跳超时」，措辞不再指向单一文件） |
| ⚠️-4 | p5 同页「主跨 1420 m」/「主跨 1420m」两种排版 | `:295` 与 `:300`（Lead 说明为轴标注/正文有意区分，保留） |
| ⚠️-6 | `示意波形` 规格字段无渲染路径 | `build_deck.py:950-952`；`TOTAL missing = 1`（非缺陷） |

**本轮新增（3 条，均低危）**：

| ⚠️ | 摘要 | 证据 |
|---|---|---|
| ⚠️-N1 | 基线偏移 reason 示例丢掉末尾「（相对应变指标）」，与 `rules.py:120-121` 仍非逐字 | `pptx_text_r4.txt:545` 现为 `'近期均值 118.60 相对基线 96.10 偏移 +22.50，超过阈值 20.00'`；同页其余 5 条示例（`:537/:539/:541/:543`）**都带**该括注，仅此条因卡片宽度被删（Lead 说明为放不下）。实体错误已修正，仅剩格式不齐 |
| ⚠️-N2 | p4 场景枚举中「严重」为缩写（代码 `SCENARIO_LABELS` 为「严重报警」） | `pptx_text_r4.txt:198` `'正常/预警/报警/严重/离线/恢复'`；`app.py:47-50`。属场景标签非等级名（见 §3.3） |
| ⚠️-N3 | `SPEC_diagrams.json` `figures[11]._note` 仍写已废弃的旧口径（规格卫生，**非渲染字段**） | `SPEC_diagrams.json:3946` `"只报已核实总数（101 passed in 15.38s、0 failed / 0 skipped、11 个测试文件 = 10 个 test_*.py + conftest.py）…"` —— 与正文现值已不一致，建议随手更新以免下轮再传抄 |

---

## 7. 复验结论

### **❌ 剩余 2 条；改完这 2 处文案即可答辩。**

- **已彻底收口（7 类）**：❌-2 口令说法（正文+notes，6 个扫描形态 0 命中）、❌-4 两条 reason（含离线判据条件）、⚠️-2「同一份数据」、R3 三处同源遗漏、R4 的 s12 标题「测试覆盖」。加上第一轮已验证通过的技术主体与 42 项事实，**内容层面已无其他待改项**。
- **仅剩 2 处文案**：第 12 页 KPI `101 passed in 15.38s`（改为不含「passed/耗时」的口径）＋ 第 7 页正文「判严重」→「判严重报警」。两处都在规格文件的单一 `text` 字段，改完重建即完成。
- **校验器全绿**：`check_spec.py` / `build_deck.py --check` / `verify_deck.py` 三者均 0 error / 0 warn，PPT 可见文本与 SPEC 逐字一致（仅 1 处已解释的非缺陷差异），红线 16 禁词 0 命中、「工程级」1 处且为允许的否定句、「3D」0 处。
- **诚实提示**：第 12 页保留「101 项用例」这一**可稳定复现**的计数是正确取舍（第一轮实测 101 收集数每次一致）；而「passed」「全绿」「0 failed」这类会被现场复跑推翻的断言已基本清除，**只剩 `td_kpi_v` 一处**。

*复验员：fact-checker ｜ 复验节生成于 2026-10-09 19:57（本机）｜ 基准指纹 `8C0BC84D9766DC5B5D1FDFDACEBC5E6456FEA69DD085339BE3708CD03849064D`（91,663 bytes）｜ 全部结论均可用本文列出的「文件:行号」或「命令 + 原始输出」复核。*

---

## 附：第三轮确认（最终）

### 0. 被核验文件 / 指纹 / 时间

| 项 | 值 |
|---|---|
| **被核验文件名** | `桥体卫士答辩PPT_v2/桥体卫士答辩PPT_12分钟版.pptx`（交付名） |
| **自算 SHA256（核验前 / 核验后）** | 核验前 `DAD6921B8084213ECF4BA6AECCE4C3BCE536C5C6A0938875A0706C89B0160391`<br>核验后 `DAD6921B8084213ECF4BA6AECCE4C3BCE536C5C6A0938875A0706C89B0160391` → **一致，核验期间未被改动 ✅** |
| 字节数 / 页数 | 91,666 bytes / 15 页 |
| 文件 mtime | 2026-10-09 19:54:27 |
| 复验时间 | 2026-10-09 19:54 – 20:02（本机） |
| 与 Lead 下发指纹是否一致 | `MATCH = True` |
| 文本提取物（本人重新生成） | `_work/pptx_text_r6.txt`（1,356 行，python-pptx + 独立 raw-XML `<a:t>` 双通道） |

> 本轮实际经历两次指纹变更，均在本次确认窗口内，均已核：**R5 = `BA5C91B5…DDF5D9`（91,649 bytes，19:53:48）** 被 **R6 = `DAD6921B…60391`（91,666 bytes，19:54:27）** 取代。R5 的三处改动已在 R6 中复查仍然生效（见 §1），故最终结论以 R6 为准。
> 至此累计实测 7 个构建版本：`69E3294A` → `BD97178C` → `4E0C5F5C` → `634761E5` → `24921A15` → `8C0BC84D` → `BA5C91B5` → **`DAD6921B`（交付版）**。

### 1. 两轮改动是否落到 PPTX

**(a) R5 三处（在 R6 中复查仍生效）**

| # | 元素 | 结论 | R6 实测 |
|---|---|---|---|
| a1 | `SPEC_diagrams.json` `figures[11]`(`tests_dist`) `elements[1].id="td_kpi_v"` | ✅ 仍生效 | PPT 第 12 页 `pptx_text_r6.txt:790` `p0: '101 项用例'`（原「101 passed in 15.38s」） |
| a2 | `SPEC_content.json` `slides[6]`(`s07_risk`) `elements[5].id="e4"` | ✅ 仍生效 | 第 7 页 `:464` `p0: '超过阈值 1.2 倍判严重报警，'`（原「…判严重，」） |
| a3 | `SPEC_diagrams.json` `figures[11]._note`（非渲染） | ✅ 已更新 | JSON 现值：「…只报可稳定复现的计数（101 项用例、11 个测试文件 = 10 个 test_*.py + conftest.py）。**不写 passed/耗时/0 failed 这类单次快照断言**（套件含一个 headless 浏览器用例，存在间歇性 flake）。」—— 其中 `passed`/`0 failed` 两串位于「**不写**…这类断言」的否定从句内，属正确表述，**非残留** |

**(b) R6 两处 notes**

| # | 元素 | 结论 | R6 实测 |
|---|---|---|---|
| b1 | `s07_risk` notes：删「分级口径**统一**」 | ✅ 落地且与代码吻合 | `:482`（p7 notes）现为「风险分四级：正常、预警、报警、严重报警，对应绿、黄、橙、红。**分级口径是**：超过阈值 1.2 倍判严重报警，1.1 倍判报警，其余是预警。…」。`分级口径统一` / `口径统一` 在 **s07 已 0 命中**；新措辞与 `rules.py:42-46`（`>=` 语义）**逐字吻合** ✅。Lead 修正理由成立：引擎 `rules.py:42-44` 用 `>=`，而 `templates/dashboard.html:626-627` 与 `templates/trend.html:231-232` 的 `riskOf()` 用 `<=`，132/144 两点口径确实不同，不应说「统一」 |
| b2 | `s12_evidence` notes：「三端用的是同一份生效参数」→ 历史页动态拉取 | ✅ 落地且与代码吻合 | `:859`（p12 notes）现为「…另外，**历史页会动态拉取当前生效阈值，超限统计和阈值线跟设置页保持一致**。每个结论都能用源码、测试输出或现场演示复核。」。可核依据：`templates/history.html:131` `let currentThreshold = {{ threshold }};`、`:275-281` `loadThreshold()` 内 `fetch('/api/settings')` → `currentThreshold = s.threshold`、`:218` 超限统计用 `currentThreshold`、`:263` markLine 用 `currentThreshold`。**`同一份生效参数` 形态全文 0 命中** ✅ |

### 2. ❌ 本轮发现的新残留 **1 条**（与 b2 同源，幻灯片正文没跟上）

| 项 | 内容 |
|---|---|
| **位置（可见文本）** | `pptx_text_r6.txt:843`（**第 12 页正文左栏「口径一致」卡片**）`p0: '数据、阈值、历史三端用同一生效参数。'`（卡片标题 `:841` 为 `'口径一致'`） |
| **SPEC 位置** | `SPEC_content.json` → `slides[11]`（`slide_id: s12_evidence`）→ `elements[6].id = "e5"` 的 `.text` |
| **为什么是 ❌** | 这正是 Lead 在 b2 中判定为「**过头表述**」并已从 notes 删除的同一句话。notes 已改为「历史页会动态拉取当前生效阈值…跟设置页保持一致」，而**幻灯片正文仍写「三端用同一生效参数」** → **同一页正文与讲稿自相矛盾**，现场照念会与屏幕文字冲突。Lead 的自查模式 `同一份生效参数`（带「份」）**匹配不到**实际字符串 `同一生效参数`（无「份」），故漏检——与此前 `15.38`/`判严重` 两次漏检同类的「模式与实体串不一致」问题 |
| **可核反证** | 三端确实同源于 `simulator.latest["threshold"]`（`app.py:393,412,421,429,437` 渲染期传入 + `:451` `/api/data` + `:498` `/api/settings`），但**并非实时一致**：`templates/trend.html:201` `var INITIAL_THRESHOLD = {{ threshold }};` 为**渲染时快照**，`:375` 阈值 markLine 与 `:377` 标签都用 `INITIAL_THRESHOLD`，且 trend.html 内**没有** `loadThreshold()` 调用（全文无 `/api/settings`）——即设置页改阈值后，趋势页阈值线会停留在旧值。`history.html` 才有动态拉取（`:275-289`，但亦仅在页面加载时调用一次 `:289`，非持续轮询） |
| **最小修复建议**（请 Lead 改，我不动规格） | `SPEC_content.json` → `slides[11]`（`s12_evidence`）→ `elements[6].id = "e5"` 的 `.text`，与 notes 对齐，例如改为 `'阈值与历史口径对齐设置页。'` 或 `'历史页动态拉取当前生效阈值。'`（卡片宽 4,921,000 EMU，11pt 下上述任一串均放得下）。**注意**：`elements[6]` 的 id 为 `e5`（标题 `'口径一致'` 为 `elements[5]`），改时勿错位 |

### 3. 模式复扫（确认无其他新的同类残留）

对 15 页可见文本 + 15 页 notes + raw-XML 镜像，按 **39 个模式**复扫（结果原始输出留存于本次会话记录）：

**(i) 全绿 / 单次快照类 —— 全部 0 命中（含 raw 镜像）** ✅
`15.38` · `101 passed` · `passed in` · `全绿` · `0 failed` · `0 skipped` · `0 失败` · `0 跳过` · `零失败` · `零跳过` · `全部通过`

**(ii) 口径类 —— 全部 0 命中** ✅
`只存哈希` · `明文` · `密码哈希` · `同一份数据` · `同一份生效参数` · `分级口径统一` · `串口连续超时` · `判严重，`

**(iii) 红线 —— 全部 0 命中** ✅
16 禁词（`数字孪生`/`机器学习`/`人工智能`/`大数据`/`微应变`/`高精度`/`工程级精度`/`真实桥梁应变监测`/`我们`/`团队`/`领先`/`革命性`/`预测`/`深度学习`/`智能算法` + `AI`）+ `3D` 均 0 命中

**(iv) 有可见命中的 4 个模式 —— 逐一确认，均非新问题**：

| 模式 | 命中 | 判定 |
|---|---|---|
| `口径统一` | `:712`（p10 notes）「时间、设备号、来源、状态这些**字段口径统一**」 | ✅ **合规**：`db.py:17-66` `SCHEMA` 五表统一用 `ts`，`device_id`/`source` 在三表同名同义，字段口径确实统一。与 s07 已删的「分级口径统一」不是同一命题 |
| `正常/预警/报警/严重/离线/恢复` | `:198`（p4） | ⚠️-N2（`app.py:47-50` 场景标签缩写，非等级名）—— 已记录 |
| `参数集中在 rules.py` | `:551`（p8） | ⚠️-3（不含 `offline_after`）—— 已记录，Lead 决定不改 |
| `主跨 1420` | `:295`/`:300`/`:326` | ⚠️-4（轴标注/正文有意区分）—— 已记录，Lead 决定保留 |

> **结论：除 §2 的 1 条外，无其他新的同类残留 ✅。**

### 4. 附加核验（本轮实跑）

| 检查 | 结论 | 原始输出 |
|---|---|---|
| `check_spec.py` | ✅ `校验结果: 0 error / 0 warn` ＋ `结论: 通过 ✅` | 实跑 |
| `build_deck.py --check` | ✅ `校验结果: 0 error / 0 warn` | 实跑 |
| `verify_deck.py` | ✅ `结构复核通过 ✅（页数/尺寸/零位图/字号/字体/备注一致性）` | 实跑 |
| PPT 可见文本 vs 两份 SPEC（逐字双向） | ✅ `TOTAL missing = 1 ; TOTAL extra = 0`（唯一差异 `示意波形`，单序列不画图例，**非缺陷**，⚠️-6） | `_work/fc_consistency_r5.txt`（R6 复查一致） |
| notes vs SPEC notes | ✅ `notes mismatched slides = 0 / 15` | 同上 |
| 红线专项 | ✅ 16 禁词全 `clean`；`工程级` 全文 1 处 = p13 `'未做工程级标定与量值溯源'`（`disallowed = 0`）；`3D` 0 处；`压力传感器` 0 处；`ESP32` 仅 p3 | 同上 |
| 讲稿预算（Lead 报 s07 136/202、s12 151/225） | ✅ 与 `build_deck.py --check` 逐页输出一致 | 实跑 |
| SHA256 前后一致 | ✅ `DAD6921B…60391`（91,666 bytes）核验前后一字未变 | 实跑 |

### 5. 最终结论

### **❌ 剩余 1 条（第 12 页正文 `e5`），⚠️ 剩余 6 条。**

**改掉 §2 的 `e5` 一处文案，即可走最终交付。**

| 项 | 状态 |
|---|---|
| ❌ 必须修 | **1** —— `SPEC_content.json` `slides[11]` `s12_evidence` `elements[6].id="e5"`：`'数据、阈值、历史三端用同一生效参数。'` → 与 notes 对齐的窄口径（如 `'阈值与历史口径对齐设置页。'`） |
| ❌ 历史四条（第一轮） | **全部收口** ✅：❌-1（测试断言）· ❌-2（口令）· ❌-3（四级名称）· ❌-4（两条 reason） |
| ⚠️ 存疑/口径提示 | **6**：⚠️-1（`three-boot.js:37-39,185` unpkg CDN 兜底）· ⚠️-3（「参数集中在 rules.py」不含 `offline_after`）· ⚠️-4（「1420 m」/「1420m」两种排版）· ⚠️-6（`示意波形` 无渲染路径）· ⚠️-N1（基线偏移示例末缺「（相对应变指标）」）· ⚠️-N2（p4 场景标签「严重」缩写）。**⚠️-N3 已于 R5 闭环** |
| ✅ 第一轮 42 项事实核验 | 全部通过，未受后续改动影响（19 路由 / 6 模块约 1500 行 / 五表五字段三索引 / 6 类规则与全部默认参数 / 双模式与 6 场景 / 401 / CSRF / .env / three.js r160 与 OrbitControls 本地化及 sha256 / 5 个预设视角 / 线框与标注开关 / 涟漪联动 / 二维降级 / UA 302 与 ≤768px / ECharts 本地化） |
| 校验器 | `check_spec.py` / `build_deck.py --check` / `verify_deck.py` 三者 **0 error / 0 warn / 结构复核通过** |
| 内容一致性 | PPT 可见文本 vs 两份 SPEC **逐字一致**（1 处已解释的非缺陷差异）；notes **15/15** 逐字一致 |
| 红线 | 16 禁词 0 命中；「工程级」仅 1 处且为 s13 允许的否定句；「3D」0 处；硬件口径仅出现在允许位置 |
| 可被现场推翻的断言 | 已全部清除 ✅ —— `passed` / `耗时` / `0 failed` / `全绿` / `全部通过` 0 命中，仅保留可稳定复现的「101 项用例」（第一轮实测 `101 tests collected` 每次一致） |

**答辩口头准备（沿用）**：⚠️-1（被问「是否完全不依赖外网」时承认存在最后一级 CDN 兜底分支，主路径本地化且断网实测 `fallbackUsed:false`）；⚠️-3（被问「参数都在 rules.py 吗」时答「5 类采样值规则在 rules.py，设备离线 `offline_after` 在 `datasource.py:137`」）。修掉 `e5` 后，第 7 页与第 12 页的**正文与讲稿将完全同口径**，无自相矛盾点。

*最终确认：fact-checker ｜ 2026-10-09 20:02（本机）｜ 基准指纹 `DAD6921B8084213ECF4BA6AECCE4C3BCE536C5C6A0938875A0706C89B0160391`（91,666 bytes）｜ 核验前后指纹一致。若该文件再次被替换，本节结论即失效，须以新指纹复跑 §3 的 39 模式复扫 + §4 的三个校验器。*

---

## 附：终版确认（`BF03F5AB`）

### 0. 被核验文件 / 指纹

| 项 | 值 |
|---|---|
| **文件名** | `桥体卫士答辩PPT_v2/桥体卫士答辩PPT_12分钟版.pptx`（交付名） |
| **自算 SHA256（前 / 后）** | 前 `BF03F5ABC2038BF89F84C75596E4C0592148D418D1964BD719255D48081F8408`<br>后 `BF03F5ABC2038BF89F84C75596E4C0592148D418D1964BD719255D48081F8408` → **一致，未改动 ✅** |
| 字节数 / 页数 / mtime | 91,659 bytes / 15 页 / 2026-10-09 19:55:55 |
| 确认时间 | 2026-10-09 19:56 – 20:06（本机） |
| 与 Lead 下发一致 | `MATCH = True` |
| 提取物 / 扫描脚本 | `_work/pptx_text_r7.txt` · `_work/fc_final_sweep.py` · `_work/fc_final_sweep_out.txt` · `_work/fc_consistency_r7.txt` |

### 1. 两处改动落地

| 元素 | 结论 | 终版实测 |
|---|---|---|
| `SPEC_content.json` `slides[11]`(`s12_evidence`) `elements[6].id="e5"` | ✅ | `pptx_text_r7.txt:843`（p12）`p0: '阈值与历史口径对齐设置页。'`（原「数据、阈值、历史三端用同一生效参数。」）；`数据、阈值、历史三端` 0 命中；`三端` 通配 0 命中 |
| 同卡片 `elements[5].id="e4"`（标题） | ✅ | `:841`（p12）`p0: '阈值口径同步'`（原「口径一致」）；`口径一致` 通配 **0 命中** |

### 2. 通配复扫（教训修正：用 `同一.{0,4}生效参数` 而非定长串）

**结果：0 命中 ✅** —— `同一.{0,4}生效参数` / `同一.{0,2}参数` / `口径一致` / `分级口径统一` / `三端` / `同一份.{0,6}` / `同一份生效` 全部 visible=0（raw 镜像亦 0）。即 `同一生效参数`（无「份」）与 `同一份生效参数`（有「份」）两种形态**均已消失**。

全绿/快照类通配（`15\.38` / `passed` / `全绿` / `0\s*failed` / `0\s*skipped` / `0\s*失败` / `0\s*跳过` / `零失败` / `零跳过` / `全部通过`）**全部 0 命中**；`判严重，` / `只存哈希` / `密码哈希` / `串口连续超时` / `同一份数据` 亦 **0 命中**。

唯一命中：`口径统一` → `:712`（p10 notes）「时间、设备号、来源、状态这些**字段口径统一**」= **合规**（`db.py:17-66` `SCHEMA` 五表确实统一用 `ts`，`device_id`/`source` 三表同名同义；与 s07 已删的「分级口径统一」不是同一命题）。与 Lead 自查结论一致。

### 3. 39 模式复扫（终版重跑）

有可见命中的 **4** 个模式，**全部为此前已记录项，无新增**：

| 模式 | 命中 | 判定 |
|---|---|---|
| `口径统一` | `:712`（p10 notes） | ✅ 合规（见 §2） |
| `正常/预警/报警/严重/离线/恢复` | `:198`（p4） | ⚠️-N2（`app.py:47-50` 场景标签缩写，非等级名） |
| `参数集中在 rules.py` | `:551`（p8） | ⚠️-3（不含 `offline_after`） |
| `主跨 1420` | `:295`/`:300`/`:326` | ⚠️-4（轴标注/正文有意区分） |

其余 35 个模式（全绿类 11 + 口径类 8 + 16 禁词 + `3D`）**全部 0 命中**。

### 4. 校验器与一致性（终版）

`check_spec.py` **0 error / 0 warn，结论通过 ✅** · `build_deck.py --check` **0 error / 0 warn** · `verify_deck.py` **结构复核通过 ✅**；PPT 可见文本 vs 两份 SPEC `TOTAL missing = 1 / extra = 0`（唯一差异 `示意波形`，单序列无图例，非缺陷）；notes **15/15** 逐字一致；红线 16 禁词全 `clean`、`工程级` 1 处（p13 允许否定句，`disallowed = 0`）、`3D` 0 处、`ESP32` 仅 p3。

### 5. 结论

### **❌ 剩余 0 条 —— 准予最终交付。**

第一轮 4 条 ❌（❌-1 测试断言 / ❌-2 口令 / ❌-3 四级名称 / ❌-4 两条 reason）与第二、三轮新增的 3 条（❌-A `td_kpi_v` / ❌-B `s07 e4` / `e5` 三端表述）**全部闭环**。第一轮 42 项事实核验结论不受后续改动影响，仍然成立。

剩余 **6 条 ⚠️** 均为已记录、Lead 已判定保留或不改的口径提示（⚠️-1 CDN 兜底 · ⚠️-3 `offline_after` 位置 · ⚠️-4「1420 m」/「1420m」排版 · ⚠️-6 `示意波形` 无渲染路径 · ⚠️-N1 基线偏移示例末缺括注 · ⚠️-N2 p4 场景标签缩写），不影响交付；建议准备 ⚠️-1 与 ⚠️-3 两条口头答法。

*终版确认：fact-checker ｜ 2026-10-09 20:06（本机）｜ 基准指纹 `BF03F5ABC2038BF89F84C75596E4C0592148D418D1964BD719255D48081F8408`（91,659 bytes）｜ 核验前后指纹一致。本报告全部结论绑定该指纹；文件一旦再被替换即失效。*
