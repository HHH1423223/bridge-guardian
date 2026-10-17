# static/fonts —— 本地字体目录

规范 2.2.1 / D5 要求 **Inter 本地打包**（拉丁与数字），中文字符走系统字体，
并且**禁止引用任何字体 CDN**（离线红线）。

## 现在缺什么

仓库里还没有 Inter 的 woff2 二进制（构建环境无外网，无法下载）。
`static/css/base.css` 里的 `@font-face` 段落已经写好，但**被注释掉了**；
`--font-ui` / `--font-data` 已把 `"Inter"` 排在字体栈首位，所以：

- 现场机器如果**装过 Inter**（系统字体里有），数字与拉丁字符会自动使用它；
- 没装时回落到 `PingFang SC` / `Microsoft YaHei UI` / `Microsoft YaHei`，功能完全正常，
  只是数字的字形与宽度一致性略差一点。

## 怎么补齐（三步）

1. 把四个字重的文件放进本目录，文件名必须完全一致：

   ```
   static/fonts/Inter-400.woff2
   static/fonts/Inter-500.woff2
   static/fonts/Inter-600.woff2
   static/fonts/Inter-700.woff2
   ```

2. 打开 `static/css/base.css`，把文件开头那段 `@font-face` 的注释标记删掉。
   只打包拉丁子集（`unicode-range` 已写好）：U+0000–00FF、U+0391–03C9、
   U+2000–206F、U+2070–209F、U+2100–214F、U+2212，合计不超过 150KB。

3. 刷新页面，DevTools → Network 里确认四个 woff2 都是 `200`（不是 `404`），
   并且 **没有任何对外的字体请求**。

## 子集化参考命令

```bash
# 需要 fonttools + brotli
pyftsubset Inter-Regular.ttf \
  --flavor=woff2 \
  --output-file=Inter-400.woff2 \
  --unicodes="U+0000-00FF,U+0391-03C9,U+2000-206F,U+2070-209F,U+2100-214F,U+2212"
```

`Inter-500/600/700` 同上，换成对应字重的源文件即可。

## 为什么中文字体不打包

思源黑体每个字重约 8MB，子集化后仍超过 1MB，对现场工控机代价太高，视觉收益有限；
Windows 现场电脑必有微软雅黑，Mac 必有苹方，直接走系统字体即可（规范 2.2.1 理由段）。
