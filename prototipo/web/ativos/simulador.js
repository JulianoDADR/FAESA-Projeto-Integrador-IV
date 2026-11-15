// Atualização ao vivo: pede /status a cada 3 s. Com a fonte simulada, avança um passo (10 min simulados) por pedido;
// pausar e mudar a velocidade só mudam o ritmo. Com a fonte banco (gateway), só busca a leitura mais recente.
class Simulador {
  constructor({ talhao = null, aoAtualizar, aoErrar }) {
    this.talhao = talhao;
    this.aoAtualizar = aoAtualizar;
    this.aoErrar = aoErrar || (() => {});
    this.passo = null;
    this.velocidade = 1;
    this.pausado = false;
    this.ultimaAtualizacao = null;
    this.relogio = null;
    this.ocupado = false;
    this.fonte = null;
  }

  intervaloMs() { return 3000 / this.velocidade; }

  async buscar() {
    if (this.ocupado) return;
    this.ocupado = true;
    const p = new URLSearchParams();
    if (this.passo !== null) p.set("passo", this.passo);
    if (this.talhao) p.set("talhao", this.talhao);
    const r = await chamarApi("/status" + (p.toString() ? "?" + p : ""));
    this.ocupado = false;
    if (!r.ok) { this.aoErrar(r); return; }
    this.passo = r.dados.passo; // null com a fonte banco: não há passo para avançar
    this.fonte = r.dados.fonte;
    this.ultimaAtualizacao = Date.now();
    this.aoAtualizar(r.dados, this);
  }

  agendar() {
    clearTimeout(this.relogio);
    if (this.pausado) return;
    this.relogio = setTimeout(async () => {
      if (this.passo !== null) this.passo += 1;
      await this.buscar();
      this.agendar();
    }, this.intervaloMs());
  }

  async iniciar() { await this.buscar(); this.agendar(); }
  pausar() { this.pausado = true; clearTimeout(this.relogio); }
  continuar() { this.pausado = false; this.agendar(); }
  alternar() { this.pausado ? this.continuar() : this.pausar(); return this.pausado; }
  mudarVelocidade(v) { this.velocidade = v; this.agendar(); }
  async trocarTalhao(talhao) { this.talhao = talhao; await this.buscar(); this.agendar(); }
}

// Controles prontos (pausar, velocidade, "atualizado há X s"). Devolve a função que atualiza o texto do relógio.
function montarControlesSimulador(alvo, simulador) {
  alvo.innerHTML = `<div class="flex flex-wrap items-center gap-2">
      <button type="button" class="botao pequeno" data-acao="pausar" aria-pressed="false">⏸ Pausar</button>
      <span class="font-semibold ml-1" id="rotulo-velocidade" data-so-simulado>Velocidade:</span>
      <div role="group" aria-labelledby="rotulo-velocidade" class="flex gap-1" data-so-simulado>
        ${[1, 2, 4].map((v) => `<button type="button" class="botao pequeno" data-velocidade="${v}" aria-pressed="${v === 1}">${v}×</button>`).join("")}
      </div>
      <span class="text-base ml-auto" data-relogio aria-live="off">—</span>
    </div>`;
  const botaoPausa = alvo.querySelector('[data-acao="pausar"]');
  botaoPausa.addEventListener("click", () => {
    const pausado = simulador.alternar();
    botaoPausa.setAttribute("aria-pressed", pausado);
    botaoPausa.textContent = pausado ? "▶ Continuar" : "⏸ Pausar";
  });
  alvo.querySelectorAll("[data-velocidade]").forEach((b) => b.addEventListener("click", () => {
    alvo.querySelectorAll("[data-velocidade]").forEach((x) => x.setAttribute("aria-pressed", x === b));
    simulador.mudarVelocidade(Number(b.dataset.velocidade));
  }));
  const relogio = alvo.querySelector("[data-relogio]");
  const atualizar = (horaSimulada) => {
    const simulada = simulador.fonte !== "banco";
    alvo.querySelectorAll("[data-so-simulado]").forEach((e) => (e.hidden = !simulada));
    if (horaSimulada) relogio.dataset.hora = horaSimulada;
    const hora = !simulada ? "Leituras do gateway · " : relogio.dataset.hora ? `Hora simulada ${relogio.dataset.hora} · ` : "";
    relogio.textContent = simulador.ultimaAtualizacao
      ? `${hora}atualizado ${tempoDesde(simulador.ultimaAtualizacao)}${simulador.pausado ? " (pausado)" : ""}` : "carregando…";
  };
  setInterval(() => atualizar(), 1000);
  return atualizar;
}
