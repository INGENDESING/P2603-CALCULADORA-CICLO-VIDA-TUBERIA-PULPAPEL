/* =========================================================================
   P2603 SW-K60 — Frontend: Resumen Ejecutivo + Calculadora
   ========================================================================= */
const API = '/api';

const schedulesPorMaterial = {
    'SS304': ['10S', '20S', '30S', '40S'],
    'SS304L': ['10S', '20S', '30S', '40S'],
    'A53 GRB': ['10', '20', '30', '40'],
};

const escenariosNombres = {
    'Alcalino': 'Alcalino',
    'Acido': 'Ácido severo',
    'Neutro': 'Neutro-oxidante',
    'Recuperacion': 'Recuperación',
};

/* ------------------------------------------------------------------ THEME */
const THEME = {
    accent: '#00e676',
    data: '#00d4ff',
    data2: '#7c4dff',
    warn: '#ffb74d',
    crit: '#ff5370',
    series: ['#00e676', '#00d4ff', '#7c4dff', '#ffb74d'],
    grid: '#223354',
    text: '#e8eef8',
    dim: '#93a4c0',
    heatscale: [[0, '#0d1526'], [0.5, '#00d4ff'], [1, '#00e676']],
    layout(extra = {}) {
        return Object.assign({
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Titillium Web, Segoe UI, sans-serif', color: this.text, size: 12 },
            xaxis: { gridcolor: this.grid, zerolinecolor: this.grid },
            yaxis: { gridcolor: this.grid, zerolinecolor: this.grid },
            legend: { font: { color: this.dim } },
            separators: ',.',
            margin: { t: 30, b: 48, l: 56, r: 24 },
        }, extra);
    },
};

const PLOT_CONFIG = { responsive: true, displaylogo: false };

/* Formato es-CO: coma decimal, punto de miles */
function fmt(n, d = 1) {
    if (n === null || n === undefined || Number.isNaN(n)) return '—';
    return n.toLocaleString('es-CO', { minimumFractionDigits: d, maximumFractionDigits: d });
}

/* Umbral de criticidad de vida útil (años) */
function vidaClass(v) {
    if (v < 10) return 'vida-crit';
    if (v < 25) return 'vida-warn';
    return 'vida-ok';
}

function $(id) { return document.getElementById(id); }

/* ------------------------------------------------------------------ toast */
function toast(msg, tipo = 'error') {
    const div = document.createElement('div');
    div.className = 'toast' + (tipo === 'info' ? ' info' : '');
    div.textContent = msg;
    $('toast-container').appendChild(div);
    setTimeout(() => div.remove(), 6000);
}

/* Convierte la respuesta de error de FastAPI en mensaje legible */
async function apiError(res) {
    let msg = `Error ${res.status}`;
    try {
        const err = await res.json();
        if (typeof err.detail === 'string') {
            msg = err.detail;
        } else if (Array.isArray(err.detail)) {
            msg = err.detail.map(e => `${(e.loc || []).slice(1).join('.')}: ${e.msg}`).join(' · ');
        }
    } catch (_) { /* cuerpo no JSON */ }
    return new Error(msg);
}

