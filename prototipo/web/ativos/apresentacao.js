// Modo apresentação: percorre web/ativos/roteiro_demo.json com legendas, pausar/avançar/voltar e teclado (← → espaço, Esc).
class Apresentacao {
  constructor(roteiro, faixas, modoDemo = true) {
    this.roteiro = roteiro;
    this.faixas = faixas;
    this.modoDemo = modoDemo;
    this.indice = 0;
    this.pausado = false;
    this.inicioPasso = 0;
    this.decorrido = 0;
    this.relogio = null;
    this.focoAnterior = null;
    this.ficha = 0; // cada ida a um passo ganha uma ficha; respostas de passos antigos são descartadas
    this.aoTeclar = this.aoTeclar.bind(this);
  }

  abrir() {
    this.focoAnterior = document.activeElement;
    document.body.insertAdjacentHTML("beforeend", `
      <div class="demo" id="demo" role="dialog" aria-modal="true" aria-labelledby="demo-titulo">
        <div class="demo-caixa">
          <div class="demo-progresso" aria-hidden="true"><span id="demo-barra" style="width:0"></span></div>
          <div class="p-5 space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <p class="text-sm font-bold" id="demo-contador"></p>
              <p class="text-sm font-bold">DADOS SIMULADOS</p>
            </div>
            <h2 id="demo-titulo" class="text-3xl font-extrabold"></h2>
            <p id="demo-legenda" class="legenda" aria-live="polite"></p>
            <div id="demo-palco"></div>
            <div class="flex flex-wrap gap-2 pt-2" role="group" aria-label="Controles da apresentação">
              <button type="button" class="botao" id="demo-voltar">← Voltar</button>
              <button type="button" class="botao" id="demo-pausar" aria-pressed="false">⏸ Pausar</button>
              <button type="button" class="botao principal" id="demo-avancar">Avançar →</button>
              <button type="button" class="botao ml-auto" id="demo-sair">Sair (Esc)</button>
            </div>
            <p class="text-sm">Teclado: ← volta, → avança, espaço pausa, Esc sai.</p>
          </div>
        </div>
      </div>`);
    document.getElementById("demo-voltar").addEventListener("click", () => this.ir(this.indice - 1));
    document.getElementById("demo-avancar").addEventListener("click", () => this.ir(this.indice + 1));
    document.getElementById("demo-pausar").addEventListener("click", () => this.alternarPausa());
    document.getElementById("demo-sair").addEventListener("click", () => this.fechar());
    document.addEventListener("keydown", this.aoTeclar);
    this.ir(0);
    document.getElementById("demo-avancar").focus();
  }

  fechar() {
    clearInterval(this.relogio);
    document.removeEventListener("keydown", this.aoTeclar);
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    document.getElementById("demo")?.remove();
    this.focoAnterior?.focus();
  }

  aoTeclar(evento) {
    if (evento.key === "ArrowRight") { evento.preventDefault(); this.ir(this.indice + 1); }
    else if (evento.key === "ArrowLeft") { evento.preventDefault(); this.ir(this.indice - 1); }
    else if (evento.key === " " && !["BUTTON", "A"].includes(document.activeElement?.tagName)) { evento.preventDefault(); this.alternarPausa(); }
    else if (evento.key === "Escape") { this.fechar(); }
    else if (evento.key === "Tab") { this.prenderFoco(evento); }
  }

  prenderFoco(evento) {
    const focaveis = [...document.querySelectorAll("#demo button, #demo a")];
    if (!focaveis.length) return;
    const [primeiro, ultimo] = [focaveis[0], focaveis[focaveis.length - 1]];
    if (evento.shiftKey && document.activeElement === primeiro) { evento.preventDefault(); ultimo.focus(); }
    else if (!evento.shiftKey && document.activeElement === ultimo) { evento.preventDefault(); primeiro.focus(); }
  }

  alternarPausa() {
    this.pausado = !this.pausado;
    const b = document.getElementById("demo-pausar");
    b.setAttribute("aria-pressed", this.pausado);
    b.textContent = this.pausado ? "▶ Continuar" : "⏸ Pausar";
    if (this.pausado) this.decorrido += Date.now() - this.inicioPasso;
    else this.inicioPasso = Date.now();
  }

