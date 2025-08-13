from scripts.setup_db import reset_parameters,create_tables,\
grant_priveleges,insert_data

reset_parameters()
grant_priveleges()
create_tables()
insert_data("rooms")
insert_data("students")