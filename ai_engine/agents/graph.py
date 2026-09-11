from langgraph.graph  import StateGraph, START, END
from ai_engine.agents.state import AgentState
from ai_engine.agents.nodes.evaluator import evaluate_ats_node
from ai_engine.agents.nodes.rewriter import rewriter_bullets_node
from ai_engine.agents.nodes.generator import generate_docs_node

agent_workflow  = StateGraph(AgentState)

# Add nodes

agent_workflow.add_node("evaluate_ats", evaluate_ats_node)
agent_workflow.add_node("rewriter_bullets", rewriter_bullets_node)
agent_workflow.add_node("generator_docs", generate_docs_node)

# Flow -> Connecting edges between nodes
agent_workflow.add_edge(START, "evaluate_ats")
agent_workflow.add_edge("evaluate_ats", "rewriter_bullets")
agent_workflow.add_edge("rewriter_bullets", "generator_docs")
agent_workflow.add_edge("generator_docs", END)

compiled_workflow = agent_workflow.compile()


