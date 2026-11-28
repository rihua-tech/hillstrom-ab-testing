-- The caller loads one raw segment value per CSV data record.
WITH classified AS (
    SELECT CASE
        -- The characters here match Python's blank/whitespace-only convention.
        WHEN trim(segment, char(
            9, 10, 11, 12, 13, 28, 29, 30, 31, 32, 133, 160, 5760,
            8192, 8193, 8194, 8195, 8196, 8197, 8198, 8199, 8200, 8201,
            8202, 8232, 8233, 8239, 8287, 12288
        )) = '' THEN 'missing'
        WHEN segment = 'No E-Mail' THEN 'control'
        WHEN segment = 'Mens E-Mail' THEN 'mens'
        WHEN segment = 'Womens E-Mail' THEN 'womens'
        ELSE 'illegal'
    END AS arm
    FROM assignments
)
SELECT
    COUNT(*) AS total,
    COUNT(CASE WHEN arm = 'control' THEN 1 END) AS control,
    COUNT(CASE WHEN arm = 'mens' THEN 1 END) AS mens,
    COUNT(CASE WHEN arm = 'womens' THEN 1 END) AS womens,
    COUNT(CASE WHEN arm = 'missing' THEN 1 END) AS missing,
    COUNT(CASE WHEN arm = 'illegal' THEN 1 END) AS illegal
FROM classified;
