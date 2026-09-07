from fastapi import FastAPI
from enum import Enum


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