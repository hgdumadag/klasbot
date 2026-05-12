const state = {
  teacher: null,
  currentInputs: null,
  currentOutputId: null,
  currentOutput: null,
  activeWorkspace: 'draft',
  draftView: 'preview',
  libraryOutputs: [],
  libraryFiltersCollapsed: false,
  generating: false,
  curriculumCache: new Map(),
  lessonPlanFormats: [],
  teachingAids: [],
  currentTeachingAid: null,
  teachingAidDraft: null,
  csrfToken: '',
};

const formats = {
  lesson_plan: ['DLP', 'SDLP', 'DLL'],
  assessment: ['quiz', 'exam'],
};

const els = {
  loginView: document.getElementById('login-view'),
  appView: document.getElementById('app-view'),
  loginForm: document.getElementById('login-form'),
  loginError: document.getElementById('login-error'),
  pin: document.getElementById('pin'),
  pinPad: document.getElementById('pin-pad'),
  teacherLabel: document.getElementById('teacher-label'),
  logoutButton: document.getElementById('logout-button'),
  currentDraftButton: document.getElementById('current-draft-button'),
  libraryButton: document.getElementById('library-button'),
  adminToggle: document.getElementById('admin-toggle'),
  adminPanel: document.getElementById('admin-panel'),
  curriculumToggle: document.getElementById('curriculum-toggle'),
  curriculumPanel: document.getElementById('curriculum-panel'),
  formatAdminToggle: document.getElementById('format-admin-toggle'),
  formatAdminPanel: document.getElementById('format-admin-panel'),
  refreshFormats: document.getElementById('refresh-formats'),
  formatAdminMessage: document.getElementById('format-admin-message'),
  formatAdminSelect: document.getElementById('format-admin-select'),
  formatAdminForm: document.getElementById('format-admin-form'),
  formatAdminTitle: document.getElementById('format-admin-title'),
  formatAdminRequirements: document.getElementById('format-admin-requirements'),
  resetFormat: document.getElementById('reset-format'),
  curriculumUploadForm: document.getElementById('curriculum-upload-form'),
  curriculumList: document.getElementById('curriculum-list'),
  refreshCurriculum: document.getElementById('refresh-curriculum'),
  pacingEditor: document.getElementById('pacing-editor'),
  pacingEditorMeta: document.getElementById('pacing-editor-meta'),
  pacingForm: document.getElementById('pacing-form'),
  resetPacing: document.getElementById('reset-pacing'),
  teacherForm: document.getElementById('teacher-form'),
  teacherList: document.getElementById('teacher-list'),
  refreshTeachers: document.getElementById('refresh-teachers'),
  kind: document.getElementById('kind'),
  format: document.getElementById('format'),
  gradeLevel: document.getElementById('grade-level'),
  subject: document.getElementById('subject'),
  quarter: document.getElementById('quarter'),
  topic: document.getElementById('topic'),
  weekNumber: document.getElementById('week-number'),
  resources: document.getElementById('resources'),
  curriculumMatch: document.getElementById('curriculum-match'),
  previewPromptButton: document.getElementById('preview-prompt-button'),
  promptPreview: document.getElementById('prompt-preview'),
  generateForm: document.getElementById('generate-form'),
  editor: document.getElementById('editor'),
  saveButton: document.getElementById('save-button'),
  printButton: document.getElementById('print-button'),
  shareButton: document.getElementById('share-button'),
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
  printTeachingAid: document.getElementById('print-teaching-aid'),
  shareTeachingAid: document.getElementById('share-teaching-aid'),
  copyTeachingAid: document.getElementById('copy-teaching-aid'),
  deleteTeachingAid: document.getElementById('delete-teaching-aid'),
  statusLine: document.getElementById('status-line'),
  documentTabs: document.getElementById('document-tabs'),
  previewTab: document.getElementById('preview-tab'),
  editTab: document.getElementById('edit-tab'),
  draftViewTitle: document.getElementById('draft-view-title'),
  draftPreview: document.getElementById('draft-preview'),
  draftPanel: document.getElementById('draft-panel'),
  libraryPanel: document.getElementById('library-panel'),
  librarySearch: document.getElementById('library-search'),
  libraryTypeFilter: document.getElementById('library-type-filter'),
  librarySubjectFilter: document.getElementById('library-subject-filter'),
  libraryGradeFilter: document.getElementById('library-grade-filter'),
  libraryFormatFilter: document.getElementById('library-format-filter'),
  librarySort: document.getElementById('library-sort'),
  libraryFilterRow: document.getElementById('library-filter-row'),
  libraryFiltersToggle: document.getElementById('library-filters-toggle'),
  librarySummary: document.getElementById('library-summary'),
  libraryList: document.getElementById('library-list'),
  refreshLibrary: document.getElementById('refresh-library'),
  newLessonButton: document.getElementById('new-lesson-button'),
  documentTitle: document.getElementById('document-title'),
  documentMeta: document.getElementById('document-meta'),
  formatBadge: document.getElementById('format-badge'),
  formatTitle: document.getElementById('format-title'),
  checkOllamaButton: document.getElementById('check-ollama-button'),
  ollamaState: document.getElementById('ollama-state'),
  ollamaDetail: document.getElementById('ollama-detail'),
  statusbarOllama: document.getElementById('statusbar-ollama'),
  statusbarOllamaDot: document.getElementById('statusbar-ollama-dot'),
  systemModel: document.getElementById('system-model'),
  mobilePairButton: document.getElementById('mobile-pair-button'),
  mobilePairPanel: document.getElementById('mobile-pair-panel'),
  mobilePairQr: document.getElementById('mobile-pair-qr'),
  mobilePairLink: document.getElementById('mobile-pair-link'),
  mobilePairExpiry: document.getElementById('mobile-pair-expiry'),
};

function setStatus(message, isError = false) {
  els.statusLine.textContent = message;
  els.statusLine.style.color = isError ? 'var(--danger)' : 'var(--accent-strong)';
}

function normalizeLineEndings(value) {
  return value.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

function insertAtCursor(textarea, text) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const before = textarea.value.slice(0, start);
  const after = textarea.value.slice(end);
  textarea.value = `${before}${text}${after}`;
  const nextPosition = start + text.length;
  textarea.selectionStart = nextPosition;
  textarea.selectionEnd = nextPosition;
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
}

function setupEditorBehavior() {
  els.editor.addEventListener('input', () => {
    hideSharePanel();
    renderDraftPreview();
  });
  els.editor.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter') {
      return;
    }
    event.preventDefault();
    insertAtCursor(els.editor, '\n');
  });

  els.editor.addEventListener('paste', () => {
    requestAnimationFrame(() => {
      const normalized = normalizeLineEndings(els.editor.value);
      if (normalized !== els.editor.value) {
        const cursor = els.editor.selectionStart;
        els.editor.value = normalized;
        els.editor.selectionStart = Math.min(cursor, normalized.length);
        els.editor.selectionEnd = els.editor.selectionStart;
        renderDraftPreview();
      }
    });
  });
}

function setDraftView(view) {
  state.draftView = view;
  const isPreview = view === 'preview';
  els.previewTab.classList.toggle('tab--on', isPreview);
  els.editTab.classList.toggle('tab--on', !isPreview);
  els.draftPreview.classList.toggle('hidden', !isPreview);
  els.editor.classList.toggle('hidden', isPreview);
  els.draftViewTitle.textContent = isPreview ? 'Preview' : 'Editable Markdown';
  if (isPreview) {
    renderDraftPreview();
  } else {
    els.editor.focus();
  }
}

function setEditorValue(value) {
  els.editor.value = normalizeLineEndings(value || '');
  hideSharePanel();
  renderDraftPreview();
}

function appendEditorValue(value) {
  els.editor.value += normalizeLineEndings(value || '');
  hideSharePanel();
  renderDraftPreview();
}

