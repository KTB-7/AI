# ------------------------------
import os
import operator
from config import OPENAI_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_KEY

from typing import Literal, Sequence, Annotated, List
from typing_extensions import TypedDict
import re

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
# ------------------------------
# import logging

# # 개별 로거 생성
# logger = logging.getLogger('lm_graph')
# logger.setLevel(logging.INFO)

# # FileHandler 생성 및 설정
# file_handler = logging.FileHandler('lm_graph_operations.log')
# file_handler.setLevel(logging.INFO)

# # 로그 포맷 설정
# formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# file_handler.setFormatter(formatter)

# # 핸들러가 이미 추가되지 않았다면 추가
# if not logger.hasHandlers():
#     logger.addHandler(file_handler)
# ------------------------------

# class overall_state(TypedDict):
#     topic: Annotated[list[str], operator.add]
#     image_url: Annotated[list[str], operator.add]
#     review_text: Annotated[list[str], operator.add]
#     tags: Annotated[list[str], operator.add]

class overall_state(TypedDict):
    topic: Annotated[list[str], operator.add]
    image_url: Annotated[list[str], operator.add]
    review_text: Annotated[list[str], operator.add]
    positive_tags: Annotated[list[str], operator.add]
    neutral_tags: Annotated[list[str], operator.add]
    negative_tags: Annotated[list[str], operator.add]
    verified_flag: Annotated[bool, operator.add]

from model_chain import correct_tag_to_korean
async def verify_tag(state: overall_state) -> overall_state:
    """Verify if the tags use both Korean and English and correct them to Korean only."""
    
    korean_regex = re.compile('[\uac00-\ud7a3]')
    english_regex = re.compile('[A-Za-z]')

    def is_mixed_language(tag: str) -> bool:
        return bool(korean_regex.search(tag) and english_regex.search(tag))

    async def process_tags(tags: List[str]) -> List[str]:
        corrected_tags = []
        for tag in tags:
            if is_mixed_language(tag):
                corrected = await correct_tag_to_korean(tag)
                corrected_tags.append(corrected)
            else:
                corrected_tags.append(tag)
        return corrected_tags

    new_state = overall_state()

    # 비동기로 태그 처리
    positive_tags = state.get("positive_tags", [])
    corrected_positive_tags = await process_tags(positive_tags)
    new_state["positive_tags"] = corrected_positive_tags

    # 필요 시 neutral_tags와 negative_tags도 동일하게 처리
    neutral_tags = state.get("neutral_tags", [])
    corrected_neutral_tags = await process_tags(neutral_tags)
    new_state["neutral_tags"] = corrected_neutral_tags

    negative_tags = state.get("negative_tags", [])
    corrected_negative_tags = await process_tags(negative_tags)
    new_state["negative_tags"] = corrected_negative_tags

    logger.info(f"Tags verified and corrected: {new_state['positive_tags']}, {new_state['neutral_tags']}, {new_state['negative_tags']}")

    new_state["verified_flag"] = True

    return {"verified_flag": new_state["verified_flag"], "positive_tags": new_state["positive_tags"], "neutral_tags": new_state["neutral_tags"], "negative_tags": new_state["negative_tags"]}
# ------------------------------
# tmp state
def tmp(state : overall_state):
    state["verified_flag"] = False
    logger.warning(f"tmp : Topic: {state['topic']}", f"Image URL: {state['image_url']}", f"Review Text: {state['review_text']}", f"Positive Tags: {state['positive_tags']}", f"Neutral Tags: {state['neutral_tags']}", f"Negative Tags: {state['negative_tags']}")
    logger.info(f"tmp 1 : Topic: {state['topic']}", f"Image URL: {state['image_url']}", f"Review Text: {state['review_text']}", f"Positive Tags: {state['positive_tags']}", f"Neutral Tags: {state['neutral_tags']}", f"Negative Tags: {state['negative_tags']}")
    print("concat", state["topic"], state["image_url"], state["review_text"], state["positive_tags"], state["neutral_tags"], state["negative_tags"])
    # print("tmp", state["topic"][-1], state["image_url"][-1], state["review_text"][-1], state["positive_tags"][-1], state["neutral_tags"][-1], state["negative_tags"][-1])
    return state

