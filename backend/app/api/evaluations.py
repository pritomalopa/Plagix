from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.question import Question
from app.models.rubric_criterion import RubricCriterion
from app.api.deps import get_current_user
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationResponse,
    EvaluationListResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    RubricCriterionCreate,
    RubricCriterionUpdate,
    RubricCriterionResponse,
)

router = APIRouter(prefix="/evaluations", tags=["Evaluations & Questions"])


def verify_evaluation_ownership(eval_id: UUID, current_user: User, db: Session) -> Evaluation:
    """Helper to verify evaluation exists and belongs to current user's tenant."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    if evaluation.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: evaluation belongs to another tenant"
        )
    return evaluation


@router.post("", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    eval_in: EvaluationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new evaluation job with optional questions and rubric criteria.
    Enforces tenant isolation.
    """
    # 1. Create evaluation
    evaluation = Evaluation(
        tenant_id=current_user.tenant_id,
        owner_id=current_user.id,
        title=eval_in.title,
        language=eval_in.language,
        max_marks=eval_in.max_marks,
        settings=eval_in.settings or {},
        status="created"
    )
    db.add(evaluation)
    db.flush()  # get evaluation.id

    # 2. Add questions if provided
    if eval_in.questions:
        for q_in in eval_in.questions:
            question = Question(
                evaluation_id=evaluation.id,
                order=q_in.order,
                prompt=q_in.prompt,
                instructions=q_in.instructions,
                reference_answer=q_in.reference_answer,
                expected_concepts=q_in.expected_concepts,
                citation_policy=q_in.citation_policy
            )
            db.add(question)
            db.flush()

            # Add rubric criteria if provided
            if q_in.rubric_criteria:
                for r_in in q_in.rubric_criteria:
                    criterion = RubricCriterion(
                        question_id=question.id,
                        criterion=r_in.criterion,
                        description=r_in.description,
                        max_points=r_in.max_points,
                        weight=r_in.weight,
                        expected_evidence=r_in.expected_evidence,
                        order=r_in.order
                    )
                    db.add(criterion)

    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.get("", response_model=EvaluationListResponse)
def list_evaluations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all evaluations belonging to the authenticated teacher's tenant workspace.
    Supports pagination, status filtering, and title search.
    """
    query = db.query(Evaluation).filter(Evaluation.tenant_id == current_user.tenant_id)
    
    if status_filter:
        query = query.filter(Evaluation.status == status_filter)
    if search:
        query = query.filter(Evaluation.title.ilike(f"%{search}%"))
        
    total = query.count()
    evaluations = query.order_by(Evaluation.created_at.desc()) \
                       .offset((page - 1) * per_page) \
                       .limit(per_page) \
                       .all()
                       
    return {
        "evaluations": evaluations,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a single evaluation by ID with its questions and rubric criteria.
    Enforces tenant isolation.
    """
    return verify_evaluation_ownership(evaluation_id, current_user, db)


@router.patch("/{evaluation_id}", response_model=EvaluationResponse)
def update_evaluation(
    evaluation_id: UUID,
    eval_in: EvaluationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an evaluation's metadata (title, language, max marks, settings, status).
    Enforces tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)
    
    update_data = eval_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(evaluation, field, value)
        
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evaluation(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an evaluation and its associated questions/submissions (cascade).
    Enforces tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)
    db.delete(evaluation)
    db.commit()
    db.expire_all()
    return None


# --- Question Management Endpoints ---

@router.post("/{evaluation_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def add_question(
    evaluation_id: UUID,
    q_in: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a question and optional rubric criteria to an evaluation.
    Enforces tenant isolation.
    """
    evaluation = verify_evaluation_ownership(evaluation_id, current_user, db)
    
    question = Question(
        evaluation_id=evaluation.id,
        order=q_in.order,
        prompt=q_in.prompt,
        instructions=q_in.instructions,
        reference_answer=q_in.reference_answer,
        expected_concepts=q_in.expected_concepts,
        citation_policy=q_in.citation_policy
    )
    db.add(question)
    db.flush()

    if q_in.rubric_criteria:
        for r_in in q_in.rubric_criteria:
            criterion = RubricCriterion(
                question_id=question.id,
                criterion=r_in.criterion,
                description=r_in.description,
                max_points=r_in.max_points,
                weight=r_in.weight,
                expected_evidence=r_in.expected_evidence,
                order=r_in.order
            )
            db.add(criterion)

    db.commit()
    db.refresh(question)
    return question


@router.patch("/{evaluation_id}/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    evaluation_id: UUID,
    question_id: UUID,
    q_in: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a question within an evaluation. Enforces tenant isolation.
    """
    verify_evaluation_ownership(evaluation_id, current_user, db)
    
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.evaluation_id == evaluation_id
    ).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
        
    update_data = q_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
        
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{evaluation_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    evaluation_id: UUID,
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a question from an evaluation. Enforces tenant isolation.
    """
    verify_evaluation_ownership(evaluation_id, current_user, db)
    
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.evaluation_id == evaluation_id
    ).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
        
    db.delete(question)
    db.commit()
    db.expire_all()
    return None


# --- Rubric Criteria Management Endpoints ---

@router.post("/{evaluation_id}/questions/{question_id}/rubric", response_model=RubricCriterionResponse, status_code=status.HTTP_201_CREATED)
def add_rubric_criterion(
    evaluation_id: UUID,
    question_id: UUID,
    r_in: RubricCriterionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a rubric criterion to a question. Enforces tenant isolation.
    """
    verify_evaluation_ownership(evaluation_id, current_user, db)
    
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.evaluation_id == evaluation_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    criterion = RubricCriterion(
        question_id=question.id,
        criterion=r_in.criterion,
        description=r_in.description,
        max_points=r_in.max_points,
        weight=r_in.weight,
        expected_evidence=r_in.expected_evidence,
        order=r_in.order
    )
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    return criterion


@router.patch("/{evaluation_id}/questions/{question_id}/rubric/{criterion_id}", response_model=RubricCriterionResponse)
def update_rubric_criterion(
    evaluation_id: UUID,
    question_id: UUID,
    criterion_id: UUID,
    r_in: RubricCriterionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a rubric criterion. Enforces tenant isolation.
    """
    verify_evaluation_ownership(evaluation_id, current_user, db)
    
    criterion = db.query(RubricCriterion).join(Question).filter(
        RubricCriterion.id == criterion_id,
        Question.id == question_id,
        Question.evaluation_id == evaluation_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Rubric criterion not found")
        
    update_data = r_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(criterion, field, value)
        
    db.commit()
    db.refresh(criterion)
    return criterion


@router.delete("/{evaluation_id}/questions/{question_id}/rubric/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rubric_criterion(
    evaluation_id: UUID,
    question_id: UUID,
    criterion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a rubric criterion. Enforces tenant isolation.
    """
    verify_evaluation_ownership(evaluation_id, current_user, db)
    
    criterion = db.query(RubricCriterion).join(Question).filter(
        RubricCriterion.id == criterion_id,
        Question.id == question_id,
        Question.evaluation_id == evaluation_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Rubric criterion not found")
        
    db.delete(criterion)
    db.commit()
    db.expire_all()
    return None
