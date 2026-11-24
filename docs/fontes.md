# Fontes de dados e referências

Registro das fontes usadas no projeto, conforme a seção 7.2 do relatório (identificação, endereço, data de acesso, variáveis aproveitadas e transformações). Dados simulados devem ser sempre identificados como simulados. 

| Fonte | Endereço | Acesso | O que foi aproveitado | Transformações | 
|---|---|---|---|---|
| SEAG-ES – Programa de Desenvolvimento da Agricultura Familiar (dados do Censo Agropecuário IBGE 2017) | https://seag.es.gov.br/media/Documentos/Apresentacao-programa-vida-no-campo.pdf | 04/11/2026 | 108.014 estabelecimentos; 80.775 familiares (75%); 1,08 milhão de ha; 213.557 de 357.258 pessoas ocupadas; 21,2% com assistência técnica; participação de 51% (Conilon) e 57% (Arábica) | Usada como pista inicial; os números do relatório foram conferidos no IBGE e o relatório cita o IBGE |
| Bliska et al. (2021), Revista Ifes Ciência, v. 7, n. 1 (DOI 10.36524/ric.v7i1.1117) | https://revistas.ifes.edu.br/index.php/ric/article/view/1117 | 04/11/2026 | 63.976 estabelecimentos com café; 78,23% familiares; regiões e municípios produtores de Conilon | Transcrição |
| IBGE – Censo Agropecuário 2017 (SIDRA; API de dados abertos), tabelas 6778, 6780, 6882, 6887 e 6955 | https://sidra.ibge.gov.br e https://servicodados.ibge.gov.br/api/v3/agregados | 04/11/2026 | **Fonte primária dos números do relatório (UF 32):** 108.014 e 80.775 estabelecimentos; 17.088 com orientação técnica; 213.557 de 357.258 pessoas ocupadas; 1.079.038 de 3.246.763 ha; produção de café por espécie (Conilon 180.444 de 353.753 t; Arábica 65.376 de 113.511 t) | Percentuais calculados pelo grupo a partir dos valores publicados | 
| FAO EcoCrop | https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/ | 26/10/2026 | Faixas de referência de temperatura e precipitação (*Coffea arabica*) | Referência geral; não usar como limite operacional sem validação |
| INMET – Estações automáticas | https://portal.inmet.gov.br/servicos/esta%C3%A7%C3%B5es-autom%C3%A1ticas | 26/10/2026 | Dados meteorológicos de contexto | A definir |
| MAPA – ZARC Café | https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/notas-tecnicas-air/cafe_arabica | 26/10/2026 | Contexto de risco climático | Não usar como gatilho de irrigação |
| Embrapa – Bonomo et al. (2014), manejo de água em Conilon | https://www.embrapa.br/en/busca-de-publicacoes/-/publicacao/997903/alternativas-de-manejo-de-agua-de-irrigacao-em-cultivos-de-conilon | 26/10/2026 | Contexto do manejo de irrigação no Norte do ES | Nenhuma |
| Kaggle | A definir | – | Possível composição do dataset | Registrar o conjunto exato quando for usado | 
| GroqCloud – documentação | https://console.groq.com/docs | 04/11/2026 | LLM da camada de explicação (plano gratuito) | Conferir os limites vigentes do plano antes do C3 |
