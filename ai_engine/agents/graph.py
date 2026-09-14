from langgraph.graph  import StateGraph, START, END
from ai_engine.agents.state import AgentState
from ai_engine.agents.nodes.evaluator import evaluate_ats_node, re_evaluate_tailored_ats_node
from ai_engine.agents.nodes.tailor_resume import tailor_resume_node
from ai_engine.agents.nodes.rewriter import rewriter_bullets_node
from ai_engine.agents.nodes.generator import generate_docs_node

agent_workflow  = StateGraph(AgentState)

# Add nodes

agent_workflow.add_node("evaluate_ats", evaluate_ats_node)
agent_workflow.add_node("tailor_resume", tailor_resume_node)
agent_workflow.add_node("rewriter_bullets", rewriter_bullets_node)
agent_workflow.add_node("generator_docs", generate_docs_node)
agent_workflow.add_node("re_evaluate_ats", re_evaluate_tailored_ats_node)

# Flow -> Connecting edges between nodes
agent_workflow.add_edge(START, "evaluate_ats")
agent_workflow.add_edge("evaluate_ats", "tailor_resume")
agent_workflow.add_edge("tailor_resume", "rewriter_bullets")
agent_workflow.add_edge("rewriter_bullets", "generator_docs")
agent_workflow.add_edge("generator_docs", "re_evaluate_ats")
agent_workflow.add_edge("re_evaluate_ats", END)

compiled_workflow = agent_workflow.compile()