async function post(endpoint, body) {
    const res = await fetch(API + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw await apiError(res);
    return res.json();
}

async function get(endpoint) {
    const res = await fetch(API + endpoint);
    if (!res.ok) throw await apiError(res);
    return res.json();
}

/* Deshabilita el botón durante la operación (evita requests duplicados) */
async function withLoading(btn, fn) {
    if (btn.disabled) return;
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>' + original;
    try {
        await fn();
    } catch (e) {
        toast(e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = original;
    }
}

/* ------------------------------------------------------- tabla compartida */
function buildTable({ headers, rows, cellClass = null }) {
    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const trh = document.createElement('tr');
    headers.forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        trh.appendChild(th);
    });
    thead.appendChild(trh);
    const tbody = document.createElement('tbody');
    rows.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach((cell, idx) => {
            if (cell === null) return; // celda absorbida por rowspan previo
            const td = document.createElement('td');
            if (typeof cell === 'object') {
                td.textContent = cell.text;
                if (cell.rowSpan) td.rowSpan = cell.rowSpan;
                if (cell.bold) td.style.fontWeight = 'bold';
            } else {
                td.textContent = cell;
            }
            if (cellClass) {
                const cls = cellClass(cell, idx);
                if (cls) td.className = cls;
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(thead);
    table.appendChild(tbody);
    return table;
}

/* Clase condicional para celdas numéricas de vida útil (ignora texto) */
function vidaCellClass(cell, idx) {
    const raw = typeof cell === 'object' ? cell.text : cell;
    const num = parseFloat(String(raw).replace(/\./g, '').replace(',', '.'));
    if (idx === 0 || Number.isNaN(num)) return null;
    return vidaClass(num);
}

/* ==========================================================================
   PESTAÑAS
   ========================================================================== */
function initTabs() {
    document.querySelectorAll('.tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(b => {
                b.classList.toggle('active', b === btn);
                b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
            });
            document.querySelectorAll('.tab-panel').forEach(p => {
                p.classList.toggle('active', p.id === 'tab-' + btn.dataset.tab);
            });
            // Plotly colapsa en contenedores display:none; redimensionar al mostrar
            document.querySelectorAll('#tab-' + btn.dataset.tab + ' .plot').forEach(div => {
                if (div.data) Plotly.Plots.resize(div);
            });
            history.replaceState(null, '', '#' + btn.dataset.tab);
        });
    });
    // Enlace directo: /static/index.html#calculadora abre esa pestaña
    const hash = location.hash.replace('#', '');
    if (hash && hash !== 'resumen') {
        const btn = document.querySelector(`.tab[data-tab="${hash}"]`);
        if (btn) btn.click();
    }
}

/* ==========================================================================
   RESUMEN EJECUTIVO (dashboard)
   ========================================================================== */
