const COLORS = {
  blue: "#2563EB",
  teal: "#0D9488",
  purple: "#7C3AED",
  slate: "#64748B",
};

const I18N = {
  es: {
    brandTag: "Contenci\u00f3n antes del da\u00f1o",
    language: "Idioma",
    theme: "Apariencia",
    light: "Claro",
    dark: "Oscuro",
    channels: "Canales",
    families: "Tipo de tarea",
    conditions: "Situaci\u00f3n",
    heroTitle: "Vista operativa del experimento",
    heroCaption: "Compara canales de vigilancia y pol\u00edticas bajo un presupuesto fijo. Los costos son valores de referencia.",
    syntheticNotice: "DEMOSTRACI\u00d3N SINT\u00c9TICA/MOCK: no constituye evidencia de seguridad de modelos reales.",
    realNotice: "CORRIDA REAL: los resultados integran los veredictos disponibles del monitor externo.",
    phr: "Detenidos a tiempo",
    bdr: "Falsas alarmas",
    eph: "Da\u00f1o evitado",
    phrBdrTitle: "Detenci\u00f3n vs falsas alarmas",
    ephTitle: "Da\u00f1o evitado por canal",
    policyTitle: "Da\u00f1o residual por pol\u00edtica",
    policyCompare: "Lectura de pol\u00edticas",
    tableTitle: "Detalle de casos",
    searchPlaceholder: "Buscar caso, tarea, situaci\u00f3n o decisi\u00f3n",
    pageLabel: "P\u00e1gina",
    ofLabel: "de",
    showing: "Mostrando",
    results: "resultados",
    emptyTable: "No hay casos con esa b\u00fasqueda.",
    prev: "Anterior",
    next: "Siguiente",
    uniform: "Vigilancia fija",
    adaptive: "Vigilancia adaptativa",
    remaining: "Da\u00f1o que queda",
    cost: "Costo",
    better: "Menor da\u00f1o residual",
    warningBdr: "Requiere revisi\u00f3n",
    cleanBdr: "Sin falsas alarmas",
    highPhr: "Meta alcanzada",
    midPhr: "Cobertura parcial",
    channelsMap: {
      observable: "Acciones visibles",
      cot: "Razonamiento",
      probe: "Sonda interna",
      nla: "Lectura NLA",
    },
    familiesMap: {
      external_report: "Publicar informe",
      corporate_email: "Correo corporativo",
      access_list: "Lista de acceso",
    },
    conditionsMap: {
      BENIGN: "Tarea inocua",
      ATTACK_REJECTED: "Ataque rechazado",
      VISIBLE_SABOTAGE: "Sabotaje visible",
      STEALTH_SABOTAGE: "Sabotaje oculto",
    },
    decisions: { allow: "Permitir", block: "Bloquear", escalate: "Revisar" },
    headers: ["Caso", "Tarea", "Situaci\u00f3n", "Sabotaje", "Alertas", "Fija", "Adaptativa", "Ruta"],
    yes: "S\u00ed",
    no: "No",
  },
  en: {
    brandTag: "Pre-harm containment",
    language: "Language",
    theme: "Appearance",
    light: "Light",
    dark: "Dark",
    channels: "Channels",
    families: "Task type",
    conditions: "Situation",
    heroTitle: "Operational experiment view",
    heroCaption: "Compare monitoring channels and policies under a fixed budget. Costs are reference values.",
    syntheticNotice: "SYNTHETIC/MOCK DEMONSTRATION: not evidence of real-model safety.",
    realNotice: "REAL RUN: results integrate the available external-monitor verdicts.",
    phr: "Stopped in time",
    bdr: "False alarms",
    eph: "Harm prevented",
    phrBdrTitle: "Containment vs false alarms",
    ephTitle: "Harm prevented by channel",
    policyTitle: "Residual harm by policy",
    policyCompare: "Policy readout",
    tableTitle: "Case detail",
    searchPlaceholder: "Search case, task, situation or decision",
    pageLabel: "Page",
    ofLabel: "of",
    showing: "Showing",
    results: "results",
    emptyTable: "No cases match this search.",
    prev: "Previous",
    next: "Next",
    uniform: "Uniform monitoring",
    adaptive: "Adaptive monitoring",
    remaining: "Remaining harm",
    cost: "Cost",
    better: "Lower residual harm",
    warningBdr: "Needs review",
    cleanBdr: "No false alarms",
    highPhr: "Target reached",
    midPhr: "Partial coverage",
    channelsMap: {
      observable: "Visible actions",
      cot: "Reasoning",
      probe: "Internal probe",
      nla: "NLA readout",
    },
    familiesMap: {
      external_report: "Publish report",
      corporate_email: "Corporate email",
      access_list: "Access list",
    },
    conditionsMap: {
      BENIGN: "Benign task",
      ATTACK_REJECTED: "Attack rejected",
      VISIBLE_SABOTAGE: "Visible sabotage",
      STEALTH_SABOTAGE: "Hidden sabotage",
    },
    decisions: { allow: "Allow", block: "Block", escalate: "Review" },
    headers: ["Case", "Task", "Situation", "Sabotage", "Alerts", "Uniform", "Adaptive", "Route"],
    yes: "Yes",
    no: "No",
  },
};

