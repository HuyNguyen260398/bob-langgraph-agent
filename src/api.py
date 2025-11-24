"""FastAPI server for Bob LangGraph Agent."""

import os
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import BobAgent
from config import BobConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global agent instance
agent: Optional[BobAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    global agent

    # Startup: Initialize the agent
    logger.info("Initializing Bob LangGraph Agent...")
    try:
        config = BobConfig.from_env()
        agent = BobAgent(config)
        logger.info(f"✅ Agent initialized successfully (Model: {config.model_name})")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Bob LangGraph Agent...")


# Create FastAPI app
app = FastAPI(
    title="Bob LangGraph Agent API",
    description="API server for Bob, a helpful AI assistant and operations buddy",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message to send to the agent")
    thread_id: Optional[str] = Field(
        default="default", description="Conversation thread ID"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="Agent's response")
    thread_id: str = Field(..., description="Conversation thread ID")


class HistoryResponse(BaseModel):
    """Response model for conversation history."""

    thread_id: str
    messages: List[Dict[str, Any]]
    message_count: int


class SummaryResponse(BaseModel):
    """Response model for conversation summary."""

    thread_id: str
    summary: str


class AnalysisResponse(BaseModel):
    """Response model for conversation analysis."""

    thread_id: str
    analysis: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model: Optional[str] = None


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Bob LangGraph Agent API",
        "version": "1.0.0",
        "description": "Your AI Operations Buddy",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return HealthResponse(status="healthy", model=agent.config.model_name)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with Bob agent.

    Send a message to the agent and receive a response.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        logger.info(
            f"Chat request - Thread: {request.thread_id}, Message: {request.message[:50]}..."
        )
        response = agent.chat(request.message, thread_id=request.thread_id)

        return ChatResponse(response=response, thread_id=request.thread_id)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses from Bob agent.

    Returns a streaming response as the agent processes the message.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    async def generate():
        try:
            logger.info(f"Stream chat request - Thread: {request.thread_id}")
            for update in agent.stream_chat(
                request.message, thread_id=request.thread_id
            ):
                # Extract response from update
                if "agent_response" in update:
                    agent_response = update["agent_response"]
                    if hasattr(agent_response, "content"):
                        content = agent_response.content
                    elif isinstance(agent_response, str):
                        content = agent_response
                    else:
                        continue

                    # Yield as Server-Sent Events format
                    yield f"data: {content}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/history/{thread_id}", response_model=HistoryResponse)
async def get_history(thread_id: str):
    """
    Get conversation history for a thread.

    Returns all messages in the conversation thread.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        messages = agent.get_conversation_history(thread_id=thread_id)

        # Convert messages to serializable format
        serializable_messages = []
        for msg in messages:
            if hasattr(msg, "content"):
                msg_type = "human" if msg.__class__.__name__ == "HumanMessage" else "ai"
                serializable_messages.append({"type": msg_type, "content": msg.content})

        return HistoryResponse(
            thread_id=thread_id,
            messages=serializable_messages,
            message_count=len(serializable_messages),
        )
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@app.get("/summary/{thread_id}", response_model=SummaryResponse)
async def get_summary(thread_id: str):
    """
    Get a summary of the conversation thread.

    Returns an AI-generated summary of the conversation.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        summary = agent.get_conversation_summary(thread_id=thread_id)

        return SummaryResponse(thread_id=thread_id, summary=summary)
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate summary: {str(e)}"
        )


@app.get("/analysis/{thread_id}", response_model=AnalysisResponse)
async def get_analysis(thread_id: str):
    """
    Get detailed analysis of the conversation thread.

    Returns metadata and insights about the conversation.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        analysis = agent.get_conversation_analysis(thread_id=thread_id)

        return AnalysisResponse(thread_id=thread_id, analysis=analysis)
    except Exception as e:
        logger.error(f"Analysis generation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate analysis: {str(e)}"
        )


@app.delete("/thread/{thread_id}")
async def clear_thread(thread_id: str):
    """
    Clear conversation history for a thread.

    Removes all messages and state for the specified thread.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        success = agent.clear_conversation(thread_id=thread_id)

        if success:
            return {"status": "cleared", "thread_id": thread_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear thread")
    except Exception as e:
        logger.error(f"Thread clearing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear thread: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
