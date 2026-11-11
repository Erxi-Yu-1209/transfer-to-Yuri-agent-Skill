# Yuri Card Workbench 1.1.1（百合角色卡工作台）

本项目的重点是：按照已保存的百合定义，将角色卡、论坛叙事和小说节选改编为百合角色卡。来源事实与虚构改编决定分别保存；不会把“原作者性别未知”改写成“原作者本来就是女性”，也不会为了百合而强迫恋爱、抹去冲突或改变人物自主性。

核心工作流、推理准则、代码及配置值保持英文；用户交互及三个默认选项使用中文。

## 交给智能体

打开项目后直接说：

> 使用 post-to-yuri-card 或 novel-excerpt-to-yuri-card 处理这个来源。复用 config/preferences.json，先估算阅读成本，再选择适量样本并生成百合角色卡。原始事实、改编决定和新写的开场分别记录。有重要创作选择时在对话中询问我，记录由你维护。

已有 JSON 角色卡继续使用 `skills/yuri-card-adapter/SKILL.md`。两个新技能分别处理帖子和小说，内部共用 `shared/`；独立技能文件夹内也包含所需实现与来源声明。新技能以百合改编为默认目标，原设定分支用于对照。脚本不调用模型；理解文本和编写计划由智能体负责。

## 环境与一次性默认值

需要 Python 3.10+。执行 `python -m pip install -r requirements.txt`。

| 设置 | 中文默认选项 | 保存值 |
| --- | --- | --- |
| 女性定义 | 由作者定义为女性的角色，包括虚拟及非人角色 | `author_defined_inclusive` |
| 转换范围 | 转换主要角色，保留背景角色 | `main_cast` |
| 关系调整 | 允许由情境变化及明确因果支持的关系调整 | `rederive_if_causal` |

运行 `python scripts/setup_profile.py --show` 可查看。需要修改时用 `--output config/preferences.local.json` 新存一份，后续显式选择该配置即可，无需逐卡重填。默认保留玩家身份及来源语言。

## 帖子／小说到百合卡

```bash
python scripts/source_pipeline.py ingest input.txt --kind post --source-id post-001 --project private-casework/my-post --max-chars 6000
python scripts/source_pipeline.py ingest novel.epub --kind novel --source-id novel-scene --project private-casework/my-novel --chapter 1 --max-chars 3000
```

这是两个独立项目示例。支持 TXT、Markdown、EPUB。网页由智能体使用宿主可用工具获取并保存正文快照，再以 `--url` 记录来源；脚本不自动浏览或登录。EPUB 按实质叙事 spine 成员选择，可能不等于文学章节。截取范围与未读范围会明确记录。

智能体填写 `extracted.json`、编写原设定 `card.md` 和百合改编计划，随后执行：

```bash
python scripts/source_pipeline.py validate --project private-casework/my-post
python scripts/source_pipeline.py bind-plan --project private-casework/my-post --draft private-casework/my-post/card.md --plan private-casework/my-post/plan.unbound.json --profile config/preferences.json --output private-casework/my-post/plan.json
python scripts/source_pipeline.py build --project private-casework/my-post --draft private-casework/my-post/card.md --plan private-casework/my-post/plan.json --profile config/preferences.json --output private-casework/my-post/results
```

结果含原设定卡、百合卡、世界书及 `adaptation.json`。后者记录来源性别、虚构性别指定、依据、创作补充及精确改动。原本已经是女性的角色可以不做身份改动；亲情、友情和矛盾也可以属于已保存的百合定义。已有章节资料可复用于同一作品的其他角色，不必反复阅读全文。

通用 JSON／PNG 序列化直接复用 Foreverse 的 MIT 工具；本项目新增部分重点处理百合决策和来源绑定。所有非空叙事字段都必须关联来源主张或明确标注为创作补充。不会把整章小说堆进角色卡。

## PNG 与世界书

```bash
python scripts/source_pipeline.py unpack-png input.png --output runs/input-card.json
python scripts/source_pipeline.py pack-png output-card.json --avatar original.png --output runs/output-card.png
python scripts/source_pipeline.py extract-worldbook output-card.json --output runs/worldbook.json
python scripts/source_pipeline.py embed-worldbook output-card.json runs/worldbook.json --replace --output runs/card-with-book.json
```

输出必须使用新路径。PNG 嵌卡复用上游实现并保留所给图像数据；读取目前支持未压缩的 `tEXt` chara/ccv3 载荷。结构化世界书可显式拆出／装回；把描述里的设定正文改造成可激活条目仍需内容计划。这是 SillyTavern 文件适配器，不代表已连接真实宿主 API。

## 审阅与交付

智能体维护文件，你直接在当前对话中确认、纠正或改变创作方向，不需要手填 Markdown 表单。复用已保存配置和资料库；单个案例需要决策时保留其他已完成结果。已编写计划可用 `scripts/batch_source_build.py --jobs jobs.json --report runs/batch-status.json` 批量构建；每项独立记录成功或失败，可识别哈希一致的已完成结果。没有实际后台宿主时，不宣称会话结束后仍能继续批处理。

本轮只用完整帖子、普通小说第一章及 GL 小说一个场景。实际范围与结果见英文 `docs/SAMPLE_RESULTS.md`；私人证据与生成卡在主目录的 `private-casework/`，不属于公开源码。没有把整本小说或 EPUB 原始插图加入公开发行内容。

本轮及后续默认按 Google Drive 文件夹交付。公共代码和私人案例由清单与 `.gitignore` 区分。第三方代码与许可见 `THIRD_PARTY_NOTICES.md`；项目自身整体许可证仍待权利人决定。

维护者在英文主目录修改核心与 `locales/zh-CN/`，然后执行：

```bash
python scripts/sync_source_skills.py
python scripts/build_release.py --sync-chinese
python scripts/build_release.py --check
python -m unittest discover -s tests -p test_yuri_sources.py -q
```

中文运行版不单独维护打包工具。更多实现边界见英文技术文档。

## 玩家视角与大输入（1.1.1）

第一人称主角通常绑定为 `{{user}}`，模型扮演对方。原作姓名保留在来源证据和作者说明，实际卡内的描述、开场和世界书统一用玩家宏；不再混用“发帖者”或“叙述者”。已有玩家人设仍需保留，当前动作、内心和回答由玩家决定。本轮两张第一人称卡已按反馈修复，具体角色分配使用项目内 `profile.player.json`，没有修改三个全局默认选项。

`--max-chars` 是文本节选选项，不是现有 JSON 角色卡或整本小说的总长度限制。完整长篇可运行：

```bash
python scripts/source_pipeline.py ingest novel.txt --kind novel --source-id book --project private-casework/book --all --chunk-chars 6000
python scripts/source_pipeline.py next-unit --project private-casework/book
python scripts/source_pipeline.py review-unit --project private-casework/book --unit book-000001
```

智能体逐个阅读单元、更新来源提取并标记已读，然后续接下一个单元。登记整本书不会把全文一次送给模型；未读单元不能自动计作已完整处理。图像较多的 EPUB 可另用 `--max-file-mib 256` 调整默认64 MiB输入字节保护，与每次阅读量分开。现有 JSON 检查器读取完整文件，不使用这个文本节选选项。详见英文 `docs/LARGE_INPUTS.md`。