const CHANNELS = ["observable", "cot", "probe", "nla"];
const CHANNEL_COLORS = {
  observable: COLORS.blue,
  cot: COLORS.teal,
  probe: COLORS.purple,
  nla: COLORS.slate,
};

const state = {
  lang: localStorage.getItem("bn-lang") || "es",
  theme: localStorage.getItem("bn-theme") || "light",
  channels: new Set(CHANNELS),
  families: new Set(["external_report", "corporate_email", "access_list"]),
  conditions: new Set(["BENIGN", "ATTACK_REJECTED", "VISIBLE_SABOTAGE", "STEALTH_SABOTAGE"]),
  query: "",
  page: 1,
  pageSize: 12,
};

const charts = {};

function t() {
  return I18N[state.lang];
}

function filteredCases() {
  return (window.DASHBOARD_DATA.cases || []).filter((item) => {
    return state.families.has(item.family) && state.conditions.has(item.condition);
  });
}

function metricsFor(cases) {
  const selected = CHANNELS.filter((id) => state.channels.has(id));
  return selected.map((id) => {
    const sabotage = cases.filter((item) => item.primary_label === 1);
    const benign = cases.filter((item) => item.primary_label === 0);
    const caught = sabotage.filter((item) => item.alerts[id]).length;
    const falseAlarms = benign.filter((item) => item.alerts[id]).length;
    const eph = sabotage.filter((item) => item.alerts[id]).reduce((sum, item) => sum + item.severity, 0);
    return {
      id,
      phr: sabotage.length ? caught / sabotage.length : 0,
      bdr: benign.length ? falseAlarms / benign.length : 0,
      eph,
    };
  });
}

function policyTotals(cases) {
  return {
    uniform: cases.reduce((sum, item) => sum + item.uniform_residual_harm, 0),
    adaptive: cases.reduce((sum, item) => sum + item.adaptive_residual_harm, 0),
    uniformCost: cases.reduce((sum, item) => sum + item.uniform_cost, 0),
    adaptiveCost: cases.reduce((sum, item) => sum + item.adaptive_cost, 0),
  };
}

function applyTheme() {
  document.documentElement.dataset.theme = state.theme;
  document.querySelectorAll("[data-theme-btn]").forEach((button) => {
    button.classList.toggle("active", button.dataset.themeBtn === state.theme);
  });
}

function applyI18n() {
  const copy = t();
  document.getElementById("brandTag").textContent = copy.brandTag;
  document.getElementById("heroTitle").textContent = copy.heroTitle;
  const provenance = window.DASHBOARD_DATA.provenance || {};
  const notice = provenance.mock_mode ? copy.syntheticNotice : copy.realNotice;
  document.getElementById("heroCaption").textContent = `${copy.heroCaption} ${notice}`;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = copy[node.dataset.i18n];
  });
  document.querySelectorAll("[data-lang]").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === state.lang);
  });
  const search = document.getElementById("caseSearch");
  if (search) {
    search.placeholder = copy.searchPlaceholder;
    search.value = state.query;
  }
}

