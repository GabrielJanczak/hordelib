# initialisation.py
# Initialise hordelib.
import os
import shutil
import sys

from loguru import logger

from hordelib import install_comfy
from hordelib.config_path import get_hordelib_path, set_system_path
from hordelib.consts import (
    COMFYUI_VERSION,
    RELEASE_VERSION,
)
from hordelib.utils.logger import HordeLog

_is_initialised = False


def initialise(
    # model_managers_to_load: dict[MODEL_CATEGORY_NAMES, bool] = DEFAULT_MODEL_MANAGERS,
    *,
    setup_logging=True,
    clear_logs=False,
    logging_verbosity=3,
    process_id: int | None = None,
):  # XXX # TODO Do we need `model_managers_to_load`?
    global _is_initialised

    # Wipe existing logs if requested
    if clear_logs and os.path.exists("./logs"):
        shutil.rmtree("./logs")

    # Setup logging if requested
    HordeLog.initialise(
        setup_logging=setup_logging,
        process_id=process_id,
        verbosity_count=logging_verbosity,
    )

    # If developer mode, don't permit some things
    if not RELEASE_VERSION and " " in str(get_hordelib_path()):
        # Our runtime patching can't handle this
        raise Exception(
            "Do not run this project in developer mode from a path that " "contains spaces in directory names.",
        )

    # Ensure we have ComfyUI
    logger.debug("Clearing command line args in sys.argv before ComfyUI load")
    sys_arg_bkp = sys.argv.copy()
    sys.argv = sys.argv[:1]
    installer = install_comfy.Installer()
    installer.install(COMFYUI_VERSION)

    # Modify python path to include comfyui
    set_system_path()

    import hordelib.comfy_horde

    hordelib.comfy_horde.do_comfy_import()

    vram_on_start_free = hordelib.comfy_horde.get_torch_free_vram_mb()
    vram_total = hordelib.comfy_horde.get_torch_total_vram_mb()
    vram_percent_used = round((vram_total - vram_on_start_free) / vram_total * 100, 2)
    message_addendum = "This will almost certainly cause issues. "
    message_addendum += "It is strongly recommended you close other applications before running the worker."
    if vram_on_start_free < 2000:
        logger.warning(f"You have less than 2GB of VRAM free. {message_addendum}")

    if vram_percent_used > 60:
        logger.warning(f"There was already {vram_percent_used}% of VRAM used on start. {message_addendum}")

    if vram_total < 4000:
        logger.warning("You have less than 4GB of VRAM total. It is likely that generations will happen very slowly.")

    # Initialise model manager
    from hordelib.shared_model_manager import SharedModelManager

    SharedModelManager()

    sys.argv = sys_arg_bkp

    _is_initialised = True


def is_initialised():
    return _is_initialised
