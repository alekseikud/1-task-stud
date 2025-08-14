DROP FUNCTION IF EXISTS conflict_resolution(pk_id INT);
CREATE OR REPLACE FUNCTION conflict_resolution(pk_id INT)
RETURNS BOOLEAN
LANGUAGE PLPGSQL
AS $$
BEGIN
	RAISE NOTICE 'Primary key with value % already exist',pk_id;
	RETURN FALSE;
END
$$;