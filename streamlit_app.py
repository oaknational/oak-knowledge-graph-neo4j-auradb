import streamlit as st
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from pipeline.pipeline import Pipeline, PipelineProgress
from pipeline.config_manager import ConfigManager, ConfigurationError
from models.config import PipelineConfig
from utils.helpers import format_duration
from pydantic import ValidationError

# Load environment variables from .env file
load_dotenv()

st.set_page_config(
    page_title="Oak Knowledge Graph Pipeline",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("🌳 Oak Knowledge Graph Pipeline")
st.markdown(
    "Transform Oak curriculum data from Hasura materialized views to "
    "Neo4j knowledge graph"
)

if "config_text" not in st.session_state:
    st.session_state.config_text = ""
if "pipeline_config" not in st.session_state:
    st.session_state.pipeline_config = None
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False
if "execution_results" not in st.session_state:
    st.session_state.execution_results = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None


def load_default_config():
    """Load the default schema configuration"""
    config_path = Path("config/oak_curriculum_schema_v0.1.0-alpha.json")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return f.read()
        except Exception as e:
            st.error(f"Failed to load default config: {str(e)}")
    return ""


def validate_config_json(config_text: str) -> Optional[Dict[str, Any]]:
    """Validate JSON configuration and return parsed config"""
    try:
        config_dict = json.loads(config_text)

        # Check for environment variable placeholders
        missing_env_vars = []

        def check_env_vars(value):
            if (
                isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                env_var = value[2:-1]
                if not os.getenv(env_var):
                    missing_env_vars.append(env_var)
            elif isinstance(value, dict):
                for v in value.values():
                    check_env_vars(v)
            elif isinstance(value, list):
                for item in value:
                    check_env_vars(item)

        check_env_vars(config_dict)

        if missing_env_vars:
            st.warning(
                f"⚠️ Configuration uses environment variables that are not set: "
                f"{', '.join(missing_env_vars)}\n\n"
                f"The configuration structure is valid, but you'll need to set these "
                f"environment variables before running the pipeline."
            )
            return config_dict

        # Create a temporary config manager for validation
        config_manager = ConfigManager()

        # Substitute environment variables
        substituted_config = config_manager._substitute_env_vars(config_dict)

        # Validate using Pydantic model directly
        try:
            PipelineConfig(**substituted_config)
            return config_dict
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                message = error["msg"]
                error_details.append(f"  {field}: {message}")

            st.error("Configuration validation failed:\n" + "\n".join(error_details))
            return None

    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {str(e)}")
        return None
    except ConfigurationError as e:
        if "Environment variable" in str(e) and "is not set" in str(e):
            # Extract environment variable from error message
            match = re.search(r"Environment variable (\w+) is not set", str(e))
            if match:
                env_var = match.group(1)
                st.warning(
                    f"⚠️ Configuration uses environment variable `{env_var}` "
                    f"that is not set.\n\n"
                    f"The configuration structure is valid, but you'll need to "
                    f"set this environment variable before running the pipeline."
                )
                return config_dict
        st.error(f"Configuration validation failed: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error validating config: {str(e)}")
        return None


def update_progress(progress: PipelineProgress):
    """Update progress in Streamlit interface"""
    if hasattr(st.session_state, "progress_bar"):
        st.session_state.progress_bar.progress(progress.progress_percent / 100.0)
    if hasattr(st.session_state, "status_text"):
        st.session_state.status_text.text(f"{progress.stage.value}: {progress.message}")


# ============================================================================
# CONFIG EDITOR SECTION (TOP)
# ============================================================================

st.header("📝 Configuration Editor")

col1, col2 = st.columns([1, 4])

with col1:
    if st.button("Load Default Config", help="Load the default Oak curriculum schema"):
        default_config = load_default_config()
        if default_config:
            st.session_state.config_text = default_config
            st.rerun()

with col2:
    pass

config_text = st.text_area(
    "JSON Configuration",
    value=st.session_state.config_text,
    height=300,
    help="Enter your JSON schema mapping configuration",
    key="config_editor",
)

if config_text != st.session_state.config_text:
    st.session_state.config_text = config_text

config_valid = False
if config_text.strip():
    config_dict = validate_config_json(config_text)
    if config_dict:
        st.success("✅ Configuration is valid!")
        st.session_state.pipeline_config = config_dict
        config_valid = True
    else:
        st.session_state.pipeline_config = None

# ============================================================================
# PREVIEW SECTION (MIDDLE)
# ============================================================================

st.header("👁️ Data Preview")

if config_valid and st.session_state.pipeline_config:
    preview_col1, preview_col2 = st.columns(2)

    with preview_col1:
        st.subheader("Configuration Summary")
        config = st.session_state.pipeline_config

        st.metric("Materialized Views", len(config.get("materialized_views", [])))
        st.metric("Node Mappings", len(config.get("node_mappings", [])))
        st.metric("Relationship Mappings", len(config.get("relationship_mappings", [])))

        if config.get("test_limit"):
            st.info(f"🧪 Test mode: Limited to {config['test_limit']} records per view")

    with preview_col2:
        st.subheader("Configured Views")
        views = config.get("materialized_views", [])
        if views:
            for view in views:
                st.code(view, language="text")
        else:
            st.warning("No materialized views configured")

    # Environment validation
    st.subheader("Environment Check")
    env_col1, env_col2, env_col3 = st.columns(3)

    required_vars = ["HASURA_ENDPOINT", "HASURA_API_KEY", "OAK_AUTH_TYPE"]
    env_status = {}

    for var in required_vars:
        env_status[var] = os.getenv(var) is not None

    with env_col1:
        status = "✅" if env_status["HASURA_ENDPOINT"] else "❌"
        st.metric("HASURA_ENDPOINT", status)

    with env_col2:
        status = "✅" if env_status["HASURA_API_KEY"] else "❌"
        st.metric("HASURA_API_KEY", status)

    with env_col3:
        status = "✅" if env_status["OAK_AUTH_TYPE"] else "❌"
        st.metric("OAK_AUTH_TYPE", status)

    all_env_valid = all(env_status.values())
    if not all_env_valid:
        st.error(
            "⚠️ Missing required environment variables. "
            "Please set them in your .env file."
        )

else:
    st.info("Enter a valid JSON configuration above to see preview")

# ============================================================================
# EXECUTION SECTION (BOTTOM)
# ============================================================================

st.header("🚀 Pipeline Execution")

execution_disabled = not (config_valid and all_env_valid)

exec_col1, exec_col2, exec_col3 = st.columns([1, 1, 2])

with exec_col1:
    full_pipeline = st.button(
        "Run Full Pipeline",
        disabled=execution_disabled or st.session_state.pipeline_running,
        help="Extract → Validate → Map → Transform → Load",
    )

with exec_col2:
    extract_only = st.button(
        "Extract Only",
        disabled=execution_disabled or st.session_state.pipeline_running,
        help="Extract data from Hasura and validate",
    )

with exec_col3:
    use_auradb = st.checkbox(
        "Use AuraDB (direct import)",
        help="Import directly to AuraDB instead of generating CSV commands",
    )
    clear_db = st.checkbox(
        "Clear database before import", help="Remove existing data before importing"
    )

# Progress indicators
if st.session_state.pipeline_running:
    st.info("🔄 Pipeline is running...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    st.session_state.progress_bar = progress_bar
    st.session_state.status_text = status_text


# Execute pipeline
def run_pipeline(full: bool = True, extract_only: bool = False):
    """Run the pipeline with progress updates"""
    try:
        st.session_state.pipeline_running = True
        st.session_state.execution_results = None
        st.session_state.error_message = None

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(st.session_state.pipeline_config, f, indent=2)
            temp_config_path = f.name

        # Initialize pipeline
        config_manager = ConfigManager()
        pipeline = Pipeline(
            config_manager=config_manager,
            progress_callback=update_progress,
            output_dir="data",
        )

        # Load config
        pipeline_config = config_manager.load_config(temp_config_path)

        # Update config with UI options
        if hasattr(pipeline_config, "clear_database_before_import"):
            pipeline_config.clear_database_before_import = clear_db

        # Run pipeline based on selection
        if extract_only:
            results = pipeline.run_partial_pipeline(
                config=pipeline_config, stages=["extract", "validate"]
            )
        else:
            if use_auradb:
                results = pipeline.run_full_pipeline(
                    config=pipeline_config, use_auradb=True
                )
            else:
                results = pipeline.run_full_pipeline(
                    config=pipeline_config, use_auradb=False
                )

        st.session_state.execution_results = results

        # Cleanup temp file
        os.unlink(temp_config_path)

    except Exception as e:
        st.session_state.error_message = str(e)
        if hasattr(e, "stage"):
            st.session_state.error_message = f"Failed at {e.stage.value}: {str(e)}"

        # Cleanup temp file
        if "temp_config_path" in locals():
            try:
                os.unlink(temp_config_path)
            except OSError:
                pass

    finally:
        st.session_state.pipeline_running = False


# Handle button clicks
if full_pipeline:
    run_pipeline(full=True)
    st.rerun()

if extract_only:
    run_pipeline(extract_only=True)
    st.rerun()

# ============================================================================
# RESULTS SECTION
# ============================================================================

if st.session_state.execution_results:
    st.header("✅ Execution Results")

    results = st.session_state.execution_results

    # Display summary metrics
    result_col1, result_col2, result_col3 = st.columns(3)

    with result_col1:
        if hasattr(results, "extraction_results"):
            total_records = sum(
                len(data) for data in results.extraction_results.values()
            )
            st.metric("Records Extracted", total_records)

    with result_col2:
        if hasattr(results, "csv_files"):
            st.metric("CSV Files Generated", len(results.csv_files))

    with result_col3:
        if hasattr(results, "execution_time"):
            st.metric("Execution Time", format_duration(results.execution_time))

    # Display detailed results
    if hasattr(results, "csv_files") and results.csv_files:
        st.subheader("Generated Files")
        for file_path in results.csv_files:
            if Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                st.code(f"{file_path} ({file_size:,} bytes)")

    if hasattr(results, "import_command") and results.import_command:
        st.subheader("Neo4j Import Command")
        st.code(results.import_command, language="bash")

    if hasattr(results, "import_summary") and results.import_summary:
        st.subheader("Import Summary")
        st.json(results.import_summary)

if st.session_state.error_message:
    st.header("❌ Execution Error")
    st.error(st.session_state.error_message)

    if st.button("Clear Error"):
        st.session_state.error_message = None
        st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "**Oak Knowledge Graph Pipeline** | "
    "Built with Streamlit | "
    f"Config: `{Path('config/oak_curriculum_schema_v0.1.0-alpha.json').name}`"
)