  async ir(indice) {
    const passos = this.roteiro.passos;
    if (indice < 0) indice = 0;
    if (indice >= passos.length) { this.fechar(); return; }
    this.indice = indice;
    const passo = passos[indice];
    document.getElementById("demo-contador").textContent = `${this.roteiro.titulo} · ${indice + 1} de ${passos.length}`;
    document.getElementById("demo-titulo").textContent = passo.titulo;
    document.getElementById("demo-legenda").textContent = passo.legenda || "";
    document.getElementById("demo-voltar").disabled = indice === 0;
    document.getElementById("demo-avancar").textContent = indice === passos.length - 1 ? "Concluir ✓" : "Avançar →";
    const palco = document.getElementById("demo-palco");
    palco.innerHTML = esqueleto("12rem");
    const ficha = ++this.ficha;
    await this.desenharPasso(palco, passo, () => ficha === this.ficha);
    if (ficha !== this.ficha) return;
    this.decorrido = 0;
    this.inicioPasso = Date.now();
    clearInterval(this.relogio);
    this.relogio = setInterval(() => this.tique(), 200);
  }

  tique() {
    const passo = this.roteiro.passos[this.indice];
    const total = (passo.duracao_s || 8) * 1000;
    const feito = this.decorrido + (this.pausado ? 0 : Date.now() - this.inicioPasso);
    const barra = document.getElementById("demo-barra");
    if (barra) barra.style.width = `${Math.min(100, (feito / total) * 100)}%`;
    // O último passo (resumo) fica parado até a pessoa concluir.
    if (feito >= total && !this.pausado && this.indice < this.roteiro.passos.length - 1) this.ir(this.indice + 1);
  }

  async desenharPasso(palco, passo, atual) {
    if (passo.tipo === "abertura") {
      palco.innerHTML = `<div class="grid gap-4 sm:grid-cols-[auto_1fr] items-center">
        <div class="semaforo" aria-hidden="true">${lampadas("Verde")}</div>
        <ol class="grid gap-2 sm:grid-cols-2 text-lg">
          <li class="cartao"><b>1 · Sensores</b><br>solo, temperatura e ar</li><li class="cartao"><b>2 · Gateway</b><br>confere as leituras</li>
          <li class="cartao"><b>3 · API e IA</b><br>classificador decide; LLM explica</li><li class="cartao"><b>4 · Semáforo</b><br>cor, palavra, ícone e forma</li></ol></div>`;
    } else if (passo.tipo === "cenario") {
      // Sem MODO_DEMO no servidor, a falha não pode ser simulada: o passo mostra a classificação normal e avisa.
      const simular = passo.simular_falha_llm && this.modoDemo;
      if (passo.simular_falha_llm && !this.modoDemo) {
        document.getElementById("demo-legenda").textContent = "Neste servidor a simulação de falha do LLM está desligada (MODO_DEMO). " + (passo.legenda || "");
      }
      const url = "/classificar" + (simular ? "?simular_falha_llm=true" : "");
      const r = await chamarApi(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(passo.leitura) });
      if (!atual()) return;
      if (!r.ok) { palco.innerHTML = `<div class="erro-caixa">${esc(r.erros[0])}</div>`; return; }
      palco.innerHTML = `<div id="demo-sem"></div><div class="grid gap-4 sm:grid-cols-2 mt-4"><div id="demo-barras"></div>
        <div class="text-base">${proporcoesHtml(r.dados)}</div></div>`;
      desenharSemaforo(document.getElementById("demo-sem"), { classe: r.dados.classe, mensagem: r.dados.mensagem,
        atualizado_em: r.dados.atualizado_em, selo: seloMensagem(r.dados.origem_mensagem) });
      desenharBarrasZonas(document.getElementById("demo-barras"), this.faixas, passo.leitura);
    } else if (passo.tipo === "sem_dados") {
      palco.innerHTML = '<div id="demo-sem"></div>';
      desenharSemaforo(document.getElementById("demo-sem"), { classe: null,
        mensagem: "Não recebemos leitura recente dos sensores. Confira o equipamento. Nenhuma avaliação é mostrada." });
    } else if (passo.tipo === "talhoes") {
      const r = await chamarApi("/status");
      if (!atual()) return;
      if (!r.ok) { palco.innerHTML = `<div class="erro-caixa">${esc(r.erros[0])}</div>`; return; }
      const lista = [...r.dados.leituras].sort((a, b) => GRAVIDADE[a.classe] - GRAVIDADE[b.classe]);
      palco.innerHTML = `<div class="grid gap-3 grid-cols-2 sm:grid-cols-4">${lista.map((l) => {
        const e = ESTADOS[l.classe];
        return `<div class="cartao cartao-talhao ${e ? e.cor : "cinza"} p-3"><div class="font-extrabold">${esc(l.nome)}</div>
          <div class="text-sm">${esc(nomeEspecie(l.especie))}</div>
          <div class="flex items-center gap-1 mt-1" style="color:var(--${e ? e.cor : "cinza"}-texto)">${ICONES[e ? e.icone : "semdados"]}<b>${e ? e.rotulo : "Sem dados"}</b></div></div>`;
      }).join("")}</div><p class="text-sm mt-2">${r.dados.hora_simulada ? `Hora simulada ${esc(r.dados.hora_simulada)}` : "Leituras do gateway"} · <a class="underline" href="talhoes.html">abrir a página de talhões</a></p>`;
    } else if (passo.tipo === "agricultor") {
      const r = await chamarApi("/status?talhao=" + encodeURIComponent(passo.talhao || "A"));
      if (!atual()) return;
      if (!r.ok) { palco.innerHTML = `<div class="erro-caixa">${esc(r.erros[0])}</div>`; return; }
      const l = r.dados.leituras[0];
      palco.innerHTML = `<p class="text-lg font-bold mb-2">${esc(l.nome)} · ${esc(nomeEspecie(l.especie))}</p><div id="demo-sem"></div>
        <div class="grid gap-3 sm:grid-cols-2 mt-3"><button type="button" class="botao principal text-xl" id="demo-ouvir">🔊 Ouvir</button>
        <a class="botao text-xl" href="agricultor.html?talhao=${encodeURIComponent(l.id)}">Abrir a visão do agricultor</a></div>`;
      desenharSemaforo(document.getElementById("demo-sem"), { classe: l.classe, mensagem: l.mensagem, atualizado_em: l.atualizado_em, tamanho: "gigante" });
      document.getElementById("demo-ouvir").addEventListener("click", () => {
        if (!("speechSynthesis" in window)) return;
        speechSynthesis.cancel();
        const fala = new SpeechSynthesisUtterance(`${l.classe ? ESTADOS[l.classe].rotulo : "Sem dados atualizados"}. ${l.mensagem}`);
        fala.lang = "pt-BR"; speechSynthesis.speak(fala);
      });
    } else if (passo.tipo === "mapa") {
      const r = await chamarApi("/riscos/" + encodeURIComponent(passo.regiao || "serrana"));
      if (!atual()) return;
      if (!r.ok) { palco.innerHTML = `<div class="erro-caixa">${esc(r.erros[0])}</div>`; return; }
      const contagem = {};
      r.dados.camadas.features.forEach((f) => { const t = f.properties.tipo;
        contagem[t] = contagem[t] || { baixo: 0, medio: 0, alto: 0 }; contagem[t][f.properties.nivel]++; });
      palco.innerHTML = `<div class="erro-caixa mb-3"><b>${esc(r.dados.aviso)}</b></div>
        <p class="text-lg font-bold mb-2">${esc(r.dados.regiao.nome)}</p>
        <div class="grid gap-2 sm:grid-cols-2">${Object.entries(r.dados.tipos).map(([t, info]) => `<div class="cartao p-3"
          style="border-left:8px solid ${info.cor}"><b>${esc(info.nome)}</b><br><span class="text-sm">Áreas: alto ${contagem[t]?.alto || 0},
          médio ${contagem[t]?.medio || 0}, baixo ${contagem[t]?.baixo || 0}</span><br><span class="text-sm">Fonte oficial: ${esc(info.fonte_oficial)}</span></div>`).join("")}</div>
        <a class="botao text-xl mt-3" href="mapa.html?regiao=${encodeURIComponent(r.dados.regiao.id)}">Abrir o mapa</a>`;
    } else if (passo.tipo === "fim") {
      palco.innerHTML = `<ul class="space-y-2 text-xl">${(passo.itens || []).map((i) => `<li class="cartao">✓ ${esc(i)}</li>`).join("")}</ul>`;
    } else {
      palco.innerHTML = `<p>Tipo de passo desconhecido no roteiro: ${esc(passo.tipo)}.</p>`;
    }
  }
}

