"""
LangGraph 多 Agent 协作工作流

5 个 Agent 接力完成一个完整的游戏开发任务：
规划 → 配置 → 代码 → 审查 → (重试?) → 测试 → 完成
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from .smart_agent import UnitySmartAgent


# =============================================
# 1. 定义共享状态（在 Agent 之间传递的数据）
# =============================================

class GameDevState(TypedDict):
    requirement: str       # 用户原始需求
    project_path: str      # Unity 项目路径
    plan: str              # 规划 Agent 输出
    config_result: str     # 配置 Agent 输出
    code_result: str       # 代码 Agent 输出
    review_result: str     # 审查 Agent 输出
    test_result: str       # 测试 Agent 输出
    review_passed: bool    # 审查是否通过
    retry_count: int       # 代码重试次数
    final_report: str      # 最终报告


# =============================================
# 2. 定义每个 Agent 节点
# =============================================

def planner_node(state: GameDevState) -> dict:
    """规划 Agent：分析需求，决定要做哪些步骤"""
    agent = UnitySmartAgent(state["project_path"])
    result = agent.run(f"""分析以下游戏开发需求，制定执行计划：

需求：{state['requirement']}

请用 list_directory 查看项目结构后，输出：
1. 需求理解（一句话总结）
2. 是否需要生成配置文件（是/否）
3. 需要生成哪些代码文件（列出文件名和作用）
4. 是否需要生成测试（是/否）
5. 需要参考哪些已有文件（列出路径）
""", max_rounds=10)
    print(f"\n📋 规划完成")
    return {"plan": result}


def config_node(state: GameDevState) -> dict:
    """配置 Agent：生成游戏配置 JSON"""
    # 如果规划里明确说不需要配置，跳过
    if "不需要" in state.get("plan", "") and "配置" in state.get("plan", ""):
        return {"config_result": "（不需要配置文件）"}

    agent = UnitySmartAgent(state["project_path"])
    result = agent.run(f"""生成游戏配置文件：

原始需求：{state['requirement']}
规划：{state['plan']}

步骤：
1. 用 search_code 搜索已有配置文件了解格式
2. 生成 JSON 配置
3. 用 write_file 保存到 Configs/ 目录
""", max_rounds=15)
    print(f"\n📦 配置生成完成 - 文件路径: {result}")
    return {"config_result": result}


def code_node(state: GameDevState) -> dict:
    """代码 Agent：生成 C# 代码"""
    agent = UnitySmartAgent(state["project_path"])

    context_parts = [f"原始需求：{state['requirement']}", f"规划：{state['plan']}"]

    if state.get("config_result") and state["config_result"] != "（不需要配置文件）":
        context_parts.append(f"已生成的配置：{state['config_result'][:2000]}")

    # 如果是重试，带上审查意见
    if state.get("review_result") and not state.get("review_passed"):
        context_parts.append(
            f"\n⚠️ 上次审查发现的问题（你必须修复这些问题）：\n{state['review_result'][:3000]}"
        )

    combined = "\n\n".join(context_parts)

    result = agent.run(f"""生成简单的 Unity C# 代码：

需求：做一个简单的计时器系统，支持倒计时和暂停功能

生成一个简单的 Timer.cs 文件，包含基本的倒计时和暂停功能。

用 write_file 保存到 Assets/Scripts/Timer.cs
""", max_rounds=15)
    print(f"\n💻 代码生成完成 - 文件路径: {result}")
    return {"code_result": result}


def review_node(state: GameDevState) -> dict:
    """验证 Agent：验证生成的代码"""
    agent = UnitySmartAgent(state["project_path"])
    result = agent.run(f"""验证以下刚生成的代码：

代码生成报告：
{state['code_result'][:4000]}

验证要求：
1. 检查代码是否可编译
2. 检查是否有明显错误
3. 检查命名是否合理

输出格式：
- 列出所有问题（如果有）
- 最后一行必须写：REVIEW_PASSED 或 REVIEW_FAILED
""", max_rounds=15)

    passed = "REVIEW_PASSED" in result
    print(f"\n🔍 验证{'通过 ✅' if passed else '未通过 ❌'}")
    return {"review_result": result, "review_passed": passed}


def test_node(state: GameDevState) -> dict:
    """测试 Agent：生成单元测试"""
    agent = UnitySmartAgent(state["project_path"])
    result = agent.run(f"""为刚生成的代码编写单元测试：

代码生成报告：
{state['code_result'][:3000]}

要求：
1. 用 read_file 读取生成的代码文件
2. 为每个公开方法生成测试：正常路径 + 边界条件 + 异常处理
3. 使用 NUnit + Unity Test Framework
4. 用 write_file 保存到 Assets/Tests/ 目录
""", max_rounds=15)
    print(f"\n🧪 测试生成完成 - 文件路径: {result}")
    return {"test_result": result}


def report_node(state: GameDevState) -> dict:
    """汇总最终报告"""
    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 任务完成！

📋 需求：{state['requirement']}

📦 配置：{state.get('config_result', '无')[:500]}

💻 代码：{state.get('code_result', '无')[:500]}

🔍 审查：{'通过' if state.get('review_passed') else '未通过（已达重试上限）'}

🧪 测试：{state.get('test_result', '无')[:500]}

🔄 代码重试次数：{state.get('retry_count', 0)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(report)
    return {"final_report": report}


# =============================================
# 3. 条件分支：审查没通过就重试
# =============================================

def should_retry(state: GameDevState) -> str:
    """决定审查后的下一步"""
    if state.get("review_passed"):
        return "passed"  # 通过 → 生成测试
    if state.get("retry_count", 0) >= 2:
        return "max_retries"  # 重试超限 → 强制继续
    return "retry"  # 没通过 → 重新生成代码


def increment_retry(state: GameDevState) -> dict:
    """重试计数器 +1"""
    return {"retry_count": state.get("retry_count", 0) + 1}


# =============================================
# 4. 组装流程图
# =============================================

def build_workflow():
    """构建 LangGraph 工作流"""
    workflow = StateGraph(GameDevState)

    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("config", config_node)
    workflow.add_node("code", code_node)
    workflow.add_node("review", review_node)
    workflow.add_node("increment_retry", increment_retry)
    workflow.add_node("test", test_node)
    workflow.add_node("report", report_node)

    # 连接流程
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "config")
    workflow.add_edge("config", "code")
    workflow.add_edge("code", "review")

    # 审查后的条件分支
    workflow.add_conditional_edges(
        "review",
        should_retry,
        {
            "passed": "test",             # 通过 → 生成测试
            "retry": "increment_retry",   # 没通过 → 增加计数 → 重新生成
            "max_retries": "test",        # 超限 → 强制继续
        },
    )
    workflow.add_edge("increment_retry", "code")  # 重试回到代码生成
    workflow.add_edge("test", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


# =============================================
# 5. 使用入口
# =============================================

def run_workflow(requirement: str, project_path: str = ".") -> dict:
    """运行完整的多 Agent 工作流"""
    app = build_workflow()

    print("━" * 50)
    print(f"🎯 启动多 Agent 工作流")
    print(f"   需求: {requirement}")
    print("━" * 50)

    result = app.invoke({
        "requirement": requirement,
        "project_path": project_path,
        "retry_count": 0,
        "review_passed": False,
    })

    return result


# ===== 快速测试 =====
if __name__ == "__main__":
    result = run_workflow(
        requirement="做一个简单的计时器系统，支持倒计时和暂停功能",
        project_path=".",
    )