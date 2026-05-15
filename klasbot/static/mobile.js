const state = {
  teacher: null,
  csrfToken: '',
  outputs: [],
  currentOutput: null,
  currentInputs: null,
  editing: false,
  conflictOutput: null,
  teachingAids: [],
  currentTeachingAid: null,
  teachingAidDraft: null,
};

const formats = {
  lesson_plan: ['DLP', 'SDLP', 'DLL'],
  assessment: ['quiz', 'exam'],
};

const els = {
  pairView: document.getElementById('pair-view'),
  appView: document.getElementById('app-view'),
  teacherLabel: document.getElementById('teacher-label'),
  logoutButton: document.getElementById('logout-button'),
  draftTab: document.getElementById('draft-tab'),
  libraryTab: document.getElementById('library-tab'),
  generateTab: document.getElementById('generate-tab'),
  refreshButton: document.getElementById('refresh-button'),
  connectionDot: document.getElementById('connection-dot'),
  connectionText: document.getElementById('connection-text'),
  generatePanel: document.getElementById('generate-panel'),
  draftPanel: document.getElementById('draft-panel'),
  libraryPanel: document.getElementById('library-panel'),
  generateForm: document.getElementById('generate-form'),
  kind: document.getElementById('kind'),
  format: document.getElementById('format'),
  gradeLevel: document.getElementById('grade-level'),
  subject: document.getElementById('subject'),
  quarter: document.getElementById('quarter'),
  topic: document.getElementById('topic'),
  weekNumber: document.getElementById('week-number'),
  resources: document.getElementById('resources'),
  resourcesField: document.getElementById('resources-field'),
  draftTitle: document.getElementById('draft-title'),
  draftMeta: document.getElementById('draft-meta'),
  draftPreview: document.getElementById('draft-preview'),
  editor: document.getElementById('editor'),
  editToggle: document.getElementById('edit-toggle'),
  saveButton: document.getElementById('save-button'),
  shareButton: document.getElementById('share-button'),
  newButton: document.getElementById('new-button'),
  sharePanel: document.getElementById('share-panel'),
  shareQr: document.getElementById('share-qr'),
  shareLink: document.getElementById('share-link'),
  shareExpiry: document.getElementById('share-expiry'),
  teachingAidsPanel: document.getElementById('teaching-aids-panel'),
  teachingAidsStatus: document.getElementById('teaching-aids-status'),
  teachingAidRequest: document.getElementById('teaching-aid-request'),
  teachingAidsList: document.getElementById('teaching-aids-list'),
  teachingAidEditorPanel: document.getElementById('teaching-aid-editor-panel'),
  teachingAidTitle: document.getElementById('teaching-aid-title'),
  teachingAidEditor: document.getElementById('teaching-aid-editor'),
  teachingAidPreview: document.getElementById('teaching-aid-preview'),
  saveTeachingAid: document.getElementById('save-teaching-aid'),
  shareTeachingAid: document.getElementById('share-teaching-aid'),
  deleteTeachingAid: document.getElementById('delete-teaching-aid'),
  conflictPanel: document.getElementById('conflict-panel'),
  reloadConflict: document.getElementById('reload-conflict'),
  overwriteConflict: document.getElementById('overwrite-conflict'),
  librarySummary: document.getElementById('library-summary'),
  librarySearch: document.getElementById('library-search'),
  libraryList: document.getElementById('library-list'),
  statusLine: document.getElementById('status-line'),
};

function setStatus(message, isError = false) {
  els.statusLine.textContent = message;
  els.statusLine.style.color = isError ? 'var(--danger)' : 'var(--accent-strong)';
}

function showPairView() {
  els.pairView.classList.remove('hidden');
  els.appView.classList.add('hidden');
}

function showApp() {
  els.pairView.classList.add('hidden');
  els.appView.classList.remove('hidden');
  els.teacherLabel.textContent = `${state.teacher.name} | mobile`;
}