def tmp2(state : overall_state):
    logger.warning(f"tmp 2 : Topic: {state['topic']}", f"Image URL: {state['image_url']}", f"Review Text: {state['review_text']}", f"Positive Tags: {state['positive_tags']}", f"Neutral Tags: {state['neutral_tags']}", f"Negative Tags: {state['negative_tags']}")
    logger.info(f"tmp 2 : Topic: {state['topic']}", f"Image URL: {state['image_url']}", f"Review Text: {state['review_text']}", f"Positive Tags: {state['positive_tags']}", f"Neutral Tags: {state['neutral_tags']}", f"Negative Tags: {state['negative_tags']}")
    print("concat", state["topic"], state["image_url"], state["review_text"], state["positive_tags"], state["neutral_tags"], state["negative_tags"])
    # print("tmp", state["topic"][-1], state["image_url"][-1], state["review_text"][-1], state["positive_tags"][-1], state["neutral_tags"][-1], state["negative_tags"][-1])
    return {"positive_tags": state["positive_tags"], "neutral_tags": state["neutral_tags"], "negative_tags": state["negative_tags"], "verified_flag": state["verified_flag"]}
# ------------------------------
# conditional branching
def br_gene_topic(state: overall_state) -> Sequence[str]:
    logger.info(f"Topic: {state['topic'][0]}")
    if(state['topic'][0] == "VL"):
        return ["VLM_Tags", "LLM_Tags"]
    else:
        return ["LLM_Tags"]
    
def br_verify_korean(state: overall_state) -> Sequence[str]:
    korean_regex = re.compile('[\uac00-\ud7a3]')
    english_regex = re.compile('[A-Za-z]')

    flag = 0
    for tag in state["positive_tags"]:
        if (korean_regex.search(tag) and english_regex.search(tag)):
            flag = 1
    for tag in state["neutral_tags"]:
        if (korean_regex.search(tag) and english_regex.search(tag)):
            flag = 1
    for tag in state["negative_tags"]:
        if (korean_regex.search(tag) and english_regex.search(tag)):
            flag = 1

    logger.info(f"Korean-English mixed tags: {flag}, Verified flag: {state['verified_flag']}")

    if flag == 1 and state["verified_flag"] == False:
        return ["verify_tag"]
    else:
        return END
# ------------------------------
# construct vision graph
from model_chain import extract_image_hashtags
async def sub_vision_node(state: overall_state) -> overall_state:
    vlm_tags = await extract_image_hashtags(state["image_url"][0])
    # print(vlm_tags)
    logger.info(f"Vision tags: {vlm_tags}")
    return {"positive_tags": vlm_tags["positive_tags"], "neutral_tags": vlm_tags["neutral_tags"], "negative_tags": vlm_tags["negative_tags"]}

sub_vision_builder = StateGraph(overall_state)

sub_vision_builder.add_node("sub_vision_node", sub_vision_node)

sub_vision_builder.add_edge(START, "sub_vision_node")
sub_vision_builder.add_edge("sub_vision_node", END)

sub_vision_graph = sub_vision_builder.compile()
# ------------------------------
# construct language graph
from model_chain import extract_review_hashtags
async def sub_language_node(state: overall_state) -> overall_state:
    llm_tags = await extract_review_hashtags(state["review_text"][0])
    # print(llm_tags)
    logger.info(f"Language tags: {llm_tags}")
    return {"positive_tags": llm_tags["positive_tags"], "neutral_tags": llm_tags["neutral_tags"], "negative_tags": llm_tags["negative_tags"]}

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
builder.add_node("concat", tmp2)
builder.add_node("verify_tag", verify_tag)

builder.add_edge(START, "Generate_Tags")
builder.add_conditional_edges("Generate_Tags", br_gene_topic, ["VLM_Tags", "LLM_Tags"])
builder.add_edge("VLM_Tags", "concat")
builder.add_edge("LLM_Tags", "concat")
builder.add_conditional_edges("concat", br_verify_korean, ["verify_tag", END])
builder.add_edge("verify_tag", "concat")
# builder.add_edge("concat", END)

graph = builder.compile()
# ------------------------------
# graph 예시
# ret = graph.invoke({"topic": ["VL"], "image_url": ["/Users/yangtaegyu/test/AI/dummy/airplane.jpg"], "review_text": ["시원하고 분위기 좋음. 블루보틀은 여기로 처음 와봤는데 내부 인테리어가 깔끔하고 미니멀함."]})
# print(ret)
# print(ret['tags'])
# ------------------------------
# graph image 생성
from IPython.display import Image, display # type: ignore

image = Image(graph.get_graph().draw_mermaid_png())

with open("graph_image.png", "wb") as file:
    file.write(image.data)
# ------------------------------