function hideSharePanel() {
  els.sharePanel.classList.add('hidden');
  els.shareQr.removeAttribute('src');
  els.shareLink.textContent = '';
  els.shareLink.href = '#';
  els.shareExpiry.textContent = '';
}

function resetTeachingAids() {
  state.teachingAids = [];
  state.currentTeachingAid = null;
  state.teachingAidDraft = null;
  if (els.teachingAidRequest) els.teachingAidRequest.value = '';
  renderTeachingAids();
}

function setOllamaStatus(data) {
  const dotClass = data.ok && data.model_available ? 'status-dot--ok' : data.ok ? 'status-dot--warn' : 'status-dot--bad';
  const label = data.ok && data.model_available
    ? 'Connected'
    : data.ok
      ? 'Ollama running, model missing'
      : 'Not connected';
  const detail = data.ok
    ? data.model_available
      ? `Ready to generate with ${data.model}`
      : `Ollama is running at ${data.base_url}, but ${data.model} is not installed`
    : `${data.model} at ${data.base_url}: ${data.error || 'unavailable'}`;

  els.ollamaState.innerHTML = `<span class="status-dot ${dotClass}"></span><strong>${label}</strong>`;
  els.ollamaDetail.textContent = detail;
  els.statusbarOllama.textContent = `Ollama · ${label.toLowerCase()}`;
  els.statusbarOllamaDot.className = dotClass;
  els.systemModel.textContent = data.model || 'Unknown';
}

async function checkOllamaStatus() {
  els.ollamaState.innerHTML = '<span class="status-dot status-dot--unknown"></span><strong>Checking...</strong>';
  els.ollamaDetail.textContent = 'Contacting Ollama...';
  try {
    const data = await api('/api/ollama/status');
    setOllamaStatus(data);
  } catch (error) {
    setOllamaStatus({
      ok: false,
      base_url: 'unknown',
      model: 'unknown',
      error: error.message,
    });
  }
}

window.checkOllamaStatus = checkOllamaStatus;

async function configurePromptPreview() {
  try {
    const data = await api('/api/dev/prompt-preview/enabled');
    els.previewPromptButton.classList.toggle('hidden', !data.enabled);
    if (!data.enabled) {
      els.promptPreview.classList.add('hidden');
      els.promptPreview.value = '';
    }
  } catch {
    els.previewPromptButton.classList.add('hidden');
    els.promptPreview.classList.add('hidden');
    els.promptPreview.value = '';
  }
}

function showLogin() {
  els.loginView.classList.remove('hidden');
  els.appView.classList.add('hidden');
  els.adminPanel.classList.add('hidden');
  els.curriculumPanel.classList.add('hidden');
  els.formatAdminPanel.classList.add('hidden');
  els.adminToggle.classList.add('hidden');
  els.curriculumToggle.classList.add('hidden');
  els.formatAdminToggle.classList.add('hidden');
  els.teacherList.innerHTML = '';
  els.curriculumList.innerHTML = '';
  state.libraryOutputs = [];
}

function showApp() {
  els.loginView.classList.add('hidden');
  els.appView.classList.remove('hidden');
  els.teacherLabel.textContent = `${state.teacher.name}${state.teacher.is_admin ? ' | Admin' : ''}`;
  const isAdmin = Boolean(state.teacher.is_admin);
  els.adminToggle.classList.toggle('hidden', !isAdmin);
  els.curriculumToggle.classList.toggle('hidden', !isAdmin);
  els.formatAdminToggle.classList.toggle('hidden', !isAdmin);
  if (!isAdmin) {
    els.adminPanel.classList.add('hidden');
    els.curriculumPanel.classList.add('hidden');
    els.formatAdminPanel.classList.add('hidden');
    els.teacherList.innerHTML = '';
    els.curriculumList.innerHTML = '';
    state.lessonPlanFormats = [];
  }
}

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(String(options.method || 'GET').toUpperCase())) {
    headers['X-Klasbot-CSRF'] = state.csrfToken;
  }
  const response = await fetch(path, {
    headers,
    credentials: 'same-origin',
    ...options,
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Use status text when the response is not JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

async function createMobilePairingToken() {
  const data = await api('/api/mobile/pairing-token', { method: 'POST' });
  els.mobilePairQr.src = data.qr_url;
  els.mobilePairLink.href = data.url;
  els.mobilePairLink.textContent = data.url;
  els.mobilePairExpiry.textContent = `Pairing expires at ${data.expires_at}.`;
  els.mobilePairPanel.classList.remove('hidden');
  setStatus('Mobile pairing QR ready.');
}

async function cachedApi(path) {
  if (!state.curriculumCache.has(path)) {
    state.curriculumCache.set(path, api(path));
  }
  return state.curriculumCache.get(path);
}

function buildPinPad() {
  ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'Clear', '0', 'Del'].forEach((label) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;
    button.addEventListener('click', () => {
      if (label === 'Clear') {
        els.pin.value = '';
      } else if (label === 'Del') {
        els.pin.value = els.pin.value.slice(0, -1);
      } else {
        els.pin.value += label;
      }
      els.pin.focus();
    });
    els.pinPad.appendChild(button);
  });
}

function setSelectOptions(select, items, placeholder, getValue = (item) => item, getLabel = (item) => item) {
  select.innerHTML = '';
  const placeholderOption = document.createElement('option');
  placeholderOption.value = '';
  placeholderOption.textContent = placeholder;
  select.appendChild(placeholderOption);
  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = getValue(item);
    option.textContent = getLabel(item);
    select.appendChild(option);
  });
  select.disabled = items.length === 0;
}

function ensureSelectValue(select, value) {
  if (!value) return;
  const textValue = String(value);
  if (![...select.options].some((option) => option.value === textValue)) {
    const option = document.createElement('option');
    option.value = textValue;
    option.textContent = textValue;
    select.appendChild(option);
  }
  select.disabled = false;
  select.value = textValue;
}

function clearWeeks() {
  setSelectOptions(els.weekNumber, [], 'Choose week');
  renderPacingEditor(null);
}

async function loadCurriculumGrades() {
  try {
    const data = await cachedApi('/api/curriculum/grades');
    setSelectOptions(els.gradeLevel, data.grades, data.grades.length ? 'Choose grade' : 'No active curriculum');
    await loadCurriculumSubjects();
  } catch (error) {
    setSelectOptions(els.gradeLevel, [], 'Curriculum unavailable');
    els.curriculumMatch.textContent = error.message;
  }
}

async function loadCurriculumSubjects() {
  setSelectOptions(els.subject, [], 'Choose subject');
  setSelectOptions(els.quarter, [], 'Choose quarter');
  setSelectOptions(els.topic, [], 'Choose topic / domain');
  clearWeeks();
  if (!els.gradeLevel.value) {
    updateCurriculumMatch();
    updateDocumentChrome(collectInputs());
    return;
  }
  const data = await cachedApi(`/api/curriculum/subjects?grade=${encodeURIComponent(els.gradeLevel.value)}`);
  setSelectOptions(els.subject, data.subjects, data.subjects.length ? 'Choose subject' : 'No subjects for grade');
  updateCurriculumMatch();
  updateDocumentChrome(collectInputs());
}

async function loadCurriculumQuarters() {
  setSelectOptions(els.quarter, [], 'Choose quarter');
  setSelectOptions(els.topic, [], 'Choose topic / domain');
  clearWeeks();
  if (!els.gradeLevel.value || !els.subject.value) {
    updateCurriculumMatch();
    updateDocumentChrome(collectInputs());
    return;
  }
  const params = new URLSearchParams({ grade: els.gradeLevel.value, subject: els.subject.value });
  const data = await cachedApi(`/api/curriculum/quarters?${params.toString()}`);
  setSelectOptions(els.quarter, data.quarters, data.quarters.length ? 'Choose quarter' : 'No quarters');
  updateCurriculumMatch();
  updateDocumentChrome(collectInputs());
}

