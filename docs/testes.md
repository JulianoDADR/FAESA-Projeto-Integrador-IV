# Testes automatizados

Gerado por `python scripts/relatorio_testes.py` (dentro de `prototipo/`) em
2026-11-15T21:02:43+00:00, a partir de uma execução real do `pytest`.
O mesmo `pytest` roda no GitHub Actions a cada push (`.github/workflows/testes.yml`), sem segredos: o LLM é sempre
simulado e cada teste usa um banco SQLite temporário.

**Resultado: 188 de 188 testes aprovados** (`188 passed, 1 warning in 6.54s`).

## Cenários exigidos (relatório, seção 7.6) e o que cobre cada um

| Tipo | Cenário | Resultado esperado | Resultado obtido | Situação |
|---|---|---|---|---|
| Unitário | Validação de leituras (faixa, tipo, campo ausente, espécie) | 422 e nenhuma cor | 9 de 9 testes passaram | **aprovado** |
| Unitário | Conversão e tratamento da linha serial (protocolo e calibração) | valores convertidos; linha quebrada recusada | 10 de 10 testes passaram | **aprovado** |
| Unitário | Fonte única das faixas (config/faixas.json) | gerador, validação e API usam o mesmo arquivo | 6 de 6 testes passaram | **aprovado** |
| Unitário | Escolha da mensagem de contingência | mensagem-padrão quando o LLM falha ou erra | 15 de 15 testes passaram | **aprovado** |
| Unitário | Regra conservadora do Vermelho (limiar e peso) | nunca tira um Vermelho; desempate documentado | 6 de 6 testes passaram | **aprovado** |
| Integração | API ↔ modelo ↔ camada de explicação | classe do classificador; LLM só reformula | 9 de 9 testes passaram | **aprovado** |
| Integração | Caminho HTTP do LLM: 429, timeout, sem rede, JSON malformado, saída incoerente | mensagem-padrão, semáforo segue funcionando, chave fora dos logs | 14 de 14 testes passaram | **aprovado** |
| Integração | API ↔ banco: ingestão autenticada e idempotente | 401/503 sem token; 409 em conflito; sem duplicar | 16 de 16 testes passaram | **aprovado** |
| Ponta a ponta | Gateway simulado → API → classificação → /status | talhões classificados e marcados como simulados | 1 de 1 testes passaram | **aprovado** |
| Falha | Sensor desconectado (leitura bruta no extremo do ADC) | linha descartada com motivo | 7 de 7 testes passaram | **aprovado** |
| Falha | Mensagem serial incompleta | linha descartada com motivo | 14 de 14 testes passaram | **aprovado** |
| Falha | Valor fora do intervalo esperado | descartado no gateway e recusado na API (contado) | 8 de 8 testes passaram | **aprovado** |
| Falha | Ausência de dados recentes (gateway parado) | cinza, sem cor de avaliação, com a hora da última leitura | 3 de 3 testes passaram | **aprovado** |
| Falha | LLM indisponível | mensagem-padrão | 8 de 8 testes passaram | **aprovado** |
| Falha | Rede do gateway cai / API devolve 500 | leituras ficam no buffer e são reenviadas com backoff | 1 de 1 testes passaram | **aprovado** |
| Segurança | Injeção de prompt (texto livre, campo extra) | 422; nada chega ao LLM | 4 de 4 testes passaram | **aprovado** |
| Segurança | Abuso: limite por IP, corpo grande, MODO_DEMO, cabeçalhos, CORS, teto do LLM | 429, 413, 403 e cabeçalhos presentes | 17 de 17 testes passaram | **aprovado** |
| Interface | Páginas, roteiro da demonstração e privacidade (sem armazenamento local) | 200; roteiro válido | 31 de 31 testes passaram | **aprovado** |

## O que NÃO é testado automaticamente

- O Arduino e o sensor de verdade (o sketch não foi carregado em hardware; a calibração está pendente).
- A qualidade das mensagens do Groq real (só com `python ml/avaliar_llm.py --ao-vivo` e revisão humana).
- A renderização visual das páginas e a voz do botão “Ouvir” (verificadas à mão e com o Chrome sem interface,
  fora do `pytest`; a acessibilidade foi medida com o Lighthouse).
- A imagem Docker e o deploy real (o teste de fumaça `scripts/teste_fumaca.py` roda contra a URL pública).

