// Simulador ao vivo no navegador: pede /simulador/leituras a cada 3 s (passo a passo, 10 min simulados por passo).
// Pausar e mudar a velocidade só mudam o ritmo dos pedidos; o servidor não guarda estado.
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
  }

  intervaloMs() { return 3000 / this.velocidade; }

  async buscar() {
    if (this.ocupado) return;
    this.ocupado = true;
    const p = new URLSearchParams();
    if (this.passo !== null) p.set("passo", this.passo);
    if (this.talhao) p.set("talhao", this.talhao);
    const r = await chamarApi("/simulador/leituras" + (p.toString() ? "?" + p : ""));
    this.ocupado = false;
    if (!r.ok) { this.aoErrar(r); return; }
    this.passo = r.dados.passo;
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
      <span class="font-semibold ml-1" id="rotulo-velocidade">Velocidade:</span>
      <div role="group" aria-labelledby="rotulo-velocidade" class="flex gap-1">
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
    if (horaSimulada) relogio.dataset.hora = horaSimulada;
    const hora = relogio.dataset.hora ? `Hora simulada ${relogio.dataset.hora} · ` : "";
    relogio.textContent = simulador.ultimaAtualizacao
      ? `${hora}atualizado ${tempoDesde(simulador.ultimaAtualizacao)}${simulador.pausado ? " (pausado)" : ""}` : "carregando…";
  };
  setInterval(() => atualizar(), 1000);
  return atualizar;
}