async function loadDashboard() {
    let d;
    try {
        d = await get('/dashboard');
    } catch (e) {
        $('dash-descripcion').textContent = 'No fue posible cargar el dashboard: ' + e.message;
        return;
    }

    const k = d.caso_base.kpis;
    $('dash-descripcion').textContent = d.caso_base.descripcion + ' · Referencia ' + d.caso_base.nps_ref + ' · FS = ' + fmt(d.caso_base.parametros.fs, 1);

    // --- KPI cards
    $('dkpi-ss304').textContent = fmt(k.vida_ss304_40s, 1);
    $('dkpi-ss304l').textContent = fmt(k.vida_ss304l_40s, 1);
    $('dkpi-a53').textContent = fmt(k.vida_a53_40, 1);
    $('dkpi-tdisp').textContent = fmt(k.t_disp_ss304_40s, 2);
    $('dkpi-wtotal').textContent = fmt(k.W_total, 4);
    $('dkpi-wdesc').textContent = 'W_quim ' + fmt(k.W_quim, 4) + ' + W_ero ' + fmt(k.W_ero, 4) + ' mm/año';
    $('kpic-ss304').classList.add(vidaClass(k.vida_ss304_40s).replace('vida-', ''));
    $('kpic-ss304l').classList.add(vidaClass(k.vida_ss304l_40s).replace('vida-', ''));
    $('kpic-a53').classList.add(vidaClass(k.vida_a53_40).replace('vida-', ''));

    // --- Gauge vida útil SS304 40S
    Plotly.newPlot('dash-gauge', [{
        type: 'indicator',
        mode: 'gauge+number',
        value: k.vida_ss304_40s,
        number: { suffix: ' años', font: { family: 'JetBrains Mono, monospace', color: THEME.text, size: 36 }, valueformat: ',.1f' },
        gauge: {
            axis: { range: [0, 100], tickcolor: THEME.dim, tickfont: { color: THEME.dim } },
            bar: { color: THEME.accent, thickness: 0.28 },
            bgcolor: 'rgba(0,0,0,0)',
            borderwidth: 0,
            steps: [
                { range: [0, 10], color: 'rgba(255,83,112,0.25)' },
                { range: [10, 25], color: 'rgba(255,183,77,0.20)' },
                { range: [25, 100], color: 'rgba(0,230,118,0.10)' },
            ],
        },
    }], THEME.layout({ margin: { t: 30, b: 10, l: 30, r: 30 } }), PLOT_CONFIG);

    // --- Heatmap material × escenario
    const escLabels = d.heatmap.escenarios.map(e => escenariosNombres[e] || e);
    Plotly.newPlot('dash-heatmap', [{
        type: 'heatmap',
        z: d.heatmap.valores,
        x: escLabels,
        y: d.heatmap.materiales,
        colorscale: THEME.heatscale,
        texttemplate: '%{z:,.0f} a',
        textfont: { family: 'JetBrains Mono, monospace' },
        customdata: d.heatmap.valores.map(() => d.heatmap.condiciones.map(c => [c.T, c.v, c.Cs])),
        hovertemplate: '%{y} · %{x}<br>Vida útil: %{z:,.1f} años<br>T = %{customdata[0]} °C · v = %{customdata[1]} m/s · Cs = %{customdata[2]} %<extra></extra>',
        colorbar: { tickfont: { color: THEME.dim }, title: { text: 'años', font: { color: THEME.dim } } },
    }], THEME.layout({ margin: { t: 20, b: 60, l: 80, r: 20 } }), PLOT_CONFIG);

    // --- Comparativa de materiales (condición crítica)
    const colores = { ss304_s10: 'rgba(0,230,118,0.45)', ss304L_s10: 'rgba(0,212,255,0.45)', ss304_s40: THEME.accent, ss304L_s40: THEME.data, a53_s40: THEME.crit };
    Plotly.newPlot('dash-comparativa', d.comparativa.series.map(s => ({
        x: d.comparativa.nps,
        y: s.valores,
        name: s.nombre,
        type: 'bar',
        marker: { color: colores[s.id] || THEME.data2 },
    })), THEME.layout({
        barmode: 'group',
        xaxis: { title: { text: 'Diámetro nominal NPS' }, gridcolor: THEME.grid },
        yaxis: { title: { text: 'Vida útil (años)' }, gridcolor: THEME.grid },
        legend: { orientation: 'h', y: 1.12, font: { color: THEME.dim } },
        margin: { t: 40, b: 56, l: 56, r: 20 },
    }), PLOT_CONFIG);

    // --- Descomposición W_quim vs W_ero
    Plotly.newPlot('dash-descomp', [
        { type: 'bar', orientation: 'h', y: d.descomposicion.materiales, x: d.descomposicion.W_quim, name: 'W_quim (corrosión)', marker: { color: THEME.data } },
        { type: 'bar', orientation: 'h', y: d.descomposicion.materiales, x: d.descomposicion.W_ero, name: 'W_ero (erosión)', marker: { color: THEME.accent } },
    ], THEME.layout({
        barmode: 'stack',
        xaxis: { title: { text: 'Tasa de desgaste (mm/año)' }, gridcolor: THEME.grid },
        legend: { orientation: 'h', y: 1.15, font: { color: THEME.dim } },
        margin: { t: 40, b: 56, l: 80, r: 20 },
    }), PLOT_CONFIG);

    // --- Sensibilidad al FS
    Plotly.newPlot('dash-sens', [{
        x: d.sensibilidad_fs.fs,
        y: d.sensibilidad_fs.vida,
        type: 'scatter',
        mode: 'lines+markers',
        fill: 'tozeroy',
        fillcolor: 'rgba(0,212,255,0.08)',
        line: { color: THEME.data, width: 3 },
        marker: { size: 8, color: THEME.data },
        hovertemplate: 'FS = %{x:,.1f}<br>Vida útil: %{y:,.1f} años<extra></extra>',
    }], THEME.layout({
        xaxis: { title: { text: 'Factor de seguridad FS' }, gridcolor: THEME.grid },
        yaxis: { title: { text: 'Vida útil (años)' }, gridcolor: THEME.grid },
    }), PLOT_CONFIG);

    // --- Tabla condición crítica
    const cc = d.condicion_critica;
    $('dash-tabla-cc').innerHTML = '';
    $('dash-tabla-cc').appendChild(buildTable({
        headers: ['NPS', 'SS304 Sch 10S', 'SS304L Sch 10S', 'SS304 Sch 40S', 'SS304L Sch 40S', 'A53 Gr B Sch 40'],
        rows: cc.filas.map(r => [r.nps, r.ss304_s10, r.ss304L_s10, r.ss304_s40, r.ss304L_s40, r.a53_s40]),
        cellClass: vidaCellClass,
    }));

    // --- Advertencias
    const advertencias = [...(d.advertencias || []), ...(cc.advertencias || [])];
    const list = $('dash-warnings-list');
    list.innerHTML = '';
    advertencias.forEach(msg => {
        const li = document.createElement('li');
        li.textContent = msg;
        list.appendChild(li);
    });
    $('dash-warnings').style.display = advertencias.length ? 'block' : 'none';
}

/* ==========================================================================
   CALCULADORA
   ========================================================================== */