## Lista completa

### `testes/test_api.py` (8 de 8)

- ✅ `test_cenario_ideal_e_verde_e_solo_muito_seco_e_vermelho`
- ✅ `test_classificar_valido_devolve_uma_das_tres_classes`
- ✅ `test_falha_simulada_do_llm_ainda_responde_com_padrao`
- ✅ `test_fora_de_faixa_ou_ausente_da_422_sem_classe`
- ✅ `test_llm_indisponivel_de_verdade_ainda_responde`
- ✅ `test_metricas_tem_matriz_de_confusao_e_revocacao_do_vermelho`
- ✅ `test_saude_cenarios_e_historico`
- ✅ `test_texto_livre_e_recusado_na_api`

### `testes/test_avaliacao.py` (13 de 13)

- ✅ `test_avaliacao_mock_nunca_leva_caso_de_borda_ao_llm_e_nunca_quebra`
- ✅ `test_falhas_da_api_pelo_caminho_http_caem_na_mensagem_padrao`
- ✅ `test_frase_curta_em_portugues_chega_na_checagem_de_coerencia[Est\xe1 tudo \xf3timo, pode ficar tranquilo.-Amarelo]`
- ✅ `test_frase_curta_em_portugues_chega_na_checagem_de_coerencia[Fique tranquilo, est\xe1 tudo certo.-Vermelho]`
- ✅ `test_frases_boas_tipicas_continuam_aceitas`
- ✅ `test_ingles_e_espanhol_sao_recusados[Everything looks fine with your coffee field today.]`
- ✅ `test_ingles_e_espanhol_sao_recusados[Situaci\xf3n cr\xedtica en el cafetal, revise hoy.]`
- ✅ `test_intervalo_de_wilson`
- ✅ `test_ordens_de_manejo_sao_bloqueadas_mesmo_sem_numeros[Aplique adubo no talh\xe3o.]`
- ✅ `test_ordens_de_manejo_sao_bloqueadas_mesmo_sem_numeros[Pulverize as plantas amanh\xe3 cedo.]`
- ✅ `test_ordens_de_manejo_sao_bloqueadas_mesmo_sem_numeros[Regue bastante a lavoura hoje.]`
- ✅ `test_ordens_de_manejo_sao_bloqueadas_mesmo_sem_numeros[Vale irrigar a lavoura agora.]`
- ✅ `test_vermelho_sem_pedido_de_verificacao_e_recusado`

### `testes/test_concorrencia.py` (1 de 1)

- ✅ `test_llm_lento_nao_bloqueia_outras_rotas`

### `testes/test_decisao.py` (6 de 6)

- ✅ `test_api_aplica_a_regra_salva_no_modelo`
- ✅ `test_limiar_conservador_puxa_para_vermelho`
- ✅ `test_limiar_meio_desempata_a_favor_do_vermelho`
- ✅ `test_limiar_nunca_tira_um_vermelho`
- ✅ `test_metricas_tem_teto_decisao_e_comparacoes`
- ✅ `test_sem_limiar_vale_a_maior_proporcao`

### `testes/test_explicacao.py` (15 de 15)

- ✅ `test_entrada_do_llm_so_tem_campos_estruturados`
- ✅ `test_llm_bom_e_usado_e_vai_para_o_cache`
- ✅ `test_llm_com_falha_cai_no_padrao`
- ✅ `test_mensagens_padrao_passam_na_propria_validacao[Amarelo]`
- ✅ `test_mensagens_padrao_passam_na_propria_validacao[Verde]`
- ✅ `test_mensagens_padrao_passam_na_propria_validacao[Vermelho]`
- ✅ `test_saida_com_dose_do_llm_cai_no_padrao`
- ✅ `test_saida_incoerente_do_llm_cai_no_padrao`
- ✅ `test_saida_ruim_e_rejeitada[Amarelo-O solo est\xe1 seco, aplique 20 litros de \xe1gua hoje.]`
- ✅ `test_saida_ruim_e_rejeitada[Amarelo-Use 5 g de adubo por planta para o solo.]`
- ✅ `test_saida_ruim_e_rejeitada[Verde-O solo est\xe1 bom. A lavoura est\xe1 bem. As leituras est\xe3o certas. Siga assim.]`
- ✅ `test_saida_ruim_e_rejeitada[Verde-Situa\xe7\xe3o cr\xedtica, aja com urg\xeancia na lavoura.]`
- ✅ `test_saida_ruim_e_rejeitada[Verde-The soil is fine today and the crop looks good.]`
- ✅ `test_saida_ruim_e_rejeitada[Vermelho-Fique tranquilo, o solo est\xe1 \xf3timo.]`
- ✅ `test_sem_chave_usa_mensagem_padrao`

