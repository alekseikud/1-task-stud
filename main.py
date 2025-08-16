# main.py
import re

from scripts.setup_db import (
    reset_parameters,
    grant_priveleges,
    create_tables,
    load_funtions,  # (spelling kept as in your code)
    insert_data,
)
from scripts.report import report_to_json, report_to_xml


def run(label, fn, *args):
    try:
        fn(*args)
        print(f"{label}: done")
    except Exception as e:
        print(f"{label}: FAILED -> {e}")


def run_setup():
    run("reset_parameters", reset_parameters)
    run("grant_priveleges", grant_priveleges)
    run("create_tables", create_tables)
    run("load_funtions", load_funtions)
    # defaults for seeding
    insert_data.need_report_json = False  # type: ignore[attr-defined]
    insert_data.need_report_xml = False  # type: ignore[attr-defined]
    print("setup: done")


ACTIONS = {
    "1": (
        "insert_data('rooms')",
        lambda: run("insert_data(rooms)", insert_data, "rooms"),
    ),
    "2": (
        "insert_data('students')",
        lambda: run("insert_data(students)", insert_data, "students"),
    ),
    "3": ("report_to_json()", lambda: run("report_to_json", report_to_json)),
    "4": ("report_to_xml()", lambda: run("report_to_xml", report_to_xml)),
    "5": (
        "report both",
        lambda: (
            run("report_to_json", report_to_json),
            run("report_to_xml", report_to_xml),
        ),
    ),
    "6": ("rerun full setup", run_setup),
}


def print_menu():
    print("\n=== Menu ===")
    print("1. insert_data('rooms')")
    print("2. insert_data('students')")
    print("3. report_to_json()")
    print("4. report_to_xml()")
    print("5. report both (json+xml)")
    print("6. rerun full setup")
    print("0. exit")
    print("Tip: you can enter multiple actions like: 1 3 4 or 1,3,4\n")


def main():
    run_setup()  # auto-run at start

    while True:
        print_menu()
        try:
            raw = input("select action(s): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue

        low = raw.lower()
        if any(word in {"0", "q", "quit", "exit"} for word in low):
            choice = "something"
            while choice.lower() not in {"y", "n"}:
                choice = input("Would you like to close the app? (Y|N)")
            if choice.lower() == "y":
                break
            elif choice.lower() == "n":
                continue
        if any(word in {"h", "help", "?"} for word in low):
            print_menu()  # TODO: need something to write for help statement
            continue

        for tok in filter(None, re.split(r"[ ,]+", raw)):
            action = ACTIONS.get(tok)
            if not action:
                print(f"unknown option: {tok}")
                continue
            action[1]()  # run the callable

    print("bye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
