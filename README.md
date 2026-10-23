# Zuoyou Project Card

面向 **WorkBuddy、豆包工作、Codex 等 Agent** 的项目复盘知识卡 Skill。依据统一模板与复盘规范，读取项目资料并生成有来源的 Markdown 知识卡。

## 安装

从 [Releases 下载最新 ZIP](https://github.com/newDaly/Zuoyou-Project-card/releases/latest)。详细步骤见 [安装与使用](project-retrospective-card/references/安装与使用.md)。

| Agent | 安装方式 |
|---|---|
| WorkBuddy | 技能页面→添加技能→上传完整技能包，导入后启用 |
| 豆包工作 | “技能·连接器·伙伴”中的本地技能导入/自定义技能入口，按当前客户端支持的形式导入完整资源 |
| Codex | 将完整 project-retrospective-card 文件夹放入本机 ~/.agents/skills/，重新载入 Agent |

需要可访问目标文件夹的文件工具；脚本需 Python 3.10+ 及 scripts/requirements.txt 中依赖。云端环境不能直接访问电脑路径时需先提供可访问副本。各客户端的导入入口、包格式和权限以当前版本为准，完整兼容性未逐个平台实机验证。

## 使用

```text
使用项目复盘知识卡技能，读取 D:/项目资料/某项目。
先扫描并提醒其他格式、压缩包和加密文档，通过MinerU批量转换为项目内容Markdown，再据此生成知识卡，最后提醒我确认。
```

默认一个文件夹对应一个项目，递归包含子文件夹；批量项目需明确分组。

## 执行规则（v1.2.0）

1. **先扫描全部项目资料并提醒**：Word、Excel、PPT、PDF、Markdown、图片以外的格式均列入非规范项，单独突出压缩包、加密、检测未知、损坏/无权限等情况。
2. **联动MinerU批量转换**：优先本地部署；在线API须配置Token并确认项目文件上传权限。Markdown直接保留，其余按当前MinerU支持范围转换为Markdown，不支持或失败的文件明确披露。
3. **合并一个项目内容Markdown**：保留全文、来源路径、稳定编号、哈希与转换状态；转换失败默认阻止合并，使用者可明确选择不完整草稿。
4. **Agent只读取合并后的项目内容Markdown生成知识卡**，不直接读取Office/PDF/图片正文替代该流程。需要补充时先重转并更新总文档。
5. **最终保留两份正式文件**：`项目名称_项目内容.md` 和 `项目名称_项目知识卡.md`。此规则取代旧版仅保留知识卡的规则，其他本次过程文件清理。
6. **提醒人工确认**：核对客户信息、项目事实、成果状态、OCR/图像边界及待核实事项，确认后再归档。

详细部署、在线调用与批量命令见 [MinerU转换与合并](project-retrospective-card/references/MinerU转换与合并.md)。技能不会自动安装大型模型。需要Python 3.10+，在线适配使用requests，转换质量与格式支持受MinerU版本/部署/模型/配额影响；当前适配不代表已对所有文档实测。

## 推荐阅读与编辑工具
推荐使用 [Obsidian](https://obsidian.md/) 阅读编辑项目内容总文档与知识卡，利用属性、标签、链接和搜索积累公司知识。将两份Markdown放入现有仓库，或将知识卡输出目录作为仓库打开。移动文件后注意核对来源路径。

## 更新说明
v1.2.0：增加MinerU在线/本地转换联动、项目内容全文合并、只基于合并Markdown生成知识卡、人工确认提醒；交付从单份知识卡改为两份Markdown。
v1.1.0：多Agent安装与Obsidian建议、前置扫描、异常格式/压缩包/加密提醒、安全清理。
