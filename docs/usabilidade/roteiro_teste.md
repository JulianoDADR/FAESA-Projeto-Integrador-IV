# Roteiro do teste de usabilidade (C3)

Material para o grupo aplicar com pessoas (responsável sugerido: Rubiale, conforme o Quadro 7 do relatório).
Os indicadores e as metas vêm do relatório (seção 9.2, Quadro 5). **Nenhum resultado está preenchido**: os números
só existem depois da aplicação, calculados por `prototipo/ml/calcular_indicadores.py`.

## 1. Quem participa

- **Mínimo de 10 participantes** (meta do relatório), com o perfil da seção 9.1: pessoas com baixo letramento
  digital (por exemplo, familiares e conhecidos dos integrantes) e, se possível, produtores ou técnicos de extensão.
- Se não houver produtores, os resultados são **testes de protótipo** e não podem ser generalizados para a
  comunidade agrícola (relatório, seção 9.1).
- Cada pessoa recebe um **código** (P01, P02, …). **Não anote nome, telefone, endereço, foto nem gravação de rosto
  ou voz.**

## 2. Preparação (antes de cada sessão)

1. Celular com internet, brilho alto, som ligado. Abrir a URL pública em `…/agricultor.html?talhao=C`
   (talhão que costuma mostrar Atenção ou Ação crítica; confira antes) e esperar carregar (o servidor gratuito pode
   demorar no primeiro acesso).
2. Ter à mão: este roteiro, a planilha `planilha_coleta.csv` (ou uma cópia impressa) e um cronômetro.
3. Para a tarefa 3, se a tela não estiver em Ação crítica, use o modo apresentação (`index.html?demo=1`, passo
   “Calor excessivo”) ou o painel (`painel.html?modo=cenarios`, cenário “Solo muito seco”).

## 3. Termo de consentimento (ler em voz alta)

> Estamos testando um aplicativo de celular feito por estudantes da FAESA, que mostra se a lavoura de café está bem,
> pede atenção ou precisa de cuidado. **Quem está sendo avaliado é o aplicativo, não você.** Não existe resposta
> errada. Vamos pedir três tarefas e uma nota de 1 a 5. Leva uns 10 minutos.
> **Não vamos anotar seu nome nem nenhum dado que identifique você**; você vira um código, como “P03”.
> Não vamos gravar seu rosto nem sua voz. Os resultados serão usados só neste trabalho, juntos com os de outras
> pessoas. Você pode parar quando quiser, sem precisar explicar. Você aceita participar?

Anote na planilha apenas `consentiu = sim`. Se a resposta for não, agradeça e encerre.

## 4. Tarefas obrigatórias (contam para a adoção autônoma)

Leia cada tarefa como está escrita, sem apontar para a tela. Comece o cronômetro na primeira tarefa e pare na
última. **Ajuda** é qualquer dica sobre onde olhar ou o que tocar; repetir a pergunta não conta como ajuda.

| Nº | Peça assim | Resposta certa (para o observador) |
|---|---|---|
| 1 | “Olhando esta tela, como está a lavoura agora?” | A palavra ou o sentido do estado mostrado: Ideal, Atenção, Ação crítica ou Sem dados atualizados. |
| 2 | “Quando foi a última vez que o aparelho mediu a lavoura?” | A data/hora de “Última atualização” (ou “nenhuma leitura recente”). |
| 3 | (com a tela em Ação crítica) “E se aparecer esta tela, o que você faria?” | Ir até a lavoura e avaliar / olhar a situação. **Não** conta: aplicar algo, irrigar por conta do aplicativo ou “nada”. |

Conta como **autônomo** quem conclui as 3 tarefas **sem ajuda** em **até 5 minutos** no total (relatório, Quadro 5).

## 5. Tarefas extras (não entram na meta; registrar para melhorar a interface)

| Nº | Peça assim | Resposta certa |
|---|---|---|
| E1 | (em `talhoes.html`) “Qual talhão está precisando de mais cuidado?” | O primeiro cartão (Vermelho ou o mais grave). |
| E2 | “Consegue fazer o aplicativo ler a mensagem em voz alta?” | Toca em “Ouvir” e ouve a mensagem. |

## 6. Pergunta de clareza (escala de 1 a 5)

> “De 1 a 5, quanto você concorda com esta frase: **entendi o que a cor do semáforo quer dizer**?
> 1 é ‘não concordo nada’, 5 é ‘concordo totalmente’.”

Meta do relatório: **pelo menos 80% das respostas com nota 4 ou 5.**

## 7. Depois de cada sessão

- Preencha uma linha da planilha (`sim`/`nao`, tempo total em segundos, nota de 1 a 5).
- Em `observacoes`, anote só o que ajuda a melhorar a tela (onde a pessoa hesitou, palavras que não entendeu),
  **sem dados pessoais**.
- Quando todas as sessões terminarem: `python ml/calcular_indicadores.py --planilha ../docs/usabilidade/planilha_coleta.csv`
  (dentro de `prototipo/`). O script gera `docs/usabilidade/indicadores.md`.

## 8. Cuidados

- Não explique o semáforo antes das tarefas (isso mede a interface, não a explicação).
- Não use o teste para dar orientação agronômica; se a pessoa perguntar sobre manejo, sugira procurar a
  assistência técnica.
- Os dados exibidos são simulados: diga isso ao final, se a pessoa perguntar.