function normalizeLineEndings(value) {
  return value.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

async function api(path, options = {}) {
  const method = String(options.method || 'GET').toUpperCase();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers['X-Klasbot-CSRF'] = state.csrfToken;
  }
  const response = await fetch(path, {
    credentials: 'same-origin',
    ...options,
    headers,
  });
  if (!response.ok) {
    let detail = response.statusText;
    let payload = null;
    try {
      payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep status text for non-JSON responses.
    }
    const error = new Error(detail);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return response.json();
}

function updateFormats() {
  const selected = els.format.value;
  els.format.innerHTML = '';
  formats[els.kind.value].forEach((formatName) => {
    const option = document.createElement('option');
    option.value = formatName;
    option.textContent = formatName.toUpperCase();
    els.format.appendChild(option);
  });
  if ([...els.format.options].some((option) => option.value === selected)) {
    els.format.value = selected;
  }
  updateResourcesVisibility();
}

function updateResourcesVisibility() {
  const showResources = els.kind.value === 'assessment';
  els.resourcesField?.classList.toggle('hidden', !showResources);
  if (!showResources) {
    els.resources.value = '';
  }
}

function collectInputs() {
  const grade = els.gradeLevel.value.trim();
  const resources = els.kind.value === 'assessment'
    ? els.resources.value.split(',').map((item) => item.trim()).filter(Boolean)
    : [];
  return {
    kind: els.kind.value,
    format: els.format.value,
    subject: els.subject.value.trim(),
    topic: els.topic.value.trim(),
    quarter: els.quarter.value ? Number(els.quarter.value) : null,
    week_number: els.weekNumber.value ? Number(els.weekNumber.value) : null,
    grade_level: grade,
    grade_levels: grade ? [grade] : [],
    resources,
  };
}

function setFormFromInputs(inputs) {
  if (!inputs) return;
  els.kind.value = inputs.kind || 'lesson_plan';
  updateFormats();
  els.format.value = inputs.format || els.format.value;
  els.gradeLevel.value = inputs.grade_level || inputs.grade_levels?.[0] || '';
  els.subject.value = inputs.subject || '';
  els.quarter.value = inputs.quarter ? String(inputs.quarter) : '';
  els.topic.value = inputs.topic || '';
  els.weekNumber.value = inputs.week_number ? String(inputs.week_number) : '';
  els.resources.value = (inputs.resources || []).join(', ');
  updateResourcesVisibility();
}

function setEditorValue(value) {
  els.editor.value = normalizeLineEndings(value || '');
  renderDraftPreview();
}

function setActivePanel(name) {
  els.draftPanel.classList.toggle('hidden', name !== 'draft');
  els.libraryPanel.classList.toggle('hidden', name !== 'library');
  els.generatePanel.classList.toggle('hidden', name !== 'generate');
  els.draftTab.classList.toggle('mb-tab--on', name === 'draft');
  els.libraryTab.classList.toggle('mb-tab--on', name === 'library');
  els.generateTab.classList.toggle('mb-tab--on', name === 'generate');
}

function setEditing(editing) {
  state.editing = editing;
  els.editor.classList.toggle('hidden', !editing);
  els.draftPreview.classList.toggle('hidden', editing);
  els.editToggle.textContent = editing ? 'Preview' : 'Edit';
  if (!editing) renderDraftPreview();
}

async function openOutput(output) {
  state.currentOutput = output;
  state.currentInputs = output.inputs;
  state.conflictOutput = null;
  els.conflictPanel.classList.add('hidden');
  setFormFromInputs(output.inputs);
  setEditorValue(output.content_md);
  els.draftTitle.textContent = output.topic || 'Saved Output';
  const week = output.week_number || output.inputs?.week_number;
  els.draftMeta.textContent = `${output.subject || 'No subject'} | ${output.format || output.kind} | ${week ? `Week ${week} | ` : ''}${output.updated_at}`;
  setEditing(false);
  setActivePanel('draft');
  await loadTeachingAids();
  setStatus('Saved output opened.');
}

function newDraft() {
  state.currentOutput = null;
  state.currentInputs = null;
  state.conflictOutput = null;
  resetTeachingAids();
  els.conflictPanel.classList.add('hidden');
  setEditorValue('');
  els.draftTitle.textContent = 'Current Draft';
  els.draftMeta.textContent = 'Generate or open a saved output.';
  setEditing(false);
  setActivePanel('generate');
  setStatus('New draft ready.');
}

function markdownToHtml(markdown) {
  const lines = normalizeLineEndings(markdown).split('\n');
  const blocks = [];
  let paragraph = [];
  let list = null;

  function flushParagraph() {
    if (paragraph.length) {
      blocks.push(`<p>${formatInline(paragraph.join(' '))}</p>`);
      paragraph = [];
    }
  }

  function closeList() {
    if (list) {
      blocks.push(`</${list}>`);
      list = null;
    }
  }

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line) {
      flushParagraph();
      closeList();
      continue;
    }
    if (isTableStart(lines, index)) {
      flushParagraph();
      closeList();
      const table = collectTable(lines, index);
      blocks.push(renderMarkdownTable(table.rows));
      index = table.nextIndex - 1;
      continue;
    }
    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      closeList();
      blocks.push(`<h${heading[1].length}>${formatInline(heading[2])}</h${heading[1].length}>`);
      continue;
    }
    const unordered = line.match(/^[-*]\s+(.+)$/);
    if (unordered) {
      flushParagraph();
      if (list !== 'ul') {
        closeList();
        blocks.push('<ul>');
        list = 'ul';
      }
      blocks.push(`<li>${formatInline(unordered[1])}</li>`);
      continue;
    }
    const ordered = line.match(/^\d+[.)]\s+(.+)$/);
    if (ordered) {
      flushParagraph();
      if (list !== 'ol') {
        closeList();
        blocks.push('<ol>');
        list = 'ol';
      }
      blocks.push(`<li>${formatInline(ordered[1])}</li>`);
      continue;
    }
    closeList();
    paragraph.push(line);
  }
  flushParagraph();
  closeList();
  return blocks.join('\n');
}

