from scripts.setup_db import reset_parameters,create_tables,\
grant_priveleges,insert_data,load_funtions
from scripts.report import rooms_different_sex,rooms_highest_age_diff,rooms_lowest_avg_age,rooms_stud_number

reset_parameters()
grant_priveleges()
create_tables()
load_funtions()
insert_data("rooms")
insert_data("students")
rooms_different_sex()
rooms_highest_age_diff()
rooms_lowest_avg_age()
rooms_stud_number()