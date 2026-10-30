-- Exemplos para o esquema versão 1 do historiador da Aula 5.
-- Parâmetros nomeados são fornecidos pelo executor; horários UTC ISO 8601.
-- Limites de período são [inicio, fim), e todas as consultas mantêm unidades originais.

-- consulta: tags
SELECT identificador, categoria, indice, descricao, unidade
FROM tags
ORDER BY CASE categoria WHEN 'medicao' THEN 0 ELSE 1 END, indice;

-- consulta: contagem
SELECT (SELECT COUNT(*) FROM ciclos) AS ciclos,
       (SELECT COUNT(*) FROM leituras) AS leituras;

-- consulta: amostras
SELECT ciclo_id, tag_id, valor, source_timestamp, coleta_utc, status_code, qualidade, validade
FROM leituras
WHERE tag_id = :tag AND coleta_utc >= :inicio AND coleta_utc < :fim
ORDER BY coleta_utc DESC
LIMIT :limite;

-- consulta: temperatura_30min
SELECT ciclo_id, valor, source_timestamp, coleta_utc, qualidade, validade
FROM leituras
WHERE tag_id = 'XMEAS(9)' AND coleta_utc >= :inicio AND coleta_utc < :fim
ORDER BY coleta_utc DESC
LIMIT :limite;

-- consulta: resumo_minuto
-- Apenas valores válidos: não incluir NULL nem qualidade ruim nas estatísticas.
SELECT substr(coleta_utc, 1, 16) || ':00+00:00' AS minuto_utc,
       COUNT(*) AS amostras, AVG(valor) AS media, MIN(valor) AS minimo, MAX(valor) AS maximo
FROM leituras
WHERE tag_id = :tag AND coleta_utc >= :inicio AND coleta_utc < :fim
  AND validade = 'valido' AND valor IS NOT NULL
GROUP BY substr(coleta_utc, 1, 16)
ORDER BY minuto_utc DESC
LIMIT :limite;

-- consulta: comparacao
-- Agrupamento por ciclo de coleta, não por coincidência de timestamps.
SELECT p.ciclo_id, p.coleta_utc, p.valor AS pressao_kpa_g, p.validade AS pressao_validade,
       t.valor AS temperatura_c, t.validade AS temperatura_validade,
       a.valor AS agua_reator_percentual, a.validade AS agua_validade
FROM leituras AS p
JOIN leituras AS t ON t.ciclo_id = p.ciclo_id AND t.tag_id = 'XMEAS(9)'
JOIN leituras AS a ON a.ciclo_id = p.ciclo_id AND a.tag_id = 'XMV(10)'
WHERE p.tag_id = 'XMEAS(7)' AND p.coleta_utc >= :inicio AND p.coleta_utc < :fim
ORDER BY p.coleta_utc DESC
LIMIT :limite;

-- consulta: anomalias
SELECT ciclo_id, tag_id, valor, source_timestamp, coleta_utc, status_code, qualidade, validade
FROM leituras
WHERE tag_id = :tag AND coleta_utc >= :inicio AND coleta_utc < :fim
  AND (qualidade <> 'Good' OR validade <> 'valido' OR source_timestamp IS NULL)
ORDER BY coleta_utc DESC
LIMIT :limite;