async function loadCurriculumTopics() {
  setSelectOptions(els.topic, [], 'Choose topic / domain');
  clearWeeks();
  if (!els.gradeLevel.value || !els.subject.value || !els.quarter.value) {
    updateCurriculumMatch();
    updateDocumentChrome(collectInputs());
    return;
  }
  const params = new URLSearchParams({
    grade: els.gradeLevel.value,
    subject: els.subject.value,
    quarter: els.quarter.value,
  });
  const data = await cachedApi(`/api/curriculum/topics?${params.toString()}`);
  setSelectOptions(
    els.topic,
    data.topics,
    data.topics.length ? 'Choose topic / domain' : 'No topics',
    (topic) => topic.domain,
    (topic) => `${topic.domain} (p. ${topic.source_pages})`,
  );
  updateCurriculumMatch();
  updateDocumentChrome(collectInputs());
}

async function loadCurriculumPacing() {
  clearWeeks();
  if (!els.gradeLevel.value || !els.subject.value || !els.quarter.value || !els.topic.value) {
    renderPacingEditor(null);
    updateCurriculumMatch();
    updateDocumentChrome(collectInputs());
    return;
  }
  const params = new URLSearchParams({
    grade: els.gradeLevel.value,
    subject: els.subject.value,
    quarter: els.quarter.value,
    topic: els.topic.value,
  });
  const data = await cachedApi(`/api/curriculum/pacing?${params.toString()}`);
  const weeks = data.pacing.weeks || [];
  setSelectOptions(
    els.weekNumber,
    weeks,
    weeks.length ? 'Choose week' : 'No pacing weeks',
    (week) => week.week_number,
    weekOptionLabel,
  );
  renderPacingEditor(data.pacing);
  updateCurriculumMatch();
  updateDocumentChrome(collectInputs());
}

function weekOptionLabel(week) {
  const competencies = week.competencies || [];
  if (!competencies.length) {
    return `Week ${week.week_number} - ${week.focus}`;
  }
  const sequences = competencies.map((competency) => Number(competency.sequence)).filter(Boolean);
  const label = sequences.length === 1
    ? `LC ${sequences[0]}`
    : `LC ${Math.min(...sequences)}-${Math.max(...sequences)} (${sequences.length} competencies)`;
  return `Week ${week.week_number} - ${label}: ${week.focus}`;
}

async function previewPrompt() {
  const inputs = collectInputs();
  if (!inputs.subject || !inputs.topic) {
    setStatus('Choose subject and topic/domain before previewing the prompt.', true);
    return;
  }
  const data = await api('/api/dev/prompt-preview', {
    method: 'POST',
    body: JSON.stringify(inputs),
  });
  els.promptPreview.value = normalizeLineEndings(data.prompt);
  els.promptPreview.classList.remove('hidden');
  setStatus(`Prompt preview ready (${data.prompt_chars} characters).`);
}

function updateFormats() {
  els.format.innerHTML = '';
  formats[els.kind.value].forEach((format) => {
    const option = document.createElement('option');
    option.value = format;
    option.textContent = format.toUpperCase();
    els.format.appendChild(option);
  });
  updateDocumentChrome(collectInputs());
}

function formatLabel(format) {
  const labels = {
    DLP: 'Detailed Lesson Plan',
    SDLP: 'Semi-Detailed Lesson Plan',
    DLL: 'Daily Lesson Log',
    quiz: 'Quiz Assessment',
    exam: 'Exam Assessment',
  };
  return labels[format] || format || 'Draft';
}

function switchWorkspace(workspace) {
  state.activeWorkspace = workspace;
  const isDraft = workspace === 'draft';
  const isLibrary = workspace === 'library';
  const isTeacherAdmin = workspace === 'teacher-admin';
  const isCurriculum = workspace === 'curriculum';
  const isPlanFormats = workspace === 'plan-formats';

  els.draftPanel.classList.toggle('hidden', !isDraft);
  els.documentTabs.classList.toggle('hidden', !isDraft);
  els.libraryPanel.classList.toggle('hidden', !isLibrary);
  els.adminPanel.classList.toggle('hidden', !isTeacherAdmin);
  els.curriculumPanel.classList.toggle('hidden', !isCurriculum);
  els.formatAdminPanel.classList.toggle('hidden', !isPlanFormats);

  els.currentDraftButton.classList.toggle('rail-item--on', isDraft);
  els.libraryButton.classList.toggle('rail-item--on', isLibrary);
  els.adminToggle.classList.toggle('rail-item--on', isTeacherAdmin);
  els.curriculumToggle.classList.toggle('rail-item--on', isCurriculum);
  els.formatAdminToggle.classList.toggle('rail-item--on', isPlanFormats);
  els.libraryButton.querySelector('span').textContent = isLibrary ? 'Open' : `${state.libraryOutputs.length}`;

  if (isLibrary) {
    els.documentTitle.textContent = 'My Library';
    els.documentMeta.textContent = 'Saved lesson plans, quizzes, and exams grouped by subject.';
    document.querySelector('.breadcrumb').textContent = 'Workspace / My Library';
    renderLibraryView();
  } else if (isTeacherAdmin) {
    els.documentTitle.textContent = 'Teacher Admin';
    els.documentMeta.textContent = 'Add teachers and manage shared kiosk access.';
    document.querySelector('.breadcrumb').textContent = 'Workspace / Teacher Admin';
  } else if (isCurriculum) {
    els.documentTitle.textContent = 'Curriculum';
    els.documentMeta.textContent = 'Upload, activate, deactivate, and delete curriculum sources.';
    document.querySelector('.breadcrumb').textContent = 'Workspace / Curriculum';
  } else if (isPlanFormats) {
    els.documentTitle.textContent = 'Plan Formats';
    els.documentMeta.textContent = 'Edit the lesson plan format requirements used in LLM prompts.';
    document.querySelector('.breadcrumb').textContent = 'Workspace / Plan Formats';
  } else {
    document.querySelector('.breadcrumb').textContent = 'Workspace / Current Draft';
    updateDocumentChrome(state.currentInputs || collectInputs());
  }
}

function updateDocumentChrome(inputs = state.currentInputs) {
  if (state.activeWorkspace !== 'draft') {
    return;
  }
  const title = inputs?.topic || 'Untitled Lesson Plan';
  const subject = inputs?.subject || 'No subject';
  const grades = inputs?.grade_levels?.length ? inputs.grade_levels.join(' | ') : 'No grade selected';
  const format = inputs?.format || els.format.value || 'DLP';
  const week = inputs?.week_number ? ` | Week ${inputs.week_number}` : '';
  els.documentTitle.textContent = title;
  els.documentMeta.textContent = `${subject} | ${grades} | ${formatLabel(format)}${week}`;
  els.formatBadge.textContent = format.toUpperCase();
  els.formatTitle.textContent = formatLabel(format);
}

function collectInputs() {
  const gradeLevels = els.gradeLevel.value ? [els.gradeLevel.value] : [];
  const resources = els.resources.value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  return {
    kind: els.kind.value,
    format: els.format.value,
    subject: els.subject.value.trim(),
    topic: els.topic.value.trim(),
    grade_level: els.gradeLevel.value.trim(),
    quarter: els.quarter.value ? Number(els.quarter.value) : null,
    week_number: els.weekNumber.value ? Number(els.weekNumber.value) : null,
    grade_levels: gradeLevels,
    resources,
  };
}

function setFormFromInputs(inputs) {
  els.kind.value = inputs.kind || 'lesson_plan';
  updateFormats();
  els.format.value = inputs.format || formats[els.kind.value][0];
  ensureSelectValue(els.gradeLevel, inputs.grade_level || inputs.grade_levels?.[0] || '');
  ensureSelectValue(els.subject, inputs.subject || '');
  ensureSelectValue(els.quarter, inputs.quarter ? String(inputs.quarter) : '');
  ensureSelectValue(els.topic, inputs.topic || '');
  ensureSelectValue(els.weekNumber, inputs.week_number ? String(inputs.week_number) : '');
  els.resources.value = (inputs.resources || []).join(', ');
  updateDocumentChrome(inputs);
  updateCurriculumMatch();
}