function isTableStart(lines, index) {
  return hasTablePipes(lines[index]) && index + 1 < lines.length && isTableSeparator(lines[index + 1]);
}

function hasTablePipes(line) {
  return (line.match(/\|/g) || []).length >= 2;
}

function isTableSeparator(line) {
  return splitTableRow(line).every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function splitTableRow(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
}

function collectTable(lines, startIndex) {
  const rows = [splitTableRow(lines[startIndex])];
  let index = startIndex + 2;
  while (index < lines.length && lines[index].trim() && hasTablePipes(lines[index])) {
    rows.push(splitTableRow(lines[index]));
    index += 1;
  }
  return { rows, nextIndex: index };
}

function renderMarkdownTable(rows) {
  const headers = rows[0];
  const bodyRows = rows.slice(1);
  return `<table><thead><tr>${headers.map((cell) => `<th>${formatInline(cell)}</th>`).join('')}</tr></thead><tbody>${bodyRows.map((row) => `<tr>${headers.map((_, index) => `<td>${formatInline(row[index] || '')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}

function formatInline(value) {
  return splitMathSegments(String(value)).map((segment) => {
    if (segment.type === 'math') {
      return renderMathSegment(segment.content, segment.display);
    }
    return formatTextInline(segment.content);
  }).join('');
}

function formatTextInline(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>');
}

function splitMathSegments(value) {
  const segments = [];
  let cursor = 0;
  const delimiters = [
    { open: '$$', close: '$$', display: true },
    { open: '\\[', close: '\\]', display: true },
    { open: '\\(', close: '\\)', display: false },
    { open: '$', close: '$', display: false },
  ];
  while (cursor < value.length) {
    const next = delimiters
      .map((delimiter) => ({ delimiter, index: value.indexOf(delimiter.open, cursor) }))
      .filter((item) => item.index >= 0 && !isEscaped(value, item.index))
      .sort((a, b) => a.index - b.index || b.delimiter.open.length - a.delimiter.open.length)[0];
    if (!next) {
      segments.push({ type: 'text', content: value.slice(cursor) });
      break;
    }
    if (next.index > cursor) {
      segments.push({ type: 'text', content: value.slice(cursor, next.index) });
    }
    const start = next.index + next.delimiter.open.length;
    const end = findClosingDelimiter(value, next.delimiter.close, start);
    if (end < 0) {
      segments.push({ type: 'text', content: fallbackLatexText(value.slice(next.index)) });
      break;
    }
    segments.push({
      type: 'math',
      content: value.slice(start, end),
      display: next.delimiter.display,
    });
    cursor = end + next.delimiter.close.length;
  }
  return segments;
}

function findClosingDelimiter(value, delimiter, start) {
  let index = value.indexOf(delimiter, start);
  while (index >= 0 && isEscaped(value, index)) {
    index = value.indexOf(delimiter, index + delimiter.length);
  }
  return index;
}

function isEscaped(value, index) {
  let slashCount = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === '\\'; cursor -= 1) {
    slashCount += 1;
  }
  return slashCount % 2 === 1;
}

function renderMathSegment(content, displayMode) {
  const source = normalizeLatex(content);
  if (window.katex && source) {
    try {
      return window.katex.renderToString(source, {
        displayMode,
        throwOnError: false,
        strict: 'ignore',
        output: 'html',
      });
    } catch (error) {
      return `<span class="math-fallback">${escapeHtml(fallbackLatexText(source))}</span>`;
    }
  }
  return `<span class="math-fallback">${escapeHtml(fallbackLatexText(source))}</span>`;
}

function normalizeLatex(value) {
  return String(value || '')
    .replace(/\\\\/g, '\\')
    .replace(/\s+/g, ' ')
    .trim();
}

function fallbackLatexText(value) {
  return normalizeLatex(value)
    .replace(/\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g, '$1/$2')
    .replace(/\\sqrt\s*\{([^{}]+)\}/g, 'sqrt($1)')
    .replace(/\\triangle\b/g, 'triangle ')
    .replace(/\\angle\b/g, 'angle ')
    .replace(/\\times\b/g, ' x ')
    .replace(/\\cdot\b/g, ' · ')
    .replace(/\\div\b/g, ' / ')
    .replace(/\\leq?\b/g, ' <= ')
    .replace(/\\geq?\b/g, ' >= ')
    .replace(/\\neq\b/g, ' != ')
    .replace(/\\approx\b/g, ' approximately ')
    .replace(/\\degree\b/g, ' degrees')
    .replace(/\\[a-zA-Z]+/g, '')
    .replace(/[{}$]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function renderDraftPreview() {
  const markdown = els.editor.value.trim();
  els.draftPreview.innerHTML = markdown ? markdownToHtml(markdown) : '<p>Generated draft preview appears here.</p>';
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function outputTypeLabel(output) {
  if (output.kind === 'lesson_plan') return 'Lesson Plan';
  return (output.format || 'Assessment').replace(/^\w/, (letter) => letter.toUpperCase());
}

function renderLibrary() {
  const query = els.librarySearch.value.trim().toLowerCase();
  const outputs = state.outputs.filter((output) => {
    const haystack = [
      output.topic,
      output.subject,
      output.format,
      output.kind,
      output.week_number,
      output.inputs?.week_number,
      output.updated_at,
      ...(output.grade_levels || []),
    ].filter(Boolean).join(' ').toLowerCase();
    return !query || haystack.includes(query);
  });
  els.librarySummary.textContent = `${outputs.length} of ${state.outputs.length} saved output${state.outputs.length === 1 ? '' : 's'}`;
  els.libraryList.innerHTML = outputs.length ? '' : '<div class="mb-library-item"><p>No saved outputs yet.</p></div>';
  outputs.forEach((output) => {
    const item = document.createElement('article');
    item.className = 'mb-library-item';
    item.innerHTML = `
      <div>
        <h3>${escapeHtml(output.topic || 'Untitled')}</h3>
        <p>${escapeHtml(outputTypeLabel(output))} | ${escapeHtml(output.subject || 'No subject')} | ${escapeHtml(output.week_number || output.inputs?.week_number ? `Week ${output.week_number || output.inputs?.week_number}` : 'No week')} | ${escapeHtml(output.updated_at)}</p>
      </div>
      <div class="mb-library-actions">
        <button class="mb-primary" type="button" data-action="open">Open</button>
        <button class="mb-secondary" type="button" data-action="share">Share</button>
      </div>
    `;
    item.querySelector('[data-action="open"]').addEventListener('click', () => openOutput(output).catch((error) => setStatus(error.message, true)));
    item.querySelector('[data-action="share"]').addEventListener('click', async () => {
      await openOutput(output);
      await shareDraft();
    });
    els.libraryList.appendChild(item);
  });
}

async function loadLibrary() {
  const data = await api('/api/library');
  state.outputs = data.outputs;
  renderLibrary();
}

async function checkConnection() {
  try {
    const data = await api('/api/ollama/status');
    els.connectionDot.className = `mb-dot ${data.ok ? 'mb-dot--ok' : 'mb-dot--bad'}`;
    els.connectionText.textContent = data.ok && data.model_available ? `Kiosk ready | ${data.model}` : 'Kiosk connected | model unavailable';
  } catch (error) {
    els.connectionDot.className = 'mb-dot mb-dot--bad';
    els.connectionText.textContent = error.message || 'Kiosk unavailable';
  }
}

async function streamGenerate(inputs) {
  state.currentOutput = null;
  state.currentInputs = inputs;
  resetTeachingAids();
  els.sharePanel.classList.add('hidden');
  setActivePanel('draft');
  setEditing(false);
  setEditorValue('');
  els.draftTitle.textContent = inputs.topic || 'Generated Draft';
  els.draftMeta.textContent = `${inputs.subject || 'No subject'} | ${inputs.format} | ${inputs.week_number ? `Week ${inputs.week_number}` : 'No week'}`;
  setStatus('Generating draft...');

  const params = new URLSearchParams();
  Object.entries(inputs).forEach(([key, value]) => {
    if (key === 'grade_levels' || key === 'resources') {
      value.forEach((item) => params.append(key, item));
    } else if (value !== null && value !== undefined && value !== '') {
      params.set(key, value);
    }
  });

  const source = new EventSource(`/api/generate/stream?${params.toString()}`);
  source.onmessage = (event) => {
    els.editor.value += event.data;
    renderDraftPreview();
  };
  source.addEventListener('done', () => {
    source.close();
    setStatus('Draft ready. Save to sync with the kiosk.');
  });
  source.addEventListener('error', () => {
    source.close();
    setStatus('Generation stopped. Check kiosk connection.', true);
  });
}

async function saveDraft(force = false) {
  const content = normalizeLineEndings(els.editor.value);
  if (!content.trim()) {
    setStatus('Nothing to save yet.', true);
    return;
  }
  const inputs = state.currentInputs || collectInputs();
  try {
    if (state.currentOutput) {
      const data = await api(`/api/library/${state.currentOutput.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          content_md: content,
          expected_updated_at: state.currentOutput.updated_at,
          force,
        }),
      });
      state.currentOutput = data.output;
    } else {
      const data = await api('/api/library', {
        method: 'POST',
        body: JSON.stringify({ ...inputs, inputs, content_md: content }),
      });
      state.currentOutput = data.output;
    }
    state.currentInputs = state.currentOutput.inputs;
    els.conflictPanel.classList.add('hidden');
    await loadLibrary();
    await openOutput(state.currentOutput);
    setStatus('Saved and synced with kiosk.');
  } catch (error) {
    if (error.status === 409 && error.payload?.output) {
      state.conflictOutput = error.payload.output;
      els.conflictPanel.classList.remove('hidden');
      setStatus('This draft changed on another device.', true);
      return;
    }
    throw error;
  }
}

