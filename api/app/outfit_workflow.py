from typing_extensions import TypedDict
from typing import Dict, Any, Optional
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
import os
import getpass
import dotenv
import logging
import json

# ============================================================
# CONFIG & ENV
# ============================================================

LOGGER_NAME = "prompt_parallelism"
logger = logging.getLogger(LOGGER_NAME)

dotenv.load_dotenv()


def _set_env(var: str) -> None:
    """Ensure a critical env var exists, otherwise ask for it."""
    if var not in os.environ or not os.environ[var]:
        os.environ[var] = getpass.getpass(f"Enter value for {var}: ")


# Required API key
_set_env("ANTHROPIC_API_KEY")


def get_env_int(name: str, default: int) -> int:
    """Safely parse an int from env, with a default fallback."""
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


# Read from .env
MAX_ATTEMPTS = get_env_int("MAX_ATTEMPTS", 5)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure a clean, professional logger."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("langgraph").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def banner(text: str) -> None:
    """Prints a nicely formatted section header."""
    sep = "─" * 70
    logger.info("\n%s\n▶ %s\n%s", sep, text, sep)


def log_state(prefix: str, state: Dict[str, Any]) -> None:
    """Pretty-print the core state fields."""
    summary = {
        "head_item": state.get("head_item"),
        "head_gender": state.get("head_gender"),
        "torso_item": state.get("torso_item"),
        "torso_gender": state.get("torso_gender"),
        "leg_item": state.get("leg_item"),
        "leg_gender": state.get("leg_gender"),
        "overall_gender": state.get("gender"),  # male / female / none
        "consistent": state.get("consistent"),
        "attempts": state.get("attempts"),
    }
    logger.info("\n🔸 %s State:\n%s\n", prefix, summary)


# ============================================================
# MODEL
# ============================================================

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",  # adjust if needed
    max_tokens=1000,
)

# ============================================================
# STATE
# ============================================================

class State(TypedDict, total=False):
    head_item: str
    torso_item: str
    leg_item: str

    # Each item: "male" | "female" | "none"
    head_gender: str
    torso_gender: str
    leg_gender: str

    # Overall outfit gender: "male" | "female" | "none"
    gender: str
    consistent: bool   # True if outfit is accepted (all male OR all female)

    attempts: int      # how many validation cycles have run


# ============================================================
# NODES
# ============================================================

def start_outfit_cycle(state: State) -> Dict[str, Any]:
    """
    Entry node for each outfit generation cycle.
    """
    attempts = state.get("attempts", 0)
    banner("Start Outfit Generation Cycle")
    logger.info(
        "Starting outfit generation attempt %d (max=%d).",
        attempts + 1,
        MAX_ATTEMPTS,
    )
    return {}


def generate_head_item(state: State) -> Dict[str, Any]:
    banner("Generate Head Clothing")
    prompt = (
        "Generate a single clothing item worn on the HEAD such as a cap, hat, "
        "beanie, beret, etc. Return ONLY the item name (no extra words)."
    )
    msg = llm.invoke(prompt)
    raw = str(msg.content).strip()
    item = raw.split("\n")[0].strip()
    logger.info("Head item generated: %r (raw=%r)", item, raw)
    return {"head_item": item}


def generate_torso_item(state: State) -> Dict[str, Any]:
    banner("Generate Torso Clothing")
    prompt = (
        "Generate a single clothing item worn on the TORSO such as a t-shirt, "
        "shirt, blouse, top, bra, etc. Return ONLY the item name (no extra words)."
    )
    msg = llm.invoke(prompt)
    raw = str(msg.content).strip()
    item = raw.split("\n")[0].strip()
    logger.info("Torso item generated: %r (raw=%r)", item, raw)
    return {"torso_item": item}


def generate_leg_item(state: State) -> Dict[str, Any]:
    banner("Generate Leg Clothing")
    prompt = (
        "Generate a single clothing item worn on the LEGS such as pants, jeans, "
        "skirt, shorts, leggings, etc. Return ONLY the item name (no extra words)."
    )
    msg = llm.invoke(prompt)
    raw = str(msg.content).strip()
    item = raw.split("\n")[0].strip()
    logger.info("Leg item generated: %r (raw=%r)", item, raw)
    return {"leg_item": item}


