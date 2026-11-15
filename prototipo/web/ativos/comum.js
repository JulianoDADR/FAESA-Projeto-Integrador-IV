// Código comum às páginas do protótipo AgroAnálise (dados SIMULADOS). Sem localStorage/sessionStorage:
// a visão (agricultor/técnico) e o talhão escolhido vivem só na URL (?visao=, ?talhao=).
const PAGINAS = [
  ["index.html", "Início"], ["agricultor.html", "Agricultor"], ["talhoes.html", "Talhões"], ["painel.html", "Painel"],
  ["historico.html", "Histórico"], ["ia.html", "IA ao vivo"], ["avaliacao.html", "Avaliação"], ["sobre.html", "Sobre e limites"],
];

// Cada estado tem cor + palavra + ícone + FORMA própria (círculo, triângulo, octógono), para quem não distingue cores.
const ESTADOS = {
  Verde: { cor: "verde", rotulo: "Ideal", icone: "ok", forma: "círculo" },
  Amarelo: { cor: "amarelo", rotulo: "Atenção", icone: "atencao", forma: "triângulo" },
  Vermelho: { cor: "vermelho", rotulo: "Ação crítica", icone: "critico", forma: "octógono" },
};
const GRAVIDADE = { Vermelho: 0, Amarelo: 1, null: 2, Verde: 3 };

const ICONES = {
  ok: '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M7 12.5l3.2 3.2L17 9"/></svg>',
  atencao: '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.5L1.8 21h20.4L12 2.5z"/><path d="M12 9.5v5.5M12 17.6v.4"/></svg>',
  critico: '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" aria-hidden="true"><path d="M8 2h8l6 6v8l-6 6H8l-6-6V8z"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/></svg>',
  semdados: '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2.4" stroke-dasharray="3 2.2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path stroke-dasharray="none" d="M9.2 9.5a3 3 0 115 2c-1.2.9-2.2 1.4-2.2 3M12 17.5v.5"/></svg>',
};

// ---------- URL: visão e parâmetros ----------
function parametroUrl(nome) { return new URLSearchParams(location.search).get(nome); }
function paginaAtual() { return location.pathname.split("/").pop() || "index.html"; }
function visaoAtual() {
  const v = parametroUrl("visao");
  if (v === "agricultor" || v === "tecnico") return v;
  return paginaAtual() === "agricultor.html" ? "agricultor" : "tecnico";
}
// Monta um link mantendo a visão escolhida (só quando ela foi escolhida explicitamente na URL).
function linkCom(pagina, extras = {}) {
  const p = new URLSearchParams();
  if (parametroUrl("visao")) p.set("visao", parametroUrl("visao"));
  Object.entries(extras).forEach(([k, v]) => (v === null ? p.delete(k) : p.set(k, v)));
  const q = p.toString();
  return pagina + (q ? "?" + q : "");
}
function linkVisao(visao) {
  const p = new URLSearchParams(location.search); p.set("visao", visao);
  return paginaAtual() + "?" + p.toString();
}

const nomeEspecie = (e) => ({ Arabica: "Arábica", Conilon: "Conilon" }[e] || e);
const rotuloClasse = (c) => (ESTADOS[c] ? ESTADOS[c].rotulo : c);
const pct = (x) => (x * 100).toFixed(1).replace(".", ",") + "%";
const num = (x, casas = 1) => Number(x).toFixed(casas).replace(".", ",");

function montarTopo() {
  const atual = paginaAtual(), visao = visaoAtual();
  document.documentElement.dataset.visao = visao;
  const links = PAGINAS.map(([arq, nome]) =>
    `<a href="${linkCom(arq)}" ${arq === atual ? 'aria-current="page"' : ""}>${nome}</a>`).join("");
  document.body.insertAdjacentHTML("afterbegin",
    `<a href="#conteudo" class="pular">Pular para o conteúdo</a>
     <div class="faixa-simulado" role="note">DADOS SIMULADOS · MODO DEMONSTRAÇÃO</div>
     <div id="aviso-servidor" class="aviso-servidor" role="status" hidden></div>
     <div id="anuncio" class="sr-only" aria-live="polite" aria-atomic="true"></div>
     <header class="max-w-5xl mx-auto px-4 pt-4">
       <div class="flex flex-wrap items-center justify-between gap-2">
         <div class="text-2xl font-extrabold">AgroAnálise <span class="text-base font-semibold" style="color:var(--cinza-texto)">protótipo</span></div>
         <nav class="alternador" aria-label="Escolher visão">
           <a href="${linkVisao("agricultor")}" ${visao === "agricultor" ? 'aria-current="true"' : ""}>Agricultor</a>
           <a href="${linkVisao("tecnico")}" ${visao === "tecnico" ? 'aria-current="true"' : ""}>Técnico</a>
         </nav>
       </div>
       <nav class="menu flex flex-wrap gap-1 mt-2" aria-label="Menu principal">${links}</nav></header>`);
  const principal = document.querySelector("main");
  if (principal && !principal.id) principal.id = "conteudo";
}