function proporcoesHtml(d) {
  if (!d.proporcoes) return "";
  const cores = { Verde: "var(--verde)", Amarelo: "var(--amarelo)", Vermelho: "var(--vermelho)" };
  return `<p class="font-bold mb-1">Proporção de amostras parecidas</p>` + Object.entries(d.proporcoes).map(([c, p]) => `
    <div class="mb-1"><div class="flex justify-between"><span>${rotuloClasse(c)}</span><span>${pct(p)}</span></div>
    <div class="barra"><span style="width:${p * 100}%;background:${cores[c]}"></span></div></div>`).join("") +
    '<p class="text-sm mt-1">Não é confiança nem certeza do modelo.</p>';
}

async function iniciarApresentacao() {
  const [roteiro, faixas, saude] = await Promise.all([fetch("ativos/roteiro_demo.json").then((r) => r.json()).catch(() => null),
    carregarFaixas(), chamarApi("/saude")]);
  if (!roteiro) {
    const alvo = document.getElementById("erro-demo");
    if (alvo) { alvo.hidden = false; alvo.textContent = "Não consegui carregar o roteiro da demonstração. Confira se o servidor está ligado."; }
    return;
  }
  new Apresentacao(roteiro, faixas, !saude.ok || saude.dados.modo_demo).abrir();
}