def _classify_items(head: str, torso: str, legs: str) -> Dict[str, str]:
    """
    Ask the model to classify each clothing item as:
    - 'male'
    - 'female'
    - 'none' (only for non-clothing / impossible to tell)

    IMPORTANT:
    - For typical clothing items that can be worn by anyone (jeans, t-shirt, hoodie,
      sneakers, etc.), you MUST still choose 'male' or 'female' based on what is
      more commonly associated in fashion catalogs, NOT 'none'.
    - Use 'none' only if the text is clearly not a clothing item or is unreadable.
    """
    prompt = (
        "You are a fashion expert.\n"
        "Classify each clothing item by its typical target gender category.\n\n"
        "You MUST use ONLY these values: 'male', 'female', or 'none'.\n"
        "- Use 'male' if it is more commonly sold as a men's item in fashion catalogs.\n"
        "- Use 'female' if it is more commonly sold as a women's item.\n"
        "- Use 'none' ONLY IF the text is not a clothing item at all or is impossible to interpret.\n\n"
        "Very important:\n"
        "- If an item can be worn by any gender (jeans, t-shirt, sneakers, hoodie, etc.), "
        "  you MUST still choose 'male' OR 'female' based on what is more common; "
        "  DO NOT use 'none' for that.\n\n"
        f"Head item: {head}\n"
        f"Torso item: {torso}\n"
        f"Leg item: {legs}\n\n"
        "Return a JSON object ONLY, with exactly these keys and values in lowercase, like:\n"
        '{"head": "male", "torso": "female", "legs": "male"}'
    )
    msg = llm.invoke(prompt)
    raw = str(msg.content).strip()
    logger.info("Raw gender classification response: %r", raw)

    default = {"head": "none", "torso": "none", "legs": "none"}
    try:
        data = json.loads(raw)
        # Normalize & guard
        for k in default.keys():
            v = str(data.get(k, "none")).lower()
            if v not in ("male", "female", "none"):
                v = "none"
            default[k] = v
    except Exception as e:
        logger.warning("Failed to parse JSON for gender classification: %s", e)

    logger.info(
        "Classified genders → head=%s, torso=%s, legs=%s",
        default["head"], default["torso"], default["legs"]
    )
    return default


def validate_outfit(state: State) -> Dict[str, Any]:
    """
    Validate whether the three clothing items correspond to a consistent outfit.

    Rules:
    - Each item is classified as: male / female / none.
    - An outfit is accepted if:
        * all three are 'male'   → overall gender = 'male',   consistent = True
        * all three are 'female' → overall gender = 'female', consistent = True
    - Any mix of male/female/none → overall gender = 'none', consistent = False
    - attempts increments on each validation.
    - If attempts >= MAX_ATTEMPTS and still inconsistent → we stop retrying.
    """
    banner("Validate Outfit")

    head = state.get("head_item", "")
    torso = state.get("torso_item", "")
    legs = state.get("leg_item", "")

    logger.info(
        "Validating outfit with items → head=%r, torso=%r, legs=%r",
        head, torso, legs
    )

    # 1) Per-item classification
    genders = _classify_items(head, torso, legs)
    head_gender = genders["head"]
    torso_gender = genders["torso"]
    leg_gender = genders["legs"]

    item_genders = [head_gender, torso_gender, leg_gender]

    # 2) Determine overall gender consistency
    all_male = all(g == "male" for g in item_genders)
    all_female = all(g == "female" for g in item_genders)

    if all_male:
        overall_gender = "male"
        consistent = True
    elif all_female:
        overall_gender = "female"
        consistent = True
    else:
        overall_gender = "none"
        consistent = False

    # 3) Update attempts
    attempts = state.get("attempts", 0) + 1

    logger.info(
        "Per-item genders → head=%s, torso=%s, legs=%s | overall=%s | "
        "consistent=%s | attempts=%d",
        head_gender, torso_gender, leg_gender, overall_gender, consistent, attempts
    )

    if not consistent and attempts >= MAX_ATTEMPTS:
        logger.warning(
            "Max attempts (%d) reached with inconsistent outfit. "
            "Will stop retrying.",
            MAX_ATTEMPTS,
        )

    return {
        "head_gender": head_gender,
        "torso_gender": torso_gender,
        "leg_gender": leg_gender,
        "gender": overall_gender,
        "consistent": consistent,
        "attempts": attempts,
    }


