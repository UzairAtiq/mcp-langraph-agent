from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator

#Defininf the message state manually 
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