function actualizarSchedules() {
    const material = $('material').value;
    const select = $('schedule');
    select.innerHTML = '';
    schedulesPorMaterial[material].forEach((sch, idx) => {
        const opt = document.createElement('option');
        opt.value = sch;
        opt.textContent = sch;
        if (idx === 0) opt.selected = true;
        select.appendChild(opt);
    });
}

function actualizarPulpaRefinada() {
    const refinada = $('pulpa-refinada').checked;
    $('beta').value = refinada ? '0.25' : '0.0';
    $('k0_override').value = refinada ? '0.0035' : '';
}

function leerInputs() {
    const T = $('T').value.trim();
    const k0 = $('k0_override').value.trim();
    return {
        material: $('material').value,
        nps: $('nps').value,
        schedule: $('schedule').value,
        escenario: $('escenario').value,
        Cs: parseFloat($('Cs').value),
        v: parseFloat($('v').value),
        T: T === '' ? null : parseFloat(T),
        beta: parseFloat($('beta').value),
        k0_override: k0 === '' ? null : parseFloat(k0),
        fs: parseFloat($('fs').value),
    };
}

function ocultar(...ids) { ids.forEach(id => { $(id).style.display = 'none'; }); }

function setKPIs(data) {
    $('kpi-section').style.display = 'grid';
    $('kpi-vida').textContent = fmt(data.vida_util, 1) + ' años';
    $('kpi-vida').parentElement.classList.remove('ok', 'warn', 'crit');
    $('kpi-vida').parentElement.classList.add(vidaClass(data.vida_util).replace('vida-', ''));
    $('kpi-tdisp').textContent = fmt(data.t_disp, 2) + ' mm';
    $('kpi-wtotal').textContent = fmt(data.W_total, 3) + ' mm/año';
    $('kpi-wquim').textContent = fmt(data.W_quim, 3) + ' mm/año';
    $('kpi-wero').textContent = fmt(data.W_ero, 3) + ' mm/año';
    $('kpi-s').textContent = fmt(data.S, 1) + ' MPa';
    renderAdvertencias(data.advertencias || []);
}

function renderAdvertencias(advertencias) {
    const section = $('warnings-section');
    const list = $('warnings-list');
    list.innerHTML = '';
    if (!advertencias || advertencias.length === 0) {
        section.style.display = 'none';
        return;
    }
    advertencias.forEach(msg => {
        const li = document.createElement('li');
        li.textContent = msg;
        list.appendChild(li);
    });
    section.style.display = 'block';
}

async function calcularVidaUtil() {
    const data = await post('/calcular/vida-util', leerInputs());
    setKPIs(data);
    ocultar('result-section', 'export-actions', 'panel-barras', 'panel-sens');
}

function renderTablaParametrica(data) {
    const rows = [];
    for (const esc of data.escenarios) {
        data.diametros.forEach((nps, i) => {
            const row = [];
            if (i === 0) {
                row.push({ text: escenariosNombres[esc] || esc, rowSpan: data.diametros.length, bold: true });
            } else {
                row.push(null);
            }
            row.push(nps.replace('NPS ', ''));
            for (const sch of data.schedules) {
                const val = data.valores[esc][nps][sch];
                row.push(val < 1 && val > 0 ? fmt(val, 1) : String(Math.floor(val)));
            }
            rows.push(row);
        });
    }
    const container = $('result-table');
    container.innerHTML = '';
    container.appendChild(buildTable({
        headers: ['Escenario', 'NPS', ...data.schedules.map(s => 'Sch ' + s)],
        rows,
        cellClass: (cell, idx) => (idx >= 2 ? vidaCellClass(cell, idx) : null),
    }));
    $('result-section').style.display = 'block';
    $('result-title').textContent = `Tabla paramétrica — ${data.material}, Cs = ${fmt(data.Cs, 1)} %, v = ${fmt(data.v, 1)} m/s, FS = ${fmt(data.fs, 1)}`;
}

async function calcularTabla() {
    const req = leerInputs();
    const { nps, schedule, ...body } = req;
    const data = await post('/calcular/tabla', body);
    renderTablaParametrica(data);
    ocultar('kpi-section', 'panel-sens');
    $('export-actions').style.display = 'flex';
    graficarBarras(data);
    renderAdvertencias(data.advertencias || []);
}

