import asyncio                   #gives us async/await, sleep, and Future (used for the human-handoff pause)
from enum import Enum            # Enum backs our WorkflowState — gives us named, type-safe states
from fastapi import FastAPI
from typing import Any, Optional
from pydantic import BaseModel, Field  # request/response schemas with automatic validation


app = FastAPI(title = "AI ORCHESTRATION", version= "1.0")



# 1. State Machine Defination  

class WorkflowState(str,Enum):
    '''
    Enum is used to define a fixed set of valid states for the workflow.
    Enum is used here because the workflow can only have specific predefined states. 
    It prevents us from accidentally using invalid state names or typos.
    '''

    INTAKE = "intake"                        # query just recieved , not happened yet
    FETCHING_ORDER = "fetching_order"        # a tool call to order service is in flight
    NEEDS_APPROVAL =  "needs_approval"      # amount is high enough for a human must sign off
    PROCESSING = "processing"               # a tool call to payment service is in flight
    COMPLETE = "complete"                   #terminal state : refund success
    FAILED = "failed"                       #  terminal state : refund could not be processed


'''
this dict is the actual state machine - it says exactly which 
transaction are legal from each state. Trying to move to a state that
# isn't in this set is treated as a bug (see the `transition()` function
# below, which raises a RuntimeError if you try).

'''

ALLOWED_TRANSACTIONS:dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.INTAKE:{
        WorkflowState.FETCHING_ORDER,
        WorkflowState.FAILED, 
    },
    WorkflowState.FETCHING_ORDER:{
        WorkflowState.NEEDS_APPROVAL,
        WorkflowState.PROCESSING,
        WorkflowState.FAILED,
    },
    WorkflowState.NEEDS_APPROVAL:{
        WorkflowState.PROCESSING,
        WorkflowState.FAILED,
    }, 
    WorkflowState.PROCESSING:{
        WorkflowState.COMPLETE,
        WorkflowState.FAILED,
    },
    WorkflowState.COMPLETE: set(),
    WorkflowState.FAILED : set(), 

}

# refunds above this amount cannot be auto-approved and must
# go through the human-handoff step.
AUTO_APPROVE_THRESHOLD = 100.00


#2 . Data Models

class RefundRequest(BaseModel):
    order_id : str
    reason : str = Field(..., max_length= 3)


class WorkFlowEvent(BaseModel):
    timestamp : str
    state : WorkflowState
    message : str
    data : Optional[dict[str, Any]] = None


class Workflow(BaseModel):
    id : str
    state : WorkflowState
    order_id : str
    reason : str
    amount : Optional[float] = None   # filled in once we fetch the order
    events : list[WorkFlowEvent]= Field(default_factory=list)   # full audit trail
    error : Optional[str] = None    # populated only if the workflow ends in FAILED



'''
These two lines are creating in-memory storage for your orchestration system.
Why do we need it?
When a refund workflow starts, you need somewhere to remember its current state.
'''
WORKFLOWS : dict[str, Workflow] = {}

AUTO_APPROVAL_SIGNALS : dict[str, asyncio.Future ]= {}
'''
It stores waiting signals/futures for workflows that are waiting for approval.

WORKFLOWS
    ↓
"What workflows currently exist and what is their state?"

AUTO_APPROVAL_SIGNALS
    ↓
"Which workflows are currently waiting for an approval signal?"
'''

# 3. Simulated Tools
