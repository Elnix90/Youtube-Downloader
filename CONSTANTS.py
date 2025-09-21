from pathlib import Path
import tomli
import logging
import sys

# Charger la configuration TOML
CONFIG_FILE = Path("config.toml")
if not CONFIG_FILE.exists():
    print(f"Erreur: Le fichier de configuration '{CONFIG_FILE}' n'existe pas.")
    print("Veuillez créer ce fichier ou utiliser config.toml.example comme modèle.")
    sys.exit(1)

with open(CONFIG_FILE, "rb") as f:
    config = tomli.load(f)

# Validation de la configuration
def validate_config():
    required_sections = ["paths", "patterns", "processing", "logging"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Section manquante dans config.toml: [{section}]")
    
    # Vérifier les chemins critiques
    download_path = Path(config["paths"]["download_path"])
    if not download_path.parent.exists():
        print(f"Attention: Le répertoire parent de download_path n'existe pas: {download_path.parent}")
    
    db_path = Path(config["paths"]["db_path"])
    if not db_path.exists() and not db_path.parent.exists():
        print(f"Attention: Le répertoire parent de db_path n'existe pas: {db_path.parent}")

validate_config()

# Répertoires de base
JSON_DIR: Path = Path(config["paths"]["json_dir"])
CRED_DIR: Path = Path(config["paths"]["cred_dir"])
LOGS_DIR: Path = Path(config["paths"]["logs_dir"])

CONFIG_DIR: Path = Path(config["paths"]["config_dir"])
PATTERN_DIR: Path = CONFIG_DIR / "PATTERNS"
TAGS_DIR: Path = CONFIG_DIR / "TAGS"

# Chemins critiques
DOWNLOAD_PATH: Path = Path(config["paths"]["download_path"])
DB_PATH: Path = Path(config["paths"]["db_path"])

# Creds files
CLIENT_SECRETS_FILE: Path = CRED_DIR / config["paths"]["client_secrets_file"]
TOKEN_FILE: Path = CRED_DIR / config["paths"]["token_file"]
PLAYLIST_VIDEOS_FILE: Path = JSON_DIR / config["paths"]["playlist_videos_file"]

# Stats files
CORRECT_NOT_IN_DIR_FILE: Path = JSON_DIR / config["paths"]["correct_not_in_db.json"]
UNAVAILABLE_VIDEOS_FILE: Path = JSON_DIR / config["paths"]["unavailable_videos.json"]

# Fichiers de patterns
UNWANTED_PATTERNS_FILE: Path = PATTERN_DIR / config["patterns"]["unwanted_patterns_file"]
REMIX_PATTERNS_FILE: Path = PATTERN_DIR / config["patterns"]["remix_patterns_file"]
PRIVATE_PATTERNS_FILE: Path = PATTERN_DIR / config["patterns"]["private_patterns_file"]
TRUSTED_ARTISTS: Path = PATTERN_DIR / config["patterns"]["trusted_artists_file"]

# Configuration de traitement
MAX_LYRICS_RETRIES: int = config["processing"]["max_lyrics_retries"]

# Configuration de logging
LOGS_CONSOLE_GLOBALLY: bool = config["logging"]["console_globally"]
OVERLAP_FPRINT: bool = config["logging"]["overlap_fprint"]
OVERWRITE_UNCHANGED: bool = config["logging"]["overwrite_unchanged"]
 
# Mapping des niveaux de logging
LOGGING_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

LOGGING_LEVEL_CONSOLE: int = LOGGING_LEVELS.get(
    config["logging"]["level_console"].upper(), 
    logging.WARNING
)
LOGGING_LEVEL_LOGFILES: int = LOGGING_LEVELS.get(
    config["logging"]["level_logfiles"].upper(), 
    logging.DEBUG
)


# STATUS_MAP = {
#     0: "downloaded",
#     1: "unavailable",
#     2: "private",
#     3: "unknown"
# }