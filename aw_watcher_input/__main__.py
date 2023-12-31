from aw_core.log import setup_logging

from aw_watcher_input.input import INPUTWatcher
from aw_watcher_input.config import parse_args


def main() -> None:
    args = parse_args()

    # Set up logging
    setup_logging(
        "aw-watcher-input",
        testing=args.testing,
        verbose=args.verbose,
        log_stderr=True,
        log_file=True,
    )

    # Start watcher
    watcher = INPUTWatcher(args, testing=args.testing)
    watcher.run()


if __name__ == "__main__":
    main()
