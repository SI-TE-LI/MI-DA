# -*- coding: utf-8 -*-
"""
把网站里所有 .txt 文章批量转成 .js，并自动生成目录片段。
用法：把这个文件放到网站根目录（和 index.html 同一层），双击运行。
"""

import os
import re
from pathlib import Path
from collections import OrderedDict

# ============================================================
# ⭐ 关键：强制把工作目录切换到"脚本自身所在的文件夹"
#    无论从哪双击运行，都以脚本所在位置为根目录
# ============================================================
SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)

# ============================================================
# 配置区
# ============================================================
ROOT = Path('.')                      # 网站根目录（= 脚本所在文件夹）
OUTPUT_TOC = '目录片段.html'
FIRST_LINE_AS_TITLE = True

# ⭐ 跳过这些文件夹
SKIP_DIRS = {
    '历史版本',
    'history',
    'backup',
    '备份',
    '.git',
    'node_modules',
    '__pycache__',
}

# ⭐ 额外的兜底保护：如果脚本所在目录看起来像系统目录，直接报警退出
SYSTEM_DIRS = {
    'Windows', 'System32', 'SysWOW64', 'Program Files',
    'Program Files (x86)', 'ProgramData',
}
if any(part in SYSTEM_DIRS for part in SCRIPT_DIR.parts):
    print('❌ 检测到脚本被放在了系统目录：')
    print(f'   {SCRIPT_DIR}')
    print()
    print('请把这个脚本移动到你网站根目录（index.html 所在的文件夹），再运行。')
    print()
    print('按回车键退出...')
    input()
    raise SystemExit(1)

# ============================================================
# 工具函数
# ============================================================
def read_text_auto(path):
    for enc in ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'big5']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    with open(path, 'rb') as f:
        return f.read().decode('utf-8', errors='ignore')


def escape_html(text):
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))


def escape_for_template_literal(text):
    text = text.replace('\\', '\\\\')
    text = text.replace('`', '\\`')
    text = text.replace('${', '\\${')
    return text


def parse_line(line):
    line = line.rstrip()
    if not line:
        return None
    if line.startswith('#### '):
        return f'<h4>{escape_html(line[5:])}</h4>'
    if line.startswith('### '):
        return f'<h3>{escape_html(line[4:])}</h3>'
    if line.startswith('## '):
        return f'<h2>{escape_html(line[3:])}</h2>'
    if line.startswith('# '):
        return f'<h1>{escape_html(line[2:])}</h1>'
    if line.startswith('---'):
        return '<hr>'
    if line.startswith('> '):
        return f'<blockquote>{escape_html(line[2:])}</blockquote>'
    return f'<p>{escape_html(line)}</p>'


def txt_to_html(content, fallback_title):
    lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    non_empty = [l for l in lines if l.strip()]
    if not non_empty:
        return ''

    parts = []
    start_idx = 0

    if FIRST_LINE_AS_TITLE:
        first = non_empty[0].strip()
        first_clean = re.sub(r'^#+\s*', '', first)
        parts.append(f'<h1>{escape_html(first_clean)}</h1>')
        start_idx = 1

    for line in non_empty[start_idx:]:
        html = parse_line(line)
        if html:
            parts.append(html)

    return '\n'.join(parts)


def is_skipped(path):
    rel_parts = path.relative_to(ROOT).parts
    return any(part in SKIP_DIRS for part in rel_parts)


# ============================================================
# 主流程
# ============================================================
def main():
    print(f'📂 工作目录：{SCRIPT_DIR}\n')

    txt_files = []
    skipped_count = 0

    for p in ROOT.rglob('*.txt'):
        if p.name.startswith('.'):
            continue
        if is_skipped(p):
            skipped_count += 1
            continue
        txt_files.append(p)

    if skipped_count > 0:
        print(f'⏭ 已跳过 {skipped_count} 个文件（位于 {", ".join(sorted(SKIP_DIRS))} 等文件夹）\n')

    if not txt_files:
        print('❌ 没找到任何可处理的 .txt 文件')
        print('   请确认脚本和 index.html 在同一层，且 .txt 文件放进了对应子文件夹')
        return

    print(f'🔍 找到 {len(txt_files)} 个 txt 文件\n')

    tree = OrderedDict()
    count = 0

    for txt_path in txt_files:
        rel = txt_path.relative_to(ROOT)
        key = str(rel.with_suffix('')).replace('\\', '/')

        try:
            content = read_text_auto(txt_path)
        except Exception as e:
            print(f'✗ 读取失败 {txt_path}: {e}')
            continue

        title = txt_path.stem
        html = txt_to_html(content, title)
        if not html:
            print(f'⚠ 空文件跳过：{rel}')
            continue

        html_escaped = escape_for_template_literal(html)

        js_content = (
            "window.SCP_ARTICLES = window.SCP_ARTICLES || {};\n"
            f"window.SCP_ARTICLES['{key}'] = `\n{html_escaped}\n`;\n"
        )

        js_path = txt_path.with_suffix('.js')
        try:
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(js_content)
        except Exception as e:
            print(f'✗ 写入失败 {js_path}: {e}')
            continue

        parent = rel.parent
        group_name = parent.name if str(parent) != '.' else '未分类'
        tree.setdefault(group_name, []).append((title, key))

        count += 1
        print(f'✓ {rel}  →  {js_path.relative_to(ROOT)}')

    print(f'\n✅ 共转换 {count} 篇\n')

    toc_lines = ['<ul class="toc-tree">', '']
    for group_name, items in tree.items():
        toc_lines.append(f'    <li class="toc-group">')
        toc_lines.append(f'        <div class="toc-parent"><span class="parent-text">{group_name}</span></div>')
        toc_lines.append(f'        <ul class="toc-children">')
        for title, key in items:
            toc_lines.append(
                f'            <li><a href="#" class="toc-child" data-src="{key}">{title}</a></li>'
            )
        toc_lines.append(f'        </ul>')
        toc_lines.append(f'    </li>')
    toc_lines.append('</ul>')

    toc_html = '\n'.join(toc_lines)

    try:
        with open(OUTPUT_TOC, 'w', encoding='utf-8') as f:
            f.write(toc_html)
        print(f'📖 目录片段已生成：{OUTPUT_TOC}')
        print('   把它整段替换掉 index0.32.html 里的 <ul class="toc-tree">...</ul> 即可')
    except Exception as e:
        print(f'✗ 目录写入失败：{e}')

    print('\n🎉 全部完成！')


if __name__ == '__main__':
    main()
    print('\n按回车键退出...')
    input()