async function shareDraft() {
  if (!state.currentOutput) {
    await saveDraft();
  }
  if (!state.currentOutput) return;
  const data = await api(`/api/library/${state.currentOutput.id}/share`, {
    method: 'POST',
    body: JSON.stringify({ expires_minutes: 15 }),
  });
  els.shareQr.src = data.qr_url;
  els.shareLink.href = data.url;
  els.shareLink.textContent = data.url;
  els.shareExpiry.textContent = `PDF link expires at ${data.expires_at}.`;
  els.sharePanel.classList.remove('hidden');
  setStatus('Share link ready.');
}

const teachingAidLabels = {
  worked_example: 'Worked Example',
  guided_practice: 'Guided Practice',
  answer_key: 'Answer Key',
  board_notes: 'Board Notes',
  remediation: 'Remediation',
};

function teachingAidLabel(type) {
  return teachingAidLabels[type] || 'Teaching Aid';
}

function resetTeachingAids() {
  state.teachingAids = [];
  state.currentTeachingAid = null;
  state.teachingAidDraft = null;
  if (els.teachingAidRequest) els.teachingAidRequest.value = '';
  renderTeachingAids();
}

async function loadTeachingAids() {
  if (!state.currentOutput || state.currentOutput.kind !== 'lesson_plan') {
    resetTeachingAids();
    return;
  }
  const data = await api(`/api/library/${state.currentOutput.id}/teaching-aids`);
  state.teachingAids = data.teaching_aids || [];
  renderTeachingAids();
}

