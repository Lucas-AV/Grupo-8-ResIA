import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const repoDir = path.resolve(process.env.REPO_DIR || process.cwd());
const skillDir = path.resolve(process.env.SKILL_DIR || "");
const runtimePython = process.env.RUNTIME_PYTHON || "python";
if (!skillDir || skillDir === path.parse(skillDir).root) {
  throw new Error("Defina SKILL_DIR com o diretório da skill de apresentações.");
}

const { applyPresentationChartFont, finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href,
);

const BUILD = path.join(repoDir, ".presentation-build");
const OUTPUT = path.join(repoDir, "docs", "apresentacao");
const PITCH_PREVIEW = path.join(BUILD, "previews", "pitch");
const TECH_PREVIEW = path.join(BUILD, "previews", "tecnica");
const FONT = "Arial";
const C = {
  cream: "#F6F4EE",
  paper: "#FFFFFF",
  dark: "#17150F",
  ink: "#24221D",
  muted: "#69665E",
  blue: "#2A78D6",
  blueSoft: "#DCEBFA",
  green: "#1DB954",
  line: "#D8D3C8",
  warm: "#EDC56A",
  coral: "#E66B55",
};

await fs.rm(BUILD, { recursive: true, force: true });
await fs.mkdir(PITCH_PREVIEW, { recursive: true });
await fs.mkdir(TECH_PREVIEW, { recursive: true });
await fs.mkdir(path.join(OUTPUT, "pitch"), { recursive: true });
await fs.mkdir(path.join(OUTPUT, "tecnica"), { recursive: true });

function rect(slide, left, top, width, height, fill, radius = 0, line = "none") {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: { left, top, width, height },
    fill,
    line: line === "none" ? { fill: "none", width: 0 } : { fill: line, width: 1 },
  });
}

function textBox(slide, text, left, top, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: options.size ?? 28,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    autoFit: options.autoFit ?? "shrinkText",
    alignment: options.align ?? "left",
    verticalAlignment: options.vertical ?? "middle",
  };
  return shape;
}

function line(slide, x1, y1, x2, y2, color = C.line, width = 3) {
  return slide.shapes.add({
    geometry: "line",
    position: { left: x1, top: y1, width: x2 - x1, height: y2 - y1 },
    fill: "none",
    line: { fill: color, width, endArrowType: "triangle" },
  });
}

function baseSlide(presentation, title, section, number, dark = false) {
  const slide = presentation.slides.add();
  slide.background.fill = dark ? C.dark : C.cream;
  textBox(slide, section.toUpperCase(), 72, 35, 300, 24, {
    size: 16,
    bold: true,
    color: dark ? C.warm : C.blue,
  });
  textBox(slide, title, 72, 66, 1080, 72, {
    size: 46,
    bold: true,
    color: dark ? C.paper : C.ink,
  });
  textBox(slide, String(number).padStart(2, "0"), 1165, 44, 50, 26, {
    size: 18,
    bold: true,
    color: dark ? C.paper : C.muted,
    align: "right",
  });
  return slide;
}

function badge(slide, label, left, top, width, color = C.blue) {
  rect(slide, left, top, width, 38, color, 18);
  const inset = width < 70 ? 6 : 12;
  textBox(slide, label, left + inset, top + 3, width - inset * 2, 32, {
    size: 18,
    bold: true,
    color: C.paper,
    align: "center",
  });
}

function note(slide, duration, speech, sources) {
  slide.speakerNotes.textFrame.setText(
    `Tempo: ${duration}\nNotas de fala: ${speech}\nFontes: ${sources}`,
  );
}

function addFooter(slide, label, dark = false) {
  textBox(slide, label, 72, 684, 1136, 20, {
    size: 14,
    color: dark ? "#C7C2B8" : C.muted,
  });
}