### `testes/test_faixas.py` (6 de 6)

- ✅ `test_api_avisa_quando_entrada_sai_do_treino`
- ✅ `test_config_tem_as_tres_variaveis_e_as_duas_especies`
- ✅ `test_dataset_respeita_a_faixa_de_treino`
- ✅ `test_faixa_de_treino_cabe_no_limite_fisico_e_ideal_cabe_no_treino`
- ✅ `test_gerador_e_validacao_usam_o_mesmo_arquivo`
- ✅ `test_rota_faixas_serve_o_arquivo`

### `testes/test_gateway.py` (26 de 26)

- ✅ `test_backoff_tem_teto`
- ✅ `test_buffer_guarda_sem_duplicar_e_resume_com_pandas`
- ✅ `test_calibracao_provisoria_ida_e_volta`
- ✅ `test_envio_aceito_marca_enviada_e_manda_token`
- ✅ `test_falha_de_rede_guarda_e_espera_com_backoff_crescente`
- ✅ `test_gateway_sem_token_nao_inicia`
- ✅ `test_interpreta_linha_completa_e_formatar_e_o_inverso`
- ✅ `test_linhas_quebradas_sao_invalidas[S500;T:20;U:70]`
- ✅ `test_linhas_quebradas_sao_invalidas[S:2000;T:20;U:70]`
- ✅ `test_linhas_quebradas_sao_invalidas[S:500;S:501;T:20;U:70]`
- ✅ `test_linhas_quebradas_sao_invalidas[S:500;T:20]`
- ✅ `test_linhas_quebradas_sao_invalidas[S:500;T:;U:70]`
- ✅ `test_linhas_quebradas_sao_invalidas[S:abc;T:20;U:70]`
- ✅ `test_linhas_quebradas_sao_invalidas[]`
- ✅ `test_ponta_a_ponta_gateway_simulado_alimenta_a_api_e_parar_deixa_cinza`
- ✅ `test_recusa_da_api_nao_e_reenviada_e_token_errado_para_o_envio`
- ✅ `test_reenvio_com_mesmo_numero_de_sequencia_e_duplicado`
- ✅ `test_salto_isolado_e_descartado_mas_novo_nivel_confirmado_e_aceito`
- ✅ `test_validador_converte_bruto_para_percentual`
- ✅ `test_validador_descarta_com_motivo[N:1;S:610;T:22;U:70-sem ponto]`
- ✅ `test_validador_descarta_com_motivo[P:A;N:1;S:0;T:22;U:70-sensor de solo desconectado]`
- ✅ `test_validador_descarta_com_motivo[P:A;N:1;S:1023;T:22;U:70-sensor de solo desconectado]`
- ✅ `test_validador_descarta_com_motivo[P:A;N:1;S:610-mensagem incompleta]`
- ✅ `test_validador_descarta_com_motivo[P:A;N:1;S:610;T:75;U:70-fora da faixa]`
- ✅ `test_validador_descarta_com_motivo[P:A;N:1;S:610;T:nan;U:nan-falha no DHT11]`
- ✅ `test_validador_descarta_com_motivo[P:Z;N:1;S:610;T:22;U:70-ponto desconhecido]`

### `testes/test_ingestao.py` (31 de 31)

