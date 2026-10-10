# paper-writing

A reusable Codex skill for research proposals, academic papers, and defense materials.

一个中文科研写作技能，整理从方案讨论到成稿交付的协作经验，尤其适合研究生开题报告与临床观察性研究。重点是自然的学术表达、可核查的文献依据、明确的变量与方法，以及Word、PPT和讲稿的一致性。

## 内容

技能包含9个参考专题和64项常见问题索引，涵盖方案讨论与提问、报告结构、文献引用、研究设计、变量定义、统计规划与样本量、数据及图表、文件交付、答辩与自我复核。另附一个只读Word结构检查脚本。

公开版保留通用经验，具体研究的对象、数据、阈值、伦理和方案由使用者提供。本仓库不包含原项目的患者资料、内部研究记录或未公开分析结果。

## 安装到Codex

### 让Codex安装

向Codex发送：

```text
请使用 $skill-installer，从 https://github.com/beddomedevichou110-png/beddomechou/tree/main/paper-writing 安装 paper-writing 技能。
```

### 手动安装

1. 在本仓库点击 Code → Download ZIP，然后解压。
2. 将其中完整的 `paper-writing` 文件夹放入个人技能目录；保留 `references`、`agents` 和 `scripts`。
3. Windows目录为 `%USERPROFILE%\.agents\skills\paper-writing`；macOS/Linux为 `~/.agents/skills/paper-writing`。
4. 确认 `SKILL.md` 直接位于上述 `paper-writing` 文件夹内。若Codex尚未显示技能，重启Codex。

安装目录、自动发现及重启说明依据[OpenAI官方技能文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。不同客户端版本的目录规则以其当前文档和安装器为准。

## 使用示例

```text
请使用 $paper-writing，读取我的开题报告和修改意见，只修订研究方法部分，保留原格式和其他章节。
```

```text
请使用 $paper-writing，核对我的主要结局、随访窗口、样本量参数及文献依据，先列出需要讨论的决定。
```

```text
请使用 $paper-writing，根据最新版报告核对PPT与讲稿，并给出评委可能追问的问题。
```

默认可由Codex按任务匹配选择，也可通过 `$paper-writing` 明确调用。使用者提供当前底稿、模板和项目约定，技能按本轮要求处理。

## 可选Word检查

常规写作无需额外安装Python依赖。运行附带检查脚本时需Python 3.10或更高版本，脚本只使用标准库：

```text
python paper-writing/scripts/audit_docx_preferences.py report.docx --baseline original.docx --json audit.json
```

检查范围是Word主体段落与样式继承中的分页属性、折叠层级、标题边框及EndNote/Zotero域指令数量。脚本不修改输入Word；输出JSON保存到另一个文件。视觉版式、完整引文结构和科学内容另行核对。

## 目录

```text
paper-writing/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/audit_docx_preferences.py
```

环境中如有文档、演示文稿、文献或anti-ai-defensive-writing等相关技能，可按任务协同使用；本技能本身不要求连接特定文献管理器或外部服务。