function createPitch() {
  const p = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // 1 — capa
  let s = p.slides.add();
  s.background.fill = C.dark;
  rect(s, 72, 78, 12, 500, C.blue);
  textBox(s, "MelodIA", 118, 105, 930, 92, { size: 72, bold: true, color: C.paper });
  textBox(s, "Agente de Recomendação Musical", 122, 205, 860, 50, {
    size: 30,
    color: C.warm,
  });
  textBox(s, "Peça com suas palavras.\nReceba faixas reais e uma explicação simples.", 122, 300, 930, 130, {
    size: 38,
    bold: true,
    color: C.paper,
  });
  badge(s, "PITCH · 5 MIN", 122, 500, 190, C.blue);
  textBox(s, "Grupo 8", 1000, 615, 180, 34, { size: 20, color: "#C7C2B8", align: "right" });
  note(s, "00:15", "Apresente o nome MelodIA e a promessa: uma conversa simples que leva a sugestões verificáveis.", "docs/apresentacao/ROTEIRO_PITCH.md");

  // 2 — problema
  s = baseSlide(p, "Descobrir música não deveria virar trabalho", "O problema", 2);
  textBox(s, "“Quero um pagode animado para hoje.”", 112, 160, 1056, 70, {
    size: 40,
    bold: true,
    color: C.blue,
    align: "center",
  });
  const pain = [
    ["Filtros demais", "A intenção humana não cabe bem em menus."],
    ["Pouca confiança", "Uma sugestão inventada quebra a experiência."],
    ["Pouca explicação", "O usuário quer entender por que recebeu aquela faixa."],
  ];
  pain.forEach(([head, body], i) => {
    const x = 72 + i * 389;
    rect(s, x, 290, 350, 205, i === 1 ? C.blueSoft : C.paper, 18, C.line);
    textBox(s, head, x + 28, 315, 294, 42, { size: 28, bold: true });
    textBox(s, body, x + 28, 370, 294, 92, { size: 22, color: C.muted });
  });
  textBox(s, "O espaço em branco entre intenção e catálogo é onde o MelodIA atua.", 110, 545, 1060, 50, {
    size: 26,
    bold: true,
    align: "center",
  });
  addFooter(s, "MelodIA · descoberta por conversa");
  note(s, "00:35", "Parta do pedido cotidiano e mostre três atritos: procurar, confiar e entender.", "analise_mercado_streaming/RELATORIO.md; docs/apresentacao/ROTEIRO_PITCH.md");

  // 3 — mercado
  s = baseSlide(p, "O streaming ainda cresce — e o Brasil acelera", "Mercado", 3);
  const chart = s.charts.add("bar", {
    position: { left: 72, top: 170, width: 700, height: 405 },
    categories: ["Brasil", "Mundo"],
    series: [{ name: "Crescimento em 2024", values: [14.1, 6.4], fill: C.blue }],
    barOptions: { direction: "column", grouping: "clustered" },
    hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "0.0\"%\"" },
  });
  applyPresentationChartFont(chart, { fontFamily: FONT });
  rect(s, 830, 186, 350, 330, C.dark, 22);
  textBox(s, "#8", 875, 218, 260, 90, { size: 66, bold: true, color: C.warm, align: "center" });
  textBox(s, "Brasil no ranking\nmundial de receitas", 870, 320, 270, 90, {
    size: 28,
    bold: true,
    color: C.paper,
    align: "center",
  });
  textBox(s, "A oportunidade não é mais ter acesso.\nÉ descobrir melhor.", 830, 540, 350, 72, {
    size: 24,
    bold: true,
    color: C.blue,
    align: "center",
  });
  addFooter(s, "Crescimento de receitas gravadas em 2025");
  note(s, "00:40", "Compare 14,1% no Brasil com 6,4% no mundo e conecte crescimento com descoberta.", "Pro-Música Brasil, Mercado Brasileiro de Música 2025; IFPI Global Music Report 2026; analise_mercado_streaming/RELATORIO.md");

  // 4 — experiência
  s = baseSlide(p, "Da conversa à recomendação, sem exigir filtros", "Experiência", 4);
  const stages = [
    ["1", "Pedido", "“pagode animado”"],
    ["2", "Entendimento", "gênero + energia"],
    ["3", "Catálogo", "faixas existentes"],
    ["4", "Resposta", "sugestões + motivo"],
  ];
  stages.forEach(([n, head, body], i) => {
    const x = 62 + i * 305;
    rect(s, x, 220, 250, 245, C.paper, 20, C.line);
    badge(s, n, x + 20, 242, 48, i === 3 ? C.green : C.blue);
    textBox(s, head, x + 24, 300, 202, 42, { size: 28, bold: true });
    textBox(s, body, x + 24, 357, 202, 66, { size: 22, color: C.muted, align: "center" });
    if (i < stages.length - 1) line(s, x + 250, 342, x + 296, 342, C.blue, 4);
  });
  textBox(s, "O LLM pode ajudar a compreender. A recomendação continua presa ao catálogo.", 150, 525, 980, 64, {
    size: 27,
    bold: true,
    align: "center",
  });
  addFooter(s, "Experiência simples para o usuário; controles claros por trás");
  note(s, "00:45", "Explique os quatro passos sem jargão e destaque que a conversa é a entrada, não a fonte das músicas.", "agente_conversacional/main.py; agente_conversacional/recomendacao/busca.py");

  // 5 — confiança
  s = baseSlide(p, "A resposta não pode inventar músicas", "Confiança", 5, true);
  rect(s, 74, 170, 520, 370, "#24221D", 20, "#3B3831");
  textBox(s, "Determinístico", 112, 202, 440, 48, { size: 32, bold: true, color: C.paper });
  textBox(s, "• valida o pedido\n• busca no conjunto local\n• calcula similaridade\n• limita e diversifica resultados", 112, 272, 420, 210, {
    size: 27,
    color: "#E9E5DB",
  });
  rect(s, 686, 170, 520, 370, C.blue, 20);
  textBox(s, "LLM opcional", 724, 202, 440, 48, { size: 32, bold: true, color: C.paper });
  textBox(s, "• interpreta texto livre\n• segue um contrato JSON\n• pode falhar sem parar o fluxo\n• nunca cria a lista final", 724, 272, 420, 210, {
    size: 27,
    color: C.paper,
  });
  badge(s, "CATÁLOGO = FONTE DA VERDADE", 418, 575, 444, C.green);
  addFooter(s, "Separação de responsabilidades reduz alucinações", true);
  note(s, "00:35", "Contraste o núcleo determinístico com o apoio opcional do LLM. Reforce: o catálogo é a fonte da verdade.", "docs/PIPELINE_AGENTE_PROPOSTA_B.md; agente_conversacional/interpretacao.py; agente_conversacional/recomendacao/busca.py");

  // 6 — catálogo
  s = baseSlide(p, "Um catálogo amplo, com números que dizem coisas diferentes", "Evidências", 6);
  const chart2 = s.charts.add("bar", {
    position: { left: 72, top: 170, width: 760, height: 410 },
    categories: ["Registros", "Faixas únicas", "Repetições entre gêneros"],
    series: [{ name: "Quantidade", values: [128830, 97534, 31296], fill: C.blue }],
    barOptions: { direction: "bar", grouping: "clustered" },
    hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "#,##0" },
  });
  applyPresentationChartFont(chart2, { fontFamily: FONT });
  rect(s, 885, 190, 295, 280, C.dark, 24);
  textBox(s, "118", 915, 226, 235, 82, { size: 62, bold: true, color: C.warm, align: "center" });
  textBox(s, "gêneros no conjunto\nprocessado atual", 915, 326, 235, 92, {
    size: 25,
    bold: true,
    color: C.paper,
    align: "center",
  });
  textBox(s, "Repetição não é erro: uma faixa pode aparecer em mais de um gênero.", 868, 500, 328, 90, {
    size: 22,
    color: C.muted,
    align: "center",
  });
  addFooter(s, "Perfil do conjunto processado · setembro de 2026");
  note(s, "00:35", "Diferencie registros, faixas únicas e repetições. Diga que a análise de mercado é de agosto e o conjunto processado foi atualizado depois.", "data/analytics/dataset_profile.json; analise_exploratoria.ipynb; analise_mercado_streaming/RELATORIO.md");

  // 7 — demo
  s = baseSlide(p, "Demo: “quero um pagode animado”", "Ao vivo", 7);
  badge(s, "65 SEGUNDOS", 985, 97, 190, C.coral);
  rect(s, 85, 175, 1110, 360, C.paper, 24, C.line);
  rect(s, 125, 215, 460, 78, C.blueSoft, 18);
  textBox(s, "Você: quero um pagode animado", 150, 228, 410, 50, { size: 25, bold: true, color: C.ink });
  textBox(s, "→", 610, 220, 50, 60, { size: 42, bold: true, color: C.blue, align: "center" });
  rect(s, 685, 205, 460, 205, C.dark, 18);
  textBox(s, "MelodIA", 718, 224, 180, 38, { size: 25, bold: true, color: C.warm });
  textBox(s, "3 faixas do catálogo\n+ motivo da escolha\n+ filtros aplicados", 718, 278, 380, 110, { size: 26, color: C.paper });
  badge(s, "SEM LLM", 173, 360, 148, C.blue);
  badge(s, "SEM OAUTH", 342, 360, 168, C.blue);
  textBox(s, "Se algo falhar, entra o clipe reserva de 45 s com o mesmo fluxo.", 165, 455, 950, 48, {
    size: 25,
    bold: true,
    align: "center",
  });
  addFooter(s, "A demo principal funciona de forma anônima e determinística");
  note(s, "01:05", "Digite o cenário combinado, mostre as faixas e explique por que a resposta continua funcionando sem LLM e sem Spotify.", "docs/apresentacao/ENSAIO_GERAL.md; docs/apresentacao/video/GUIA_GRAVACAO.md");

  // 8 — fechamento
  s = baseSlide(p, "MelodIA transforma intenção em descoberta confiável", "Fechamento", 8, true);
  const claims = [
    ["Natural", "pedido em linguagem comum"],
    ["Confiável", "faixas vêm do catálogo"],
    ["Evolutivo", "LLM e Spotify são camadas opcionais"],
  ];
  claims.forEach(([head, body], i) => {
    const x = 82 + i * 390;
    textBox(s, head, x, 190, 340, 52, { size: 36, bold: true, color: i === 1 ? C.warm : C.paper, align: "center" });
    textBox(s, body, x + 15, 255, 310, 72, { size: 23, color: "#D6D1C7", align: "center" });
  });
  rect(s, 232, 390, 816, 2, C.blue);
  textBox(s, "Próximo passo", 400, 430, 480, 44, { size: 24, bold: true, color: C.blue, align: "center" });
  textBox(s, "validar com usuários e medir a qualidade percebida das recomendações", 210, 492, 860, 82, {
    size: 30,
    bold: true,
    color: C.paper,
    align: "center",
  });
  textBox(s, "Obrigado.", 485, 610, 310, 45, { size: 28, bold: true, color: C.warm, align: "center" });
  note(s, "00:30", "Retome os três diferenciais, apresente a evolução pretendida e encerre com uma frase curta.", "analise_mercado_streaming/RELATORIO.md; docs/apresentacao/ROTEIRO_PITCH.md");

  return p;
}

