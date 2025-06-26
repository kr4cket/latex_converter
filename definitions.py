from pathlib import Path


ROOT_DIR = Path(__file__).parent.resolve()
DOTENV = ROOT_DIR / ".env"

CONFIGURATION_PATH = ROOT_DIR / "config" / "application.yaml"
PROMPT_PATH = ROOT_DIR / "config" /  "prompts"