function renderTeachingAids() {
  const savedLesson = Boolean(state.currentOutput);
  const isLessonPlan = (state.currentInputs?.kind || els.kind.value) === 'lesson_plan';
  els.teachingAidsPanel.classList.toggle('hidden', !isLessonPlan);
  els.teachingAidsStatus.textContent = savedLesson
    ? 'Generate aids attached to this lesson.'
    : 'Save the lesson to generate aids.';
  document.querySelectorAll('[data-aid-type]').forEach((button) => {
    button.disabled = !savedLesson || !isLessonPlan;
  });
  els.teachingAidsList.innerHTML = '';
  if (!savedLesson || !isLessonPlan) {
    els.teachingAidEditorPanel.classList.add('hidden');
    return;
  }
  if (!state.teachingAids.length) {
    els.teachingAidsList.innerHTML = '<div class="mb-library-item"><p>No Teaching Aids yet.</p></div>';
  } else {
    state.teachingAids.forEach((aid) => {
      const item = document.createElement('article');
      item.className = 'mb-library-item';
      item.innerHTML = `
        <div>
          <h3>${escapeHtml(aid.title || teachingAidLabel(aid.aid_type))}</h3>
          <p>${escapeHtml(teachingAidLabel(aid.aid_type))} | ${escapeHtml(aid.updated_at)}</p>
        </div>
        <div class="mb-library-actions"><button class="mb-primary" type="button">Open</button></div>
      `;
      item.querySelector('button').addEventListener('click', () => openTeachingAid(aid));
      els.teachingAidsList.appendChild(item);
    });
  }
  if (state.currentTeachingAid || state.teachingAidDraft) {
    renderTeachingAidEditor();
  } else {
    els.teachingAidEditorPanel.classList.add('hidden');
  }
}

