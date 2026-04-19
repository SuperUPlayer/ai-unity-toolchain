# Unity AI 研发工具链 — 第一部分：问答式 CLI 工具集

> 基于智谱 GLM-5 的 Unity 开发辅助工具，支持代码审查、代码生成、配置生成、测试生成，并集成 GitHub Actions 实现 PR 自动 AI 审查。

## 目录
- [功能概览](#-功能概览)
- [快速开始](#-快速开始)
- [使用示例](#-使用示例)
- [GitHub Actions 自动审查](#-github-actions-自动审查)
- [后续计划（第二部分）](#-后续计划第二部分)
---

## 功能概览

| 模块 | 说明 |
|------|------|
| 代码审查 | 检测 Unity C# 代码中的性能问题、GC 分配、资源泄漏、空引用风险等 |
| 代码生成 | 根据自然语言描述生成完整可编译的 Unity C# 代码 |
| 配置生成 | 生成结构化游戏配置 JSON，支持参考已有配置、ID 自增、数值校验 |
| 测试生成 | 基于 NUnit + Unity Test Framework 自动生成单元测试 |
| PR 自动审查 | GitHub Actions 自动审查 PR 中的 C# 变更并评论结果 |

---

## 快速开始

### 1. 环境要求
- Python 3.10+
- 智谱 AI API Key（[获取地址](https://open.bigmodel.cn/)）
- Git（用于克隆仓库）

### 2. 安装步骤
```bash
git clone https://github.com/SuperUPlayer/ai-unity-toolchain.git
cd ai-unity-toolchain
python -m venv venv
```

#### Windows 激活环境
```bash
venv\Scripts\activate
```

#### macOS/Linux 激活环境
```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
#### Windows（临时）
```cmd
set ZHIPU_API_KEY=你的密钥
```

#### Windows（永久）
系统属性 → 环境变量 → 新建系统变量 `ZHIPU_API_KEY`，填入你的智谱 API Key，重启命令行生效。

#### macOS/Linux（临时）
```bash
export ZHIPU_API_KEY="你的密钥"
```

#### macOS/Linux（永久）
```bash
echo 'export ZHIPU_API_KEY="你的密钥"' >> ~/.bashrc
source ~/.bashrc
```

### 4. 修改配置文件（可选）
编辑 `config/settings.yaml`，可调整模型、温度、max_tokens 等参数，适配自身使用需求。

---

## 使用示例

### 1. 代码审查
```bash
# 审查单个C#文件
python main.py review Assets/Scripts/PlayerController.cs
# 审查指定目录下所有C#文件
python main.py review Assets/Scripts/Combat/
# 审查Git变更的代码
python main.py review-diff
```

### 2. 代码生成
```bash
python main.py gen "创建一个对象池系统，支持泛型和自动扩容" -p Assets/Scripts -o generated/
```

### 3. 配置生成
```bash
python main.py config "新英雄：火焰法师，高爆发，技能包含火球术、火焰冲击" -c Configs/Heroes/ -o generated/fire_mage.json
```

### 4. 测试生成
```bash
python main.py test Assets/Scripts/Combat/DamageSystem.cs -o generated/
```

> 生成的文件默认保存在 `generated/` 目录，确认代码无误后，手动复制到 Unity 项目对应路径即可。

---

## GitHub Actions 自动审查

### 1. 配置密钥
1. 进入 GitHub 仓库 → Settings → Secrets and variables → Actions
2. 点击「New repository secret」，名称填写 `ZHIPU_API_KEY`，值填写你的智谱 API Key，保存即可。

### 2. 触发规则
当 Pull Request 修改 `Assets/Scripts/**/*.cs` 路径下的 C# 文件时，将自动触发 AI 审查流程。

### 3. 审查输出
AI 会在 PR 评论区自动输出审查结果，包括：代码质量评分、存在的问题（性能/规范/安全）、具体修复建议。

---

## 后续计划（第二部分）
1. 基于 LangChain + LangGraph 实现多 Agent 协作，完成代码审查→生成→测试全流程自动化
2. 开发 AI 自主探索项目功能，实现代码自审、自修，减少人工干预
3. 增加安全防护机制，包括路径白名单、API 速率限制、Token 预算控制，降低使用风险
