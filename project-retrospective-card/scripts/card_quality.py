"""Deterministic gates for a concise card; evidence meaning still needs Agent review."""
import json
from pathlib import Path
import re
from decimal import Decimal
import yaml

HEADINGS = ['项目背景','核心问题','最终成果','其他备注','阅读笔记']
LIMITS = {'项目背景':260,'核心问题':600,'最终成果':1400,'其他备注':1400,'阅读笔记':2000}


def compact(value):
    return re.sub(r'\s+', '', value)


def source_chunks(project):
    return {sid:body for sid,body in re.findall(r'<!-- BEGIN (S\d{4,}) -->(.*?)<!-- END \1 -->', project, re.S)}


def stats_line(data):
    total = len(data['files'])
    done = sum(r['status']=='done' for r in data['files'])
    return f'资料处理：发现{total}份，转换完成{done}份，未完成{total-done}份；转换完成不等于语义完整。'


def check_card(text, data, project_text, review=None):
    errors, warnings = [], []
    parts = re.split(r'^---\s*$',text,maxsplit=2,flags=re.M)
    if len(parts)!=3 or parts[0].strip():
        return ['缺少合法YAML头部'], []
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return ['YAML无法解析'], []
    required=['年度','客户全称','国标行业','客户属性','项目内容','tags','aliases','资料来源','所属省市']
    if not isinstance(meta,dict) or any(k not in meta for k in required):
        errors.append('未保留全部9个模板字段')
        meta = meta if isinstance(meta,dict) else {}
    for field in ['tags','aliases','资料来源']:
        if not isinstance(meta.get(field),list):errors.append(field+'必须是YAML列表')
    if isinstance(meta.get('资料来源'),list) and len(meta['资料来源'])>5:errors.append('YAML资料来源最多5项，总文档保存完整清单')
    if isinstance(meta.get('tags'),list) and len(meta['tags'])>8:errors.append('tags最多8项')
    if not re.fullmatch(r'\d{4}|待补充|待核实',str(meta.get('年度',''))):
        errors.append('年度仅填写四位年份或待补充/待核实；项目周期放阅读笔记')
    actual=re.findall(r'^## (.+?)\s*$',parts[2],re.M)
    if actual!=HEADINGS:errors.append('须保留5个二级标题及顺序')
    sections={}
    for h in HEADINGS:
        m=re.search(r'^## '+h+r'\s*\n(.*?)(?=^## |\Z)',parts[2],re.M|re.S)
        if m:
            sections[h]=m.group(1)
            if len(compact(m.group(1)))>LIMITS[h]:errors.append(h+'超出栏目长度上限')
    if len(compact(text))>6500:errors.append('全文超过6500非空白字符，应将细节留在总文档')
    bg=sections.get('项目背景','')
    prose='\n'.join(line for line in bg.splitlines() if '背景标签' not in line)
    prose=re.sub(r'\[\[[^\]]+\]\]|\[[^\]]*S\d+[^\]]*\](?:\([^)]*\))?','',prose)
    length=len(re.findall(r'[\u4e00-\u9fffA-Za-z0-9]',prose))
    if not 100<=length<=200 and not ('资料不足' in bg and length<100):
        errors.append('背景叙述须100—200字；确有资料不足时短写并明确说明')
    contacts=re.findall(r'```[^\n]*\n(.*?)```',parts[2],re.S)
    if not any('对接人' in c for c in contacts):errors.append('缺少联系人代码块')
    for c in contacts:
        if '对接人' in c and len(compact(c))>220:errors.append('联系人块过长，限必要身份、联系方式和项目职责')
    if '待人工确认' not in sections.get('阅读笔记',''):errors.append('缺少待人工确认及确认清单')
    chunks=source_chunks(project_text)
    cited=set(re.findall(r'\bS\d{4,}\b',text))
    known={r['id']:r for r in data['files']}
    missing=cited-set(known)
    if missing:errors.append('未知来源编号:'+','.join(sorted(missing)))
    # A source map uses full relative paths; abbreviated names cannot be verified.
    notes=sections.get('阅读笔记','')
    mapped=set(re.findall(r'^\|\s*(S\d{4,})\s*\|',notes,re.M))
    if cited-mapped:errors.append('来源映射缺项:'+','.join(sorted(cited-mapped)))
    for sid in cited & set(known):
        row=next((line for line in notes.splitlines() if re.match(r'^\|\s*'+sid+r'\s*\|',line)), '')
        if known[sid]['path'] not in row:errors.append(sid+'映射须使用完整相对路径，不用省略号')
    if stats_line(data) not in notes:errors.append('资料统计须使用脚本生成的准确统计句')
    image_gap=('转换图像引用' in project_text or bool(re.search(r'!\[|<img\b',project_text,re.I)))
    if image_gap and not any(w in notes for w in ['图像','图片']):errors.append('存在图像信息边界，知识卡必须披露')
    if '未读取项：无' in text.replace('**',''):
        errors.append('不得将转换成功写成所有语义均已读取')
    for word in ['显著提高','最具差异化','可直接复用','主动越级','已实证','呈正相关']:
        if word in text:warnings.append('请人工复核强判断及适用边界：'+word)
    if not review:
        errors.append('缺少临时card_review.json：需记录全文阅读范围、关键证据与数值核对')
        return errors,warnings
    # These ranges are declared by the Agent; code validates coverage, not cognition.
    ranges=review.get('read_ranges',[])
    end=0;total_lines=len(project_text.splitlines())
    if not isinstance(ranges,list) or any(not isinstance(p,list) or len(p)!=2 or not all(isinstance(n,int) for n in p) for p in ranges):
        errors.append('阅读范围格式应为[start_line,end_line]')
        ranges=[]
    for pair in sorted(ranges):
        start,stop=pair
        if start<1 or stop<start or stop>total_lines or start>end+1:errors.append('阅读范围存在越界、空隙或倒序')
        end=max(end,stop)
    if not ranges or end<total_lines:errors.append('自报阅读范围未覆盖总文档全部行')
    claims=review.get('claims',[])
    if not claims:errors.append('缺少关键事实/成果状态证据')
    for c in claims:
        sid=c.get('source_id');excerpt=c.get('excerpt','');phrase=c.get('card_phrase','')
        if sid not in chunks or not excerpt or compact(excerpt) not in compact(chunks.get(sid,'')):
            errors.append('关键证据摘录不能在对应来源中定位:'+str(sid))
        if not phrase or phrase not in text:errors.append('关键证据未绑定卡内原句:'+str(sid))
        if not c.get('locator'):errors.append('关键证据缺少页/段/表格或合并文档行号:'+str(sid))
        if c.get('status') in ['已提交','已确认','已实施','已产生效果'] and not c.get('status_basis'):
            errors.append('成果状态缺少确认依据:'+str(sid))
    for c in review.get('calculations',[]):
        try:
            if c.get('kind')=='sum':
                valid=sum(Decimal(str(x)) for x in c['terms'])==Decimal(str(c['total']))
            elif c.get('kind')=='percentage':
                value=Decimal(str(c['numerator']))/Decimal(str(c['denominator']))*100
                valid=abs(value-Decimal(str(c['percent'])))<=Decimal(str(c.get('tolerance',0.1)))
            else:
                raise ValueError('unknown calculation kind')
            if not valid:errors.append('数值核对不通过:'+c.get('label','未命名'))
            if not c.get('card_phrase') or c['card_phrase'] not in text:errors.append('数值核对未绑定卡内原句')
        except (KeyError,ValueError,ArithmeticError,TypeError):errors.append('数值核对数据无效')
    for key in ['scope_separation','status_support','conflicts_constrain_claims','minimal_personal_data','reuse_boundaries','numbers_reviewed']:
        if review.get('semantic_review',{}).get(key) is not True:errors.append('Agent未确认语义审核项:'+key)
    return errors,warnings
