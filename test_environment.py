import sys


REQUIRED_PYTHON = "python3"


def main():
    system_major = sys.version_info.major
    required_major = 3 if REQUIRED_PYTHON == "python3" else 2

    if system_major != required_major:
        raise TypeError(
            "This project requires Python {}. Found: Python {}".format(
                required_major, sys.version
            )
        )

    print(">>> Development environment passes all tests!")


if __name__ == "__main__":
    main()