function updateCurriculumMatch() {
  if (!els.gradeLevel.value || !els.subject.value || !els.quarter.value || !els.topic.value || !els.weekNumber.value) {
    els.curriculumMatch.textContent = 'Choose grade, subject, quarter, topic/domain, and week from the active curriculum.';
    return;
  }
  const selectedWeek = els.weekNumber.options[els.weekNumber.selectedIndex]?.textContent || `Week ${els.weekNumber.value}`;
  els.curriculumMatch.textContent = `${els.subject.value} | ${els.gradeLevel.value} | Quarter ${els.quarter.value} | ${els.topic.value} | ${selectedWeek}`;
}

function streamGenerate(inputs) {
  switchWorkspace('draft');
  state.generating = true;
  state.currentInputs = inputs;
  state.currentOutputId = null;
  state.currentOutput = null;
  resetTeachingAids();
  setEditorValue('');
  setDraftView('preview');
  updateDocumentChrome(inputs);
  setStatus('Generating...');

  const params = new URLSearchParams({
    kind: inputs.kind,
    format: inputs.format,
    subject: inputs.subject,
    topic: inputs.topic,
  });
  if (inputs.grade_level) params.set('grade_level', inputs.grade_level);
  if (inputs.quarter) params.set('quarter', String(inputs.quarter));
  if (inputs.week_number) params.set('week_number', String(inputs.week_number));
  inputs.grade_levels.forEach((grade) => params.append('grade_levels', grade));
  inputs.resources.forEach((resource) => params.append('resources', resource));

  const source = new EventSource(`/api/generate/stream?${params.toString()}`);
  source.onmessage = (event) => {
    appendEditorValue(event.data);
  };
  source.addEventListener('done', () => {
    source.close();
    state.generating = false;
    setStatus('Draft ready. Edit, save, regenerate, or print.');
  });
  source.onerror = () => {
    source.close();
    state.generating = false;
    setStatus('Generation stream closed.', true);
  };
}

async function streamRegenerate(output) {
  state.generating = true;
  state.currentOutputId = null;
  state.currentOutput = null;
  state.currentInputs = output.inputs;
  resetTeachingAids();
  setEditorValue('');
  setDraftView('preview');
  setFormFromInputs(output.inputs);
  setStatus('Regenerating...');

  const response = await fetch(`/api/library/${output.id}/regenerate`, {
    method: 'POST',
    credentials: 'same-origin',
  });
  if (!response.ok || !response.body) {
    state.generating = false;
    throw new Error('Regenerate failed');
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
      if (eventName !== 'done') {
        appendEditorValue(data);
      }
    });
  }
  state.generating = false;
  setStatus('Regenerated draft ready.');
}

async function loadLibrary() {
  const data = await api('/api/library');
  state.libraryOutputs = data.outputs;
  updateLibraryFilters();
  renderLibraryView();
  if (els.libraryButton) {
    els.libraryButton.querySelector('span').textContent = state.activeWorkspace === 'library' ? 'Open' : `${data.outputs.length}`;
  }
}

function updateLibraryFilters() {
  const outputs = state.libraryOutputs;
  fillLibraryFilter(els.librarySubjectFilter, uniqueSorted(outputs.map((output) => output.subject || 'No subject')), 'All subjects');
  fillLibraryFilter(els.libraryGradeFilter, uniqueSorted(outputs.flatMap(outputGrades)), 'All grades');
  fillLibraryFilter(els.libraryFormatFilter, uniqueSorted(outputs.map((output) => output.format || output.kind)), 'All formats');
}

function fillLibraryFilter(select, values, placeholder) {
  const currentValue = select.value;
  select.innerHTML = '';
  const allOption = document.createElement('option');
  allOption.value = '';
  allOption.textContent = placeholder;
  select.appendChild(allOption);
  values.forEach((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  select.disabled = false;
  select.value = values.includes(currentValue) ? currentValue : '';
}

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean).map(String))].sort((a, b) => a.localeCompare(b));
}

function updateLibraryFilterVisibility() {
  els.libraryFilterRow.classList.toggle('hidden', state.libraryFiltersCollapsed);
  els.libraryFiltersToggle.setAttribute('aria-expanded', String(!state.libraryFiltersCollapsed));
  els.libraryFiltersToggle.textContent = state.libraryFiltersCollapsed ? 'Show filters' : 'Hide filters';
}

