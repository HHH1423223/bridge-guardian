# -*- coding: utf-8 -*-
"""preview.py —— 可信的 PPTX 视觉预览（Lead 专用）

为什么不用 `render --input x.pptx`：
    LibreOffice 的 Office 光栅化通道会把内容按 **1.5× 放大**并从左上角锚定，
    导致 PNG 只显示幻灯片左上约 2/3，肉眼会误判为"版式错乱"。
    该问题对旧 PPT 同样存在（旧文件顶部 1.875in 蓝带实测底边 337px = 1.875×1.5×120），
    因此不是我们文件的问题，而是预览通道的限制（已用标尺实验证实）。

可信通道：
    convert pptx -> pdf（LibreOffice，矢量，尺寸正确）
    render  pdf  -> png（pdfium，1:1）
    标尺实验实测：1in = 120px @120dpi，红块 (0,0,1,1)in 实测 (0,0.53)-(0.99,0.99)in ✅

用法:
    <node> <cli> convert --input deck.pptx --output deck.pdf
    <node> <cli> render  --input deck.pdf  --output-dir preview --dpi 120 [--pages 1,2,3]
"""
import pathlib
import shutil
import subprocess
import sys

NODE = (r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\runtime"
        r"\primary-runtime\dependencies\node\bin\node.exe")
CLI = (r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked"
       r"\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js")


def run(args):
    r = subprocess.run([NODE, CLI] + args, capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip()[:600])
    if r.returncode != 0:
        print("STDERR:", r.stderr.strip()[:800], file=sys.stderr)
    return r.returncode


def main():
    pptx = pathlib.Path(sys.argv[1]).resolve()
    pages = sys.argv[2] if len(sys.argv) > 2 else None
    if pages in ("", "-", "all", "None", "null"):
        pages = None
    dpi = sys.argv[3] if len(sys.argv) > 3 else "120"
    # .pdf 输入已经在矢量层，直接光栅化即可（跳过 convert）
    is_pdf = pptx.suffix.lower() == ".pdf"
    pdf = pptx if is_pdf else pptx.with_suffix(".pdf")
    outdir = pptx.parent / (pptx.stem + "_preview")

    # convert/render 都不接受已存在的输出；旧 pdf 与旧目录必须先清掉，否则 EEXIST
    if not is_pdf and pdf.exists():
        pdf.unlink()
    if outdir.exists():
        shutil.rmtree(outdir)

    if not is_pdf:
        if run(["convert", "--input", str(pptx), "--output", str(pdf)]) != 0:
            return 1
    args = ["render", "--input", str(pdf), "--output-dir", str(outdir), "--dpi", dpi]
    if pages:
        args += ["--pages", pages]
    if run(args) != 0:
        return 1
    print(f"\n预览目录: {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