function openTeachingAid(aid) {
  state.currentTeachingAid = aid;
  state.teachingAidDraft = null;
  renderTeachingAidEditor();
}

function renderTeachingAidEditor() {
  const aid = state.teachingAidDraft || state.currentTeachingAid;
  if (!aid) {
    els.teachingAidEditorPanel.classList.add('hidden');
    return;
  }
  els.teachingAidEditorPanel.classList.remove('hidden');
  els.teachingAidTitle.value = aid.title || teachingAidLabel(aid.aid_type);
  els.teachingAidEditor.value = normalizeLineEndings(aid.content_md || '');
  renderTeachingAidPreview();
  els.deleteTeachingAid.disabled = !state.currentTeachingAid;
  els.shareTeachingAid.disabled = !state.currentTeachingAid;
}

function renderTeachingAidPreview() {
  const markdown = normalizeLineEndings(els.teachingAidEditor.value);
  els.teachingAidPreview.innerHTML = markdown.trim()
    ? markdownToHtml(markdown)
    : '<p>Generated Teaching Aid preview appears here.</p>';
}

async function readSseStream(response, onData) {
  if (!response.ok || !response.body) {
    throw new Error('Generation failed');
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';
    events.forEach((eventText) => {
      const lines = eventText.split('\n');
      const eventName = lines.find((line) => line.startsWith('event: '))?.slice(7);
      const data = lines
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.slice(5).replace(/^ /, ''))
        .join('\n');
      if (eventName !== 'done') onData(data);
    });
  }
}

