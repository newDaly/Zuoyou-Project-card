#!/usr/bin/env python3
"""Extract local documents without changing sources; report every discovered file."""
import argparse
import hashlib
import json
from pathlib import Path

EXCLUDE = {'.git', '.svn', 'node_modules', '__pycache__', '.venv', 'venv', '知识卡输出'}
TEXT = {'.txt', '.md', '.csv', '.tsv', '.json', '.yaml', '.yml', '.xml', '.html', '.htm', '.log', '.rst'}

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

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',required=True)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    source=Path(args.source).expanduser().resolve()
    output=Path(args.output).expanduser().resolve()
    if not source.is_dir(): ap.error('source 必须是现有文件夹')
    if output == source or source.is_relative_to(output): ap.error('output 不得等于或包含 source')
    # Inventory before creating output; never follow directory symlinks.
    import os
    files=[]
    excluded=[]
    skill=Path(__file__).resolve().parent.parent
    for root,dirs,names in os.walk(source,followlinks=False):
        base=Path(root)
        for name in list(dirs):
            p=base/name
            if name in EXCLUDE or name.startswith('.') or p.is_symlink() or p.resolve()==skill or p.resolve()==output:
                excluded.append(str(p.relative_to(source)))
                dirs.remove(name)
        files.extend(base/n for n in names)
    output.mkdir(parents=True,exist_ok=False)
    records=[]
    for i,p in enumerate(sorted(files),1):
        r={'id':f'S{i:04d}','path':p.relative_to(source).as_posix()}
        try:
            if p.is_symlink(): raise ValueError('符号链接不读取')
            r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            content=extract(p)
            dest=output/(r['id']+'.txt')
            dest.write_text(content,encoding='utf-8')
            r.update(status='extracted' if content.strip() else 'needs_review',text_file=dest.name,characters=len(content),note='仅提取可访问文字，需 Agent 检查图像/批注/公式等遗漏')
        except Exception as e:
            r.update(status='unread',reason=f'{type(e).__name__}: {e}')
        records.append(r)
    manifest={'source':str(source),'files':records,'excluded_directories':excluded,'warning':'extracted 仅表示提取成功，不代表 Agent 已完整阅读。排除项不是已读资料。'}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'files':len(records),'extracted':sum(r['status']=='extracted' for r in records),'unread_or_review':sum(r['status']!='extracted' for r in records),'manifest':str(output/'manifest.json')},ensure_ascii=False))

if __name__=='__main__':
    main()
