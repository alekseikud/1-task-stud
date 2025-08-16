from scripts.setup_db import (
    reset_parameters,
    create_tables,
    grant_priveleges,
    insert_data,
    load_funtions,
)
from scripts.report import report_to_json, report_to_xml

if __name__ == "__main__":
    reset_parameters()
    grant_priveleges()
    create_tables()
    load_funtions()
    insert_data.need_report_json = False  # type: ignore[attr-defined]
    insert_data.need_report_xml = False  # type: ignore[attr-defined]

    insert_data("rooms")
    insert_data("students")
    report_to_json()
    report_to_xml()