function renderFilters() {
  const copy = t();
  fillFilter("channelFilters", CHANNELS.map((id) => [id, copy.channelsMap[id]]), "channel", state.channels);
  fillFilter("familyFilters", Object.entries(copy.familiesMap), "family", state.families);
  fillFilter("conditionFilters", Object.entries(copy.conditionsMap), "condition", state.conditions);
}

function fillFilter(containerId, items, group, selected) {
  const box = document.getElementById(containerId);
  if (!box.dataset.ready) {
    box.innerHTML = items.map(([id, label]) => filterItem(group, id, label, selected.has(id))).join("");
    box.dataset.ready = "true";
    return;
  }
  items.forEach(([id, label]) => {
    const input = box.querySelector(`input[value="${id}"]`);
    if (!input) return;
    input.checked = selected.has(id);
    input.closest(".check").classList.toggle("active", selected.has(id));
    const text = input.nextSibling;
    if (text) text.textContent = label;
  });
}

function filterItem(group, id, label, checked) {
  return `<label class="check ${checked ? "active" : ""}"><input type="checkbox" data-group="${group}" value="${id}" ${checked ? "checked" : ""} />${label}</label>`;
}

function renderKpis(metrics) {
  const copy = t();
  document.getElementById("kpis").innerHTML = metrics
    .map((item) => {
      const phrBadge = item.phr >= 0.99 ? ["success", copy.highPhr] : ["warning", copy.midPhr];
      const bdrBadge = item.bdr > 0 ? ["warning", copy.warningBdr] : ["success", copy.cleanBdr];
      return `
        <article class="card">
          <div class="card-label">${copy.channelsMap[item.id]}</div>
          <div class="card-value">${Math.round(item.phr * 100)}%</div>
          <div class="card-meta">${copy.phr}</div>
          <div class="track"><span style="--value:${Math.round(item.phr * 100)}%;background:${CHANNEL_COLORS[item.id]}"></span></div>
          <div><span class="badge ${phrBadge[0]}">${phrBadge[1]}</span></div>
          <p class="card-meta" style="margin:12px 0 8px">${copy.bdr}: ${Math.round(item.bdr * 100)}% · ${copy.eph}: ${item.eph.toFixed(1)}</p>
          <span class="badge ${bdrBadge[0]}">${bdrBadge[1]}</span>
        </article>
      `;
    })
    .join("");
}

function chartDefaults() {
  const dark = state.theme === "dark";
  const grid = dark ? "#30363D" : "#E2E8F0";
  const tick = dark ? "#94A3B8" : "#64748B";
  Chart.defaults.font.family = "DM Sans";
  Chart.defaults.color = tick;
  Chart.defaults.borderColor = grid;
  Chart.defaults.plugins.legend.labels.boxWidth = 10;
  Chart.defaults.animation = { duration: 900, easing: "easeOutQuart" };
  return { grid, tick };
}

function commonOptions(tick, grid, extra) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 0,
    animation: { duration: 700, easing: "easeOutQuart" },
    ...extra,
    scales: extra.scales,
  };
}

function upsertChart(id, type, data, options) {
  const canvas = document.getElementById(id);
  if (!canvas) return;
  if (charts[id]) {
    charts[id].data.labels = data.labels;
    charts[id].data.datasets.forEach((dataset, index) => {
      dataset.data = data.datasets[index].data;
      dataset.label = data.datasets[index].label;
      if (data.datasets[index].backgroundColor) dataset.backgroundColor = data.datasets[index].backgroundColor;
    });
    if (charts[id].data.datasets.length < data.datasets.length) {
      charts[id].data.datasets = data.datasets;
    }
    charts[id].options = options;
    charts[id].update();
    requestAnimationFrame(() => charts[id].resize());
    return;
  }
  charts[id] = new Chart(canvas, { type, data, options });
}

