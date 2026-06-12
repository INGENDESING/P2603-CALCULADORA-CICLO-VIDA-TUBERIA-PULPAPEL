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

function $(id) { return document.getElementById(id); }

function mostrarError(msg) {
    const div = document.createElement('div');
    div.className = 'error';
    div.textContent = msg;
    const main = document.querySelector('main');
    main.insertBefore(div, main.children[1]);
    setTimeout(() => div.remove(), 5000);
}

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

async function post(endpoint, body) {
    const res = await fetch(API + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error en la solicitud');
    }
    return res.json();
}

async function get(endpoint) {
    const res = await fetch(API + endpoint);
    if (!res.ok) throw new Error('Error en la solicitud');
    return res.json();
}

function setKPIs(data) {
    $('kpi-section').style.display = 'grid';
    $('kpi-vida').textContent = data.vida_util.toFixed(1) + ' años';
    $('kpi-tdisp').textContent = data.t_disp.toFixed(2) + ' mm';
    $('kpi-wtotal').textContent = data.W_total.toFixed(3) + ' mm/a';
    $('kpi-wquim').textContent = data.W_quim.toFixed(3) + ' mm/a';
    $('kpi-wero').textContent = data.W_ero.toFixed(3) + ' mm/a';
    $('kpi-s').textContent = data.S.toFixed(1) + ' MPa';
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
    try {
        const data = await post('/calcular/vida-util', leerInputs());
        setKPIs(data);
        $('result-section').style.display = 'none';
        $('export-actions').style.display = 'none';
        $('plot-barras').innerHTML = '';
        $('plot-sens').innerHTML = '';
    } catch (e) {
        mostrarError(e.message);
    }
}

function renderTabla(data) {
    const container = $('result-table');
    container.innerHTML = '';
    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    const schedules = data.schedules;
    const header = document.createElement('tr');
    header.innerHTML = '<th>Escenario</th><th>NPS</th>' + schedules.map(s => `<th>Sch ${s}</th>`).join('');
    thead.appendChild(header);

    for (const esc of data.escenarios) {
        for (let i = 0; i < data.diametros.length; i++) {
            const nps = data.diametros[i];
            const tr = document.createElement('tr');
            if (i === 0) {
                const tdEsc = document.createElement('td');
                tdEsc.textContent = escenariosNombres[esc] || esc;
                tdEsc.style.fontWeight = 'bold';
                tdEsc.rowSpan = data.diametros.length;
                tr.appendChild(tdEsc);
            }
            const tdNps = document.createElement('td');
            tdNps.textContent = nps.replace('NPS ', '');
            tr.appendChild(tdNps);
            for (const sch of schedules) {
                const td = document.createElement('td');
                const val = data.valores[esc][nps][sch];
                td.textContent = val < 1 && val > 0 ? val.toFixed(1) : Math.floor(val);
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }
    }

    table.appendChild(thead);
    table.appendChild(tbody);
    container.appendChild(table);
    $('result-section').style.display = 'block';
    $('result-title').textContent = `Tabla paramétrica — ${data.material}, Cs=${data.Cs}%, v=${data.v} m/s, FS=${data.fs}`;
}

async function calcularTabla() {
    try {
        const req = leerInputs();
        const { nps, schedule, ...body } = req;
        const data = await post('/calcular/tabla', body);
        renderTabla(data);
        $('kpi-section').style.display = 'none';
        $('export-actions').style.display = 'flex';
        graficarBarras(data);
        $('plot-sens').innerHTML = '';
        renderAdvertencias(data.advertencias || []);
    } catch (e) {
        mostrarError(e.message);
    }
}

function graficarBarras(data) {
    const schedules = data.schedules;
    const traces = schedules.map((sch, idx) => ({
        x: data.diametros.map(n => n.replace('NPS ', '')),
        y: data.diametros.map(n => data.valores[data.escenarios[0]][n][sch]),
        name: `Sch ${sch}`,
        type: 'bar',
        marker: { color: ['#2e7d32', '#558b2f', '#81c784', '#a5d6a7'][idx] },
    }));
    const layout = {
        title: `Vida útil por diámetro — ${data.escenarios.map(e => escenariosNombres[e] || e).join(', ')}`,
        yaxis: { title: 'Vida útil (años)' },
        barmode: 'group',
        margin: { t: 50, b: 50 },
    };
    Plotly.newPlot('plot-barras', traces, layout, { responsive: true });
}

async function calcularSensibilidad() {
    try {
        const req = leerInputs();
        const data = await post('/calcular/sensibilidad-fs', req);
        const x = Object.keys(data.resultados);
        const y = Object.values(data.resultados);
        const trace = {
            x: x,
            y: y,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#2e7d32', width: 3 },
            marker: { size: 10 },
        };
        const layout = {
            title: `Sensibilidad al FS — ${data.material} ${data.nps} Sch ${data.schedule}`,
            xaxis: { title: 'Factor de seguridad FS' },
            yaxis: { title: 'Vida útil (años)' },
            margin: { t: 50, b: 50 },
        };
        Plotly.newPlot('plot-sens', [trace], layout, { responsive: true });
        $('kpi-section').style.display = 'none';
        $('result-section').style.display = 'none';
        $('export-actions').style.display = 'none';
        $('plot-barras').innerHTML = '';
        renderAdvertencias(data.advertencias || []);
    } catch (e) {
        mostrarError(e.message);
    }
}

async function calcularCondicionCritica() {
    try {
        const data = await get('/calcular/condicion-critica');
        const container = $('result-table');
        container.innerHTML = '';
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');
        thead.innerHTML = '<tr><th>NPS</th><th>SS304 Sch 10S</th><th>SS304L Sch 10S</th><th>SS304 Sch 40S</th><th>SS304L Sch 40S</th><th>A53 Gr B Sch 40</th></tr>';
        for (const r of data.filas) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${r.nps}</td><td>${r.ss304_s10}</td><td>${r.ss304L_s10}</td><td>${r.ss304_s40}</td><td>${r.ss304L_s40}</td><td>${r.a53_s40}</td>`;
            tbody.appendChild(tr);
        }
        table.appendChild(thead);
        table.appendChild(tbody);
        container.appendChild(table);
        $('result-section').style.display = 'block';
        $('result-title').textContent = `Condición crítica 60 °C — Cs=${data.parametros.Cs}%, v=${data.parametros.v} m/s, β=${data.parametros.beta}, FS=${data.parametros.fs}`;
        $('kpi-section').style.display = 'none';
        $('export-actions').style.display = 'none';
        $('plot-barras').innerHTML = '';
        $('plot-sens').innerHTML = '';
        renderAdvertencias(data.advertencias || []);
    } catch (e) {
        mostrarError(e.message);
    }
}

async function exportar(formato) {
    try {
        const req = leerInputs();
        const { nps, schedule, ...body } = req;
        const endpoint = formato === 'csv' ? '/export/csv' : '/export/excel';
        const res = await fetch(API + endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error('Error al exportar');
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
    } catch (e) {
        mostrarError(e.message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    actualizarSchedules();
    $('material').addEventListener('change', actualizarSchedules);
    $('btn-vida').addEventListener('click', calcularVidaUtil);
    $('btn-tabla').addEventListener('click', calcularTabla);
    $('btn-sens').addEventListener('click', calcularSensibilidad);
    $('btn-critica').addEventListener('click', calcularCondicionCritica);
    $('btn-csv').addEventListener('click', () => exportar('csv'));
    $('btn-excel').addEventListener('click', () => exportar('excel'));
});