async function createTechnical() {
  const p = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  let s = p.slides.add();
  s.background.fill = C.dark;
  textBox(s, "MelodIA", 88, 88, 420, 68, { size: 58, bold: true, color: C.paper });
  textBox(s, "Arquitetura do agente\ne uso responsável de LLM", 88, 205, 920, 150, {
    size: 48,
    bold: true,
    color: C.paper,
  });
  rect(s, 88, 398, 720, 4, C.blue);
  textBox(s, "Apresentação técnica · 8 minutos", 88, 438, 620, 42, { size: 28, color: C.warm });
  badge(s, "GRUPO 8", 88, 542, 150, C.blue);
  note(s, "00:20", "Defina o escopo: do texto do usuário até sugestões verificáveis, com o LLM como componente opcional.", "docs/PIPELINE_AGENTE_PROPOSTA_B.md; docs/apresentacao/ROTEIRO_TECNICO.md");

  // 2
  s = baseSlide(p, "Componentes atuais do sistema", "Arquitetura", 2);
  const comps = [
    ["Interface", "React / experiência"],
    ["API", "FastAPI / sessões"],
    ["Agente", "interpretação + regras"],
    ["Dados", "CSV processado"],
  ];
  comps.forEach(([head, body], i) => {
    const x = 52 + i * 305;
    rect(s, x, 230, 250, 180, i === 2 ? C.blueSoft : C.paper, 18, C.line);
    textBox(s, head, x + 20, 260, 210, 42, { size: 29, bold: true, align: "center" });
    textBox(s, body, x + 20, 318, 210, 58, { size: 21, color: C.muted, align: "center" });
    if (i < comps.length - 1) line(s, x + 250, 320, x + 298, 320, C.blue, 4);
  });
  rect(s, 202, 480, 876, 86, C.dark, 16);
  textBox(s, "LLM e Spotify são integrações opcionais; o núcleo local continua utilizável.", 230, 494, 820, 58, {
    size: 26,
    bold: true,
    color: C.paper,
    align: "center",
  });
  addFooter(s, "Separar componentes deixa falhas isoladas e caminhos de contingência claros");
  note(s, "00:45", "Percorra interface, API, agente e dados. Posicione LLM e Spotify como integrações opcionais.", "spotify_explorer/frontend/src; agente_conversacional/main.py; agente_conversacional/recomendacao/dataset.py");

  // 3
  s = baseSlide(p, "Fluxo completo de uma mensagem", "Pipeline", 3);
  const flow = ["Receber", "Validar", "Interpretar", "Buscar", "Diversificar", "Explicar"];
  flow.forEach((label, i) => {
    const x = 48 + i * 202;
    rect(s, x, 250, 168, 112, i === 3 ? C.blue : C.paper, 18, C.line);
    textBox(s, String(i + 1), x + 18, 268, 36, 28, { size: 20, bold: true, color: i === 3 ? C.paper : C.blue });
    textBox(s, label, x + 18, 304, 132, 42, { size: 23, bold: true, color: i === 3 ? C.paper : C.ink, align: "center" });
    if (i < flow.length - 1) line(s, x + 168, 306, x + 197, 306, C.blue, 3);
  });
  textBox(s, "Entrada e saída são registradas com identificadores técnicos, sem precisar guardar a conversa inteira.", 140, 448, 1000, 78, {
    size: 27,
    bold: true,
    align: "center",
  });
  badge(s, "FALLBACK EM CADA FRONTEIRA", 432, 560, 416, C.coral);
  addFooter(s, "Cada etapa tem uma responsabilidade específica");
  note(s, "01:05", "Conte uma mensagem ponta a ponta. Destaque validação, busca local, diversidade e explicação.", "agente_conversacional/main.py; agente_conversacional/pipeline.py; agente_conversacional/recomendacao/busca.py");

  // 4
  s = baseSlide(p, "O que é regra e onde o LLM entra", "Responsabilidades", 4, true);
  textBox(s, "Determinístico", 105, 165, 440, 52, { size: 34, bold: true, color: C.warm, align: "center" });
  textBox(s, "• valida o contrato\n• filtra o catálogo\n• calcula o ranking\n• aplica diversidade\n• monta fallback", 145, 240, 360, 250, {
    size: 28,
    color: C.paper,
  });
  rect(s, 626, 166, 2, 385, C.blue);
  textBox(s, "LLM opcional", 720, 165, 440, 52, { size: 34, bold: true, color: C.blue, align: "center" });
  textBox(s, "• converte texto livre em estrutura\n• recebe contexto limitado\n• devolve JSON esperado\n• cai para regras se falhar", 742, 240, 390, 230, {
    size: 28,
    color: C.paper,
  });
  textBox(s, "Decisão central: o LLM interpreta; o código decide.", 255, 565, 770, 54, {
    size: 30,
    bold: true,
    color: C.paper,
    align: "center",
  });
  note(s, "00:50", "Separe claramente as partes previsíveis da parte linguística. Enfatize o limite de autoridade do modelo.", "docs/PIPELINE_AGENTE_PROPOSTA_B.md; agente_conversacional/interpretacao.py");

  // 5
  s = baseSlide(p, "Extração estruturada e contrato JSON", "LLM", 5);
  rect(s, 70, 165, 600, 400, C.dark, 18);
  textBox(s, "{\n  \"generos\": [\"pagode\"],\n  \"mood\": \"animado\",\n  \"energia\": \"alta\",\n  \"limite\": 3\n}", 110, 205, 520, 320, {
    size: 28,
    color: C.paper,
  });
  textBox(s, "Validação antes de usar", 742, 180, 420, 44, { size: 31, bold: true });
  const validations = ["campos conhecidos", "tipos e limites", "normalização de gênero", "fallback seguro"];
  validations.forEach((v, i) => {
    badge(s, String(i + 1), 742, 250 + i * 72, 44, i === 3 ? C.coral : C.blue);
    textBox(s, v, 810, 247 + i * 72, 330, 48, { size: 25, bold: true });
  });
  addFooter(s, "O JSON é uma proposta do modelo; a aplicação valida antes de confiar");
  note(s, "00:45", "Mostre um exemplo de estrutura e explique que dados inválidos não seguem para a busca.", "agente_conversacional/modelos.py; agente_conversacional/interpretacao.py");

  // 6
  s = baseSlide(p, "Similaridade por cosseno e perfil do usuário", "Recomendação", 6);
  const weights = s.charts.add("bar", {
    position: { left: 60, top: 175, width: 610, height: 375 },
    categories: ["Preferência do pedido", "Histórico do perfil"],
    series: [{ name: "Peso ilustrativo", values: [70, 30], fill: C.blue }],
    barOptions: { direction: "bar", grouping: "clustered" },
    hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "0\"%\"" },
  });
  applyPresentationChartFont(weights, { fontFamily: FONT });
  rect(s, 734, 178, 472, 372, C.paper, 20, C.line);
  textBox(s, "cos(θ) = (u · faixa) / (|u| |faixa|)", 770, 222, 400, 65, {
    size: 27,
    bold: true,
    color: C.blue,
    align: "center",
  });
  textBox(s, "O sistema compara vetores normalizados em memória. Não depende de um serviço externo de k-NN.", 785, 320, 370, 128, {
    size: 25,
    color: C.ink,
    align: "center",
  });
  textBox(s, "128.830 registros · 97.534 faixas únicas", 780, 486, 380, 38, { size: 20, bold: true, color: C.muted, align: "center" });
  addFooter(s, "Os pesos exibidos são didáticos; a implementação real usa seus parâmetros configurados");
  note(s, "00:50", "Explique a ideia de proximidade entre vetores, sem transformar a fórmula no centro da fala. O gráfico é didático, não um benchmark.", "agente_conversacional/recomendacao/busca.py; data/analytics/dataset_profile.json");

  // 7
  s = baseSlide(p, "Fallback, auditoria, diversidade e observabilidade", "Confiabilidade", 7);
  const cols = [
    ["Fallback", "regras locais quando integração falha", C.coral],
    ["Auditoria", "IDs, origem e decisões do fluxo", C.blue],
    ["Diversidade", "limites para evitar repetição", C.green],
    ["Observabilidade", "tempo, erro e estágio atingido", C.warm],
  ];
  cols.forEach(([head, body, color], i) => {
    const x = 62 + i * 303;
    rect(s, x, 190, 260, 332, C.paper, 20, C.line);
    rect(s, x, 190, 260, 12, color);
    textBox(s, head, x + 16, 230, 228, 56, {
      size: head === "Observabilidade" ? 23 : 28,
      bold: true,
      align: "center",
    });
    textBox(s, body, x + 24, 310, 212, 116, { size: 23, color: C.muted, align: "center" });
  });
  textBox(s, "Falhar com clareza é parte da arquitetura.", 290, 566, 700, 48, { size: 30, bold: true, color: C.blue, align: "center" });
  addFooter(s, "Controles pensados para operação e investigação de problemas");
  note(s, "00:50", "Use os quatro blocos para explicar como o sistema degrada com segurança e como o grupo investiga falhas.", "docs/PIPELINE_AGENTE_PROPOSTA_B.md; agente_conversacional/observabilidade.py; agente_conversacional/recomendacao/diversidade.py");

  // 8
  s = baseSlide(p, "OAuth, PKCE, tokens e privacidade", "Integração Spotify", 8);
  const auth = ["Usuário autoriza", "PKCE protege o código", "Backend troca por token", "Token fica no servidor"];
  auth.forEach((label, i) => {
    const x = 52 + i * 305;
    rect(s, x, 220, 250, 170, i === 3 ? C.green : C.paper, 18, C.line);
    textBox(s, String(i + 1), x + 20, 242, 40, 36, { size: 23, bold: true, color: i === 3 ? C.paper : C.blue });
    textBox(s, label, x + 26, 292, 198, 70, { size: 24, bold: true, color: i === 3 ? C.paper : C.ink, align: "center" });
    if (i < auth.length - 1) line(s, x + 250, 305, x + 298, 305, C.blue, 4);
  });
  rect(s, 188, 465, 904, 93, C.dark, 16);
  textBox(s, "Sem autorização, a recomendação local continua disponível.", 225, 483, 830, 58, { size: 29, bold: true, color: C.paper, align: "center" });
  addFooter(s, "PKCE reduz o risco de interceptação; segredos não vão para o navegador");
  note(s, "00:40", "Resuma o fluxo OAuth com PKCE e explique que tokens permanecem no backend. Não exiba credenciais.", "agente_conversacional/spotify_auth.py; agente_conversacional/README.md");

  // 9
  s = baseSlide(p, "Notebook: perfil e correlação em dois passos", "Demonstração", 9);
  const heatmap = path.join(repoDir, "images", "correlation_heatmap.png");
  s.images.add({
    blob: await fs.readFile(heatmap),
    contentType: "image/png",
    alt: "Mapa de calor das correlações entre características musicais",
    fit: "contain",
    position: { left: 70, top: 160, width: 690, height: 450 },
  });
  rect(s, 810, 170, 390, 390, C.paper, 20, C.line);
  badge(s, "1", 844, 210, 44, C.blue);
  textBox(s, "Perfil do conjunto", 910, 204, 250, 48, { size: 27, bold: true });
  textBox(s, "128.830 registros\n97.534 faixas únicas\n118 gêneros", 850, 270, 310, 120, { size: 26, color: C.ink, align: "center" });
  badge(s, "2", 844, 420, 44, C.blue);
  textBox(s, "Correlação", 910, 414, 250, 48, { size: 27, bold: true });
  textBox(s, "reexecutar apenas\nas células selecionadas", 850, 470, 310, 64, { size: 23, color: C.muted, align: "center" });
  badge(s, "PLANO B: IMAGEM JÁ GERADA", 780, 590, 425, C.coral);
  note(s, "01:30", "Abra o notebook já executado. Reexecute somente as células de perfil e correlação; se o kernel falhar, explique o mapa já incorporado.", "analise_exploratoria.ipynb; images/correlation_heatmap.png; data/analytics/dataset_profile.json");

  // 10
  s = baseSlide(p, "Testes, limitações e evolução", "Fechamento técnico", 10, true);
  const finalCols = [
    ["Evidências", "testes do pipeline\nvalidação do notebook\nprévia da demo"],
    ["Limitações", "LLM e rede variam\nOAuth exige configuração\navaliação humana pendente"],
    ["Evolução", "métricas de qualidade\nfeedback do usuário\ntestes de carga"],
  ];
  finalCols.forEach(([head, body], i) => {
    const x = 72 + i * 392;
    textBox(s, head, x, 180, 352, 48, { size: 33, bold: true, color: i === 1 ? C.warm : C.paper, align: "center" });
    textBox(s, body, x + 28, 260, 296, 180, { size: 26, color: "#D8D3C8", align: "center" });
  });
  rect(s, 180, 500, 920, 2, C.blue);
  textBox(s, "O objetivo não é esconder limites — é controlá-los e medi-los.", 210, 544, 860, 62, { size: 31, bold: true, color: C.paper, align: "center" });
  textBox(s, "Perguntas?", 490, 630, 300, 36, { size: 24, bold: true, color: C.warm, align: "center" });
  note(s, "00:25", "Feche com o que já é verificável, os limites conhecidos e a agenda de evolução. Abra para perguntas.", "agente_conversacional/test_*.py; scripts/validate_notebook_demo.py; scripts/run_notebook_demo.py; docs/apresentacao/ROTEIRO_TECNICO.md");

  return p;
}

