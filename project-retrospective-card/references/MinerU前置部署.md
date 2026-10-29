# MinerU前置部署：首次安装者必读

## 目录
- [准备与安装顺序](#准备与安装顺序)
- [Windows部署](#windows部署)
- [macOS与Linux](#macos与linux)
- [连接Skill](#连接skill)
- [验收清单与常见问题](#验收清单与常见问题)

## 准备与安装顺序

本Skill不内置MinerU程序或模型。**安装Skill不等于已经具备解析能力**。首次使用顺序为：部署MinerU → 准备并验证模型 → 转换一份样本文档 → 安装完整Skill → 安装Skill脚本依赖 → 发出一次项目处理请求。

已经能用本地MinerU成功解析的同事，直接跳到“连接Skill”，不要重复创建环境或下载模型。

本说明适配MinerU 4.x、本地命令`mineru-kit parse`。推荐单独Python 3.12环境，不将依赖混入系统环境。不要求每位同事安装同样的GPU引擎；CPU、Apple Silicon、NVIDIA环境的速度和可用加速方式不同，以官方平台说明及实际样本转换为准。单卡8GB显存先采用Skill默认串行解析，不保证任意规模/版式都在固定时间内成功。

安装依赖和首次模型下载需要联网、足够磁盘空间及可能的公司软件安装权限；请提前准备。模型、软件缓存、临时转换文件和项目结果是不同目录，容量以实际下载清单为准。不要把项目原始资料放在程序目录中。

## Windows部署

以下使用PowerShell，以`D:\MinerU`为示例；没有D盘可改为自己的盘符，之后调用路径也相应修改。无需管理员权限修改系统执行策略，也不要求启动WebUI。

### 1. 安装uv

已有uv时先运行`uv --version`，可用即可跳过安装。

```powershell
winget install --id=astral-sh.uv -e
```

安装后新开一个PowerShell窗口并检查：

```powershell
uv --version
```

没有WinGet的电脑，按[uv官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)选用官方二进制或已有Python的安装方式。不要在不知道来源时运行他人提供的安装脚本。

### 2. 创建独立环境并安装MinerU

仅首次新建环境时执行；如果已有同名环境，先确认其用途，不覆盖已有安装。

```powershell
New-Item -ItemType Directory -Force "D:\MinerU" | Out-Null
Set-Location "D:\MinerU"
$env:UV_CACHE_DIR = "D:\MinerU\uv-cache"
uv venv --python 3.12 "D:\MinerU\.venv"
uv pip install --python "D:\MinerU\.venv\Scripts\python.exe" "mineru>=4.0,<5"
& "D:\MinerU\.venv\Scripts\mineru-kit.exe" --help
```

uv可在需要时下载Python。无需激活虚拟环境：后续使用完整可执行文件路径，避免PowerShell激活策略或系统Python混用。`UV_CACHE_DIR`只影响uv缓存，不保证MinerU模型、第三方模型缓存和临时文件全部改到D盘；需要迁移模型时按官方文档设置`model.base_dir`并保持下载/验证/解析配置一致。

先用基础包验证，不默认添加旧版3.x安装参数或大型GPU扩展；需要Torch、LMDeploy等额外加速时，由技术人员按实际系统/驱动选择官方扩展方案。

### 3. 下载模型并验证

示例使用ModelScope；公司网络允许访问Hugging Face时，也可将`modelscope`改为`huggingface`。下载与解析使用同一用户、同一配置及后端。

```powershell
$env:MINERU_MODEL_SOURCE = "modelscope"
& "D:\MinerU\.venv\Scripts\mineru-kit.exe" models download --tier standard --source modelscope
& "D:\MinerU\.venv\Scripts\mineru-kit.exe" models verify --tier standard
& "D:\MinerU\.venv\Scripts\mineru-kit.exe" models show
```

只有下载和verify正常完成后再继续。若缺少模型或后端不匹配，按报错调整；`models show`用于查看配置，不能代替`models verify`和实际转换。不要手工创建模型完成标记，不把“安装118个包”等安装成功信息当成模型已就绪。

### 4. 转换一份小样本

先选一份非敏感的小PDF，替换下面的实际文件路径，输出文件使用新名称：

```powershell
New-Item -ItemType Directory -Force "D:\MinerU\sample-output" | Out-Null
& "D:\MinerU\.venv\Scripts\mineru-kit.exe" parse "D:\样本资料\测试.pdf" -o "D:\MinerU\sample-output\测试.md" --tier standard
```

打开输出Markdown，核对首尾页、中文、表格及扫描文字；确认不是空文档或仅部分页面。实际有Word/Excel/PPT时，也各选一份代表性样本试转。格式支持和OCR效果以当前部署结果为准，不能从PDF成功推断所有Office/图片都已支持。

Skill使用无状态`mineru-kit parse`完整导出；不要用`mineru parse`默认交互前10页结果替代全文。

### 5. 可选：模型就绪后限制为本地模型

```powershell
$env:MINERU_MODEL_SOURCE = "local"
```

此设置只对当前PowerShell及其子进程生效。希望新启动的Agent也继承，可在确认模型就绪后设置用户环境变量：

```powershell
[Environment]::SetEnvironmentVariable("MINERU_MODEL_SOURCE", "local", "User")
```

缺模型时local模式会失败而不是自动下载。它不等同于禁用一切网络：还应确认MinerU配置中没有不需要的远程VLM服务或外部LLM后处理。敏感项目使用前由负责部署的同事核对实际配置及必要的网络策略；本Skill不会自动关闭安全措施或把资料改送云端。

## macOS与Linux

先按[uv官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)安装uv；macOS已有Homebrew可使用`brew install uv`。然后在终端创建新的独立目录：

```bash
mkdir -p "$HOME/MinerU"
uv venv --python 3.12 "$HOME/MinerU/.venv"
uv pip install --python "$HOME/MinerU/.venv/bin/python" 'mineru>=4.0,<5'
"$HOME/MinerU/.venv/bin/mineru-kit" models download --tier standard --source modelscope
"$HOME/MinerU/.venv/bin/mineru-kit" models verify --tier standard
"$HOME/MinerU/.venv/bin/mineru-kit" models show
"$HOME/MinerU/.venv/bin/mineru-kit" parse '/实际路径/测试.pdf' -o '/实际路径/测试输出.md' --tier standard
```

目录已有环境时不要重复创建。样本验证成功后，可在Agent启动环境中设置`MINERU_MODEL_SOURCE=local`，并告诉Agent实际`mineru-kit`路径。Apple Silicon、Linux GPU或特殊平台的扩展引擎按官方指南配置，本说明不保证统一的GPU加速效果。

## 连接Skill

### 安装Skill及其小型脚本依赖

从本仓库Releases下载完整ZIP并按[安装与使用](安装与使用.md)导入WorkBuddy、豆包工作或Codex；保留assets、references、scripts等全部子目录。只复制SKILL.md会丢失模板和脚本。

假设解压/安装后的Skill位置是`D:\Skills\project-retrospective-card`，请改为自己的实际目录：

```powershell
uv pip install --python "D:\MinerU\.venv\Scripts\python.exe" -r "D:\Skills\project-retrospective-card\scripts\requirements.txt"
```

uv创建的环境不一定自带pip，因此这里优先使用`uv pip --python`，不要因`python -m pip`不存在而重装MinerU。若Agent使用另一Python运行脚本，需要在那一环境同样满足Skill依赖；最简单是让Agent使用已配置的MinerU虚拟环境Python。

### 让Agent找到部署

Windows的`D:\MinerU\.venv\Scripts\mineru-kit.exe`是默认识别路径。其他位置可在任务中明确告诉Agent，或设置环境变量：

```powershell
$env:PROJECT_CARD_MINERU_COMMAND = "E:\Apps\MinerU\.venv\Scripts\mineru-kit.exe"
[Environment]::SetEnvironmentVariable("PROJECT_CARD_MINERU_COMMAND", "E:\Apps\MinerU\.venv\Scripts\mineru-kit.exe", "User")
```

仅把示例改成真实路径后执行，不要将不存在的E盘路径写入配置。用户环境变量只由新启动的进程继承；当前Agent未读到变量时，直接在任务里提供完整路径即可，不需更改系统PATH。

Agent必须运行在能够访问该电脑文件与程序的环境；网页/云端Agent不能凭`D:/...`路径访问用户本机，需改用本地客户端或可访问的受控执行环境。

### 日常一次调用

```text
使用项目复盘知识卡技能，处理 D:/项目资料/某项目。
MinerU已部署在 D:/MinerU，请自动扫描提醒、解析合并、按规范生成知识卡并清理过程文件，保留两份Markdown。
如需运行Python，请使用 D:/MinerU/.venv/Scripts/python.exe。
```

Agent完成后只留下项目内容总文档与项目知识卡两份正式Markdown，并提醒人工确认；出现阻断时先解决资料或部署问题，不静默跳过或改为云端上传。

## 验收清单与常见问题

使用前确认以下事项：
- `mineru-kit --help`可运行，且模型verify通过。
- 一份真实小样本完整转换成功，首尾页和关键表格可读。
- 已记录真实MinerU可执行文件及Python路径。
- 完整Skill资源已导入，运行脚本的Python依赖齐备。
- Agent可访问本机项目目录，并在小项目上完成两份Markdown和自动清理验证。

| 现象 | 处理方式 |
|---|---|
| 找不到uv | 按官方方式安装，新开终端验证；无需反复重建MinerU |
| 找不到mineru-kit | 检查完整路径或告诉Agent实际路径；不要求必须加入PATH |
| PowerShell禁止Activate.ps1 | 使用本文完整exe路径，无需激活或修改系统执行策略 |
| Python没有pip | 使用uv pip --python指定环境安装Skill依赖 |
| 下载慢/失败 | 核对网络和模型源；可按官方文档选择ModelScope/Hugging Face，未成功前不处理整个项目 |
| 模型verify失败 | 检查下载完整性、配置及后端一致性；不要伪造模型标记 |
| 7860端口被占用 | 本Skill不使用WebUI，无需解决该端口即可用CLI；WebUI另用时再选择空闲端口 |
| 显存不足 | 保持workers=1，减少同时占用GPU的任务，按官方平台指南调整，不盲目增加并发 |
| 只解析前几页 | 使用本Skill的mineru-kit完整导出；检查输入/模型返回是否有限额或错误 |
| 有加密/压缩包/不支持文件 | 按扫描提示提供已解密/已解压或预转换副本，不将失败当作空内容忽略 |
| 能解析但Agent不能写卡 | 确认Agent继续读取合并总文档并按Skill规范写卡；脚本本身不负责调用大模型 |
| 依赖安装成功但解析失败 | 软件、模型、实际样本转换是三项独立检查，按真实错误逐项排查 |

本指南经官方命令核对，未在每位同事的硬件与权限环境实机安装。不会自动重装已部署环境、下载安装大型模型或将本地数据上传；这些操作由使用者按公司规则完成。

官方参考：[MinerU快速部署](https://opendatalab.github.io/MinerU/quick_start/) · [模型下载与配置](https://opendatalab.github.io/MinerU/usage/model_source/) · [uv安装](https://docs.astral.sh/uv/getting-started/installation/)。