async function generateTeachingAid(aidType) {
  if (!state.currentOutput) {
    await saveDraft();
  }
  if (!state.currentOutput) return;
  const title = teachingAidLabel(aidType);
  state.currentTeachingAid = null;
  state.teachingAidDraft = { aid_type: aidType, title, source_section: '', content_md: '' };
  renderTeachingAidEditor();
  setStatus(`Generating ${title}...`);
  const response = await fetch(`/api/library/${state.currentOutput.id}/teaching-aids/stream`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      ...(state.csrfToken ? { 'X-Klasbot-CSRF': state.csrfToken } : {}),
    },
    body: JSON.stringify({
      aid_type: aidType,
      source_section: '',
      custom_request: els.teachingAidRequest.value.trim(),
    }),
  });
  await readSseStream(response, (chunk) => {
    state.teachingAidDraft.content_md += normalizeLineEndings(chunk || '');
    els.teachingAidEditor.value = state.teachingAidDraft.content_md;
    renderTeachingAidPreview();
  });
  setStatus(`${title} ready. Edit and save the aid.`);
}

async function saveTeachingAid() {
  const aid = state.currentTeachingAid || state.teachingAidDraft;
  if (!aid || !els.teachingAidEditor.value.trim()) {
    setStatus('No Teaching Aid to save.', true);
    return;
  }
  if (state.currentTeachingAid) {
    const data = await api(`/api/library/${state.currentOutput.id}/teaching-aids/${state.currentTeachingAid.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: els.teachingAidTitle.value.trim() || teachingAidLabel(aid.aid_type),
        content_md: normalizeLineEndings(els.teachingAidEditor.value),
      }),
    });
    state.currentTeachingAid = data.teaching_aid;
  } else {
    const data = await api(`/api/library/${state.currentOutput.id}/teaching-aids`, {
      method: 'POST',
      body: JSON.stringify({
        aid_type: aid.aid_type,
        title: els.teachingAidTitle.value.trim() || teachingAidLabel(aid.aid_type),
        source_section: '',
        custom_request: els.teachingAidRequest.value.trim(),
        content_md: normalizeLineEndings(els.teachingAidEditor.value),
      }),
    });
    state.currentTeachingAid = data.teaching_aid;
    state.teachingAidDraft = null;
  }
  await loadTeachingAids();
  openTeachingAid(state.currentTeachingAid);
  setStatus('Teaching Aid saved.');
}

async function shareTeachingAid() {
  if (!state.currentTeachingAid) {
    await saveTeachingAid();
  }
  if (!state.currentTeachingAid) return;
  const data = await api(`/api/library/${state.currentOutput.id}/teaching-aids/${state.currentTeachingAid.id}/share`, {
    method: 'POST',
    body: JSON.stringify({ expires_minutes: 15 }),
  });
  els.shareQr.src = data.qr_url;
  els.shareLink.href = data.url;
  els.shareLink.textContent = data.url;
  els.shareExpiry.textContent = `PDF link expires at ${data.expires_at}.`;
  els.sharePanel.classList.remove('hidden');
  setStatus('Teaching Aid share link ready.');
}

async function deleteTeachingAid() {
  if (!state.currentTeachingAid) return;
  await api(`/api/library/${state.currentOutput.id}/teaching-aids/${state.currentTeachingAid.id}`, { method: 'DELETE' });
  state.currentTeachingAid = null;
  await loadTeachingAids();
  setStatus('Teaching Aid deleted.');
}

async function bootstrap() {
  updateFormats();
  try {
    const data = await api('/api/me');
    state.teacher = data.teacher;
    state.csrfToken = data.csrf_token || '';
    showApp();
    await Promise.all([loadLibrary(), checkConnection()]);
  } catch {
    showPairView();
  }
}

els.kind.addEventListener('change', () => {
  updateFormats();
  renderTeachingAids();
});
els.draftTab.addEventListener('click', () => setActivePanel('draft'));
els.libraryTab.addEventListener('click', () => {
  setActivePanel('library');
  loadLibrary().catch((error) => setStatus(error.message, true));
});
els.generateTab.addEventListener('click', () => setActivePanel('generate'));
els.refreshButton.addEventListener('click', () => Promise.all([loadLibrary(), checkConnection()]).catch((error) => setStatus(error.message, true)));
els.editToggle.addEventListener('click', () => setEditing(!state.editing));
els.editor.addEventListener('input', renderDraftPreview);
els.generateForm.addEventListener('submit', (event) => {
  event.preventDefault();
  streamGenerate(collectInputs()).catch((error) => setStatus(error.message, true));
});
els.saveButton.addEventListener('click', () => saveDraft().catch((error) => setStatus(error.message, true)));
els.shareButton.addEventListener('click', () => shareDraft().catch((error) => setStatus(error.message, true)));
els.newButton.addEventListener('click', newDraft);
document.querySelectorAll('[data-aid-type]').forEach((button) => {
  button.addEventListener('click', () => generateTeachingAid(button.dataset.aidType).catch((error) => setStatus(error.message, true)));
});
els.teachingAidEditor.addEventListener('input', () => {
  if (state.teachingAidDraft) {
    state.teachingAidDraft.content_md = normalizeLineEndings(els.teachingAidEditor.value);
  }
  renderTeachingAidPreview();
});
els.saveTeachingAid.addEventListener('click', () => saveTeachingAid().catch((error) => setStatus(error.message, true)));
els.shareTeachingAid.addEventListener('click', () => shareTeachingAid().catch((error) => setStatus(error.message, true)));
els.deleteTeachingAid.addEventListener('click', () => deleteTeachingAid().catch((error) => setStatus(error.message, true)));
els.librarySearch.addEventListener('input', renderLibrary);
els.reloadConflict.addEventListener('click', () => {
  if (state.conflictOutput) openOutput(state.conflictOutput).catch((error) => setStatus(error.message, true));
});
els.overwriteConflict.addEventListener('click', () => saveDraft(true).catch((error) => setStatus(error.message, true)));
els.logoutButton.addEventListener('click', async () => {
  await api('/api/auth/logout', { method: 'POST' });
  state.teacher = null;
  state.csrfToken = '';
  showPairView();
});

renderDraftPreview();
renderTeachingAids();
bootstrap();
