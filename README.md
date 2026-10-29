# Zuoyou Project Card

面向 **WorkBuddy、豆包工作、Codex等Agent** 的项目复盘知识卡Skill。

已部署本地MinerU后，用户提供项目文件夹并发出一次请求，Agent自动完成：

**扫描提醒 → 本地解析 → 全文合并 → 按规范生成知识卡 → 核验清理 → 提醒人工确认**

## 下载与安装

下载 [最新Release安装包](https://github.com/newDaly/Zuoyou-Project-card/releases/latest)。详细安装方法见 [安装与使用](project-retrospective-card/references/安装与使用.md)。

| Agent | 安装方式 |
|---|---|
| WorkBuddy | 技能页面→添加技能→上传完整技能包，导入后启用 |
| 豆包工作 | 按当前客户端本地技能导入/自定义技能入口导入完整资源 |
| Codex | 将完整project-retrospective-card目录放入本机技能目录（当前本地CLI通常为~/.agents/skills/），特殊宿主以其导入入口为准 |

需要文件访问与脚本执行能力，云端Agent不能直接读取用户电脑D盘；在本机执行或提供可访问的部署与文件环境。需Python 3.10+及scripts/requirements.txt中依赖。安装包包含模板、复盘规范与脚本，不包含MinerU本体及模型。

## 一次调用

直接向Agent发送：

```text
使用项目复盘知识卡技能，处理 D:/项目资料/某项目。
我已在 D:/MinerU 部署MinerU，请自动解析、合并，按规范生成知识卡，清理过程文件，最终保留两份Markdown并提醒我确认。
```

不需要用户逐条运行解析/合并命令。脚本负责确定性解析和合并，知识卡业务内容由Agent读取总文档后按规范撰写，Agent自动执行收尾；普通Python脚本脱离Agent不能自行完成智能复盘。

## 已有本地部署自动识别

依次查找：显式指定路径、`PROJECT_CARD_MINERU_COMMAND`环境变量、Windows常见部署路径 `D:/MinerU/.venv/Scripts/mineru-kit.exe`、PATH中的`mineru-kit`。你的现有D盘部署可以直接命中，不需重新安装或下载模型。

- 不需要启动WebUI，不需要7860端口，不要求在线Token。
- 默认串行解析，适配单卡8GB显存；验证硬件余量后可增加并发。
- 本地找不到才提示补充路径，不自动切换在线上传。
- 先核查本地MinerU配置，避免自行配置的远程后处理；本地CLI不等于对所有组件作绝对断网保证。

完整说明见 [本地一键执行](project-retrospective-card/references/本地一键执行.md)。

## 执行规则与输出

1. 递归扫描全部非排除目录，提醒Word、Excel、PPT、PDF、Markdown、图片以外的格式；突出压缩包、加密、检测未知或访问失败项。默认不解压、不破解、不修改原文件。
2. 用MinerU本地无状态完整导出逐文件Markdown，再合并为总文档，保留来源编号、路径、哈希和转换状态。源Markdown直接保留。
3. Agent仅从合并后的项目内容Markdown生成知识卡，不直接分析Office/PDF/图片正文绕过转换。需补充时先重转再读取。
4. 失败或不支持项默认阻止完整合并；用户明确同意才生成不完整草稿。OCR、表格、公式与图像语义的缺失须披露，不能把占位符当成已读事实。
5. Agent写卡并核验后自动清理本次临时工作区，不删除源资料、历史结果、模型缓存或部署。
6. 最后提醒人工确认客户信息、项目事实、成果状态及待核实事项，确认后再归档。

默认仅新增/保留以下两份正式成果到项目目录的`知识卡输出`，同名历史成果保留，新结果加时间戳：

- `项目名称_项目内容.md`
- `项目名称_项目知识卡.md`

## Obsidian阅读与编辑

推荐用 [Obsidian](https://obsidian.md/) 打开知识卡输出目录或将两份Markdown移入已有仓库，使用属性、标签、链接和搜索管理项目知识。移动文件后核对来源相对路径。

## 在线模式及排错

在线模式只在用户明确要求时使用，需Token及本批项目上传授权。逐阶段命令及在线API说明见 [MinerU转换与合并](project-retrospective-card/references/MinerU转换与合并.md)，默认流程不要求用户逐条执行。

## 版本

v1.3.0：本地默认一键流程、D盘/PATH自动识别、8GB显存默认串行、自动衔接Agent写卡与结构核验清理。

v1.2.0：MinerU在线/本地转换、项目内容全文合并、仅基于总Markdown生成知识卡、人工确认。

v1.1.0：多Agent安装、Obsidian建议、前置扫描、异常提醒、安全清理。

已通过本地调度及模拟可执行文件测试；尚未直接访问使用者Windows D盘实机验收。格式支持与解析质量以实际MinerU部署为准，不承诺任意格式全自动成功。
