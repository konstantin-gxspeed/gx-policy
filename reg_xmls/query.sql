SELECT
	MAX(1 - (regulations.embedding <=> sops.embedding)) AS cosine_similarity,
    sops.name    
FROM
    sops 
JOIN regulations ON 1 = 1

WHERE regulations.title='§ 211.25 Personnel qualifications.'
group by sops.name
ORDER BY
    cosine_similarity DESC

LIMIT 1000
