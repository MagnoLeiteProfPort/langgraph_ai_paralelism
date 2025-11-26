from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .outfit_workflow import run_workflow

app = FastAPI(
    title="Outfit Gender Workflow API",
    version="1.0.0",
)

# Allow frontend (Django/React) to call us
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-outfit")
def generate_outfit():
    """
    Run the workflow once and return the final state as JSON.
    """
    final_state = run_workflow()

    # final_state is your State TypedDict; just cast to plain dict
    return {
        "head_item": final_state.get("head_item"),
        "head_gender": final_state.get("head_gender"),
        "torso_item": final_state.get("torso_item"),
        "torso_gender": final_state.get("torso_gender"),
        "leg_item": final_state.get("leg_item"),
        "leg_gender": final_state.get("leg_gender"),
        "gender": final_state.get("gender"),
        "consistent": final_state.get("consistent"),
        "attempts": final_state.get("attempts"),
    }
