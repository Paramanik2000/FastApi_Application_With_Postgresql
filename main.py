from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import model
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

model.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/questions/{question_id}")
def read_question(question_id: int, db: Session = Depends(get_db)):

    result = db.query(model.Question)\
               .filter(model.Question.id == question_id)\
               .first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )

    return result

@app.get("/choices/{question_id}")
def read_choices(question_id: int, db: Session = Depends(get_db)):

    result = db.query(model.Choice)\
               .filter(model.Choice.question_id == question_id)\
               .all()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Choices not found"
        )

    return result

@app.put("/questions/{question_id}")
def update_question(
    question_id: int,
    question: QuestionBase,
    db: Session = Depends(get_db)
):
    # 1️⃣ Find question
    db_question = db.query(model.Question)\
                    .filter(model.Question.id == question_id)\
                    .first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    # 2️⃣ Update question text
    db_question.question_text = question.question_text

    # 3️⃣ Delete old choices
    db.query(model.Choice)\
      .filter(model.Choice.question_id == question_id)\
      .delete()

    # 4️⃣ Add new choices
    for choice in question.choices:
        db_choice = model.Choice(
            choice_text=choice.choice_text,
            is_correct=choice.is_correct,
            question_id=question_id
        )
        db.add(db_choice)

    db.commit()

    return {"message": "Question updated successfully"}

@app.delete("/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):

    db_question = db.query(model.Question)\
                    .filter(model.Question.id == question_id)\
                    .first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    # 1️⃣ Delete choices first
    db.query(model.Choice)\
      .filter(model.Choice.question_id == question_id)\
      .delete()

    # 2️⃣ Delete question
    db.delete(db_question)

    db.commit()

    return {"message": "Question deleted successfully"}




@app.post("/questions/")
def create_questions(question: QuestionBase, db: Session = Depends(get_db)):

    db_question = model.Question(
        question_text=question.question_text
    )

    db.add(db_question)
    db.commit()
    db.refresh(db_question)

    for choice in question.choices:
        db_choice = model.Choice(
            choice_text=choice.choice_text,
            is_correct=choice.is_correct,
            question_id=db_question.id
        )
        db.add(db_choice)

    db.commit()

    return {"message": "Question created successfully"}
