#!/usr/bin/env python3
"""Extract local documents without changing sources; report every discovered file."""
import argparse
import hashlib
import json
from pathlib import Path

EXCLUDE = {'.git', '.svn', 'node_modules', '__pycache__', '.venv', 'venv', '知识卡输出'}
TEXT = {'.txt', '.md', '.markdown', '.mdown', '.csv', '.tsv', '.json', '.yaml', '.yml', '.xml', '.html', '.htm', '.log', '.rst'}

def extract(p):
    ext = p.suffix.lower()
    if ext in TEXT:
        raw = p.read_bytes()
        for enc in ('utf-8-sig', 'utf-16', 'gb18030'):
            try:
                value = raw.decode(enc)
                return '\n'.join(f'L{i}: {line}' for i, line in enumerate(value.splitlines(), 1))
            except UnicodeError:
                continue
        raise ValueError('无法可靠解码文本')
    if ext == '.docx':
        from docx import Document
        from docx.oxml.ns import qn
        from docx.table import Table
        from docx.text.paragraph import Paragraph
        d = Document(p)
        out = []
        for i, e in enumerate(d.element.body, 1):
            if e.tag == qn('w:p'):
                out.append(f'段落块{i}: {Paragraph(e,d).text}')
            elif e.tag == qn('w:tbl'):
                for j,r in enumerate(Table(e,d).rows,1):
                    out.append(f'表格块{i} 行{j}: ' + ' | '.join(c.text for c in r.cells))
        return '\n'.join(out)
    if ext == '.pdf':
        from pypdf import PdfReader
        return '\n\n'.join(f'页{i}\n{page.extract_text() or "[无可提取文字，需视觉检查/OCR]"}' for i,page in enumerate(PdfReader(p).pages,1))
    if ext == '.pptx':
        from pptx import Presentation
        out=[]
        def shapes_text(shapes):
            for sh in shapes:
                if sh.shape_type == 6:
                    yield from shapes_text(sh.shapes)
                if sh.has_text_frame:
                    yield sh.text
                if sh.has_table:
                    for row in sh.table.rows:
                        yield ' | '.join(c.text for c in row.cells)
        for i,sl in enumerate(Presentation(p).slides,1):
            out.append(f'幻灯片{i}\n'+'\n'.join(shapes_text(sl.shapes)))
            if sl.has_notes_slide:
                out.append('备注: '+sl.notes_slide.notes_text_frame.text)
        return '\n\n'.join(out)
    if ext in {'.xlsx', '.xlsm'}:
        from openpyxl import load_workbook
        w=load_workbook(p,read_only=True,data_only=False)
        try:
            out=[]
            for sh in w:
                out.append(f'工作表: {sh.title} ({sh.sheet_state})')
                for row in sh:
                    cells=[f'{c.coordinate}={c.value}' for c in row if c.value is not None]
                    if cells: out.append(' | '.join(cells))
            return '\n'.join(out)
        finally:
            w.close()
    raise ValueError('格式不支持自动提取，需 Agent 补读或本地转换')

STANDARD = {'.doc', '.docx', '.docm', '.dot', '.dotx', '.dotm', '.xls', '.xlsx', '.xlsm', '.xlsb', '.xlt', '.xltx', '.xltm', '.ppt', '.pptx', '.pptm', '.pps', '.ppsx', '.ppsm', '.pot', '.potx', '.potm', '.pdf', '.md', '.markdown', '.mdown', '.png', '.jpg', '.jpeg', '.jp2', '.gif', '.bmp', '.tif', '.tiff', '.webp', '.heic', '.heif', '.svg', '.avif', '.ico'}
ARCHIVES = {'.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.bz2', '.xz', '.zst', '.cab', '.iso'}
IMAGES = {'.png', '.jpg', '.jpeg', '.jp2', '.gif', '.bmp', '.tif', '.tiff', '.webp', '.heic', '.heif', '.svg', '.avif', '.ico'}
OFFICE = {e for e in STANDARD if e.startswith(('.doc', '.dot', '.xls', '.xlt', '.ppt', '.pps', '.pot'))}


