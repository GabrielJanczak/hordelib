import contextlib
import sys

from loguru import logger


class HordeLog:
    # By default we're at error level or higher
    verbosity: int = 20
    quiet: int = 0

    process_id: int = 0

    CUSTOM_STATS_LEVELS = ["STATS"]

    # Our sink IDs
    sinks: list[int] = []  # default mutable because this is a class variable (class is a singleton)

    @classmethod
    def set_logger_verbosity(cls, count):
        # The count comes reversed. So count = 0 means minimum verbosity
        # While count 5 means maximum verbosity
        # So the more count we have, the lowe we drop the versbosity maximum
        cls.verbosity = 20 - (count * 10)

    @classmethod
    def quiesce_logger(cls, count):
        # The bigger the count, the more silent we want our logger
        cls.quiet = count * 10

    @classmethod
    def is_stats_log(cls, record):
        if record["level"].name not in HordeLog.CUSTOM_STATS_LEVELS:
            return False
        return True

    @classmethod
    def is_not_stats_log(cls, record):
        if record["level"].name in HordeLog.CUSTOM_STATS_LEVELS:
            return False
        return True

    @classmethod
    def is_stderr_log(cls, record):
        if record["level"].name not in ["ERROR", "CRITICAL", "TRACE"]:
            return False
        return True

    @classmethod
    def is_trace_log(cls, record):
        if record["level"].name != "ERROR":
            return False
        return True

    @classmethod
    def test_logger(cls):
        logger.debug("Debug Message")
        logger.info("Info Message")
        logger.warning("Info Warning")
        logger.error("Error Message")
        logger.critical("Critical Message")

        logger.log("STATS", "Stats Message")

        a = 0

        @logger.catch
        def main():
            a.item()  # This will raise an exception

        main()

        sys.exit()

    @classmethod
    def initialise(cls, setup_logging=True, process_id: int | None = None):
        if setup_logging:
            cls.setup()
            cls.set_sinks()
            if process_id is not None:
                cls.process_id = process_id

        logger.disable("hordelib.clip.interrogate")

    @classmethod
    def setup(cls):
        for level in cls.CUSTOM_STATS_LEVELS:
            logger.level(level, no=cls.verbosity + cls.quiet)

    @classmethod
    def set_sinks(cls):
        # Remove any existing sinks that we added
        for sink in cls.sinks:
            with contextlib.suppress(ValueError):
                # Suppress if someone else beat us to it
                logger.remove(sink)

        cls.sinks = []

        config = {
            "handlers": [
                {
                    "sink": sys.stderr,
                    "colorize": True,
                    "filter": cls.is_stderr_log,
                    "enqueue": True,
                },
                {
                    "sink": sys.stdout,
                    "colorize": True,
                    "enqueue": True,
                },
                {
                    "sink": "logs/bridge.log" if not cls.process_id else f"logs/bridge_{cls.process_id}.log",
                    "level": "DEBUG",
                    "retention": "2 days",
                    "rotation": "1 days",
                    "enqueue": True,
                },
                {
                    "sink": "logs/stats.log" if not cls.process_id else f"logs/stats_{cls.process_id}.log",
                    "level": "STATS",
                    "filter": cls.is_stats_log,
                    "retention": "7 days",
                    "rotation": "1 days",
                    "enqueue": True,
                },
                {
                    "sink": "logs/trace.log" if not cls.process_id else f"logs/trace_{cls.process_id}.log",
                    "level": "ERROR",
                    "retention": "3 days",
                    "rotation": "1 days",
                    "backtrace": True,
                    "diagnose": True,
                    "enqueue": True,
                },
            ],
        }

        cls.sinks = logger.configure(**config)
