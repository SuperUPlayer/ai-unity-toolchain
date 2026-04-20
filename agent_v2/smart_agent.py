"""
智能 Agent V2 - 基于 LangGraph 预构建 ReAct Agent

使用 LangGraph 的 create_react_agent 替代手动循环，提供：
- 内置的 ReAct 循环（思考→工具调用→观察→判断）
- 自动的终止条件检测
- 持久化状态管理
- 更好的稳定性
"""

import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from tools.unity_tools import ALL_TOOLS


class UnitySmartAgent:
    """基于 LangGraph 的 Unity 开发智能 Agent"""

    def __init__(self, project_path: str = "."):
        self.project_path = project_path

        # 初始化 LLM（智谱 GLM-5，兼容 OpenAI 接口）
        self.llm = ChatOpenAI(
            model="glm-5",
            api_key=os.getenv("ZHIPU_API_KEY"),
            base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
            temperature=0.2,
            max_tokens=4096,
            max_retries=3,
        )

        # 使用预构建的 ReAct Agent
        # MemorySaver 提供状态持久化，支持多轮对话
        self.agent = create_react_agent(
            model=self.llm,
            tools=ALL_TOOLS,
            checkpointer=MemorySaver(),
            state_modifier=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """返回系统提示词"""
        return f"""你是一个 Unity 游戏开发 Agent，项目路径为 {self.project_path}。

## 你可以使用的工具
- read_file: 读取代码/配置文件
- write_file: 写入/创建文件（有安全限制，会自动备份）
- list_directory: 查看目录结构
- search_code: 在代码中搜索关键词
- git_diff: 查看 Git 变更
- find_file: 按文件名查找

## 工作原则
1. 先了解再动手：用 list_directory 和 search_code 了解项目结构和已有代码
2. 参考已有风格：读取相关文件，学习命名规范和架构模式
3. 生成后自查：生成代码后，自己审查一遍，检查：
   - Update 中是否有 GC Alloc（new、ToString、string拼接、LINQ）
   - GetComponent 是否在 Update 中调用
   - 事件订阅是否在 OnDestroy 中取消
   - 命名是否符合项目规范
4. 发现问题就修：自查发现问题后直接修复
5. 只做用户要求的事：不要跑去修别的文件
6. 每一步说清楚你在做什么和为什么

## Unity C# 编码规范
- 类名：PascalCase
- 私有字段：_camelCase
- 公开属性/方法：PascalCase
- 使用 [SerializeField] private 代替 public 字段
- 为公开方法添加 XML 注释

## 任务完成规则
- 当任务完成时，直接输出最终答案，不要继续调用工具
- 不要重复调用相同的工具获取相同的信息
- 不要在生成代码后反复修改同一个文件"""

    def run(self, user_request: str, max_rounds: Optional[int] = None, thread_id: str = "default") -> str:
        """
        运行 Agent

        Args:
            user_request: 用户请求
            max_rounds: 最大循环次数（None 表示使用默认值，通常为 25）
            thread_id: 会话线程 ID，用于多轮对话隔离

        Returns:
            Agent 的最终回复
        """
        config = {"configurable": {"thread_id": thread_id}}
        if max_rounds is not None:
            config["recursion_limit"] = max_rounds

        final_state = self.agent.invoke(
            {"messages": [("user", user_request)]},
            config=config,
        )

        # 提取最后一条消息作为结果
        messages = final_state.get("messages", [])
        if not messages:
            return "Agent 没有返回任何结果。"

        last_message = messages[-1]
        return last_message.content


# 快速测试
if __name__ == "__main__":
    agent = UnitySmartAgent(project_path=".")
    print("=" * 60)
    print("🤖 Smart Agent 测试（LangGraph 版）")
    print("=" * 60)

    result = agent.run("列出当前目录的结构，告诉我这个项目有哪些模块")
    print(result)