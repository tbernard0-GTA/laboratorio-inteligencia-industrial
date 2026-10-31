-- Uma consulta SELECT por arquivo. Execute em modo somente leitura.
SELECT tag_id, COUNT(*) AS registros, MAX(coleta_utc) AS ultima_coleta
FROM leituras
GROUP BY tag_id
ORDER BY tag_id;
