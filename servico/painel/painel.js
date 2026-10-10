(() => {
  'use strict';

  const API = '/api/v1';
  const INTERVALO_LISTA_MS = 3000;
  const INTERVALO_DETALHE_MS = 2000;
  const ATIVOS = ['na_fila', 'executando'];
  const ROTULOS = { na_fila: 'Na fila', executando: 'Executando', concluido: 'Concluído', falhou: 'Falhou', cancelado: 'Cancelado' };
  const MODOS = { completo: 'Completo', base: 'Só base', verbas: 'Só verbas' };
  const EXEMPLO_BASE = 'C:\\Testes\\17329\\17329 - Planilha Base v3.41.xlsb';
  const EXEMPLO_VERBAS = 'C:\\Testes\\17329\\17329 - Verbas v1.12.xlsm';

  const $ = (seletor) => document.querySelector(seletor);
  const estado = {
    pagina: 1, paginas: 1, registros: [], selecionado: null, logDesde: 0,
    timerLista: null, timerDetalhe: null, buscaTimer: null, filtroCard: null,
  };

  // ---------- utilidades ----------
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function guardar(chave, valor) { try { localStorage.setItem(chave, valor); } catch (_) { /* sem armazenamento */ } }
  function ler(chave) { try { return localStorage.getItem(chave) || ''; } catch (_) { return ''; } }

  function dataHora(iso) {
    if (!iso) return '—';
    const [d, h] = iso.split('T');
    const [a, m, dia] = d.split('-');
    return `${dia}/${m}/${a} ${h}`;
  }

  function duracao(seg) {
    if (seg === null || seg === undefined) return '—';
    const h = Math.floor(seg / 3600), m = Math.floor((seg % 3600) / 60), s = seg % 60;
    if (h) return `${h}h ${String(m).padStart(2, '0')}m`;
    if (m) return `${m}m ${String(s).padStart(2, '0')}s`;
    return `${s}s`;
  }

  const PADRAO_CNJ = /\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/;
  const SUBPASTA_DE_TRABALHO = /^(\d{2}[_ ].+|03 automa..o)$/i;

  function pastaDoProcesso(r) {
    const caminho = r.planilha_base || r.planilha_verbas || r.lancamentos || '';
    const partes = caminho.split(/[\\/]/).filter(Boolean);
    const comCnj = partes.find((p) => PADRAO_CNJ.test(p));
    if (comCnj) return comCnj;
    const pastas = partes.slice(0, -1);
    for (let i = pastas.length - 1; i >= 0; i -= 1) {
      if (!SUBPASTA_DE_TRABALHO.test(pastas[i])) return pastas[i];
    }
    return caminho;
  }

  function pilula(status) {
    return `<span class="pilula ${esc(status)}">${esc(ROTULOS[status] || status)}</span>`;
  }

  const ICONE_BAIXAR = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M8 2v8M4.5 7 8 10.5 11.5 7M3 13.5h10"/></svg>';
  const ICONE_CAMERA = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M2 5.5h2.5L6 3.5h4l1.5 2H14v7.5H2z"/><circle cx="8" cy="9" r="2.3"/></svg>';

  const nomeDoArquivo = (caminho) => String(caminho || '').split(/[\\/]/).pop();
  const extensao = (caminho) => (nomeDoArquivo(caminho).split('.').pop() || '').toUpperCase();

  function botoesArquivos(e) {
    return `<span class="acoes-linha">${(e.arquivos || []).map((a, i) =>
      `<button class="chip-arquivo" type="button" data-baixar="${esc(e.id)}" data-indice="${i}" data-nome="${esc(nomeDoArquivo(a))}" title="Baixar ${esc(nomeDoArquivo(a))}">${ICONE_BAIXAR}${esc(extensao(a))}</button>`).join('')}</span>`;
  }

  const ICONE_CONSOLE = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M3 4.5 6.5 8 3 11.5M8 12h5"/></svg>';

  function botaoConsole(e) {
    if (e.status !== 'executando') return '';
    return `<button class="icone-console" type="button" data-console="${esc(e.id)}" title="Acompanhar o andamento em tempo real">${ICONE_CONSOLE}console</button>`;
  }

  function botaoCaptura(e) {
    if (!e.captura) return '';
    return `<button class="icone-captura" type="button" data-captura="${esc(e.id)}" title="Ver a captura de tela da falha">${ICONE_CAMERA}</button>`;
  }

  // ---------- downloads ----------
  async function buscarBlob(caminho) {
    const resposta = await fetch(API + caminho, { headers: { 'X-API-Token': $('#token').value.trim() } });
    if (!resposta.ok) {
      let mensagem = `Erro ${resposta.status}`;
      try { mensagem = (await resposta.json()).erro.mensagem; } catch (_) { /* corpo não é JSON */ }
      throw new Error(mensagem);
    }
    return resposta.blob();
  }

  function salvarBlob(blob, nome) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nome;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  async function baixarArquivo(id, indice, nome, botao) {
    if (botao) botao.disabled = true;
    try {
      salvarBlob(await buscarBlob(`/calculos/${encodeURIComponent(id)}/arquivos/${indice}`), nome);
    } catch (erro) {
      mostrarAviso(`Não foi possível baixar "${nome}": ${erro.message}`);
    } finally {
      if (botao) botao.disabled = false;
    }
  }

  const capturas = new Map();

  async function urlDaCaptura(id) {
    if (!capturas.has(id)) {
      const blob = await buscarBlob(`/calculos/${encodeURIComponent(id)}/captura`);
      capturas.set(id, { blob, url: URL.createObjectURL(blob) });
    }
    return capturas.get(id);
  }

  async function abrirCaptura(id) {
    const registro = estado.registros.find((r) => r.id === id) || {};
    try {
      const { url } = await urlDaCaptura(id);
      $('#captura-img').src = url;
      $('#captura-info').textContent = `Execução ${id} · ${registro.mensagem || ''} · ${nomeDoArquivo(registro.captura)}`;
      $('#modal-captura').dataset.id = id;
      $('#modal-captura').dataset.nome = nomeDoArquivo(registro.captura) || `captura_${id}.png`;
      abrirModal('#modal-captura');
    } catch (erro) {
      mostrarAviso(`Não foi possível abrir a captura: ${erro.message}`);
    }
  }

  async function chamar(caminho, opcoes = {}) {
    const headers = Object.assign({ 'X-API-Token': $('#token').value.trim() }, opcoes.headers || {});
    const resposta = await fetch(API + caminho, Object.assign({}, opcoes, { headers }));
    let corpo = null;
    try { corpo = await resposta.json(); } catch (_) { /* corpo vazio */ }
    return { ok: resposta.ok, status: resposta.status, corpo };
  }

  function mostrarAviso(texto) {
    const aviso = $('#aviso');
    aviso.hidden = !texto;
    aviso.textContent = texto || '';
  }

  async function copiar(texto, botao) {
    const rotulo = botao.dataset.rotulo || botao.textContent;
    botao.dataset.rotulo = rotulo;
    try {
      await navigator.clipboard.writeText(texto);
      botao.textContent = 'Copiado';
    } catch (_) {
      botao.textContent = 'Selecione e copie';
    }
    setTimeout(() => { botao.textContent = rotulo; }, 1500);
  }

  // ---------- saúde e indicadores ----------
  async function carregarSaude() {
    try {
      const r = await fetch(API + '/health');
      const s = await r.json();
      const itens = [
        { ok: s.status === 'ok', texto: s.status === 'ok' ? 'Serviço ok' : 'Serviço degradado', dica: (s.motivos || []).join('; ') },
        { ok: s.pjecalc_online, texto: s.pjecalc_online ? 'PJe-Calc online' : 'PJe-Calc offline' },
      ];
      $('#saude').innerHTML = itens.map((i) =>
        `<span class="pilula-saude ${i.ok ? '' : 'ruim'}" title="${esc(i.dica || '')}">${esc(i.texto)}</span>`).join('');
    } catch (_) {
      $('#saude').innerHTML = '<span class="pilula-saude ruim">Serviço fora do ar</span>';
    }
  }

  function card(rotulo, valor, extra, classe, filtro) {
    const ativo = filtro && estado.filtroCard === filtro ? ' ativo' : '';
    const atributo = filtro ? ` data-filtro="${esc(filtro)}" role="button" tabindex="0"` : '';
    return `<div class="card ${classe || ''}${ativo}"${atributo}>
      <span class="rot">${esc(rotulo)}</span>
      <span class="val">${esc(valor)}</span>
      <span class="extra">${esc(extra || '')}</span>
    </div>`;
  }

  async function carregarIndicadores() {
    const r = await chamar('/indicadores');
    if (!r.ok) return;
    const { indicadores: ind, fila } = r.corpo;
    const ps = ind.por_status, hoje = ind.hoje.por_status;
    const taxa = ind.taxa_sucesso === null ? '—' : `${(ind.taxa_sucesso * 100).toFixed(1)}%`;
    $('#cards').innerHTML = [
      card('Total', ind.total, `${ind.hoje.total} hoje`, '', ''),
      card('Na fila', ps.na_fila, `${hoje.na_fila} hoje`, 's-na_fila', 'na_fila'),
      card('Executando', ps.executando, fila.executando ? `ID ${fila.executando}` : 'worker livre', 's-executando', 'executando'),
      card('Concluídos', ps.concluido, `${hoje.concluido} hoje`, 's-concluido', 'concluido'),
      card('Falhas', ps.falhou, `${hoje.falhou} hoje`, 's-falhou', 'falhou'),
      card('Cancelados', ps.cancelado, `${hoje.cancelado} hoje`, 's-cancelado', 'cancelado'),
      card('Taxa de sucesso', taxa, 'concluídos ÷ finalizados', '', ''),
      card('Duração média', duracao(ind.duracao_media_seg), 'últimos 50 concluídos', '', ''),
      card('Worker', fila.worker_ativo ? 'Ativo' : 'Parado', `${fila.na_fila.length} aguardando`, fila.worker_ativo ? 's-concluido' : 's-falhou', ''),
    ].join('');
  }

  // ---------- lista ----------
  function consultaLista() {
    const p = new URLSearchParams({ pagina: estado.pagina, limite: $('#f-limite').value });
    const campos = { situacao: '#f-situacao', modo: '#f-modo', busca: '#f-busca', de: '#f-de', ate: '#f-ate' };
    Object.entries(campos).forEach(([nome, seletor]) => {
      const valor = $(seletor).value.trim();
      if (valor) p.set(nome, valor);
    });
    return p.toString();
  }

  async function carregarLista() {
    const r = await chamar('/calculos?' + consultaLista());
    if (r.status === 401) {
      mostrarAviso('Informe o token da API no campo "Token" do topo para ver as execuções.');
      $('#linhas').innerHTML = '<tr><td colspan="11" class="vazio">Sem acesso: token ausente ou inválido.</td></tr>';
      return;
    }
    if (!r.ok) {
      mostrarAviso(r.corpo?.erro?.mensagem || `Erro ${r.status} ao carregar as execuções.`);
      return;
    }
    mostrarAviso('');
    const c = r.corpo;
    estado.registros = c.execucoes;
    estado.paginas = c.paginas;
    if (estado.pagina > c.paginas) { estado.pagina = c.paginas; return carregarLista(); }

    $('#linhas').innerHTML = c.execucoes.length ? c.execucoes.map((e) => `
      <tr data-id="${esc(e.id)}" class="${e.id === estado.selecionado ? 'selecionada' : ''}">
        <td><span class="mono">${esc(e.id)}</span></td>
        <td>${pilula(e.status)}${e.status === 'na_fila' && e.posicao_na_fila ? ` <span class="etiqueta">#${esc(e.posicao_na_fila)}</span>` : ''}${botaoConsole(e)}${botaoCaptura(e)}</td>
        <td>${esc(MODOS[e.modo] || '—')}</td>
        <td><span class="etiqueta ${e.navegador === 'interativo' ? 'interativo' : ''}">${esc(e.navegador === 'interativo' ? 'Interativo' : 'Oculto')}</span></td>
        <td class="processo" title="${esc(e.planilha_base || e.planilha_verbas || '')}">${esc(pastaDoProcesso(e))}</td>
        <td>${esc(e.solicitante || '—')}</td>
        <td>${esc(e.origem || '—')}</td>
        <td>${esc(dataHora(e.criado_em))}</td>
        <td class="num">${esc(duracao(e.duracao_seg))}</td>
        <td class="mensagem" title="${esc(e.mensagem || '')}">${esc(e.mensagem || '')}</td>
        <td>${(e.arquivos || []).length ? botoesArquivos(e) : '<span class="etiqueta">—</span>'}</td>
      </tr>`).join('')
      : '<tr><td colspan="11" class="vazio">Nenhuma execução encontrada com esses filtros.</td></tr>';

    const inicio = c.total_geral ? (c.pagina - 1) * c.limite + 1 : 0;
    $('#pag-info').textContent = `${inicio}–${inicio + c.total - (c.total ? 1 : 0)} de ${c.total_geral} execuções`;
    $('#pag-atual').textContent = `Página ${c.pagina} de ${c.paginas}`;
    $('#pag-primeira').disabled = $('#pag-anterior').disabled = c.pagina <= 1;
    $('#pag-proxima').disabled = $('#pag-ultima').disabled = c.pagina >= c.paginas;
    $('#atualizado').textContent = 'Atualizado às ' + new Date().toLocaleTimeString('pt-BR');
  }

  async function atualizarTudo() {
    await Promise.allSettled([carregarSaude(), carregarIndicadores(), carregarLista()]);
  }

  function agendarLista() {
    clearTimeout(estado.timerLista);
    estado.timerLista = setTimeout(async () => {
      if ($('#auto').checked && !document.hidden) await atualizarTudo();
      agendarLista();
    }, INTERVALO_LISTA_MS);
  }

  function irParaPagina(pagina) {
    estado.pagina = Math.min(Math.max(pagina, 1), estado.paginas);
    carregarLista();
  }

  function filtrosMudaram() {
    estado.pagina = 1;
    estado.filtroCard = $('#f-situacao').value || null;
    atualizarTudo();
  }

  // ---------- detalhe ----------
  function linhaDetalhe(rotulo, valor, mono) {
    return `<dt>${esc(rotulo)}</dt><dd${mono ? ' class="mono"' : ''}>${valor}</dd>`;
  }

  function renderizarDetalhe(e) {
    $('#d-id').textContent = e.id;
    $('#d-campos').innerHTML = [
      linhaDetalhe('Situação', pilula(e.status) + (e.posicao_na_fila ? ` <span class="etiqueta">posição ${esc(e.posicao_na_fila)}</span>` : '')),
      linhaDetalhe('Mensagem', esc(e.mensagem || '—')),
      linhaDetalhe('Modo', esc(MODOS[e.modo] || 'definido ao iniciar')),
      linhaDetalhe('Navegador', esc(e.navegador === 'interativo' ? 'Interativo' : 'Oculto')),
      linhaDetalhe('Planilha base', esc(e.planilha_base || '—'), true),
      linhaDetalhe('Planilha de verbas', esc(e.planilha_verbas || '—'), true),
      linhaDetalhe('Lançamentos (.json)', esc(e.lancamentos || '—'), true),
      linhaDetalhe('Solicitante', esc(e.solicitante || '—')),
      linhaDetalhe('Origem', esc(e.origem || '—')),
      linhaDetalhe('Criado em', esc(dataHora(e.criado_em))),
      linhaDetalhe('Iniciado em', esc(dataHora(e.iniciado_em))),
      linhaDetalhe('Concluído em', esc(dataHora(e.concluido_em))),
      linhaDetalhe('Duração', esc(duracao(e.duracao_seg))),
    ].join('');

    const arquivos = e.arquivos || [];
    $('#d-arquivos-bloco').hidden = !arquivos.length;
    $('#d-arquivos').innerHTML = arquivos.map((a, i) => `<li><span>${esc(a)}</span>
      <button class="btn fantasma" type="button" data-baixar="${esc(e.id)}" data-indice="${i}" data-nome="${esc(nomeDoArquivo(a))}">${ICONE_BAIXAR}Baixar</button></li>`).join('');

    const blocoCaptura = $('#d-captura-bloco');
    if (!e.captura) {
      blocoCaptura.hidden = true;
    } else if (blocoCaptura.dataset.id !== e.id) {
      blocoCaptura.dataset.id = e.id;
      urlDaCaptura(e.id)
        .then(({ url }) => { if (estado.selecionado === e.id) { $('#d-captura-img').src = url; blocoCaptura.hidden = false; } })
        .catch(() => { blocoCaptura.hidden = true; });
    }
    const resumo = e.lancamentos_resumo;
    $('#d-lancamentos-bloco').hidden = !resumo;
    if (resumo) {
      const ignorados = Object.entries(resumo.ignorados || {});
      $('#d-lancamentos-info').textContent = `${(resumo.usados || []).length} usados · ${ignorados.length} ignorados · ${(resumo.avisos || []).length} avisos`;
      $('#d-lancamentos').innerHTML = [
        (resumo.avisos || []).length ? `<ul>${resumo.avisos.map((a) => `<li class="aviso-lanc">${esc(a)}</li>`).join('')}</ul>` : '',
        ignorados.length ? `<details open><summary>Ignorados</summary><ul>${ignorados.map(([c, m]) => `<li><code>${esc(c)}</code> — ${esc(m)}</li>`).join('')}</ul></details>` : '',
        `<details><summary>Usados</summary><ul>${(resumo.usados || []).map((c) => `<li><code>${esc(c)}</code></li>`).join('')}</ul></details>`,
      ].join('');
    }
    $('#d-erro-bloco').hidden = !e.erro;
    $('#d-erro').textContent = e.erro || '';
    $('#d-cancelar').hidden = e.status !== 'na_fila';
  }

  function anexarLog(linhas) {
    if (!linhas.length) return;
    const log = $('#d-log');
    const fragmento = document.createDocumentFragment();
    linhas.forEach((l) => {
      const hora = document.createElement('span');
      hora.className = 'hora';
      hora.textContent = `${l.hora}  `;
      fragmento.append(hora, document.createTextNode(`${l.mensagem}\n`));
    });
    log.append(fragmento);
    if ($('#d-seguir').checked) log.scrollTop = log.scrollHeight;
  }

  async function carregarDetalhe() {
    const id = estado.selecionado;
    if (!id) return;
    const r = await chamar(`/calculos/${encodeURIComponent(id)}?desde=${estado.logDesde}`);
    if (id !== estado.selecionado || !r.ok) return;
    const e = r.corpo.execucao;
    renderizarDetalhe(e);
    anexarLog(e.log || []);
    estado.logDesde = e.log_ultimo_seq;
    $('#d-log-info').textContent = `${estado.logDesde} linhas`;
    clearTimeout(estado.timerDetalhe);
    if (ATIVOS.includes(e.status)) {
      estado.timerDetalhe = setTimeout(carregarDetalhe, INTERVALO_DETALHE_MS);
    }
  }

  function abrirDetalhe(id) {
    estado.selecionado = id;
    estado.logDesde = 0;
    $('#d-log').textContent = '';
    $('#d-captura-bloco').hidden = true;
    $('#d-captura-bloco').dataset.id = '';
    $('#gaveta').hidden = false;
    document.querySelectorAll('#linhas tr').forEach((tr) => tr.classList.toggle('selecionada', tr.dataset.id === id));
    carregarDetalhe();
  }

  function fecharDetalhe() {
    clearTimeout(estado.timerDetalhe);
    estado.selecionado = null;
    $('#gaveta').hidden = true;
    document.querySelectorAll('#linhas tr.selecionada').forEach((tr) => tr.classList.remove('selecionada'));
  }

  async function cancelarSelecionado() {
    const botao = $('#d-cancelar');
    if (botao.dataset.confirmar !== '1') {
      botao.dataset.confirmar = '1';
      botao.textContent = 'Confirmar cancelamento';
      setTimeout(() => { botao.dataset.confirmar = ''; botao.textContent = 'Cancelar'; }, 4000);
      return;
    }
    botao.dataset.confirmar = '';
    botao.textContent = 'Cancelar';
    const r = await chamar(`/calculos/${encodeURIComponent(estado.selecionado)}/cancelar`, { method: 'POST' });
    if (!r.ok) mostrarAviso(r.corpo?.erro?.mensagem || 'Não foi possível cancelar.');
    await Promise.allSettled([carregarDetalhe(), atualizarTudo()]);
  }

  // ---------- console em tempo real ----------
  const INTERVALO_CONSOLE_MS = 1500;
  const console_ = { id: null, desde: 0, timer: null, finalizado: false };

  function classeDaLinha(mensagem) {
    if (/except|erro|falh|traceback|\[!!\]/i.test(mensagem)) return 'erro';
    if (/\[ok\]|sucesso|conclu[ií]d/i.test(mensagem)) return 'ok';
    return '';
  }

  function anexarConsole(linhas) {
    const log = $('#console-log');
    log.querySelector('.cursor')?.remove();
    const fragmento = document.createDocumentFragment();
    linhas.forEach((l) => {
      const hora = document.createElement('span');
      hora.className = 'hora';
      hora.textContent = `${l.hora}  `;
      const texto = document.createElement('span');
      texto.className = classeDaLinha(l.mensagem);
      texto.textContent = `${l.mensagem}\n`;
      fragmento.append(hora, texto);
    });
    log.append(fragmento);
    if (!console_.finalizado) {
      const cursor = document.createElement('span');
      cursor.className = 'cursor';
      log.append(cursor);
    }
    if ($('#console-seguir').checked) log.scrollTop = log.scrollHeight;
  }

  async function carregarConsole() {
    const id = console_.id;
    if (!id || $('#modal-console').hidden) return;
    const r = await chamar(`/calculos/${encodeURIComponent(id)}?desde=${console_.desde}`);
    if (id !== console_.id) return;
    if (!r.ok) {
      $('#console-atualizado').textContent = r.corpo?.erro?.mensagem || `Erro ${r.status} ao ler o log`;
    } else {
      const e = r.corpo.execucao;
      console_.finalizado = !ATIVOS.includes(e.status);
      $('#console-status').innerHTML = pilula(e.status);
      $('#console-processo').textContent = `${pastaDoProcesso(e)} · ${MODOS[e.modo] || 'modo a definir'} · navegador ${e.navegador}`;
      $('#console-tempo').textContent = `Duração: ${duracao(e.duracao_seg)}`;
      anexarConsole(e.log || []);
      console_.desde = e.log_ultimo_seq;
      if (console_.finalizado) {
        anexarConsole([{ hora: '', mensagem: `— execução encerrada: ${ROTULOS[e.status] || e.status}${e.mensagem ? ` · ${e.mensagem}` : ''} —` }]);
        $('#console-log').lastChild.className = 'fim';
      }
      $('#console-linhas').textContent = `${console_.desde} linhas`;
      $('#console-atualizado').textContent = console_.finalizado
        ? 'Execução encerrada; atualização parada.'
        : `Ao vivo · atualizado às ${new Date().toLocaleTimeString('pt-BR')}`;
    }
    clearTimeout(console_.timer);
    if (!console_.finalizado) console_.timer = setTimeout(carregarConsole, INTERVALO_CONSOLE_MS);
  }

  function abrirConsole(id) {
    clearTimeout(console_.timer);
    Object.assign(console_, { id, desde: 0, finalizado: false });
    $('#console-id').textContent = id;
    $('#console-log').textContent = '';
    $('#console-status').innerHTML = '';
    $('#console-processo').textContent = '';
    $('#console-linhas').textContent = '';
    $('#console-atualizado').textContent = 'Conectando…';
    abrirModal('#modal-console');
    carregarConsole();
  }

  // ---------- modais ----------
  function abrirModal(id) {
    const modal = $(id);
    modal.hidden = false;
    const foco = modal.querySelector('textarea, input, button');
    if (foco) foco.focus();
  }

  function fecharModais() {
    document.querySelectorAll('.modal-fundo').forEach((m) => { m.hidden = true; });
    clearTimeout(console_.timer);
    console_.id = null;
  }

  function caminhosReais() {
    const par = estado.registros.find((r) => r.planilha_base && r.planilha_verbas);
    if (par) return { base: par.planilha_base, verbas: par.planilha_verbas };
    return { base: EXEMPLO_BASE, verbas: EXEMPLO_VERBAS };
  }

  function modeloPedido(tipo) {
    const c = caminhosReais();
    const pedido = {};
    if (tipo !== 'verbas') pedido.planilha_base = c.base;
    if (tipo !== 'base') pedido.planilha_verbas = c.verbas;
    pedido.solicitante = 'painel';
    pedido.origem = 'painel';
    pedido.navegador = document.querySelector('input[name="novo-navegador"]:checked').value;
    return JSON.stringify(pedido, null, 2);
  }

  function validarJson() {
    const area = $('#novo-json');
    const saida = $('#novo-validacao');
    let pedido;
    try {
      pedido = JSON.parse(area.value);
    } catch (erro) {
      area.classList.add('invalido');
      saida.className = 'validacao erro';
      saida.textContent = `JSON inválido: ${erro.message}`;
      return null;
    }
    const problemas = [];
    if (!pedido || typeof pedido !== 'object' || Array.isArray(pedido)) problemas.push('o JSON precisa ser um objeto { … }');
    else {
      if (!pedido.planilha_base && !pedido.planilha_verbas && !pedido.lancamentos) problemas.push("informe 'planilha_base', 'planilha_verbas' ou 'lancamentos'");
      if (pedido.navegador !== undefined && !['oculto', 'interativo'].includes(pedido.navegador)) problemas.push("'navegador' deve ser 'oculto' ou 'interativo'");
    }
    area.classList.toggle('invalido', problemas.length > 0);
    saida.className = 'validacao ' + (problemas.length ? 'erro' : 'ok');
    saida.textContent = problemas.length ? problemas.join('; ') : 'JSON válido.';
    if (!problemas.length) {
      const radio = document.querySelector(`input[name="novo-navegador"][value="${pedido.navegador === 'interativo' ? 'interativo' : 'oculto'}"]`);
      radio.checked = true;
    }
    return problemas.length ? null : pedido;
  }

  function aplicarNavegadorNoJson(valor) {
    try {
      const pedido = JSON.parse($('#novo-json').value);
      if (pedido && typeof pedido === 'object' && !Array.isArray(pedido)) {
        pedido.navegador = valor;
        $('#novo-json').value = JSON.stringify(pedido, null, 2);
      }
    } catch (_) { /* o usuário corrige o JSON antes */ }
    validarJson();
  }

  async function enviarPedido() {
    const pedido = validarJson();
    if (!pedido) return;
    const botao = $('#novo-enviar');
    const resultado = $('#novo-resultado');
    const headers = { 'Content-Type': 'application/json; charset=utf-8' };
    const chave = $('#novo-chave').value.trim();
    if (chave) headers['Idempotency-Key'] = chave;
    botao.disabled = true;
    try {
      const r = await chamar('/calculos', { method: 'POST', headers, body: JSON.stringify(pedido) });
      resultado.hidden = false;
      if (r.ok) {
        const e = r.corpo.execucao;
        const texto = r.status === 202
          ? `Pedido aceito. Execução ${e.id} na posição ${r.corpo.posicao_na_fila} da fila.`
          : `Esta Idempotency-Key já foi usada: devolvida a execução ${e.id} (${ROTULOS[e.status] || e.status}). Nenhum cálculo novo foi criado.`;
        resultado.className = 'resultado ok';
        resultado.innerHTML = `${esc(texto)} <button class="btn fantasma" type="button" id="novo-abrir">Acompanhar</button>`;
        $('#novo-abrir').addEventListener('click', () => { fecharModais(); abrirDetalhe(e.id); });
        await atualizarTudo();
      } else {
        resultado.className = 'resultado erro';
        resultado.innerHTML = `${esc(r.corpo?.erro?.mensagem || `Erro ${r.status}`)}<pre>${esc(JSON.stringify(r.corpo, null, 2))}</pre>`;
      }
    } catch (erro) {
      resultado.hidden = false;
      resultado.className = 'resultado erro';
      resultado.textContent = `Não foi possível falar com o serviço: ${erro.message}`;
    } finally {
      botao.disabled = false;
    }
  }

  // ---------- documentação ----------
  function blocoCodigo(codigo) {
    return `<div class="bloco-codigo"><button class="btn fantasma copiar" type="button">Copiar</button><pre>${esc(codigo)}</pre></div>`;
  }

  function tabela(cabecalho, linhas) {
    return `<div class="tabela-rolo"><table><thead><tr>${cabecalho.map((c) => `<th>${esc(c)}</th>`).join('')}</tr></thead>
      <tbody>${linhas.map((l) => `<tr>${l.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }

  function secoesDocumentacao() {
    const url = window.location.origin + API;
    const c = caminhosReais();
    const idReal = estado.registros[0]?.id || 'bef3ecb0d82c';
    const corpo = { planilha_base: c.base, planilha_verbas: c.verbas, solicitante: 'sap', origem: 'tarefas-jrs', navegador: 'oculto' };
    const corpoJson = JSON.stringify(corpo, null, 2);
    const psCorpo = `@{
    planilha_base   = "${c.base}"
    planilha_verbas = "${c.verbas}"
    solicitante     = "sap"
    origem          = "tarefas-jrs"
    navegador       = "oculto"      # ou "interativo"
}`;

    return [
      {
        id: 'visao', titulo: 'Visão geral',
        html: `
          <h3>O que a API faz</h3>
          <p>Recebe o caminho da planilha base e/ou da planilha de verbas, põe o cálculo numa fila e roda a automação do PJe-Calc
            um de cada vez. O resultado (.PJC e relatório em PDF) é gravado em <code>03 Automação</code>, ao lado da planilha.</p>
          <h4>Endereço base</h4>${blocoCodigo(url)}
          <h4>Modo, decidido pelas planilhas enviadas</h4>
          ${tabela(['Envio', 'Modo', 'Observação'], [
            ['<code>planilha_base</code> + <code>planilha_verbas</code>', 'completo', 'Caminho recomendado.'],
            ['só <code>planilha_base</code>', 'base', 'Precisa da aba <code>CAD</code>.'],
            ['só <code>planilha_verbas</code>', 'verbas', 'Precisa da aba <code>TBCALCULO</code> e de um .PJC na mesma pasta. <strong>Hoje está com defeito e termina em falha.</strong>'],
          ])}
          <h4>Ciclo de vida</h4>
          <p>${pilula('na_fila')} → ${pilula('executando')} → ${pilula('concluido')} ou ${pilula('falhou')}.
            Só o que está ${pilula('na_fila')} pode ir para ${pilula('cancelado')}.</p>
          <p>A execução só fica <strong>concluída</strong> se um .PJC novo for exportado. Qualquer alerta da automação,
            exceção ou encerramento antecipado vira <strong>falhou</strong>, com o motivo em <code>mensagem</code>.</p>
          <h4>Regras importantes</h4>
          <ul>
            <li>Os caminhos são lidos <strong>no disco da máquina do serviço</strong>. Para arquivos em rede, use caminho UNC (<code>\\\\192.168.11.3\\Acervo\\…</code>), não letra de unidade.</li>
            <li>Envie o corpo em <strong>UTF-8</strong>. Sem isso, "Perícias" e "03 Automação" chegam corrompidos e o arquivo "não é encontrado".</li>
            <li>Para saber onde ficaram os arquivos, use o campo <code>arquivos</code> da execução. Não monte o caminho por conta própria.
              Para baixá-los pela API, use <code>/calculos/{id}/arquivos/{indice}</code>.</li>
            <li>Quando a execução falha, o serviço salva uma captura de tela em <code>diagnostico\\falhas</code>, dentro do projeto,
              e a disponibiliza em <code>/calculos/{id}/captura</code>. É a página inteira do Firefox da automação, nos dois modos; a tela da máquina só é usada se o navegador já tiver fechado.</li>
            <li><code>lancamentos</code>: caminho do <code>.json</code> do SAP. Cada execução devolve em <code>lancamentos_resumo</code> o que foi <strong>usado</strong>, o que foi <strong>ignorado</strong> (com o motivo) e os <strong>avisos</strong>; campo desconhecido é ignorado, valor fora da lista recusa o pedido.</li>
            <li><code>navegador</code>: <code>oculto</code> (padrão) roda o Firefox sem janela; <code>interativo</code> mostra a janela na máquina do serviço, útil para acompanhar ou depurar.</li>
          </ul>`,
      },
      {
        id: 'auth', titulo: 'Autenticação',
        html: `
          <p>Todas as rotas, menos <code>/health</code>, exigem o token definido em <code>PJECALC_API_TOKEN</code> no <code>.env</code> do serviço.</p>
          ${tabela(['Forma', 'Exemplo'], [
            ['Cabeçalho (preferido)', '<code>X-API-Token: &lt;SEU_TOKEN&gt;</code>'],
            ['Bearer (aceito)', '<code>Authorization: Bearer &lt;SEU_TOKEN&gt;</code>'],
          ])}
          <p>Token ausente ou errado devolve <code>401</code> com código <code>nao_autorizado</code>.</p>`,
      },
      {
        id: 'rotas', titulo: 'Endpoints',
        html: `
          ${tabela(['Método', 'Rota', 'Para quê', 'Respostas'], [
            ['<span class="metodo get">GET</span>', '<code>/health</code>', 'Saúde do serviço e do PJe-Calc. Sem token.', '200'],
            ['<span class="metodo post">POST</span>', '<code>/calculos</code>', 'Pede um cálculo. Aceita <code>Idempotency-Key</code>.', '202 aceito · 200 existente · 400 · 401'],
            ['<span class="metodo get">GET</span>', '<code>/calculos</code>', 'Lista da mais recente à mais antiga. Filtros: <code>situacao</code>, <code>modo</code>, <code>busca</code>, <code>de</code>, <code>ate</code> (AAAA-MM-DD), <code>pagina</code>, <code>limite</code> (1–200).', '200 · 400'],
            ['<span class="metodo get">GET</span>', '<code>/calculos/{id}?desde=N</code>', 'Detalhe e log incremental: devolve só as linhas com <code>seq</code> maior que N.', '200 · 404'],
            ['<span class="metodo get">GET</span>', '<code>/calculos/{id}/arquivos/{indice}</code>', 'Baixa o arquivo gerado na posição <code>indice</code> (0, 1, …) da lista <code>arquivos</code>.', '200 · 404 · 410'],
            ['<span class="metodo get">GET</span>', '<code>/calculos/{id}/captura</code>', 'Captura de tela (PNG) tirada quando a execução falhou. Com <code>?baixar=1</code> vem como anexo.', '200 · 404 · 410'],
            ['<span class="metodo post">POST</span>', '<code>/calculos/{id}/cancelar</code>', 'Cancela o que ainda está na fila.', '200 · 404 · 409'],
            ['<span class="metodo get">GET</span>', '<code>/fila</code>', 'O que está executando e o que aguarda.', '200'],
            ['<span class="metodo get">GET</span>', '<code>/indicadores</code>', 'Contagens por situação, hoje, taxa de sucesso e duração média.', '200'],
          ])}
          <h4>Corpo do POST /calculos</h4>
          ${tabela(['Campo', 'Tipo', 'Obrig.', 'Descrição'], [
            ['<code>planilha_base</code>', 'texto', 'um dos dois', 'Caminho da planilha base (.xlsb, .xlsm, .xlsx, .xls).'],
            ['<code>planilha_verbas</code>', 'texto', 'um dos três', 'Caminho da planilha de verbas.'],
            ['<code>lancamentos</code>', 'texto', 'um dos três', 'Caminho do <code>.json</code> de lançamentos (contrato <code>lancamentos-pjecalc/1</code>). Sem planilha base, o cálculo é montado só com ele; com planilha, completa o que ela deixou vazio (a planilha manda). Honorários, multas e custas entram como bloco inteiro.'],
            ['<code>navegador</code>', 'texto', 'não', '<code>oculto</code> (padrão) ou <code>interativo</code>.'],
            ['<code>solicitante</code>', 'texto', 'não', 'Quem pediu (até 100 caracteres).'],
            ['<code>origem</code>', 'texto', 'não', 'Sistema de origem (até 100 caracteres).'],
          ])}
          ${blocoCodigo(corpoJson)}`,
      },
      {
        id: 'ps', titulo: 'PowerShell',
        html: `
          <h4>1. Sessão</h4>
          ${blocoCodigo(`$api = "${url}"
$h   = @{ "X-API-Token" = "<SEU_TOKEN>" }`)}
          <h4>2. Pedir o cálculo (corpo em UTF-8)</h4>
          ${blocoCodigo(`$corpo = ${psCorpo} | ConvertTo-Json
$r = Invoke-RestMethod -Method Post "$api/calculos" -Headers $h \`
     -Body ([Text.Encoding]::UTF8.GetBytes($corpo)) -ContentType "application/json; charset=utf-8"
$id = $r.execucao.id
$id`)}
          <h4>3. Acompanhar até terminar, com log incremental</h4>
          ${blocoCodigo(`$desde = 0
do {
    Start-Sleep 5
    $e = (Invoke-RestMethod "$api/calculos/$($id)?desde=$desde" -Headers $h).execucao
    $e.log | ForEach-Object { "$($_.hora)  $($_.mensagem)" }
    $desde = $e.log_ultimo_seq
} while ($e.status -in "na_fila", "executando")
$e | Select-Object status, mensagem, arquivos, duracao_seg | Format-List`)}
          <h4>Consultar uma execução existente</h4>
          ${blocoCodigo(`Invoke-RestMethod "$api/calculos/${idReal}" -Headers $h | ConvertTo-Json -Depth 5`)}
          <h4>Baixar os arquivos gerados</h4>
          ${blocoCodigo(`$e = (Invoke-RestMethod "$api/calculos/${idReal}" -Headers $h).execucao
for ($i = 0; $i -lt $e.arquivos.Count; $i++) {
    $nome = Split-Path $e.arquivos[$i] -Leaf
    Invoke-WebRequest "$api/calculos/${idReal}/arquivos/$i" -Headers $h -OutFile $nome
}`)}
          <h4>Baixar a captura de uma falha</h4>
          ${blocoCodigo(`Invoke-WebRequest "$api/calculos/${idReal}/captura" -Headers $h -OutFile "captura_${idReal}.png"`)}
          <h4>Listar falhas de hoje</h4>
          ${blocoCodigo(`$hoje = Get-Date -Format yyyy-MM-dd
Invoke-RestMethod "$api/calculos?situacao=falhou&de=$hoje&limite=50" -Headers $h`)}
          <h4>Ver o corpo de um erro</h4>
          ${blocoCodigo(`try { Invoke-RestMethod -Method Post "$api/calculos" -Headers $h -Body "{}" -ContentType "application/json" }
catch { $_.ErrorDetails.Message }`)}`,
      },
      {
        id: 'curl', titulo: 'curl',
        html: `
          <p>No Windows use <code>curl.exe</code>. Grave o corpo em arquivo UTF-8 para não perder acentos.
            No JSON, a barra invertida do caminho vai duplicada.</p>
          <h4>Pedir o cálculo</h4>
          ${blocoCodigo(`curl.exe -s -X POST "${url}/calculos" ^
  -H "X-API-Token: <SEU_TOKEN>" ^
  -H "Content-Type: application/json; charset=utf-8" ^
  -H "Idempotency-Key: 17329-teste-1" ^
  --data-binary "@pedido.json"`)}
          <p>Conteúdo de <code>pedido.json</code>:</p>
          ${blocoCodigo(corpoJson)}
          <h4>Acompanhar</h4>
          ${blocoCodigo(`curl.exe -s "${url}/calculos/${idReal}?desde=0" -H "X-API-Token: <SEU_TOKEN>"`)}
          <h4>Baixar o primeiro arquivo gerado</h4>
          ${blocoCodigo(`curl.exe -s -OJ "${url}/calculos/${idReal}/arquivos/0" -H "X-API-Token: <SEU_TOKEN>"`)}
          <h4>Baixar a captura de uma falha</h4>
          ${blocoCodigo(`curl.exe -s -o captura.png "${url}/calculos/${idReal}/captura" -H "X-API-Token: <SEU_TOKEN>"`)}
          <h4>Cancelar (só na fila)</h4>
          ${blocoCodigo(`curl.exe -s -X POST "${url}/calculos/${idReal}/cancelar" -H "X-API-Token: <SEU_TOKEN>"`)}
          <h4>Saúde (sem token)</h4>
          ${blocoCodigo(`curl.exe -s "${url}/health"`)}`,
      },
      {
        id: 'py', titulo: 'Python',
        html: `
          ${blocoCodigo(`import time
import requests

API = "${url}"
CABECALHOS = {"X-API-Token": "<SEU_TOKEN>"}

pedido = ${JSON.stringify(corpo, null, 4).replace(/\n/g, '\n')}

r = requests.post(f"{API}/calculos", json=pedido,
                  headers={**CABECALHOS, "Idempotency-Key": "17329-teste-1"}, timeout=30)
r.raise_for_status()
execucao_id = r.json()["execucao"]["id"]

desde = 0
while True:
    e = requests.get(f"{API}/calculos/{execucao_id}", params={"desde": desde},
                     headers=CABECALHOS, timeout=30).json()["execucao"]
    for linha in e["log"]:
        print(linha["hora"], linha["mensagem"])
    desde = e["log_ultimo_seq"]
    if e["status"] not in ("na_fila", "executando"):
        break
    time.sleep(5)

print(e["status"], e["mensagem"], e["arquivos"])`)}
          <p><code>requests</code> já envia o JSON em UTF-8.</p>`,
      },
      {
        id: 'respostas', titulo: 'Respostas e erros',
        html: `
          <h4>202 · pedido aceito</h4>
          ${blocoCodigo(JSON.stringify({
            status: 'aceito', mensagem: 'Cálculo na fila.', posicao_na_fila: 1, acompanhar_em: `${API}/calculos/${idReal}`,
            execucao: { id: idReal, status: 'na_fila', modo: null, navegador: 'oculto', planilha_base: c.base, planilha_verbas: c.verbas, solicitante: 'sap', origem: 'tarefas-jrs', criado_em: '2026-09-25T17:14:01', arquivos: [] },
          }, null, 2))}
          <h4>200 · Idempotency-Key repetida</h4>
          <p>Devolve a execução já existente com <code>"status": "existente"</code>. <strong>Nenhum cálculo novo é criado</strong>; a tela deve dizer "já foi pedido".</p>
          <h4>GET /calculos/{id} · concluído</h4>
          ${blocoCodigo(JSON.stringify({
            execucao: {
              id: idReal, status: 'concluido', modo: 'completo', navegador: 'oculto', mensagem: 'Cálculo concluído.', erro: null,
              arquivos: [c.base.replace(/[^\\/]+$/, '') + '03 Automação\\PROCESSO_00001234520245060001_CALCULO_15_DATA_25092026_HORA_172512.PJC',
                c.base.replace(/[^\\/]+$/, '') + '03 Automação\\Relatório de Cálculo - FULANO DE TAL.pdf'],
              criado_em: '2026-09-25T17:14:01', iniciado_em: '2026-09-25T17:14:01', concluido_em: '2026-09-25T17:26:40', duracao_seg: 759,
              log: [{ seq: 1, hora: '17:14:05', mensagem: '- Horário Inicial: 17:14:05' }], log_ultimo_seq: 1,
            },
          }, null, 2))}
          <h4>Envelope de erro (todas as rotas)</h4>
          ${blocoCodigo(JSON.stringify({ status: 'erro', erro: { codigo: 'parametro_invalido', mensagem: "'planilha_base' não foi encontrada: C:\\Testes\\x.xlsb" } }, null, 2))}
          ${tabela(['HTTP', 'Código', 'Quando'], [
            ['400', '<code>parametro_invalido</code>', 'JSON inválido, planilha inexistente, extensão errada, fora das pastas permitidas, mesmo arquivo nos dois campos, <code>navegador</code> inválido.'],
            ['400', '<code>lancamentos_invalido</code>', '<code>.json</code> ilegível, contrato de outra versão, ou valores fora das listas do PJe-Calc. Vem com <code>erros: [{campo, valor, mensagem, aceitos}]</code>.'],
            ['400', '<code>lancamentos_incompleto</code>', 'Pedido sem planilha base cujo <code>.json</code> não traz o mínimo (reclamante, reclamado, UF, município, admissão, ajuizamento). Vem com <code>faltando</code>.'],
            ['401', '<code>nao_autorizado</code>', 'Token ausente ou errado.'],
            ['404', '<code>nao_encontrado</code> / <code>rota_inexistente</code>', 'Execução ou rota inexistente.'],
            ['409', '<code>em_execucao</code>', 'Cancelar algo que já começou.'],
            ['409', '<code>ja_finalizada</code>', 'Cancelar algo que já terminou.'],
            ['404', '<code>sem_captura</code>', 'Pedir a captura de uma execução que não falhou ou não tem imagem.'],
            ['410', '<code>arquivo_indisponivel</code>', 'O arquivo ou a captura foi movido ou apagado do local registrado.'],
            ['413', '<code>corpo_grande_demais</code>', 'Corpo acima de 64 KB.'],
            ['500', '<code>erro_interno</code>', 'Falha do serviço. Veja o log em <code>logs\\</code>.'],
          ])}
          <h4>Falha da automação</h4>
          <p>Não é erro HTTP: a execução termina com <code>status: "falhou"</code>, o motivo em <code>mensagem</code>
            (por exemplo, o texto do alerta da automação) e, se houver, o traceback em <code>erro</code>.</p>`,
      },
    ];
  }

  function abrirDocumentacao() {
    const secoes = secoesDocumentacao();
    const abas = $('#docs-abas');
    const corpo = $('#docs-corpo');
    const mostrar = (id) => {
      const secao = secoes.find((s) => s.id === id) || secoes[0];
      abas.querySelectorAll('.aba').forEach((a) => a.setAttribute('aria-selected', String(a.dataset.aba === secao.id)));
      corpo.innerHTML = secao.html;
      corpo.scrollTop = 0;
      guardar('pjecalc_docs_aba', secao.id);
    };
    abas.innerHTML = secoes.map((s) => `<button class="aba" role="tab" type="button" data-aba="${esc(s.id)}">${esc(s.titulo)}</button>`).join('');
    abas.onclick = (ev) => { const aba = ev.target.closest('.aba'); if (aba) mostrar(aba.dataset.aba); };
    corpo.onclick = (ev) => {
      const botao = ev.target.closest('.copiar');
      if (botao) copiar(botao.nextElementSibling.textContent, botao);
    };
    mostrar(ler('pjecalc_docs_aba') || 'visao');
    abrirModal('#modal-docs');
  }

  // ---------- eventos ----------
  function ligarEventos() {
    $('#token').value = ler('pjecalc_token');
    $('#token').addEventListener('change', () => { guardar('pjecalc_token', $('#token').value.trim()); atualizarTudo(); });

    ['#f-situacao', '#f-modo', '#f-de', '#f-ate', '#f-limite'].forEach((s) => $(s).addEventListener('change', filtrosMudaram));
    $('#f-busca').addEventListener('input', () => {
      clearTimeout(estado.buscaTimer);
      estado.buscaTimer = setTimeout(filtrosMudaram, 350);
    });
    $('#f-limpar').addEventListener('click', () => {
      ['#f-situacao', '#f-modo', '#f-busca', '#f-de', '#f-ate'].forEach((s) => { $(s).value = ''; });
      filtrosMudaram();
    });

    $('#cards').addEventListener('click', (ev) => {
      const alvo = ev.target.closest('[data-filtro]');
      if (!alvo) return;
      $('#f-situacao').value = $('#f-situacao').value === alvo.dataset.filtro ? '' : alvo.dataset.filtro;
      filtrosMudaram();
    });
    $('#cards').addEventListener('keydown', (ev) => {
      if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.matches('[data-filtro]')) { ev.preventDefault(); ev.target.click(); }
    });

    $('#pag-primeira').addEventListener('click', () => irParaPagina(1));
    $('#pag-anterior').addEventListener('click', () => irParaPagina(estado.pagina - 1));
    $('#pag-proxima').addEventListener('click', () => irParaPagina(estado.pagina + 1));
    $('#pag-ultima').addEventListener('click', () => irParaPagina(estado.paginas));

    const tratarAcao = (ev) => {
      const baixar = ev.target.closest('[data-baixar]');
      if (baixar) {
        baixarArquivo(baixar.dataset.baixar, baixar.dataset.indice, baixar.dataset.nome, baixar);
        return true;
      }
      const captura = ev.target.closest('[data-captura]');
      if (captura) {
        abrirCaptura(captura.dataset.captura);
        return true;
      }
      const consoleBotao = ev.target.closest('[data-console]');
      if (consoleBotao) {
        abrirConsole(consoleBotao.dataset.console);
        return true;
      }
      return false;
    };
    $('#console-copiar').addEventListener('click', (ev) => copiar($('#console-log').textContent, ev.currentTarget));
    $('#console-seguir').addEventListener('change', () => {
      if ($('#console-seguir').checked) $('#console-log').scrollTop = $('#console-log').scrollHeight;
    });
    $('#linhas').addEventListener('click', (ev) => {
      if (tratarAcao(ev)) return;
      const tr = ev.target.closest('tr[data-id]');
      if (tr) abrirDetalhe(tr.dataset.id);
    });
    $('#d-arquivos').addEventListener('click', tratarAcao);
    $('#d-captura').addEventListener('click', () => abrirCaptura(estado.selecionado));
    $('#captura-baixar').addEventListener('click', async () => {
      const modal = $('#modal-captura');
      const { blob } = await urlDaCaptura(modal.dataset.id);
      salvarBlob(blob, modal.dataset.nome);
    });
    $('#captura-nova-aba').addEventListener('click', () => window.open($('#captura-img').src, '_blank'));
    $('#d-fechar').addEventListener('click', fecharDetalhe);
    $('#d-cancelar').addEventListener('click', cancelarSelecionado);

    $('#btn-novo').addEventListener('click', () => {
      if (!$('#novo-json').value.trim()) $('#novo-json').value = modeloPedido('completo');
      $('#novo-resultado').hidden = true;
      validarJson();
      abrirModal('#modal-novo');
    });
    document.querySelectorAll('[data-modelo]').forEach((b) => b.addEventListener('click', () => {
      $('#novo-json').value = modeloPedido(b.dataset.modelo);
      validarJson();
    }));
    $('#novo-formatar').addEventListener('click', () => {
      const pedido = validarJson();
      if (pedido) $('#novo-json').value = JSON.stringify(pedido, null, 2);
    });
    $('#novo-json').addEventListener('input', validarJson);
    document.querySelectorAll('input[name="novo-navegador"]').forEach((r) => r.addEventListener('change', () => aplicarNavegadorNoJson(r.value)));
    $('#novo-enviar').addEventListener('click', enviarPedido);

    $('#btn-docs').addEventListener('click', abrirDocumentacao);
    document.querySelectorAll('[data-fechar]').forEach((b) => b.addEventListener('click', fecharModais));
    document.querySelectorAll('.modal-fundo').forEach((m) => m.addEventListener('click', (ev) => { if (ev.target === m) fecharModais(); }));
    document.addEventListener('keydown', (ev) => {
      if (ev.key !== 'Escape') return;
      if (document.querySelector('.modal-fundo:not([hidden])')) fecharModais();
      else if (!$('#gaveta').hidden) fecharDetalhe();
    });
    document.addEventListener('visibilitychange', () => { if (!document.hidden && $('#auto').checked) atualizarTudo(); });
  }

  ligarEventos();
  atualizarTudo();
  agendarLista();
})();
