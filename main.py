from fastapi import FastAPI
from enum import Enum
from pydantic import BaseModel , Field
from typing import Any, Optional
import asyncio


app = FastAPI(title = "AI orchestration Demo", version="1.0")


#  1. STATE MACHINE DEFINITION

class WorkFlowState(str, Enum):
    INTAKE = "intake"
    FETCHING_ORDER = "fetching_order"
    NEEDS_APPROVAL = "needs_approval"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"

ALLOWED_TRANSITIONS : dict[WorkFlowState, set[WorkFlowState]]= {
    WorkFlowState.INTAKE: {
        WorkFlowState.FETCHING_ORDER,
        WorkFlowState.FAILED,
    },
    WorkFlowState.FETCHING_ORDER:{
        WorkFlowState.NEEDS_APPROVAL,
        WorkFlowState.PROCESSING,
        WorkFlowState.FAILED,
    },
    WorkFlowState.NEEDS_APPROVAL:{
        WorkFlowState.PROCESSING,
        WorkFlowState.FAILED,
    },
    WorkFlowState.PROCESSING:{
        WorkFlowState.COMPLETE,
        WorkFlowState.FAILED,
    },
    WorkFlowState.COMPLETE:set(),
    WorkFlowState.FAILED : set(),
}

AUTO_APPROVE_THRESHOLD = 100.00

# Data Models

class RefundRequest(BaseModel):
    # whats the caller sends us to kick off a new refund workflow 
    order_id : str
    reason : str = Field(..., min_length= 3)


class WorkflowEvent(BaseModel):
    timestamp : str
    state : WorkFlowState
    message : str
    data : Optional[dict[str, Any]] = None


class Workflow(BaseModel):
    id : str
    state : WorkFlowState
    order_id : str
    reason : str
    amount : Optional[float] = None
    events : list[WorkflowEvent] = Field(default_factory= list)
    error : Optional[str] = None



WORKFLOWS : dict[str, Workflow]= {}

APPROVAL_SIGNALS : dict[str, asyncio.Future] = {}