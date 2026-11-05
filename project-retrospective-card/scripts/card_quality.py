"""Deterministic gates for a concise card; evidence meaning still needs Agent review."""
import json
from pathlib import Path
import re
from decimal import Decimal
import yaml

HEADINGS = ['一、项目背景','二、项目核心诉求与关键解决思路','三、项目其他创新亮点','四、项目运作经验总结']


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
    parts=re.split(r'^---\s*$',text,maxsplit=2,flags=re.M)
    if len(parts)!=3 or parts[0].strip():
        return ['缺少合法YAML头部'], []
    try:
        meta=yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return ['YAML无法解析'], []
    required=['年度','客户全称','国标行业','客户属性','项目内容','tags','aliases','资料来源','所属省市']
    if not isinstance(meta,dict):
        return ['YAML必须为属性映射'], []
    for field in required:
        if field not in meta:errors.append('缺少强制YAML字段:'+field)
        elif field not in ['tags','aliases','资料来源'] and (not isinstance(meta[field],(str,int)) or not str(meta[field]).strip()):
            errors.append('YAML属性不得空置:'+field)
    for field in ['tags','aliases','资料来源']:
        if not isinstance(meta.get(field),list):errors.append(field+'必须是YAML列表')
    if not re.fullmatch(r'\d{4}|待补充|待核实',str(meta.get('年度',''))):
        errors.append('年度仅填四位项目年度或待补充/待核实')
    if isinstance(meta.get('资料来源'),list) and not meta['资料来源']:
        errors.append('资料来源须指向正式项目内容总文档')
    for field,yaml_key in [('客户名称','客户全称'),('项目内容','项目内容')]:
        match=re.search(r'^\*\*'+field+r'：\*\*[ \t]*(.+)$',parts[2],re.M)
        if match and meta.get(yaml_key) is not None and compact(str(meta[yaml_key]))!=compact(match.group(1)):
            errors.append('YAML与正文信息不一致:'+field)

    for field in ['客户名称','项目编号','项目名称','项目内容','项目时间']:
        if not re.search(r'^\*\*'+field+r'：\*\*\s*\S',text,re.M):
            errors.append('缺少基本信息:'+field)
    actual=re.findall(r'^## (.+?)\s*$',text,re.M)
    if actual!=HEADINGS:errors.append('须保留新版四部分二级标题及顺序')
    sections={}
    for h in HEADINGS:
        m=re.search(r'^## '+h+r'\s*\n(.*?)(?=^## |\Z)',text,re.M|re.S)
        if m:sections[h]=m.group(1)
    bg=sections.get(HEADINGS[0],'')
    for sub in ['（一）行业与企业背景','（二）战略与经营背景']:
        if not re.search(r'^### '+re.escape(sub)+r'\s*$',bg,re.M):errors.append('缺少背景层次:'+sub)
    core=sections.get(HEADINGS[1],'')
    groups=re.split(r'^### 项目核心诉求\d+[：:]',core,flags=re.M)[1:]
    if not groups and not any(w in core for w in ['资料不足','待补充','未提供']):
        errors.append('核心诉求缺失且未说明资料不足')
    for group in groups:
        if not re.search(r'关键解决思路[：:]',group):errors.append('核心诉求缺少对应关键解决思路')
    if len(compact(text))>6500:warnings.append('全文较长，请复核重复与无关信息，保留复用所需机制与参数')
    if re.search(r'填写说明|可选标签示例|________|待补充具体问题场景|待填写脚本生成',text):
        errors.append('正式知识卡仍残留填写提示或空白占位')
    if '<summary>核验附注（非复盘正文）</summary>' not in text or '</details>' not in text:
        errors.append('缺少文末可折叠核验附注')
    notes=text.split('<summary>核验附注（非复盘正文）</summary>',1)[-1] if '<summary>核验附注（非复盘正文）</summary>' in text else ''
    if '待人工确认' not in notes:errors.append('缺少待人工确认及确认清单')
    chunks=source_chunks(project_text)
    cited=set(re.findall(r'\bS\d{4,}\b',text))
    known={r['id']:r for r in data['files']}
    missing=cited-set(known)
    if missing:errors.append('未知来源编号:'+','.join(sorted(missing)))
    # A source map uses full relative paths; abbreviated names cannot be verified.
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
