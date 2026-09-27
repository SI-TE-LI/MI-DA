# -*- coding: utf-8 -*-
"""
把 辰/ 文件夹（含所有子文件夹）下的所有 .txt 转换成兼容 SCP 站点的 .js
并在 output.txt 中输出可直接粘贴进 index.html 的目录 HTML 代码。
"""

import os

# ============ 可配置项 ============
FOLDER = '辰'
ENCODING_TRY = ('utf-8-sig', 'utf-8', 'gbk', 'gb18030')
# =================================


def read_text(path):
    for enc in ENCODING_TRY:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def escape_html(s):
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;'))


def escape_js_template(s):
    return (s.replace('\\', '\\\\')
             .replace('`', '\\`')
             .replace('${', '\\${'))


def escape_attr(s):
    """HTML 属性值转义，主要处理双引号"""
    return s.replace('&', '&amp;').replace('"', '&quot;')


def txt_to_html(text, title):
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    html_parts = [f'<h1>{escape_html(title)}</h1>']

    idx = 0
    if lines and lines[0].strip() == title:
        idx = 1

    paragraphs = []
    current = []
    for line in lines[idx:]:
        if line.strip() == '':
            if current:
                paragraphs.append('\n'.join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append('\n'.join(current))

    for p in paragraphs:
        s = p.strip()
        if s.startswith('#'):
            level = len(s) - len(s.lstrip('#'))
            level = max(1, min(level, 6))
            html_parts.append(f'<h{level}>{escape_html(s[level:].strip())}</h{level}>')
        elif s.startswith('>'):
            html_parts.append(f'<blockquote><p>{escape_html(s.lstrip(">").strip())}</p></blockquote>')
        elif s in ('---', '***', '___'):
            html_parts.append('<hr>')
        else:
            escaped = escape_html(p).replace('\n', '<br>')
            html_parts.append(f'<p>{escaped}</p>')

    return '\n'.join(html_parts)


def collect_groups(folder_path, project_root):
    """递归扫描，返回 [(group_name, [(title, data_src), ...]), ...]"""
    groups = []

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.'))

        txts = sorted(f for f in files if f.lower().endswith('.txt'))
        if not txts:
            continue

        rel_dir = os.path.relpath(root, folder_path)

        if rel_dir == '.':
            # txt 直接放在 辰/ 下，集合名就用 "辰"
            group_name = os.path.basename(folder_path)
        else:
            # 集合名 = 相对于 辰 的路径（用 / 分隔）
            group_name = rel_dir.replace('\\', '/')

        children = []
        for name in txts:
            title = os.path.splitext(name)[0]
            rel_path = os.path.relpath(os.path.join(root, name), project_root)
            data_src = os.path.splitext(rel_path)[0].replace('\\', '/')
            children.append((title, data_src))

        groups.append((group_name, children))

    return groups


def build_toc_html(groups):
    """根据分组数据生成可以直接粘贴进 HTML 的目录代码"""
    lines = []
    lines.append('<ul class="toc-tree">')

    for gi, (group_name, children) in enumerate(groups):
        is_first_group = (gi == 0)
        group_cls = 'toc-group open' if is_first_group else 'toc-group'

        lines.append(f'    <li class="{group_cls}">')
        lines.append(f'        <div class="toc-parent"><span class="parent-text">{escape_html(group_name)}</span></div>')
        lines.append(f'        <ul class="toc-children">')

        for ci, (title, data_src) in enumerate(children):
            is_first_child = (is_first_group and ci == 0)
            child_cls = 'toc-child active' if is_first_child else 'toc-child'
            lines.append(
                f'            <li><a href="#" class="{child_cls}" '
                f'data-src="{escape_attr(data_src)}">{escape_html(title)}</a></li>'
            )

        lines.append(f'        </ul>')
        lines.append(f'    </li>')

    lines.append('</ul>')
    return '\n'.join(lines)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    folder_path = os.path.join(project_root, FOLDER)
    output_path = os.path.join(project_root, 'output.txt')

    if not os.path.isdir(folder_path):
        print('找不到文件夹：', folder_path)
        return

    # ---------- 第一步：生成 js ----------
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for name in sorted(files):
            if not name.lower().endswith('.txt'):
                continue

            txt_path = os.path.join(root, name)
            base_name = os.path.splitext(name)[0]
            rel_path = os.path.relpath(txt_path, project_root)
            rel_key = os.path.splitext(rel_path)[0].replace('\\', '/')

            try:
                text = read_text(txt_path)
            except Exception:
                continue

            html = txt_to_html(text, base_name)
            js_content = (
                '// 本文件由 convert.py 自动生成，请勿手动修改\n'
                'window.SCP_ARTICLES = window.SCP_ARTICLES || {};\n'
                f'window.SCP_ARTICLES["{rel_key}"] = '
                f'`{escape_js_template(html)}`;\n'
            )

            js_path = os.path.splitext(txt_path)[0] + '.js'
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(js_content)

    # ---------- 第二步：生成目录 HTML ----------
    groups = collect_groups(folder_path, project_root)
    toc_html = build_toc_html(groups)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(toc_html)

    print('转换完成。')
    print('目录 HTML 已写入：', output_path)
    print()
    print('请打开 output.txt，全选复制，替换 index.html 中')
    print(' <ul class="toc-tree"> ... </ul> 之间的内容。')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()