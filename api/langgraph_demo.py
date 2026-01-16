from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class InputState(TypedDict):
    question: str


class OutputState(TypedDict):
    answer: str


class OverallState(InputState, OutputState):
    pass


def run_demo(question: str) -> OutputState:
    def answer_node(state: InputState) -> dict:
        return {"answer": f"bye — you said: {state['question']}", "question": state["question"]}

    builder = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)
    builder.add_node(answer_node)
    builder.add_edge(START, "answer_node")
    builder.add_edge("answer_node", END)

    graph = builder.compile()
    return graph.invoke({"question": question})
