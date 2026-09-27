from assurance_system.interfaces.cli import AssuranceCLI
import sys


if __name__ == "__main__":
    sys.exit(
        AssuranceCLI().run()
    )
