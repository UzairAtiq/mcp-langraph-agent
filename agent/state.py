from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated
import operator

#Defininf the message state manually 
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    llm_calls: int


