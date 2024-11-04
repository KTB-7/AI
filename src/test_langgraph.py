# ------------------------------
import os
import operator
from config import OPENAI_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

from typing import Literal, Sequence, Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
# ------------------------------

model = ChatOpenAI(model="gpt-4o-mini")

class overall_state(TypedDict):
    topic: Annotated[list[str], operator.add]
    image_url: Annotated[list[str], operator.add]
    review_text: Annotated[list[str], operator.add]
    tags: Annotated[list[str], operator.add]

# ------------------------------
def tmp(state : overall_state):
    print(state["topic"], state["image_url"], state["review_text"], state["tags"])
    return 
    
def br_gene_topic(state: overall_state) -> Sequence[str]:
    if(state['topic'][0] == "VL"):
        return ["VLM_Tags", "LLM_Tags"]
    else:
        return ["LLM_Tags"]
# ------------------------------
# construct vision graph
def sub_vision_node(state: overall_state) -> overall_state:
    print(state["topic"])
    return

sub_vision_builder = StateGraph(overall_state)

sub_vision_builder.add_node("sub_vision_node", sub_vision_node)

sub_vision_builder.add_edge(START, "sub_vision_node")
sub_vision_builder.add_edge("sub_vision_node", END)

sub_vision_graph = sub_vision_builder.compile()
# ------------------------------
# construct language graph
from tmp_chain import extract_review_hashtags
def sub_language_node(state: overall_state) -> overall_state:
    print(state["topic"])
    llm_tags = extract_review_hashtags(state["review_text"][0])
    print(llm_tags)
    print(llm_tags["tags"])
    print(llm_tags["index"])
    # print(llm_tags[0])
    return {"tags": llm_tags["tags"]}

sub_language_builder = StateGraph(overall_state)

sub_language_builder.add_node("sub_language_node", sub_language_node)

sub_language_builder.add_edge(START, "sub_language_node")
sub_language_builder.add_edge("sub_language_node", END)

sub_language_graph = sub_language_builder.compile()
# ------------------------------
# construct main graph
builder = StateGraph(overall_state)

builder.add_node("Generate_Tags", tmp)
builder.add_node("VLM_Tags", sub_vision_graph)
builder.add_node("LLM_Tags", sub_language_graph)
builder.add_node("concat", tmp)

builder.add_edge(START, "Generate_Tags")
builder.add_conditional_edges("Generate_Tags", br_gene_topic, ["VLM_Tags", "LLM_Tags"])
builder.add_edge("VLM_Tags", "concat")
builder.add_edge("LLM_Tags", "concat")
builder.add_edge("concat", END)

graph = builder.compile()
# ------------------------------
# for chunk in graph.stream({"topic": ["VL"], "image_url": ["1234"]}):
#     print(chunk)

graph.invoke({"topic": ["VL"], "image_url": ["1234"], "review_text": ["빽다방 별로에요 맛이 없어요"]})
# ------------------------------
# graph image 생성
from IPython.display import Image, display # type: ignore

image = Image(graph.get_graph().draw_mermaid_png())

with open("graph_image.png", "wb") as file:
    file.write(image.data)
# ------------------------------