function renderDraftPreview() {
  const markdown = normalizeLineEndings(els.editor.value);
  els.draftPreview.innerHTML = markdown.trim()
    ? markdownToHtml(markdown)
    : '<div class="draft-preview__empty">Generated draft preview appears here.</div>';
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
    const rawLine = lines[index];
    const line = rawLine.trim();
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

    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      closeList();
      const level = heading[1].length;
      blocks.push(`<h${level}>${formatInline(heading[2])}</h${level}>`);
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
  const cells = splitTableRow(line);
  return cells.length > 1 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function splitTableRow(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
}

function collectTable(lines, startIndex) {
  const rows = [splitTableRow(lines[startIndex])];
  let index = startIndex + 2;
  while (index < lines.length && hasTablePipes(lines[index]) && lines[index].trim()) {
    rows.push(splitTableRow(lines[index]));
    index += 1;
  }
  return { rows, nextIndex: index };
}

function renderMarkdownTable(rows) {
  const headers = rows[0];
  const bodyRows = rows.slice(1);
  const headerHtml = headers.map((cell) => `<th>${formatInline(cell)}</th>`).join('');
  const bodyHtml = bodyRows.map((row) => {
    const cells = headers.map((_, index) => `<td>${formatInline(row[index] || '')}</td>`).join('');
    return `<tr>${cells}</tr>`;
  }).join('');
  return `<div class="draft-table-wrap"><table><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`;
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

function outputGrades(output) {
  return output.grade_levels?.length ? output.grade_levels : output.inputs?.grade_levels || [];
}

function outputQuarter(output) {
  return output.inputs?.quarter ? `Quarter ${output.inputs.quarter}` : 'No quarter';
}

function outputWeek(output) {
  const week = output.week_number || output.inputs?.week_number;
  return week ? `Week ${week}` : 'No week';
}

function outputType(output) {
  const format = String(output.format || '').toLowerCase();
  if (output.kind === 'assessment' && ['quiz', 'exam'].includes(format)) {
    return format;
  }
  return output.kind;
}

function outputTypeLabel(output) {
  const type = outputType(output);
  if (type === 'lesson_plan') return 'Lesson Plan';
  return type.charAt(0).toUpperCase() + type.slice(1);
}

function outputMetadataText(output) {
  return [
    output.topic,
    output.subject,
    output.kind,
    output.format,
    outputTypeLabel(output),
    outputQuarter(output),
    outputWeek(output),
    output.created_at,
    output.updated_at,
    ...outputGrades(output),
  ].filter(Boolean).join(' ').toLowerCase();
}

function filteredLibraryOutputs() {
  const query = els.librarySearch.value.trim().toLowerCase();
  const type = els.libraryTypeFilter.value;
  const subject = els.librarySubjectFilter.value;
  const grade = els.libraryGradeFilter.value;
  const format = els.libraryFormatFilter.value;
  let outputs = state.libraryOutputs.filter((output) => {
    if (query && !outputMetadataText(output).includes(query)) return false;
    if (type && outputType(output) !== type) return false;
    if (subject && (output.subject || 'No subject') !== subject) return false;
    if (grade && !outputGrades(output).includes(grade)) return false;
    if (format && (output.format || output.kind) !== format) return false;
    return true;
  });
  outputs = [...outputs].sort((a, b) => {
    if (els.librarySort.value === 'created_desc') {
      return String(b.created_at).localeCompare(String(a.created_at));
    }
    if (els.librarySort.value === 'topic_asc') {
      return String(a.topic || 'Untitled').localeCompare(String(b.topic || 'Untitled'));
    }
    return String(b.updated_at).localeCompare(String(a.updated_at));
  });
  return outputs;
}

function renderLibraryView() {
  els.libraryList.innerHTML = '';
  if (!state.libraryOutputs.length) {
    els.librarySummary.textContent = 'No saved outputs yet.';
    els.libraryList.innerHTML = '<div class="library-empty">Saved lesson plans, quizzes, and exams will appear here after you save a draft.</div>';
    return;
  }
  const outputs = filteredLibraryOutputs();
  els.librarySummary.textContent = `${outputs.length} of ${state.libraryOutputs.length} saved output${state.libraryOutputs.length === 1 ? '' : 's'}`;
  if (!outputs.length) {
    els.libraryList.innerHTML = '<div class="library-empty">No saved outputs match the current search and filters.</div>';
    return;
  }
  groupedBySubject(outputs).forEach(([subject, subjectOutputs]) => {
    const group = document.createElement('section');
    group.className = 'library-group';
    group.innerHTML = `
      <div class="library-group__head">
        <h2>${escapeHtml(subject)}</h2>
        <span>${subjectOutputs.length} item${subjectOutputs.length === 1 ? '' : 's'}</span>
      </div>
      <div class="library-grid"></div>
    `;
    const grid = group.querySelector('.library-grid');
    subjectOutputs.forEach((output) => grid.appendChild(createLibraryItem(output)));
    els.libraryList.appendChild(group);
  });
}

function groupedBySubject(outputs) {
  const groups = new Map();
  outputs.forEach((output) => {
    const subject = output.subject || 'No subject';
    if (!groups.has(subject)) groups.set(subject, []);
    groups.get(subject).push(output);
  });
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
}

function createLibraryItem(output) {
  const item = document.createElement('article');
  item.className = 'library-item';
  const grades = outputGrades(output);
  const format = output.format || output.kind;
  item.innerHTML = `
    <div>
      <div class="library-item__kicker">${escapeHtml(outputTypeLabel(output))} | ${escapeHtml(format)}</div>
      <h3>${escapeHtml(output.topic || 'Untitled')}</h3>
    </div>
    <dl class="library-item__meta">
      <div><dt>Grade</dt><dd>${escapeHtml(grades.length ? grades.join(', ') : 'No grade')}</dd></div>
      <div><dt>Quarter</dt><dd>${escapeHtml(outputQuarter(output))}</dd></div>
      <div><dt>Week</dt><dd>${escapeHtml(outputWeek(output))}</dd></div>
      <div><dt>Updated</dt><dd>${escapeHtml(output.updated_at)}</dd></div>
    </dl>
    <div class="item-actions">
      <button class="secondary" data-action="open">Open</button>
      <button class="secondary" data-action="share">Share</button>
      <button class="secondary" data-action="regenerate">Regenerate</button>
      <button class="secondary" data-action="delete">Delete</button>
    </div>
  `;
  item.querySelector('[data-action="open"]').addEventListener('click', () => openOutput(output).catch((error) => setStatus(error.message, true)));
  item.querySelector('[data-action="share"]').addEventListener('click', async () => {
    try {
      await openOutput(output);
      await shareOutput(output.id);
    } catch (error) {
      setStatus(error.message, true);
    }
  });
  item.querySelector('[data-action="regenerate"]').addEventListener('click', async () => {
    try {
      switchWorkspace('draft');
      await streamRegenerate(output);
    } catch (error) {
      setStatus(error.message, true);
    }
  });
  item.querySelector('[data-action="delete"]').addEventListener('click', async () => {
    await api(`/api/library/${output.id}`, { method: 'DELETE' });
    if (state.currentOutputId === output.id) {
      state.currentOutputId = null;
      state.currentOutput = null;
    }
    await loadLibrary();
    setStatus('Deleted saved output.');
  });
  return item;
}

async function openOutput(output) {
  switchWorkspace('draft');
  state.currentOutputId = output.id;
  state.currentOutput = output;
  state.currentInputs = output.inputs;
  setFormFromInputs(output.inputs);
  setEditorValue(output.content_md);
  setDraftView('preview');
  await loadTeachingAids(output.id);
  setStatus('Saved output opened.');
}

function newLesson() {
  switchWorkspace('draft');
  state.currentInputs = null;
  state.currentOutputId = null;
  state.currentOutput = null;
  resetTeachingAids();
  els.generateForm.reset();
  updateFormats();
  setEditorValue('');
  setDraftView('preview');
  setStatus('New draft ready.');
}

async function saveDraft() {
  if (!els.editor.value.trim()) {
    setStatus('Nothing to save yet.', true);
    return;
  }
  if (state.currentOutputId) {
    try {
      const data = await api(`/api/library/${state.currentOutputId}`, {
        method: 'PUT',
        body: JSON.stringify({ content_md: normalizeLineEndings(els.editor.value) }),
      });
      state.currentOutput = data.output;
      setStatus('Saved edits.');
    } catch (error) {
      if (!/not found/i.test(error.message || '')) {
        throw error;
      }
      state.currentOutputId = null;
      state.currentOutput = null;
      await createDraftRecord();
    }
  } else {
    await createDraftRecord();
  }
  await loadLibrary();
}

async function createDraftRecord() {
  const inputs = state.currentInputs || collectInputs();
  const data = await api('/api/library', {
    method: 'POST',
    body: JSON.stringify({ ...inputs, inputs, content_md: normalizeLineEndings(els.editor.value) }),
  });
  state.currentOutputId = data.output.id;
  state.currentOutput = data.output;
  await loadTeachingAids(data.output.id);
  setStatus('Saved to library.');
}

async function printDraft() {
  if (!els.editor.value.trim()) {
    setStatus('Nothing to print yet.', true);
    return;
  }
  const payload = state.currentOutputId
    ? { output_id: state.currentOutputId }
    : { content_md: normalizeLineEndings(els.editor.value), metadata: collectInputs() };
  const data = await api('/api/print', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (data.fallback && data.html) {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(data.html);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    setStatus('Opened browser print fallback.');
  } else {
    setStatus('Sent to printer.');
  }
}

function showShareResult(data) {
  els.shareQr.src = data.qr_url;
  els.shareLink.href = data.url;
  els.shareLink.textContent = data.url;
  els.shareExpiry.textContent = `PDF link expires at ${data.expires_at}.`;
  els.sharePanel.classList.remove('hidden');
  setStatus('Share link ready.');
}

async function shareOutput(outputId) {
  try {
    const data = await api(`/api/library/${outputId}/share`, {
      method: 'POST',
      body: JSON.stringify({ expires_minutes: 15 }),
    });
    showShareResult(data);
  } catch (error) {
    if (!/not found/i.test(error.message || '')) {
      throw error;
    }
    state.currentOutputId = null;
    state.currentOutput = null;
    await saveDraft();
    if (!state.currentOutputId) {
      throw error;
    }
    const data = await api(`/api/library/${state.currentOutputId}/share`, {
      method: 'POST',
      body: JSON.stringify({ expires_minutes: 15 }),
    });
    showShareResult(data);
  }
}

async function shareDraft() {
  if (!els.editor.value.trim()) {
    setStatus('Nothing to share yet.', true);
    return;
  }
  await saveDraft();
  if (!state.currentOutputId) {
    setStatus('Save the draft before sharing.', true);
    return;
  }
  await shareOutput(state.currentOutputId);
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

async function loadTeachingAids(outputId = state.currentOutputId) {
  if (!outputId || state.currentInputs?.kind !== 'lesson_plan') {
    resetTeachingAids();
    return;
  }
  const data = await api(`/api/library/${outputId}/teaching-aids`);
  state.teachingAids = data.teaching_aids || [];
  renderTeachingAids();
}

function renderTeachingAids() {
  const savedLesson = Boolean(state.currentOutputId);
  const isLessonPlan = (state.currentInputs?.kind || els.kind.value) === 'lesson_plan';
  els.teachingAidsPanel.classList.toggle('hidden', !isLessonPlan);
  els.teachingAidsStatus.textContent = savedLesson
    ? 'Generate practical classroom materials attached to this lesson.'
    : 'Save the lesson plan to generate attached classroom materials.';
  document.querySelectorAll('[data-aid-type]').forEach((button) => {
    button.disabled = !savedLesson || !isLessonPlan || state.generating;
  });
  els.teachingAidsList.innerHTML = '';
  if (!savedLesson || !isLessonPlan) {
    els.teachingAidEditorPanel.classList.add('hidden');
    return;
  }
  if (!state.teachingAids.length) {
    els.teachingAidsList.innerHTML = '<p class="microcopy">No Teaching Aids yet.</p>';
  } else {
    state.teachingAids.forEach((aid) => {
      const button = document.createElement('button');
      button.className = 'teaching-aid-item';
      button.type = 'button';
      button.innerHTML = `<strong>${escapeHtml(aid.title || teachingAidLabel(aid.aid_type))}</strong><span>${escapeHtml(teachingAidLabel(aid.aid_type))} | ${escapeHtml(aid.updated_at)}</span>`;
      button.addEventListener('click', () => openTeachingAid(aid));
      els.teachingAidsList.appendChild(button);
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
    : '<div class="draft-preview__empty">Generated Teaching Aid preview appears here.</div>';
}

function selectedSourceSection() {
  const editorSelection = els.editor.selectionStart !== els.editor.selectionEnd
    ? els.editor.value.slice(els.editor.selectionStart, els.editor.selectionEnd)
    : '';
  const browserSelection = String(window.getSelection?.() || '').trim();
  return normalizeLineEndings(editorSelection || browserSelection).trim();
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
      if (eventName !== 'done') {
        onData(data);
      }
    });
  }
}

async function generateTeachingAid(aidType) {
  if (!state.currentOutputId) {
    await saveDraft();
  }
  if (!state.currentOutputId) {
    setStatus('Save the lesson before generating Teaching Aids.', true);
    return;
  }
  const title = teachingAidLabel(aidType);
  state.currentTeachingAid = null;
  state.teachingAidDraft = {
    aid_type: aidType,
    title,
    source_section: selectedSourceSection(),
    content_md: '',
  };
  renderTeachingAidEditor();
  setStatus(`Generating ${title}...`);
  const response = await fetch(`/api/library/${state.currentOutputId}/teaching-aids/stream`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      ...(state.csrfToken ? { 'X-Klasbot-CSRF': state.csrfToken } : {}),
    },
    body: JSON.stringify({
      aid_type: aidType,
      source_section: state.teachingAidDraft.source_section,
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
    const data = await api(`/api/library/${state.currentOutputId}/teaching-aids/${state.currentTeachingAid.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: els.teachingAidTitle.value.trim() || teachingAidLabel(aid.aid_type),
        content_md: normalizeLineEndings(els.teachingAidEditor.value),
      }),
    });
    state.currentTeachingAid = data.teaching_aid;
  } else {
    const data = await api(`/api/library/${state.currentOutputId}/teaching-aids`, {
      method: 'POST',
      body: JSON.stringify({
        aid_type: aid.aid_type,
        title: els.teachingAidTitle.value.trim() || teachingAidLabel(aid.aid_type),
        source_section: aid.source_section || '',
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

async function printTeachingAid() {
  const aid = state.currentTeachingAid || state.teachingAidDraft;
  if (!aid || !els.teachingAidEditor.value.trim()) {
    setStatus('No Teaching Aid to print.', true);
    return;
  }
  const payload = state.currentTeachingAid
    ? { output_id: state.currentOutputId, teaching_aid_id: state.currentTeachingAid.id }
    : {
        content_md: normalizeLineEndings(els.teachingAidEditor.value),
        metadata: { ...collectInputs(), format: 'Teaching Aid', title: els.teachingAidTitle.value.trim() || teachingAidLabel(aid.aid_type) },
      };
  const data = await api('/api/print', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (data.fallback && data.html) {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(data.html);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  }
  setStatus('Teaching Aid sent to printer.');
}

async function shareTeachingAid() {
  if (!state.currentTeachingAid) {
    await saveTeachingAid();
  }
  if (!state.currentTeachingAid) {
    setStatus('Save the Teaching Aid before sharing.', true);
    return;
  }
  const data = await api(`/api/library/${state.currentOutputId}/teaching-aids/${state.currentTeachingAid.id}/share`, {
    method: 'POST',
    body: JSON.stringify({ expires_minutes: 15 }),
  });
  showShareResult(data);
}

function copyTeachingAidIntoLesson() {
  const title = els.teachingAidTitle.value.trim() || 'Teaching Aid';
  const content = normalizeLineEndings(els.teachingAidEditor.value).trim();
  if (!content) return;
  els.editor.value = `${normalizeLineEndings(els.editor.value).trim()}\n\n---\n\n# ${title}\n\n${content}\n`;
  renderDraftPreview();
  setStatus('Teaching Aid copied into the lesson draft.');
}

async function deleteTeachingAid() {
  if (!state.currentTeachingAid) return;
  await api(`/api/library/${state.currentOutputId}/teaching-aids/${state.currentTeachingAid.id}`, { method: 'DELETE' });
  state.currentTeachingAid = null;
  await loadTeachingAids();
  setStatus('Teaching Aid deleted.');
}

async function loadTeachers() {
  if (!state.teacher?.is_admin) return;
  const data = await api('/api/admin/teachers');
  els.teacherList.innerHTML = '';
  data.teachers.forEach((teacher) => {
    const item = document.createElement('article');
    item.className = 'list-item';
    item.innerHTML = `
      <h3>${escapeHtml(teacher.name)}</h3>
      <p>${teacher.is_admin ? 'Admin' : 'Teacher'} | Created ${escapeHtml(teacher.created_at)}</p>
      <div class="item-actions">
        <button class="secondary" type="button">Reset PIN</button>
      </div>
    `;
    item.querySelector('button').addEventListener('click', async () => {
      const pin = window.prompt(`New PIN for ${teacher.name}`);
      if (!pin) return;
      await api(`/api/admin/teachers/${teacher.id}/reset-pin`, {
        method: 'POST',
        body: JSON.stringify({ pin }),
      });
      setStatus('PIN reset.');
    });
    els.teacherList.appendChild(item);
  });
}

async function loadCurriculumDocuments() {
  if (!state.teacher?.is_admin) return;
  const data = await api('/api/admin/curriculum');
  els.curriculumList.innerHTML = '';
  if (!data.documents.length) {
    els.curriculumList.innerHTML = '<p>No uploaded curriculum yet.</p>';
    return;
  }
  data.documents.forEach((curriculumDocument) => {
    const item = document.createElement('article');
    item.className = 'list-item';
    const summary = curriculumDocument.parse_summary || {};
    const confidence = summary.average_confidence ?? 0;
    const warningCount = summary.warning_count ?? 0;
    item.innerHTML = `
      <h3>${escapeHtml(curriculumDocument.subject)} ${curriculumDocument.active ? '(active)' : ''}</h3>
      <p>${escapeHtml(curriculumDocument.title)} | ${escapeHtml(curriculumDocument.version_label)} | ${curriculumDocument.unit_count} units</p>
      <p>Parse confidence ${escapeHtml(confidence)} | ${warningCount} warning${warningCount === 1 ? '' : 's'}</p>
      ${formatParseWarnings(summary)}
      <p>Uploaded ${escapeHtml(curriculumDocument.created_at)}</p>
      <div class="item-actions">
        <button class="secondary" data-action="activate" type="button">Activate</button>
        <button class="secondary" data-action="deactivate" type="button">Deactivate</button>
        <button class="secondary" data-action="delete" type="button">Delete</button>
      </div>
    `;
    item.querySelector('[data-action="activate"]').disabled = curriculumDocument.active;
    item.querySelector('[data-action="activate"]').addEventListener('click', async () => {
      await api(`/api/admin/curriculum/${curriculumDocument.id}/activate`, { method: 'POST' });
      state.curriculumCache.clear();
      await loadCurriculumDocuments();
      await loadCurriculumGrades();
      setStatus('Curriculum activated.');
    });
    item.querySelector('[data-action="deactivate"]').disabled = !curriculumDocument.active;
    item.querySelector('[data-action="deactivate"]').addEventListener('click', async () => {
      await api(`/api/admin/curriculum/${curriculumDocument.id}/deactivate`, { method: 'POST' });
      state.curriculumCache.clear();
      await loadCurriculumDocuments();
      await loadCurriculumGrades();
      setStatus('Curriculum deactivated.');
    });
    item.querySelector('[data-action="delete"]').disabled = curriculumDocument.active;
    item.querySelector('[data-action="delete"]').addEventListener('click', async () => {
      await api(`/api/admin/curriculum/${curriculumDocument.id}`, { method: 'DELETE' });
      state.curriculumCache.clear();
      await loadCurriculumDocuments();
      setStatus('Inactive curriculum deleted.');
    });
    els.curriculumList.appendChild(item);
  });
}

function renderPacingEditor(pacing) {
  if (!els.pacingEditor || !els.pacingForm) return;
  if (!pacing || !state.teacher?.is_admin) {
    els.pacingEditor.classList.add('hidden');
    els.pacingForm.innerHTML = '';
    return;
  }
  els.pacingEditor.classList.remove('hidden');
  els.pacingEditor.dataset.unitId = pacing.unit.id;
  els.pacingEditorMeta.textContent = `${pacing.unit.subject} | ${pacing.unit.grade_level} | Quarter ${pacing.unit.quarter} | ${pacing.unit.domain}`;
  const competencyOptions = (selectedIds) => (pacing.competencies || []).map((competency) => `
    <label class="checkbox">
      <input type="checkbox" value="${competency.id}" ${selectedIds.includes(competency.id) ? 'checked' : ''} />
      ${competency.sequence}. ${escapeHtml(competency.competency_text)}
    </label>
  `).join('');
  els.pacingForm.innerHTML = (pacing.weeks || []).map((week) => `
    <fieldset class="pacing-week" data-week="${week.week_number}">
      <legend>Week ${week.week_number}</legend>
      <label>
        Focus
        <input data-field="focus" type="text" value="${escapeHtml(week.focus)}" required />
      </label>
      <label>
        Notes
        <textarea data-field="notes" rows="2">${escapeHtml(week.notes || '')}</textarea>
      </label>
      <div class="pacing-competencies">${competencyOptions(week.competency_ids || [])}</div>
    </fieldset>
  `).join('') + '<button class="primary compact" type="submit">Save pacing</button>';
}

async function savePacing(event) {
  event.preventDefault();
  const unitId = els.pacingEditor.dataset.unitId;
  if (!unitId) return;
  const weeks = [...els.pacingForm.querySelectorAll('.pacing-week')].map((fieldset) => ({
    week_number: Number(fieldset.dataset.week),
    focus: fieldset.querySelector('[data-field="focus"]').value.trim(),
    notes: fieldset.querySelector('[data-field="notes"]').value.trim(),
    competency_ids: [...fieldset.querySelectorAll('input[type="checkbox"]:checked')].map((input) => Number(input.value)),
  }));
  const data = await api(`/api/admin/curriculum/pacing/${unitId}`, {
    method: 'PUT',
    body: JSON.stringify({ weeks }),
  });
  state.curriculumCache.clear();
  renderPacingEditor(data.pacing);
  await loadCurriculumPacing();
  setStatus('Weekly pacing saved.');
}

async function resetPacing() {
  const unitId = els.pacingEditor.dataset.unitId;
  if (!unitId) return;
  const data = await api(`/api/admin/curriculum/pacing/${unitId}/reset`, { method: 'POST' });
  state.curriculumCache.clear();
  renderPacingEditor(data.pacing);
  await loadCurriculumPacing();
  setStatus('Weekly pacing reset.');
}

async function loadLessonPlanFormats() {
  if (!state.teacher?.is_admin) return;
  els.formatAdminMessage.textContent = '';
  els.formatAdminSelect.innerHTML = '<option value="">Loading formats...</option>';
  els.formatAdminSelect.disabled = true;
  els.formatAdminTitle.value = '';
  els.formatAdminRequirements.value = '';
  let data;
  try {
    data = await api('/api/admin/lesson-plan-formats');
  } catch (error) {
    els.formatAdminSelect.innerHTML = '<option value="">Formats unavailable</option>';
    els.formatAdminMessage.textContent = `Could not load plan formats: ${error.message}`;
    setStatus(error.message, true);
    return;
  }
  state.lessonPlanFormats = data.formats || [];
  els.formatAdminSelect.innerHTML = '';
  if (!state.lessonPlanFormats.length) {
    els.formatAdminSelect.innerHTML = '<option value="">No formats configured</option>';
    els.formatAdminMessage.textContent = 'No lesson plan formats are configured in the local database.';
    setStatus('No lesson plan formats are configured.', true);
    return;
  }
  state.lessonPlanFormats.forEach((formatConfig) => {
    const option = document.createElement('option');
    option.value = formatConfig.format;
    option.textContent = `${formatConfig.format} - ${formatConfig.title}`;
    els.formatAdminSelect.appendChild(option);
  });
  els.formatAdminSelect.disabled = false;
  const defaultFormat = state.lessonPlanFormats.some((formatConfig) => formatConfig.format === 'DLP')
    ? 'DLP'
    : state.lessonPlanFormats[0].format;
  els.formatAdminSelect.value = defaultFormat;
  [...els.formatAdminSelect.options].forEach((option) => {
    option.selected = option.value === defaultFormat;
  });
  renderSelectedLessonPlanFormat();
}

function renderSelectedLessonPlanFormat() {
  const selected = state.lessonPlanFormats.find((formatConfig) => formatConfig.format === els.formatAdminSelect.value)
    || state.lessonPlanFormats.find((formatConfig) => formatConfig.format === 'DLP')
    || state.lessonPlanFormats[0];
  if (!selected) {
    els.formatAdminTitle.value = '';
    els.formatAdminRequirements.value = '';
    return;
  }
  els.formatAdminSelect.value = selected.format;
  els.formatAdminTitle.value = selected.title || '';
  els.formatAdminRequirements.value = normalizeLineEndings(selected.requirements || '');
}

async function saveSelectedLessonPlanFormat(event) {
  event.preventDefault();
  const formatName = els.formatAdminSelect.value;
  if (!formatName) return;
  const data = await api(`/api/admin/lesson-plan-formats/${encodeURIComponent(formatName)}`, {
    method: 'PUT',
    body: JSON.stringify({
      title: els.formatAdminTitle.value,
      requirements: normalizeLineEndings(els.formatAdminRequirements.value),
    }),
  });
  state.lessonPlanFormats = state.lessonPlanFormats.map((formatConfig) => (
    formatConfig.format === data.format.format ? data.format : formatConfig
  ));
  renderSelectedLessonPlanFormat();
  setStatus(`${formatName} format saved. New generations will use the updated requirements.`);
}

async function resetSelectedLessonPlanFormat() {
  const formatName = els.formatAdminSelect.value;
  if (!formatName) return;
  const data = await api(`/api/admin/lesson-plan-formats/${encodeURIComponent(formatName)}/reset`, {
    method: 'POST',
  });
  state.lessonPlanFormats = state.lessonPlanFormats.map((formatConfig) => (
    formatConfig.format === data.format.format ? data.format : formatConfig
  ));
  renderSelectedLessonPlanFormat();
  setStatus(`${formatName} format reset to default.`);
}

function formatParseWarnings(summary) {
  const warnings = summary?.warnings || [];
  if (!warnings.length) {
    return '<p>No parse warnings.</p>';
  }
  const preview = warnings.slice(0, 3).map((warning) => `<li>${escapeHtml(warning)}</li>`).join('');
  const more = warnings.length > 3 ? `<li>${warnings.length - 3} more warning(s)</li>` : '';
  return `<ul class="warning-list">${preview}${more}</ul>`;
}

async function uploadCurriculum(event) {
  event.preventDefault();
  const fileInput = document.getElementById('curriculum-file');
  if (!fileInput.files.length) return;
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('subject', document.getElementById('curriculum-subject').value);
  formData.append('version_label', document.getElementById('curriculum-version').value);
  setStatus('Uploading and parsing curriculum...');
  const response = await fetch('/api/admin/curriculum/upload', {
    method: 'POST',
    body: formData,
    credentials: 'same-origin',
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Use status text when upload errors are not JSON.
    }
    throw new Error(message);
  }
  els.curriculumUploadForm.reset();
  state.curriculumCache.clear();
  const uploadResult = await response.json();
  await loadCurriculumDocuments();
  await loadCurriculumGrades();
  const summary = uploadResult.document.parse_summary || {};
  setStatus(`Curriculum uploaded. Confidence ${summary.average_confidence ?? 0}; warnings ${summary.warning_count ?? 0}.`);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

async function bootstrap() {
  buildPinPad();
  setupEditorBehavior();
  updateFormats();
  try {
    const data = await api('/api/me');
    state.teacher = data.teacher;
    state.csrfToken = data.csrf_token || '';
    showApp();
    await loadLibrary();
    await loadTeachers();
    await loadCurriculumDocuments();
    await loadLessonPlanFormats();
    await loadCurriculumGrades();
    await configurePromptPreview();
    await checkOllamaStatus();
  } catch {
    showLogin();
  }
}

els.loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  els.loginError.textContent = '';
  try {
    const data = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ pin: els.pin.value }),
    });
    state.teacher = data.teacher;
    const session = await api('/api/me');
    state.csrfToken = session.csrf_token || '';
    els.pin.value = '';
    showApp();
    await loadLibrary();
    await loadTeachers();
    await loadCurriculumDocuments();
    await loadLessonPlanFormats();
    await loadCurriculumGrades();
    await configurePromptPreview();
    await checkOllamaStatus();
  } catch (error) {
    els.loginError.textContent = error.message;
  }
});

els.logoutButton.addEventListener('click', async () => {
  await api('/api/auth/logout', { method: 'POST' });
  state.teacher = null;
  state.csrfToken = '';
  showLogin();
});

els.adminToggle.addEventListener('click', () => {
  switchWorkspace('teacher-admin');
  loadTeachers().catch((error) => setStatus(error.message, true));
});

els.curriculumToggle.addEventListener('click', () => {
  switchWorkspace('curriculum');
  loadCurriculumDocuments().catch((error) => setStatus(error.message, true));
});

els.formatAdminToggle.addEventListener('click', () => {
  switchWorkspace('plan-formats');
  loadLessonPlanFormats().catch((error) => setStatus(error.message, true));
});

els.teacherForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  await api('/api/admin/teachers', {
    method: 'POST',
    body: JSON.stringify({
      name: document.getElementById('teacher-name').value,
      pin: document.getElementById('teacher-pin').value,
      is_admin: document.getElementById('teacher-admin').checked,
    }),
  });
  els.teacherForm.reset();
  await loadTeachers();
  setStatus('Teacher added.');
});