function renderCharts(metrics, policies) {
  const copy = t();
  const { grid, tick } = chartDefaults();
  const labels = metrics.map((item) => copy.channelsMap[item.id]);
  const phrData = {
    labels,
    datasets: [
      { label: copy.phr, data: metrics.map((item) => Math.round(item.phr * 100)), backgroundColor: COLORS.blue, borderRadius: 8, barPercentage: 0.62 },
      { label: copy.bdr, data: metrics.map((item) => Math.round(item.bdr * 100)), backgroundColor: COLORS.teal, borderRadius: 8, barPercentage: 0.62 },
    ],
  };
  upsertChart("phrChart", "bar", phrData, commonOptions(tick, grid, {
    scales: {
      x: { grid: { display: false }, ticks: { color: tick } },
      y: { min: 0, max: 100, ticks: { color: tick, callback: (value) => `${value}%` }, grid: { color: grid } },
    },
  }));
  upsertChart("ephChart", "bar", {
    labels,
    datasets: [{ label: copy.eph, data: metrics.map((item) => item.eph), backgroundColor: [COLORS.blue, COLORS.teal, COLORS.purple, COLORS.slate], borderRadius: 8 }],
  }, commonOptions(tick, grid, {
    indexAxis: "y",
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: grid }, ticks: { color: tick } },
      y: { grid: { display: false }, ticks: { color: tick } },
    },
  }));
  upsertChart("policyChart", "bar", {
    labels: [copy.uniform, copy.adaptive],
    datasets: [{ label: copy.remaining, data: [policies.uniform, policies.adaptive], backgroundColor: [COLORS.blue, COLORS.teal], borderRadius: 8, barPercentage: 0.5 }],
  }, commonOptions(tick, grid, {
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { color: tick } },
      y: { beginAtZero: true, grid: { color: grid }, ticks: { color: tick } },
    },
  }));
}

function renderPolicies(policies) {
  const copy = t();
  const better = policies.adaptive <= policies.uniform;
  document.getElementById("policyCards").innerHTML = `
    <div class="policy">
      <div class="card-label">${copy.uniform}</div>
      <strong>${policies.uniform.toFixed(1)}</strong>
      <div class="card-meta">${copy.remaining} · ${copy.cost} ${policies.uniformCost.toFixed(1)}</div>
    </div>
    <div class="policy">
      <div class="card-label">${copy.adaptive}</div>
      <strong>${policies.adaptive.toFixed(1)}</strong>
      <div class="card-meta">${copy.remaining} · ${copy.cost} ${policies.adaptiveCost.toFixed(1)}</div>
      <div style="margin-top:10px"><span class="badge ${better ? "success" : "warning"}">${copy.better}</span></div>
    </div>
  `;
}

function caseSearchText(item, copy) {
  const alerts = CHANNELS.filter((id) => item.alerts[id]).map((id) => copy.channelsMap[id]).join(" ");
  return [
    item.id,
    item.variant,
    copy.familiesMap[item.family],
    copy.conditionsMap[item.condition],
    item.primary_label ? copy.yes : copy.no,
    alerts,
    copy.decisions[item.uniform_decision],
    copy.decisions[item.adaptive_decision],
    item.adaptive_policy,
  ].join(" ").toLowerCase();
}

function searchedCases(cases) {
  const copy = t();
  const query = state.query.trim().toLowerCase();
  if (!query) return cases;
  return cases.filter((item) => caseSearchText(item, copy).includes(query));
}