def protection(p):
    """Return evidence of encryption, never infer encryption from a parser error."""
    import zipfile
    ext = p.suffix.lower()
    try:
        if ext == '.pdf':
            from pypdf import PdfReader
            return 'encrypted' if PdfReader(p).is_encrypted else 'not_detected'
        if ext == '.zip':
            with zipfile.ZipFile(p) as z:
                return 'encrypted' if any(i.flag_bits & 1 for i in z.infolist()) else 'not_detected'
        if ext in OFFICE:
            import msoffcrypto
            with p.open('rb') as f:
                return 'encrypted' if msoffcrypto.OfficeFile(f).is_encrypted() else 'not_detected'
        if ext in ARCHIVES:
            return 'unknown_archive_encryption'
        return 'not_applicable'
    except ImportError:
        return 'unknown_missing_dependency'
    except Exception as e:
        return 'unknown_probe_failed:' + type(e).__name__


def inventory(source, output=None):
    import os
    files, excluded = [], []
    skill = Path(__file__).resolve().parent.parent
    def walk_error(e):
        excluded.append({'path': str(e.filename), 'reason': '访问失败:' + str(e)})
    for root, dirs, names in os.walk(source, followlinks=False, onerror=walk_error):
        base = Path(root)
        for name in list(dirs):
            p = base / name
            if name in EXCLUDE or name.startswith('.') or p.is_symlink() or p.resolve() == skill or (output and p.resolve() == output):
                excluded.append({'path': str(p.relative_to(source)), 'reason': '排除目录/符号链接/输出目录'})
                dirs.remove(name)
        files.extend(base / n for n in names)
    records = []
    for i, p in enumerate(sorted(files), 1):
        ext = p.suffix.lower()
        r = {'id': f'S{i:04d}', 'path': p.relative_to(source).as_posix(), 'extension': ext or '[无扩展名]', 'nonstandard': ext not in STANDARD, 'archive': ext in ARCHIVES}
        if p.is_symlink():
            r.update(encryption='unknown_symlink', status='unread', reason='不跟随符号链接')
        else:
            r['encryption'] = protection(p)
        records.append(r)
    return records, excluded


def main():
    import tempfile, shutil
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--scan-only', action='store_true')
    ap.add_argument('--cleanup-workspace')
    args = ap.parse_args()
    if args.cleanup_workspace:
        target = Path(args.cleanup_workspace).resolve()
        temp = Path(tempfile.gettempdir()).resolve()
        marker = target / '.project-card-workspace.json'
        if target.parent != temp or not target.name.startswith('project-card-') or target.is_symlink() or not marker.is_file():
            ap.error('拒绝清理：不是本脚本创建的独立临时工作区')
        data = json.loads(marker.read_text(encoding='utf-8'))
        if data.get('kind') != 'project-card-workspace-v1' or data.get('path') != str(target):
            ap.error('工作区标记不匹配')
        shutil.rmtree(target)
        print(json.dumps({'cleaned': str(target)}, ensure_ascii=False))
        return
    if not args.source:
        ap.error('必须指定 --source')
    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        ap.error('source 必须是现有文件夹')
    records, excluded = inventory(source)
    manifest = {'source': str(source), 'files': records, 'excluded_directories': excluded,
                'warning': '提取成功不代表已完整阅读；加密未检出不代表已确认无加密；unknown 必须提醒。'}
    if args.scan_only:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return
    output = Path(tempfile.mkdtemp(prefix='project-card-')).resolve()
    (output / '.project-card-workspace.json').write_text(json.dumps({'kind': 'project-card-workspace-v1', 'path': str(output)}), encoding='utf-8')
    for r in records:
        p = source / r['path']
        if r.get('status') == 'unread':
            continue
        if r['encryption'] == 'encrypted':
            r.update(status='unread', reason='检测到加密，需用户先解密副本')
            continue
        if r['archive']:
            r.update(status='unread', reason='压缩包：先提醒，待用户解压或明确授权临时解压')
            continue
        if p.suffix.lower() in IMAGES:
            r.update(status='needs_visual_read', reason='图片须由 Agent 视觉工具读取，不能当作未支持格式忽略')
            continue
        try:
            r['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
            content = extract(p)
            dest = output / (r['id'] + '.txt')
            dest.write_text(content, encoding='utf-8')
            r.update(status='extracted' if content.strip() else 'needs_review', text_file=dest.name, characters=len(content))
        except Exception as e:
            r.update(status='unread', reason=f'{type(e).__name__}: {e}')
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'workspace': str(output), 'manifest': str(output / 'manifest.json'), 'files': len(records)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
