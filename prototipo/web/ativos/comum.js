// Código comum às páginas do protótipo AgroAnálise (dados SIMULADOS). Sem localStorage/sessionStorage.
const PAGINAS = [
  ["index.html", "Início"], ["painel.html", "Painel"], ["historico.html", "Histórico"],
  ["ia.html", "IA ao vivo"], ["avaliacao.html", "Avaliação"], ["sobre.html", "Sobre e limites"],
];

const ESTADOS = {
  Verde: { cor: "verde", rotulo: "Ideal", icone: "ok" },
  Amarelo: { cor: "amarelo", rotulo: "Atenção", icone: "atencao" },
  Vermelho: { cor: "vermelho", rotulo: "Ação crítica", icone: "critico" },
};

const ICONES = {
  ok: '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M7 12.5l3.2 3.2L17 9"/></svg>',
  atencao: '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><path d="M12 3L2 21h20L12 3z"/><path d="M12 10v5M12 18v.5"/></svg>',
  critico: '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.8" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M8 8l8 8M16 8l-8 8"/></svg>',
  semdados: '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M9.2 9.5a3 3 0 115 2c-1.2.9-2.2 1.4-2.2 3M12 17.5v.5"/></svg>',
};

function montarTopo() {
  const atual = location.pathname.split("/").pop() || "index.html";
  const links = PAGINAS.map(([arq, nome]) =>
    `<a href="${arq}" ${arq === atual || (atual === "" && arq === "index.html") ? 'aria-current="page"' : ""}>${nome}</a>`).join("");
  document.body.insertAdjacentHTML("afterbegin",
    `<div class="faixa-simulado" role="status">DADOS SIMULADOS · MODO DEMONSTRAÇÃO</div>
     <header class="max-w-4xl mx-auto px-4 pt-4"><div class="text-2xl font-extrabold">AgroAnálise <span class="text-base font-semibold" style="color:var(--cinza-texto)">protótipo</span></div>
     <nav class="menu flex flex-wrap gap-1 mt-2" aria-label="Menu principal">${links}</nav></header>`);
}

async function chamarApi(caminho, opcoes) {
  let resposta;
  try {
    resposta = await fetch(caminho, opcoes);
  } catch (e) {
    return { falhaRede: true, erros: ["Não consegui falar com o servidor. Confira se ele está ligado (uvicorn app.principal:app)."] };
  }
  let dados = null;
  try { dados = await resposta.json(); } catch (e) { /* corpo vazio */ }
  return { ok: resposta.ok, status: resposta.status, dados, erros: (dados && dados.erros) || (resposta.ok ? [] : ["Algo deu errado no servidor."]) };
}

function formatarHora(iso) {
  const d = new Date(iso);
  return isNaN(d) ? "—" : d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "medium" });
}

function esc(texto) {
  return String(texto).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Desenha o semáforo: três lâmpadas + texto + ícone (a cor nunca é o único sinal). classe = null => sem dados (cinza).
function desenharSemaforo(raiz, { classe, mensagem, atualizado_em, selo }) {
  const e = ESTADOS[classe];
  const lampadas = ["Vermelho", "Amarelo", "Verde"].map((c) =>
    `<div class="lampada ${ESTADOS[c].cor} ${c === classe ? "acesa" : ""}"></div>`).join("");
  const bloco = e
    ? `<div class="estado ${e.cor}"><div class="flex items-center gap-3">${ICONES[e.icone]}<span class="text-3xl font-extrabold">${e.rotulo}</span></div>
       <p class="mt-2 text-xl leading-snug">${esc(mensagem)}</p></div>`
    : `<div class="estado cinza"><div class="flex items-center gap-3">${ICONES.semdados}<span class="text-3xl font-extrabold">Sem dados atualizados</span></div>
       <p class="mt-2 text-xl leading-snug">${esc(mensagem)}</p></div>`;
  raiz.innerHTML = `<div class="grid gap-4 sm:grid-cols-[auto_1fr] items-center">
      <div class="semaforo" role="img" aria-label="${e ? "Semáforo: " + e.rotulo : "Semáforo apagado: sem dados atualizados"}">${lampadas}</div>
      <div>${bloco}
      <p class="mt-3 text-base">Última atualização: <b>${atualizado_em ? formatarHora(atualizado_em) : "nenhuma leitura recente"}</b></p>
      ${selo || ""}</div></div>`;
}

function seloMensagem(origem) {
  return origem === "llm"
    ? '<span class="selo llm">Mensagem gerada por: LLM (Groq)</span>'
    : '<span class="selo padrao">Mensagem-padrão (LLM indisponível)</span>';
}

const rotuloClasse = (c) => (ESTADOS[c] ? ESTADOS[c].rotulo : c);
const pct = (x) => (x * 100).toFixed(1).replace(".", ",") + "%";

document.addEventListener("DOMContentLoaded", montarTopo);
