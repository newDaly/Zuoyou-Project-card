#!/usr/bin/env python3
"""One Agent request: local MinerU conversion/merge, then Agent card and finalize."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import mineru_pipeline as pipeline


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def find_mineru(explicit=None):
    if explicit and not Path(explicit).expanduser().is_file() and not shutil.which(explicit):
        raise ValueError('显式指定的MinerU可执行文件不存在，请更正路径')
    candidates = [explicit, os.environ.get('PROJECT_CARD_MINERU_COMMAND'),
                  r'D:\MinerU\.venv\Scripts\mineru-kit.exe', shutil.which('mineru-kit')]
    for value in candidates:
        if value:
            p = Path(value).expanduser()
            if p.is_file():
                return str(p.resolve())
            found = shutil.which(value)
            if found:
                return found
    raise ValueError('未找到本地MinerU：请提供mineru-kit可执行文件路径，或配置PROJECT_CARD_MINERU_COMMAND；不会改用在线API')


def cleanup(root):
    subprocess.run([sys.executable, str(Path(__file__).with_name('collect_documents.py')),
                    '--cleanup-workspace', str(root)], check=True, capture_output=True, text=True)


def finalize(workspace):
    import yaml
    root, data = pipeline.load(workspace)
    final = data.get('deliverables')
    if not final:
        raise ValueError('本工作区没有可核验的正式成果')
    project = Path(final['project_markdown'])
    card = Path(final['knowledge_card'])
    if project.is_symlink() or card.is_symlink() or not project.is_file() or not card.is_file():
        raise ValueError('两份正式Markdown必须存在，且不能是符号链接')
    if hashlib.sha256(project.read_bytes()).hexdigest() != final['project_sha256']:
        raise ValueError('项目内容Markdown在生成后发生变化，请重新读取并核验后再清理')
    from card_quality import check_card
    review_path = root / 'card_review.json'
    review = json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else None
    errors, warnings = check_card(card.read_text(encoding='utf-8-sig'), data,
                                  project.read_text(encoding='utf-8-sig'), review)
    if errors:
        raise ValueError('知识卡质量校验未通过：' + '；'.join(errors))
    if warnings:
        emit({'stage':'quality_warnings','warnings':warnings,
              'notice':'规则提示须结合证据人工复核，代码不能判定事实真伪或效果因果。'})
    cleanup(root)
    emit({'status':'complete','files':[str(project),str(card)],
          'reminder':'请核对客户信息、项目事实、成果状态及待核实事项，确认后再正式归档。'})


def run(args):
    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        raise ValueError('目标文件夹不存在或当前Agent不可访问')
    files, excluded = pipeline.inventory(source)
    anomalies = [r for r in files if r['nonstandard'] or r['archive'] or r['encryption'].startswith(('encrypted','unknown'))]
    emit({'stage':'preflight','files':len(files),'alerts':anomalies,'excluded':excluded,
          'notice':'先向使用者展示本次扫描提醒；加密检测未知不等于无加密。'})
    if args.scan_only:
        return
    if not files:
        raise ValueError('未发现可用项目文档，请确认目标路径或排除目录')
    # A single GPU with 8GB VRAM benefits from serialized parsing by default.
    needs_mineru = any(Path(r['path']).suffix.lower() not in pipeline.NATIVE_MD for r in files)
    command = find_mineru(args.mineru_command) if needs_mineru else None
    out = source / '知识卡输出'
    if args.output_dir:
        out = Path(args.output_dir).expanduser().resolve()
    # Custom folders inside the source would be ingested on a later run. Use the
    # well-known excluded output directory, or a separate directory outside source.
    if out.is_relative_to(source) and out != source / '知识卡输出':
        raise ValueError('源目录内请使用默认知识卡输出目录；自定义输出目录应位于源目录外')
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', args.project_name or source.name).strip(' .') or '项目'
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    project = out / (name + '_项目内容.md')
    card = out / (name + '_项目知识卡.md')
    if project.exists() or card.exists():
        project = out / (name + '_' + stamp + '_项目内容.md')
        card = out / (name + '_' + stamp + '_项目知识卡.md')
    root = None
    try:
        root, data = pipeline.prepare(source, 'local')
        emit({'stage':'converting','workspace':str(root),'mineru':command,'workers':args.workers})
        with ThreadPoolExecutor(max_workers=max(1,min(args.workers,8))) as pool:
            futures = {pool.submit(pipeline.local_one,root,source,r,command,args.timeout):r for r in data['files']}
            for future in as_completed(futures):
                future.result()
                r = futures[future]
                emit({'stage':'file','id':r['id'],'path':r['path'],'status':r['status'],'reason':r.get('reason')})
        pipeline.save(root,data)
        pipeline.merge(root,data,project,args.allow_partial)
        data['deliverables'] = {'project_markdown':str(project),'knowledge_card':str(card),
                                'project_sha256':hashlib.sha256(project.read_bytes()).hexdigest()}
        pipeline.save(root,data)
        from card_quality import stats_line
        review_file = root / 'card_review.json'
        review_file.write_text(json.dumps({'read_ranges':[], 'claims':[], 'calculations':[],
            'semantic_review':{key:False for key in ['scope_separation','status_support',
                'conflicts_constrain_claims','minimal_personal_data','reuse_boundaries','numbers_reviewed']}},
            ensure_ascii=False,indent=2),encoding='utf-8')
        emit({'stage':'awaiting_agent_card', 'review_file':str(review_file),
              'statistics_sentence':stats_line(data),'workspace':str(root),**data['deliverables'],
              'next':'Agent完整读取总文档，按新版四部分模板写卡，并填写临时review_file的全文阅读范围、关键证据、计算与语义审核；完成后自动--finish。失败先修正，不将合并成功作为全流程结束。'})
    except BaseException:
        if root is not None:
            cleanup(root)
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--finish')
    ap.add_argument('--scan-only', action='store_true')
    ap.add_argument('--mineru-command')
    ap.add_argument('--output-dir')
    ap.add_argument('--project-name')
    ap.add_argument('--workers',type=int,default=1)
    ap.add_argument('--timeout',type=int,default=1800)
    ap.add_argument('--allow-partial',action='store_true')
    args = ap.parse_args()
    try:
        if args.finish:
            finalize(args.finish)
        elif args.source:
            run(args)
        else:
            ap.error('--source 或 --finish 为必填')
    except Exception as e:
        emit({'status':'failed','error':str(e)})
        raise SystemExit(1)


if __name__ == '__main__':
    main()
