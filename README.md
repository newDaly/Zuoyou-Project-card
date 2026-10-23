# Zuoyou Project Card

面向咨询项目复盘与知识沉淀的 Agent Skill。递归读取指定项目文件夹，依据统一模板与复盘规范生成 Markdown 项目知识卡及资料核查文件。

## 功能

- 保留知识卡元数据、联系人及五个主栏目。
- 建立“核心问题—解决方案—最终成果”对应关系。
- 提炼项目挑战、改进经验及有依据的可复制方法。
- 记录资料来源、冲突、未读文件及待补充内容，不将规范示例视为项目事实。

## 安装到 Codex

需要 Git、Python 3.10 或以上版本，以及具有本地文件访问和代码执行能力的 Agent。私有仓库需要先获得读取权限并完成 GitHub 身份验证。

先克隆仓库：

```bash
git clone https://github.com/newDaly/Zuoyou-Project-card.git
```

macOS / Linux：

```bash
mkdir -p ~/.codex/skills
cp -R Zuoyou-Project-card/project-retrospective-card ~/.codex/skills/
python3 -m pip install -r ~/.codex/skills/project-retrospective-card/scripts/requirements.txt
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse ".\Zuoyou-Project-card\project-retrospective-card" "$env:USERPROFILE\.codex\skills\"
python -m pip install -r "$env:USERPROFILE\.codex\skills\project-retrospective-card\scripts\requirements.txt"
```

安装后重新载入 Agent。若已存在同名技能，请先备份旧版本再替换。其他支持 SKILL.md 的 Agent 按其技能目录规则安装。

## 使用

向 Agent 输入：

```text
使用 $project-retrospective-card，读取 D:/项目资料/某项目，生成项目知识卡。
```

默认一个文件夹对应一个项目，包含子文件夹。发现混合项目时先确认分组。

输出到目标文件夹的 `知识卡输出`：

- `项目名称_项目知识卡.md`
- `项目名称_资料读取与核查.md`
- 文档提取文本和清单

已存在输出不会被直接覆盖。安装本身不会扫描文件，只有调用后才读取指定目录。

## 文档支持与限制

脚本支持 DOCX、XLSX/XLSM、PPTX、PDF 和常见文本格式；它负责清点与文字提取，分析及知识卡填写由 Agent 完成。扫描件、图片、图表、批注和嵌入对象需宿主工具补读；旧版 Office 文件需本地转换。无法读取时必须在核查文件中披露，不保证任何格式都能自动完整解析。

资料缺失写“待补充”，存在冲突写“待核实”；建议、已交付成果、已实施机制和实际效果分别表述。

## 仓库内容

`project-retrospective-card/` 内含执行说明、原始 Markdown 模板、复盘规范转录、文档提取脚本及依赖清单。

项目原始资料、联系人信息及生成结果不应提交到本仓库。默认不调用外部 OCR 服务、不执行宏、不修改源文档。