function graficarBarras(data) {
    $('panel-barras').style.display = 'block';
    const traces = data.schedules.map((sch, idx) => ({
        x: data.diametros.map(n => n.replace('NPS ', '')),
        y: data.diametros.map(n => data.valores[data.escenarios[0]][n][sch]),
        name: `Sch ${sch}`,
        type: 'bar',
        marker: { color: THEME.series[idx % THEME.series.length] },
    }));
    Plotly.newPlot('plot-barras', traces, THEME.layout({
        title: { text: `Vida útil por diámetro — ${escenariosNombres[data.escenarios[0]] || data.escenarios[0]}`, font: { size: 14, color: THEME.dim } },
        yaxis: { title: { text: 'Vida útil (años)' }, gridcolor: THEME.grid },
        barmode: 'group',
        margin: { t: 50, b: 50, l: 56, r: 24 },
    }), PLOT_CONFIG);
}

async function calcularSensibilidad() {
    const data = await post('/calcular/sensibilidad-fs', leerInputs());
    const x = Object.keys(data.resultados).map(parseFloat);
    const y = Object.values(data.resultados);
    $('panel-sens').style.display = 'block';
    Plotly.newPlot('plot-sens', [{
        x, y,
        type: 'scatter',
        mode: 'lines+markers',
        fill: 'tozeroy',
        fillcolor: 'rgba(0,212,255,0.08)',
        line: { color: THEME.data, width: 3 },
        marker: { size: 10, color: THEME.data },
        hovertemplate: 'FS = %{x:,.1f}<br>Vida útil: %{y:,.1f} años<extra></extra>',
    }], THEME.layout({
        title: { text: `Sensibilidad al FS — ${data.material} ${data.nps} Sch ${data.schedule}`, font: { size: 14, color: THEME.dim } },
        xaxis: { title: { text: 'Factor de seguridad FS' }, gridcolor: THEME.grid },
        yaxis: { title: { text: 'Vida útil (años)' }, gridcolor: THEME.grid },
        margin: { t: 50, b: 50, l: 56, r: 24 },
    }), PLOT_CONFIG);
    ocultar('kpi-section', 'result-section', 'export-actions', 'panel-barras');
    renderAdvertencias(data.advertencias || []);
}

async function calcularCondicionCritica() {
    const data = await get('/calcular/condicion-critica');
    const container = $('result-table');
    container.innerHTML = '';
    container.appendChild(buildTable({
        headers: ['NPS', 'SS304 Sch 10S', 'SS304L Sch 10S', 'SS304 Sch 40S', 'SS304L Sch 40S', 'A53 Gr B Sch 40'],
        rows: data.filas.map(r => [r.nps, r.ss304_s10, r.ss304L_s10, r.ss304_s40, r.ss304L_s40, r.a53_s40]),
        cellClass: vidaCellClass,
    }));
    $('result-section').style.display = 'block';
    $('result-title').textContent = `Condición crítica 60 °C — Cs = ${fmt(data.parametros.Cs, 0)} %, v = ${fmt(data.parametros.v, 1)} m/s, β = ${fmt(data.parametros.beta, 2)}, FS = ${fmt(data.parametros.fs, 1)}`;
    ocultar('kpi-section', 'export-actions', 'panel-barras', 'panel-sens');
    renderAdvertencias(data.advertencias || []);
}

async function exportar(formato) {
    const req = leerInputs();
    const { nps, schedule, ...body } = req;
    const endpoint = formato === 'csv' ? '/export/csv' : '/export/excel';
    const res = await fetch(API + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw await apiError(res);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const disp = res.headers.get('content-disposition');
    const match = disp && disp.match(/filename="?([^"]+)"?/);
    a.download = match ? match[1] : `vida_util.${formato}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}

/* ==========================================================================
   INIT
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadDashboard();
    actualizarSchedules();
    actualizarPulpaRefinada();
    $('material').addEventListener('change', actualizarSchedules);
    $('pulpa-refinada').addEventListener('change', actualizarPulpaRefinada);
    $('btn-vida').addEventListener('click', e => withLoading(e.currentTarget, calcularVidaUtil));
    $('btn-tabla').addEventListener('click', e => withLoading(e.currentTarget, calcularTabla));
    $('btn-sens').addEventListener('click', e => withLoading(e.currentTarget, calcularSensibilidad));
    $('btn-critica').addEventListener('click', e => withLoading(e.currentTarget, calcularCondicionCritica));
    $('btn-csv').addEventListener('click', e => withLoading(e.currentTarget, () => exportar('csv')));
    $('btn-excel').addEventListener('click', e => withLoading(e.currentTarget, () => exportar('excel')));
});
