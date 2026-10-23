# MinerU 转换与合并

## 工作链路
扫描全部文档并提醒 → 选择本地/在线路由 → MinerU逐文件转换 → 一个总的项目内容Markdown → Agent完整读取该Markdown → 知识卡 → 人工确认。

仅通过Markdown分析，禁止Agent直接阅读原始Office/PDF/图片正文后跳过转换。原始Markdown无需重复OCR，直接作为转换合并输入。失败不伪装成成功；总文档不是内容摘要。

## 首次配置
- 先确定使用已有本地部署还是MinerU在线API。没有可用部署/Token时，询问用户选择，不能声称已转换。
- 本地部署按 [MinerU官方部署文档](https://opendatalab.github.io/MinerU/quick_start/) 安装并配置模型，确认 `mineru-kit parse --help` 可用，先对小样本验证完整导出。大型依赖/模型下载由使用者选择环境，脚本不自动安装MinerU。
- 在线精准批量API：[官方文档](https://mineru.net/doc/docs/)。使用者在MinerU申请Token后，配置环境变量 `MINERU_API_TOKEN`；不要把Token发到对话、提交到仓库或写入产物。脚本只读取变量。
- 本地 CLI 适配 MinerU 4.x `mineru-kit parse 输入 -o 输出.md` 的无状态完整导出；其他版本须先核对命令，可通过 `--mineru-command` 指定兼容可执行文件路径，不传任意shell字符串。旧版 `mineru -p -o` 目录输出不能直接冒充本适配器。
- 本地CLI默认清除远程API环境变量；仍应检查MinerU配置未启用外部模型/后处理服务。内网HTTP部署或其他API版本需按其OpenAPI适配，不将在线v4端点套到本地v1。

## 步骤1：前置扫描
```bash
python scripts/collect_documents.py --source "D:/项目资料/某项目" --scan-only
```
向用户汇总非规范扩展名、压缩包、加密与检测未知项。六类正常资料不等于六类都已验证可被当前MinerU版本解析。隐藏、版本控制、依赖、既有输出目录明确排除；访问失败列入边界。默认不自动解压。

## 步骤2A：本地批量转换
```bash
python scripts/mineru_pipeline.py local --source "D:/项目资料/某项目" --workers 2
```
命令返回 workspace；每个输入有稳定编号、独立Markdown输出和状态，默认最多2个并发，可用 `--workers` 调整为1—8。单文件超时默认1800秒，可用 `--timeout` 设置。长任务用宿主后台执行/短间隔查询能力，不长时间阻塞用户更新。
底层调用为 `mineru-kit parse 输入 -o 输出.md`；此无状态导出默认完整页，不使用交互 `mineru parse` 默认前10页输出。依赖、模型、格式、文件损坏和超时可能导致失败，均须处理。
官方命令参考：[CLI tools](https://opendatalab.github.io/MinerU/usage/cli_tools/)。

## 步骤2B：在线批量转换
上传前向使用者确认本批项目文件可发送到MinerU；已明确授权则继续。API Token存在不等于授权上传所有文件。
```bash
python scripts/mineru_pipeline.py cloud-submit --source "D:/项目资料/某项目" --allow-cloud-upload
python scripts/mineru_pipeline.py cloud-poll --workspace "返回的workspace"
```
submit：每批最多200个文件申请上传URL，再逐个PUT；不记录Token或签名URL。状态持久化在临时工作区。poll：只查询一次并下载已完成结果，不阻塞等待；仍有running/submitted时稍后再调用，定期向使用者更新进展。超时/服务限额时报告并选择稍后继续或清理退出，不无限重试。勿反复submit造成重复上传。
固定API：`https://mineru.net/api/v4/file-urls/batch` 和 `/extract-results/batch/{batch_id}`；读取结果包 `full.md`，不解压/执行返回包中的其他文件。脚本设置200MB输入文件上限，页数/配额/格式以服务当前实际返回为准，超限需拆分后重新扫描；不要使用页数有限的Agent轻量API冒充全项目转换。
在线支持格式按当前批量API能力校验；Excel支持情况存在不同版本文档差异，遇不支持必须提示并改用可用本地部署或用户预转换副本，不能静默丢弃。HTML等非标准格式本地可转换，在线脚本暂不路由HTML专用模型。其他本地/在线格式差异同样登记。

## 步骤3：合并全文
```bash
python scripts/mineru_pipeline.py merge --workspace "本次workspace" --output "D:/项目资料/某项目/知识卡输出/某项目_项目内容.md"
```
不完整输入默认阻止合并。用户明确接受不完整草稿时才加 `--allow-partial`，在总文档与知识卡中披露缺失；没有真正转换成功的核心资料时先补资料，不交付伪造复盘。
正文按稳定编号、来源路径、哈希分隔。Markdown原始标题、表格与正文保留；不改变业务内容。图片引用转换成明确的待人工确认占位，避免删除过程图片后留下假可用链接；纯图像含义并不等同已转成文本，需MinerU更合适的OCR/解析配置重转或由使用者确认。卡片引用总文档编号及原文件路径，不引用临时文件。

## 步骤4：生成、确认与清理
Agent完整读取总文档后按模板生成知识卡。总文档与知识卡均保留；临时逐文件MD、日志、清单和下载数据清理：
```bash
python scripts/collect_documents.py --cleanup-workspace "本次workspace"
```
不要删除原始文档、历史输出、模型缓存或MinerU部署。最后提供两份Markdown，提醒使用者检查客户信息、项目事实、成果状态、缺页/图片/OCR/公式及待核实内容后归档。两份文件均可放入Obsidian阅读编辑。

## 验证边界
脚本测试应覆盖本地命令调度、在线提交/状态/结果协议、同名文件映射、失败合并拦截和清理边界。无真实MinerU环境或有效API Token时，只能报告模拟协议测试通过；不能声称完成真实在线/本地模型解析验收。