# ============================================================
# GRAPH BUILD
# ============================================================

workflow = StateGraph(State)

# Nodes
workflow.add_node("Start Outfit Cycle", start_outfit_cycle)
workflow.add_node("Generate Head Item", generate_head_item)
workflow.add_node("Generate Torso Item", generate_torso_item)
workflow.add_node("Generate Leg Item", generate_leg_item)
workflow.add_node("Validate Outfit", validate_outfit)

# Edges:
workflow.add_edge(START, "Start Outfit Cycle")

# Parallel generation
workflow.add_edge("Start Outfit Cycle", "Generate Head Item")
workflow.add_edge("Start Outfit Cycle", "Generate Torso Item")
workflow.add_edge("Start Outfit Cycle", "Generate Leg Item")

# All generators → validator
workflow.add_edge("Generate Head Item", "Validate Outfit")
workflow.add_edge("Generate Torso Item", "Validate Outfit")
workflow.add_edge("Generate Leg Item", "Validate Outfit")


def outfit_loop_router(s: State) -> str:
    """
    Decide whether to approve, retry, or give up based on state.
    """
    if s.get("consistent"):
        return "approve"

    attempts = s.get("attempts", 0)
    if attempts >= MAX_ATTEMPTS:
        # Stop looping if we tried too many times
        return "give_up"

    return "retry"


workflow.add_conditional_edges(
    "Validate Outfit",
    outfit_loop_router,
    {
        "approve": END,
        "retry": "Start Outfit Cycle",
        "give_up": END,
    },
)

app = workflow.compile()

# ============================================================
# GRAPH DIAGRAM EXPORT
# ============================================================

def render_graph_diagram(output_path: str = "workflow_graph.png") -> None:
    graph = app.get_graph()

    banner("Rendering Workflow Diagram")

    # Try Mermaid PNG export (newer API returns bytes and takes no path)
    try:
        png_bytes = graph.draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        logger.info("Diagram saved as PNG → %s", output_path)
        return
    except Exception as e:
        logger.warning("PNG export failed: %s", e)

    # Try .visualize() API used in some older versions
    try:
        viz = workflow.visualize()
        with open(output_path, "wb") as f:
            f.write(viz.render_png())
        logger.info("Diagram saved using fallback visualize() → %s", output_path)
        return
    except Exception as e:
        logger.warning("visualize() fallback failed: %s", e)

    # Last fallback → save Mermaid source as a Markdown file
    try:
        md_path = "workflow_graph.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("```mermaid\n")
            f.write(graph.draw_mermaid())
            f.write("\n```")
        logger.info("Saved Mermaid diagram source → %s", md_path)
    except Exception as e:
        logger.error("Could NOT generate any diagram: %s", e)


# ============================================================
# MAIN EXECUTION
# ============================================================

def run_workflow() -> State:
    """
    Run the LangGraph workflow once and return the final state.
    Also (re)generate the workflow_graph.png.
    """
    configure_logging()

    banner("WORKFLOW START")
    logger.info("MAX_ATTEMPTS from env = %d", MAX_ATTEMPTS)

    # Generate / update diagram in project root
    render_graph_diagram("workflow_graph.png")

    initial_state: State = {
        "attempts": 0,
    }
    log_state("Initial", initial_state)

    logger.info("Running workflow...")

    final_state: Optional[State] = None

    for update in app.stream(initial_state, stream_mode="values"):
        log_state("Step", update)
        final_state = update

    banner("WORKFLOW COMPLETE")
    return final_state or {}


if __name__ == "__main__":
    # Keep CLI usage working as well
    result = run_workflow()
    print("\nFinal State:\n", result)
