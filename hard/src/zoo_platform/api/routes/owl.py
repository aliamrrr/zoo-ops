from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from zoo_platform.api.deps import current_principal, get_container
from zoo_platform.api.schemas import AnswerRequest, AnswerResponse, FactUpdate
from zoo_platform.container import Container
from zoo_platform.domain.models import Principal

router = APIRouter(prefix="/v1/owl", tags=["owl"])


@router.post("/answers", response_model=AnswerResponse)
def ask(
    body: AnswerRequest,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> AnswerResponse:
    answer = container.owl.answer(body.question, body.temperature, principal)
    return AnswerResponse(answer=answer.text, model=answer.model)


@router.get("/stream")
def ask_streaming(
    question: str = Query(min_length=1, max_length=2_000),
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> AnswerResponse:
    answer = container.owl.answer(question, 0.0, principal)
    return AnswerResponse(answer=answer.text, model=answer.model)


@router.put("/facts/{topic}", status_code=204)
def update_fact(
    topic: str,
    body: FactUpdate,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> Response:
    container.owl.update_fact(topic, body.text)
    return Response(status_code=204)
