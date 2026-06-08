token = ""
url = ""
model = ""

# ----------
# 串接 OpenAI Compatible API
# ----------
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    model=model,
    api_key=token,
    base_url=url,
    temperature=0.2
)

# ----------
# LangGraph ReAct 實作
# ---------
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

@tool
def code_search_tool(query: str) -> str:
    """搜尋 codebase 中的特定函式或類別。"""
    return "mocked search result"
tools = [code_search_tool]
react_agent = create_react_agent(llm, tools)

# ----------
# Master-Slave Agent 架構設計
# ----------
from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, START, END, Send
from pydantic import BaseModel, Field

# 定義子任務的資料結構
class SubTask(BaseModel):
    task_id: str
    description: str
    spec: str
    acceptance_criteria: str
    status: str = Field(default="pending")

# 子 Agent 圖的 State
class SubAgentState(TypedDict):
    task: SubTask
    current_code: str
    verification_feedback: str
    is_valid: bool
    communication_history: List[str]
    completed_results: List[dict]

# 主 Graph 的 State
class OverallState(TypedDict):
    objective: str
    tasks: List[SubTask]
    completed_results: Annotated[List[dict], operator.add] # 透過 reducer 聚合所有子 Agent 的產出
    final_summary: str

# ----------
# sub-Agent Workflow：執行、溝通與驗證迴圈 (Sub-Graph)
# ---------
def sub_executor(state: SubAgentState):
    # 這裡實作子 Agent 的 ReAct 邏輯
    # 它可以根據 task.description 呼叫工具、判斷是否需要與其他 Agent 溝通（讀寫共享記憶體/DB）
    # 最終產出 current_code
    code = llm.invoke(f"實作任務: {state['task'].spec}")
    return {"current_code": code.content}

def sub_verifier(state: SubAgentState):
    verification_result = llm.invoke(
        f"驗證此程式碼是否符合標準: {state['task'].acceptance_criteria}\nCode: {state['current_code']}"
    )
    is_passed = "PASS" in verification_result.content 
    
    # 關鍵：若驗證通過，將結果封裝進 completed_results 以便主 Graph 的 reducer 進行聚合
    result_payload = {}
    if is_passed:
         result_payload["completed_results"] = [{
             "task_id": state['task'].task_id, 
             "code": state['current_code']
         }]
         
    return {
        "is_valid": is_passed, 
        "verification_feedback": verification_result.content,
        **result_payload
    }

def check_verification(state: SubAgentState):
    if state["is_valid"]:
        return "Done"
    return "Retry"

# 建構子 Agent Graph
sub_builder = StateGraph(SubAgentState)
sub_builder.add_node("Executor", sub_executor)
sub_builder.add_node("Verifier", sub_verifier)
sub_builder.add_edge(START, "Executor")
sub_builder.add_edge("Executor", "Verifier")
sub_builder.add_conditional_edges(
    "Verifier",
    check_verification,
    {"Done": END, "Retry": "Executor"} # 這裡形成了 While Loop
)
sub_agent_graph = sub_builder.compile()

# ----------
# master-Agent Workflow：任務分解、子 Agent 管理與結果整合 (Master-Graph)
# ---------
def main_planner(state: OverallState):
    # 主 Agent 根據 objective 規劃 Spec 與 Acceptance Criteria
    # 將大目標切分為多個 SubTask
    planned_tasks = [
        SubTask(task_id="T1", description="DB Schema", spec="...", acceptance_criteria="..."),
        SubTask(task_id="T2", description="API Router", spec="...", acceptance_criteria="...")
    ]
    return {"tasks": planned_tasks}

def parallel_dispatcher(state: OverallState):
    # Map-Reduce 模式：為每一個 Task 動態建立一個子 Agent 工作流
    sends = []
    for task in state["tasks"]:
        # 將狀態封裝並送往子 Agent Graph
        sends.append(Send("Sub_Agent_Workflow", {"task": task, "is_valid": False}))
    return sends

def main_aggregator(state: OverallState):
    # 所有的 Sub_Agent_Workflow 完成後，這個節點才會觸發
    # 彙整 state["completed_results"] 並將所有任務標記為 Done
    for task in state["tasks"]:
        task.status = "done"
    return {"tasks": state["tasks"]}

def main_summarizer(state: OverallState):
    # 根據所有完成的結果，總結整體專案的執行狀況
    summary = llm.invoke(f"總結以下完成的模組: {state['completed_results']}")
    return {"final_summary": summary.content}

# 建構主 Graph
main_builder = StateGraph(OverallState)
main_builder.add_node("Planner", main_planner)
# 將先前編譯好的 sub_agent_graph 作為一個節點加入
main_builder.add_node("Sub_Agent_Workflow", sub_agent_graph) 
main_builder.add_node("Aggregator", main_aggregator)
main_builder.add_node("Summarizer", main_summarizer)

main_builder.add_edge(START, "Planner")
# Planner 完成後，觸發 Dispatcher 進行平行展開
main_builder.add_conditional_edges("Planner", parallel_dispatcher, ["Sub_Agent_Workflow"])
# 所有子節點結束後，匯流至 Aggregator
main_builder.add_edge("Sub_Agent_Workflow", "Aggregator")
main_builder.add_edge("Aggregator", "Summarizer")
main_builder.add_edge("Summarizer", END)

final_system = main_builder.compile()

if __name__ == "__main__":
    # 1. 定義主節點的初始狀態 (Initial State)
    initial_state = {
        "objective": "開發一個支援 JWT 驗證的 RESTful API 登入模組",
        # tasks, completed_results, final_summary 將在流程中被動態生成
    }

    print("🚀 啟動 Main-Sub Agent 系統，開始解析流程...")
    
    # 2. 透過 stream 逐步觀察每個節點的狀態變化
    # stream_mode="updates" 可以讓我們精準攔截每個節點對 State 造成的改變 (State Mutation)
    for event in final_system.stream(initial_state, stream_mode="updates"):
        for node_name, state_update in event.items():
            print(f"\n[執行節點] ➡️ {node_name}")
            
            # 觀察 Planner 的任務拆解
            if node_name == "Planner":
                tasks = state_update.get('tasks', [])
                print(f"✅ 規劃完成，共拆解 {len(tasks)} 項子任務:")
                for t in tasks:
                    print(f"   - [{t.task_id}] {t.description} (Status: {t.status})")
                    
            # 觀察 Sub_Agent_Workflow 平行展開的回傳
            elif node_name == "Sub_Agent_Workflow":
                results = state_update.get('completed_results', [])
                print(f"✅ 子 Agent 任務完成並回傳。目前累積成果數: {len(results)}")
                
            # 觀察主 Graph 最終匯合
            elif node_name == "Aggregator":
                print(f"✅ 所有平行任務皆已整合，將任務狀態標記為 Done。")
                
            elif node_name == "Summarizer":
                print(f"\n======== 最終總結報告 ========\n{state_update.get('final_summary')}")