- ✅ `test_disponibilidade_conta_validas_sobre_esperadas`
- ✅ `test_fonte_banco_mostra_a_leitura_mais_recente`
- ✅ `test_fonte_desconhecida_e_erro_claro`
- ✅ `test_gateway_parado_deixa_o_painel_cinza_com_o_passar_do_tempo`
- ✅ `test_historico_do_banco_tem_um_ponto_por_hora_e_buracos_sem_dados`
- ✅ `test_json_invalido_e_recusado`
- ✅ `test_leitura_antiga_vira_sem_dados_e_nunca_cor`
- ✅ `test_leitura_valida_e_gravada_com_especie_do_cadastro`
- ✅ `test_mesmo_instante_em_outro_fuso_e_a_mesma_leitura`
- ✅ `test_reenvio_igual_e_idempotente_e_valor_diferente_e_conflito`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo0-Campo n\xe3o permitido]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo1-Falta informar]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo2-desconhecido]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo3-origem]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo4-n\xfamero]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo5-ISO 8601]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo6-fuso]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo7-futuro]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo8-antigo]`
- ✅ `test_requisicoes_malformadas_sao_recusadas[corpo9-objeto]`
- ✅ `test_rota_disponibilidade`
- ✅ `test_sem_token_configurado_o_recebimento_fica_desligado`
- ✅ `test_semente_grava_simulado_alinhado_ao_relogio_e_pode_rodar_de_novo`
- ✅ `test_simulador_continua_simulado_mesmo_com_fonte_banco`
- ✅ `test_status_com_banco_classifica_pelo_mesmo_caminho`
- ✅ `test_talhao_que_nunca_enviou_fica_sem_dados`
- ✅ `test_token_ausente_ou_errado_e_recusado[Basic abc]`
- ✅ `test_token_ausente_ou_errado_e_recusado[Bearer errado]`
- ✅ `test_token_ausente_ou_errado_e_recusado[None]`
- ✅ `test_token_ausente_ou_errado_e_recusado[bearer token-de-teste-123]`
- ✅ `test_valor_fora_do_possivel_e_recusado_e_contado`

### `testes/test_interface.py` (31 de 31)

- ✅ `test_ativos_novos_sao_servidos`
- ✅ `test_menu_aponta_para_paginas_que_existem`
- ✅ `test_paginas_e_ativos_sao_servidos[agricultor.html]`
- ✅ `test_paginas_e_ativos_sao_servidos[avaliacao.html]`
- ✅ `test_paginas_e_ativos_sao_servidos[historico.html]`
- ✅ `test_paginas_e_ativos_sao_servidos[ia.html]`
- ✅ `test_paginas_e_ativos_sao_servidos[index.html]`
- ✅ `test_paginas_e_ativos_sao_servidos[painel.html]`
- ✅ `test_paginas_e_ativos_sao_servidos[sobre.html]`
- ✅ `test_paginas_e_ativos_sao_servidos[talhoes.html]`
- ✅ `test_roteiro_da_demonstracao_e_valido`
- ✅ `test_sem_armazenamento_local[agricultor.html]`
- ✅ `test_sem_armazenamento_local[apresentacao.js]`
- ✅ `test_sem_armazenamento_local[avaliacao.html]`
- ✅ `test_sem_armazenamento_local[barra_zonas.js]`
- ✅ `test_sem_armazenamento_local[comum.js]`
- ✅ `test_sem_armazenamento_local[historico.html]`
- ✅ `test_sem_armazenamento_local[ia.html]`
- ✅ `test_sem_armazenamento_local[index.html]`
- ✅ `test_sem_armazenamento_local[painel.html]`
- ✅ `test_sem_armazenamento_local[simulador.js]`
- ✅ `test_sem_armazenamento_local[sobre.html]`
- ✅ `test_sem_armazenamento_local[talhoes.html]`
- ✅ `test_toda_pagina_tem_comum_js_icone_e_idioma[agricultor.html]`
- ✅ `test_toda_pagina_tem_comum_js_icone_e_idioma[avaliacao.html]`
- ✅ `test_toda_pagina_tem_comum_js_icone_e_idioma[historico.html]`
- ✅ `test_toda_pagina_tem_comum_js_icone_e_idioma[ia.html]`
- ✅ `test_toda_pagina_tem_comum_js_icone_e_idioma[index.html]`
- ✅ `test_toda_pagina_tem_comum_js_icone_e_idioma[painel.html]`
- ✅ `test_toda_pagina_tem_comum_js_icone_e_idioma[sobre.html]`
- ✅ `test_toda_pagina_tem_comum_js_icone_e_idioma[talhoes.html]`

### `testes/test_llm_http.py` (14 de 14)

- ✅ `test_cache_evita_segunda_chamada_na_mesma_faixa`
- ✅ `test_chave_nunca_aparece_nos_logs`
- ✅ `test_falhas_do_provedor_viram_mensagem_padrao[efeito0-timeout]`
- ✅ `test_falhas_do_provedor_viram_mensagem_padrao[efeito1-sem conex\xe3o]`
- ✅ `test_falhas_do_provedor_viram_mensagem_padrao[efeito2-429 do plano gratuito]`
- ✅ `test_falhas_do_provedor_viram_mensagem_padrao[efeito3-chave inv\xe1lida]`
- ✅ `test_falhas_do_provedor_viram_mensagem_padrao[efeito4-503]`
- ✅ `test_falhas_do_provedor_viram_mensagem_padrao[efeito5-JSON malformado]`
- ✅ `test_falhas_do_provedor_viram_mensagem_padrao[efeito6-sem escolhas]`
- ✅ `test_pedido_ao_groq_tem_modelo_limites_e_token_no_cabecalho`
- ✅ `test_saida_ruim_pelo_http_vira_mensagem_padrao_e_e_contada[Aplique 30 litros de \xe1gua por planta agora.]`
- ✅ `test_saida_ruim_pelo_http_vira_mensagem_padrao_e_e_contada[Everything is fine.]`
- ✅ `test_saida_ruim_pelo_http_vira_mensagem_padrao_e_e_contada[Fique tranquilo, est\xe1 tudo certo.]`
- ✅ `test_saida_ruim_pelo_http_vira_mensagem_padrao_e_e_contada[Uma frase. Outra frase. Mais uma. E mais outra.]`

### `testes/test_seguranca.py` (17 de 17)

- ✅ `test_alimentador_grava_pelo_caminho_da_ingestao_e_marca_simulado`
- ✅ `test_cabecalhos_de_seguranca_em_api_e_paginas[/index.html]`
- ✅ `test_cabecalhos_de_seguranca_em_api_e_paginas[/saude]`
- ✅ `test_com_modo_demo_os_recursos_ficam_ligados`
- ✅ `test_corpo_grande_demais_e_recusado`
- ✅ `test_corpo_grande_sem_content_length_tambem_e_recusado`
- ✅ `test_cors_so_para_as_origens_configuradas`
- ✅ `test_hsts_so_em_https`
- ✅ `test_janela_do_limitador_libera_depois_de_um_minuto`
- ✅ `test_limitador_reconhece_subrotas_e_metodo`
- ✅ `test_limite_por_ip_devolve_429_com_retry_after`
- ✅ `test_saude_mostra_uso_do_llm_sem_segredo`
- ✅ `test_sem_modo_demo_os_recursos_de_demonstracao_ficam_desligados`
- ✅ `test_sem_origens_permitidas_nao_ha_cors`
- ✅ `test_startup_semeia_banco_vazio_e_liga_alimentador`
- ✅ `test_teto_por_dia_e_janela_de_um_minuto`
- ✅ `test_teto_por_minuto_do_llm_cai_na_mensagem_padrao`

### `testes/test_simulador.py` (11 de 11)

- ✅ `test_fonte_simulada_cumpre_a_interface`
- ✅ `test_leituras_ficam_na_faixa_de_treino_e_sao_marcadas_como_simuladas`
- ✅ `test_mesmo_passo_mesma_leitura_e_passos_diferentes_mudam`
- ✅ `test_rota_simulador_avalia_todos_os_talhoes`
- ✅ `test_rota_simulador_usa_o_mesmo_classificador_do_classificar`
- ✅ `test_rota_talhoes_e_historico`
- ✅ `test_simular_falha_do_llm_no_simulador`
- ✅ `test_talhao_desconhecido_e_passo_invalido`
- ✅ `test_talhao_instavel_fica_sem_dados_em_algum_momento`
- ✅ `test_temperatura_sobe_a_tarde`
- ✅ `test_um_dia_simulado_tem_os_tres_estados_e_sem_dados`

### `testes/test_validacao.py` (9 de 9)

- ✅ `test_campo_ausente_e_especie_desconhecida`
- ✅ `test_leitura_valida_passa`
- ✅ `test_texto_livre_nao_e_aceito`
- ✅ `test_valores_invalidos_sao_recusados[temperatura-99]`
- ✅ `test_valores_invalidos_sao_recusados[temperatura-True]`
- ✅ `test_valores_invalidos_sao_recusados[umidade_ar-101]`
- ✅ `test_valores_invalidos_sao_recusados[umidade_ar-muito]`
- ✅ `test_valores_invalidos_sao_recusados[umidade_solo--1]`
- ✅ `test_valores_invalidos_sao_recusados[umidade_solo-140]`