// Leitor de tela: avisa só quando algo muda de verdade (ex.: o estado do semáforo).
function anunciar(texto) {
  const alvo = document.getElementById("anuncio");
  if (!alvo) return;
  alvo.textContent = "";
  setTimeout(() => (alvo.textContent = texto), 60);
}

// ---------- API ----------
let pedidosLentos = 0;
async function chamarApi(caminho, opcoes) {
  // No plano gratuito, o servidor "dorme" e a primeira requisição pode levar dezenas de segundos.
  const aviso = document.getElementById("aviso-servidor");
  const relogio = setTimeout(() => {
    pedidosLentos++;
    if (aviso) { aviso.hidden = false; aviso.textContent = "O servidor está acordando… o primeiro acesso pode levar até um minuto."; }
  }, 2500);
  let resposta;
  try {
    resposta = await fetch(caminho, opcoes);
  } catch (e) {
    return { falhaRede: true, erros: ["Não consegui falar com o servidor. Confira a internet ou se ele está ligado."] };
  } finally {
    clearTimeout(relogio);
    if (aviso && !aviso.hidden && --pedidosLentos <= 0) { pedidosLentos = 0; aviso.hidden = true; }
  }
  let dados = null;
  try { dados = await resposta.json(); } catch (e) { /* corpo vazio */ }
  return { ok: resposta.ok, status: resposta.status, dados, erros: (dados && dados.erros) || (resposta.ok ? [] : ["Algo deu errado no servidor."]) };
}

function formatarHora(iso) {
  const d = new Date(iso);
  return isNaN(d) ? "—" : d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "medium" });
}

function tempoDesde(instanteMs) {
  const s = Math.max(0, Math.round((Date.now() - instanteMs) / 1000));
  if (s < 5) return "agora mesmo";
  if (s < 60) return `há ${s} s`;
  const m = Math.round(s / 60);
  return m < 60 ? `há ${m} min` : `há ${Math.round(m / 60)} h`;
}

function esc(texto) {
  return String(texto).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

const esqueleto = (altura = "8rem") => `<div class="esqueleto" style="height:${altura}" aria-hidden="true"></div><span class="sr-only">Carregando…</span>`;

// ---------- Semáforo ----------
// Três lâmpadas com formas distintas + texto + ícone (a cor nunca é o único sinal). classe = null => sem dados (cinza).
function lampadas(classe) {
  return ["Vermelho", "Amarelo", "Verde"].map((c) =>
    `<div class="lampada ${ESTADOS[c].cor} ${c === classe ? "acesa" : ""}"></div>`).join("");
}

function blocoEstado(classe, mensagem, tamanho = "") {
  const e = ESTADOS[classe];
  const titulo = e ? e.rotulo : "Sem dados atualizados";
  return `<div class="estado ${e ? e.cor : "cinza"} ${tamanho}"><div class="flex items-center gap-3">${ICONES[e ? e.icone : "semdados"]}
      <span class="titulo-estado font-extrabold">${titulo}</span></div>
      <p class="mensagem-estado mt-2 leading-snug">${esc(mensagem || "")}</p></div>`;
}

function desenharSemaforo(raiz, { classe, mensagem, atualizado_em, selo, tamanho = "" }) {
  const e = ESTADOS[classe];
  raiz.innerHTML = `<div class="grid gap-4 sm:grid-cols-[auto_1fr] items-center">
      <div class="semaforo ${tamanho}" role="img" aria-label="${e ? `Semáforo: ${e.rotulo} (${e.forma})` : "Semáforo apagado: sem dados atualizados"}">${lampadas(classe)}</div>
      <div>${blocoEstado(classe, mensagem, tamanho)}
      <p class="mt-3 text-base">Última atualização: <b>${atualizado_em ? formatarHora(atualizado_em) : "nenhuma leitura recente"}</b></p>
      ${selo || ""}</div></div>`;
  const chave = String(classe);
  if (raiz.dataset.classe !== undefined && raiz.dataset.classe !== chave) {
    anunciar(`${e ? e.rotulo : "Sem dados atualizados"}. ${mensagem || ""}`);
  }
  raiz.dataset.classe = chave;
}

function seloMensagem(origem) {
  return origem === "llm"
    ? '<span class="selo llm">Mensagem gerada por: LLM (Groq)</span>'
    : '<span class="selo padrao">Mensagem-padrão (LLM indisponível ou desligado)</span>';
}

document.addEventListener("DOMContentLoaded", montarTopo);