async function renderPreviews(presentation, targetDir) {
  for (let i = 0; i < presentation.slides.items.length; i += 1) {
    const slide = presentation.slides.items[i];
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    const file = path.join(targetDir, `slide-${String(i + 1).padStart(2, "0")}.png`);
    await fs.writeFile(file, new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(file.replace(/\.png$/, ".layout.json"), await layout.text());
  }
}

async function finalizeDeck(presentation, fileName, slideCount, charts, previewDir) {
  const stagingDir = path.join(BUILD, fileName.replace(/\.pptx$/, ""));
  await fs.mkdir(stagingDir, { recursive: true });
  const candidatePath = path.join(stagingDir, "candidate.pptx");
  const finalPath = path.join(
    OUTPUT,
    fileName.includes("Pitch") ? "pitch" : "tecnica",
    fileName,
  );
  await fs.rm(finalPath, { force: true });
  await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
  await finalizePresentation({
    explicitTotalSlideCount: slideCount,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: charts,
    materializeLiteralChartWorkbooks: true,
    workspaceDir: repoDir,
    candidatePath,
    finalPath,
    pythonExecutable: runtimePython,
    integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
    layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
    layoutArgs: [
      "--expected-slide-size-emu", "12192000,6858000",
      "--validate-bullet-geometry",
      "--validate-heading-fit",
    ],
    fontPolicy: { basis: "design", families: [FONT] },
    verifyArtifactToolImport: true,
    receiptPath: path.join(stagingDir, `${fileName}.validation.json`),
  });
  await renderPreviews(presentation, previewDir);
}

const pitch = createPitch();
const technical = await createTechnical();
await finalizeDeck(pitch, "MelodIA_Pitch.pptx", 8, [3, 6], PITCH_PREVIEW);
await finalizeDeck(technical, "MelodIA_Tecnica.pptx", 10, [6], TECH_PREVIEW);

const pdfResult = spawnSync(
  runtimePython,
  [
    path.join(repoDir, "scripts", "apresentacao", "build_pdfs.py"),
    "--pitch-preview", PITCH_PREVIEW,
    "--pitch-pdf", path.join(OUTPUT, "pitch", "MelodIA_Pitch.pdf"),
    "--tecnica-preview", TECH_PREVIEW,
    "--tecnica-pdf", path.join(OUTPUT, "tecnica", "MelodIA_Tecnica.pdf"),
  ],
  { stdio: "inherit" },
);
if (pdfResult.status !== 0) throw new Error("Falha ao gerar os PDFs.");

console.log(`Materiais gerados em ${OUTPUT}`);
for (const entry of await fs.readdir(repoDir)) {
  if (entry.startsWith(".chart-data-")) {
    await fs.rm(path.join(repoDir, entry), { recursive: true, force: true });
  }
}
// O encerramento explícito evita uma falha tardia do runtime gráfico no Windows,
// depois que todos os arquivos já foram fechados e validados.
process.exit(0);
