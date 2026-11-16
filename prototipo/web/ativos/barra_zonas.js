// Barras com zonas: cada variável vira uma barra "seco / ok / encharcado" com um marcador no valor lido.
// Os limites vêm de /faixas (config/faixas.json): intervalo de treino e faixas PROVISÓRIAS de rotulagem por espécie.
let promessaFaixas = null;
function carregarFaixas() {
  if (!promessaFaixas) {
    promessaFaixas = chamarApi("/faixas").then((r) => {
      if (!r.ok) { promessaFaixas = null; return null; }
      return r.dados;
    });
  }
  return promessaFaixas;
}

const ORDEM_VARIAVEIS = ["umidade_solo", "temperatura", "umidade_ar"];
const NOME_CURTO = { umidade_solo: "Solo", temperatura: "Temperatura", umidade_ar: "Ar" };

// Devolve as zonas [{de, ate, tipo, nome}] de uma variável para uma espécie.
function zonasDaVariavel(faixas, especie, variavel) {
  const info = faixas.variaveis[variavel];
  const [minimo, maximo] = info.faixa_treino;
  const [inicio, fim, margem] = faixas.rotulagem[especie][variavel];
  const [baixo, ok, alto] = info.zonas;
  const pontos = [minimo, Math.max(minimo, inicio - margem), inicio, fim, Math.min(maximo, fim + margem), maximo];
  const tipos = [["critica", baixo], ["atencao", baixo], ["ok", ok], ["atencao", alto], ["critica", alto]];
  return tipos.map(([tipo, nome], i) => ({ de: pontos[i], ate: pontos[i + 1], tipo, nome })).filter((z) => z.ate > z.de);
}

function zonaDoValor(zonas, valor) {
  return zonas.find((z, i) => valor < z.ate || i === zonas.length - 1);
}

const DESCRICAO_TIPO = { ok: "dentro do ideal", atencao: "pede atenção", critica: "bem fora do ideal" };

function barraDeZonas(faixas, especie, variavel, valor, compacto = false) {
  const info = faixas.variaveis[variavel];
  const zonas = zonasDaVariavel(faixas, especie, variavel);
  const [minimo, maximo] = info.faixa_treino;
  const total = maximo - minimo;
  const faixasHtml = zonas.map((z) => `<div class="zona ${z.tipo}" style="width:${((z.ate - z.de) / total) * 100}%"></div>`).join("");
  const nome = NOME_CURTO[variavel];
  if (valor === null || valor === undefined) {
    return `<div class="${compacto ? "" : "mb-3"}"><div class="flex justify-between text-base"><b>${nome}</b><span>sem leitura</span></div>
      <div class="zonas" style="opacity:.4">${faixasHtml}</div></div>`;
  }
  const zona = zonaDoValor(zonas, valor);
  const posicao = Math.min(100, Math.max(0, ((valor - minimo) / total) * 100));
  const valorTexto = `${num(valor, variavel === "temperatura" ? 1 : 0)}${variavel === "temperatura" ? " °C" : "%"}`;
  const rotulo = `${nome}: ${valorTexto}, ${zona.nome} (${DESCRICAO_TIPO[zona.tipo]})`;
  return `<div class="${compacto ? "" : "mb-3"}">
    <div class="flex justify-between gap-2 ${compacto ? "text-sm" : "text-base"}"><b>${nome}</b><span><b>${valorTexto}</b> · ${esc(zona.nome)}</span></div>
    <div class="zonas" role="img" aria-label="${esc(rotulo)}">${faixasHtml}<div class="marcador" style="left:${posicao}%"></div></div>
    ${compacto ? "" : `<div class="rotulos-zonas" aria-hidden="true"><span>${esc(info.zonas[0])}</span><span>${esc(info.zonas[1])}</span><span>${esc(info.zonas[2])}</span></div>`}
  </div>`;
}

// leitura: {especie, umidade_solo, temperatura, umidade_ar}. Mostra a nota de faixas provisórias (exceto no modo compacto).
function desenharBarrasZonas(alvo, faixas, leitura, { compacto = false } = {}) {
  if (!faixas) { alvo.innerHTML = '<p class="text-sm">Faixas indisponíveis.</p>'; return; }
  alvo.innerHTML = ORDEM_VARIAVEIS.map((v) => barraDeZonas(faixas, leitura.especie, v, leitura[v], compacto)).join(compacto ? '<div class="h-2"></div>' : "") +
    (compacto ? "" : `<p class="text-sm mt-1" style="color:var(--cinza-texto)">Faixas provisórias, de demonstração (${esc(nomeEspecie(leitura.especie))}). Não são parâmetros agronômicos validados. As barras mostram cada leitura sozinha; a cor do semáforo vem do classificador, que olha as três juntas e pode divergir perto dos limites.</p>`);
}
