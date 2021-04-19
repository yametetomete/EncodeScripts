# TODO: real logging shit not this jank-ass crap

STATUS: str = '\033[94m'
WARNING: str = '\033[93m'
ERROR: str = '\033[91m'
SUCCESS: str = '\033[92m'
RESET: str = '\033[0m'


class log():
    @staticmethod
    def status(s: str) -> None:
        print(f"{STATUS}{s}{RESET}")

    @staticmethod
    def warn(s: str) -> None:
        print(f"{WARNING}{s}{RESET}")

    @staticmethod
    def error(s: str) -> None:
        print(f"{ERROR}{s}{RESET}")

    @staticmethod
    def success(s: str) -> None:
        print(f"{SUCCESS}{s}{RESET}")