els.refreshTeachers.addEventListener('click', loadTeachers);
els.refreshCurriculum.addEventListener('click', loadCurriculumDocuments);
els.refreshFormats.addEventListener('click', () => loadLessonPlanFormats().catch((error) => setStatus(error.message, true)));
els.formatAdminSelect.addEventListener('change', renderSelectedLessonPlanFormat);
els.formatAdminForm.addEventListener('submit', (event) => {
  saveSelectedLessonPlanFormat(event).catch((error) => setStatus(error.message, true));
});
els.resetFormat.addEventListener('click', () => {
  resetSelectedLessonPlanFormat().catch((error) => setStatus(error.message, true));
});
els.curriculumUploadForm.addEventListener('submit', (event) => {
  uploadCurriculum(event).catch((error) => setStatus(error.message, true));
});
if (els.pacingForm) {
  els.pacingForm.addEventListener('submit', (event) => {
    savePacing(event).catch((error) => setStatus(error.message, true));
  });
}
if (els.resetPacing) {
  els.resetPacing.addEventListener('click', () => resetPacing().catch((error) => setStatus(error.message, true)));
}
els.refreshLibrary.addEventListener('click', loadLibrary);
els.libraryFiltersToggle.addEventListener('click', () => {
  state.libraryFiltersCollapsed = !state.libraryFiltersCollapsed;
  updateLibraryFilterVisibility();
});
els.previewTab.addEventListener('click', () => setDraftView('preview'));
els.editTab.addEventListener('click', () => setDraftView('edit'));
els.currentDraftButton.addEventListener('click', () => switchWorkspace('draft'));
els.libraryButton.addEventListener('click', () => {
  switchWorkspace('library');
  loadLibrary().catch((error) => {
    els.librarySummary.textContent = error.message;
  });
});
[
  els.librarySearch,
  els.libraryTypeFilter,
  els.librarySubjectFilter,
  els.libraryGradeFilter,
  els.libraryFormatFilter,
  els.librarySort,
].forEach((control) => {
  control.addEventListener('input', renderLibraryView);
  control.addEventListener('change', renderLibraryView);
});
els.newLessonButton.addEventListener('click', newLesson);
els.previewPromptButton.addEventListener('click', () => {
  previewPrompt().catch((error) => setStatus(error.message, true));
});
if (els.checkOllamaButton) {
  els.checkOllamaButton.addEventListener('click', checkOllamaStatus);
}
els.kind.addEventListener('change', () => {
  updateFormats();
  renderTeachingAids();
});
els.format.addEventListener('change', () => updateDocumentChrome(collectInputs()));
els.gradeLevel.addEventListener('change', () => loadCurriculumSubjects().catch((error) => setStatus(error.message, true)));
els.subject.addEventListener('change', () => loadCurriculumQuarters().catch((error) => setStatus(error.message, true)));
els.quarter.addEventListener('change', () => loadCurriculumTopics().catch((error) => setStatus(error.message, true)));
els.topic.addEventListener('change', () => {
  loadCurriculumPacing().catch((error) => setStatus(error.message, true));
});
els.weekNumber.addEventListener('change', () => {
  updateCurriculumMatch();
  updateDocumentChrome(collectInputs());
});
els.generateForm.addEventListener('submit', (event) => {
  event.preventDefault();
  streamGenerate(collectInputs());
});
els.saveButton.addEventListener('click', () => saveDraft().catch((error) => setStatus(error.message, true)));
els.printButton.addEventListener('click', () => printDraft().catch((error) => setStatus(error.message, true)));
els.shareButton.addEventListener('click', () => shareDraft().catch((error) => setStatus(error.message, true)));
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
els.printTeachingAid.addEventListener('click', () => printTeachingAid().catch((error) => setStatus(error.message, true)));
els.shareTeachingAid.addEventListener('click', () => shareTeachingAid().catch((error) => setStatus(error.message, true)));
els.copyTeachingAid.addEventListener('click', copyTeachingAidIntoLesson);
els.deleteTeachingAid.addEventListener('click', () => deleteTeachingAid().catch((error) => setStatus(error.message, true)));
els.mobilePairButton.addEventListener('click', () => createMobilePairingToken().catch((error) => setStatus(error.message, true)));

updateLibraryFilterVisibility();
renderDraftPreview();
renderTeachingAids();
setDraftView('preview');
bootstrap();