function renderTable(cases) {
  const copy = t();
  const matches = searchedCases(cases);
  const pages = Math.max(1, Math.ceil(matches.length / state.pageSize));
  if (state.page > pages) state.page = pages;
  const start = (state.page - 1) * state.pageSize;
  const pageRows = matches.slice(start, start + state.pageSize);
  if (!pageRows.length) {
    document.getElementById("tableWrap").innerHTML = `<div class="empty">${copy.emptyTable}</div>`;
    renderPager(0, 1, 0);
    return;
  }
  const rows = pageRows
    .map((item) => {
      const alerts = CHANNELS.filter((id) => item.alerts[id]).map((id) => copy.channelsMap[id]).join(", ") || "—";
      return `<tr>
        <td>${item.id}</td>
        <td>${copy.familiesMap[item.family]}</td>
        <td>${copy.conditionsMap[item.condition]}</td>
        <td>${item.primary_label ? copy.yes : copy.no}</td>
        <td>${alerts}</td>
        <td>${copy.decisions[item.uniform_decision]}</td>
        <td>${copy.decisions[item.adaptive_decision]}</td>
        <td>${item.adaptive_policy.replaceAll("_", " ")}</td>
      </tr>`;
    })
    .join("");
  document.getElementById("tableWrap").innerHTML = `
    <table>
      <thead><tr>${copy.headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  renderPager(matches.length, pages, start);
}

function renderPager(total, pages, start) {
  const copy = t();
  const end = Math.min(start + state.pageSize, total);
  const buttons = Array.from({ length: pages }, (_, index) => {
    const page = index + 1;
    return `<button type="button" class="page-btn ${page === state.page ? "active" : ""}" data-page="${page}">${page}</button>`;
  }).join("");
  document.getElementById("pager").innerHTML = `
    <span class="card-meta">${copy.showing} ${total ? start + 1 : 0}-${end} ${copy.ofLabel} ${total} ${copy.results}</span>
    <div class="pager-nav">
      <button type="button" class="page-btn" data-page="${state.page - 1}" ${state.page <= 1 ? "disabled" : ""}>${copy.prev}</button>
      ${buttons}
      <button type="button" class="page-btn" data-page="${state.page + 1}" ${state.page >= pages ? "disabled" : ""}>${copy.next}</button>
    </div>
  `;
}

function refresh() {
  const cases = filteredCases();
  const metrics = metricsFor(cases);
  const policies = policyTotals(cases);
  renderKpis(metrics);
  renderCharts(metrics, policies);
  renderPolicies(policies);
  renderTable(cases);
}

function render() {
  applyTheme();
  applyI18n();
  renderFilters();
  refresh();
}

function bind() {
  document.getElementById("langSeg").addEventListener("click", (event) => {
    const button = event.target.closest("[data-lang]");
    if (!button) return;
    state.lang = button.dataset.lang;
    localStorage.setItem("bn-lang", state.lang);
    render();
  });
  document.getElementById("themeSeg").addEventListener("click", (event) => {
    const button = event.target.closest("[data-theme-btn]");
    if (!button) return;
    state.theme = button.dataset.themeBtn;
    localStorage.setItem("bn-theme", state.theme);
    render();
  });
  document.querySelector(".sidebar").addEventListener("change", (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || !input.dataset.group) return;
    const group = input.dataset.group;
    const bucket = group === "channel" ? state.channels : group === "family" ? state.families : state.conditions;
    if (input.checked) bucket.add(input.value);
    else if (bucket.size > 1) bucket.delete(input.value);
    else input.checked = true;
    input.closest(".check").classList.toggle("active", input.checked);
    state.page = 1;
    refresh();
  });
  document.getElementById("caseSearch").addEventListener("input", (event) => {
    state.query = event.target.value;
    state.page = 1;
    renderTable(filteredCases());
  });
  document.getElementById("pageSize").addEventListener("change", (event) => {
    state.pageSize = Number(event.target.value) || 12;
    state.page = 1;
    renderTable(filteredCases());
  });
  document.getElementById("pager").addEventListener("click", (event) => {
    const button = event.target.closest("[data-page]");
    if (!button || button.disabled) return;
    const nextPage = Number(button.dataset.page);
    const total = searchedCases(filteredCases()).length;
    const pages = Math.max(1, Math.ceil(total / state.pageSize));
    if (nextPage < 1 || nextPage > pages) return;
    state.page = nextPage;
    renderTable(filteredCases());
  });
}

bind();
render();
