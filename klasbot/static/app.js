const state = {
  teacher: null,
  currentInputs: null,
  currentOutputId: null,
  currentOutput: null,
  activeWorkspace: 'home',
  activeClassTab: 'dashboard',
  draftView: 'preview',
  libraryOutputs: [],
  libraryFiltersCollapsed: false,
  generating: false,
  curriculumCache: new Map(),
  lessonPlanFormats: [],
  teachingAids: [],
  teachingAidTargetId: null,
  currentTeachingAid: null,
  teachingAidDraft: null,
  teachingAidEditing: false,
  csrfToken: '',
  gradingBatches: [],
  gradingClasses: [],
  gradingAssessments: [],
  gradingTransferPreview: null,
  activeGradingBatch: null,
  classRecords: [],
  activeClassRecord: null,
  activeScoreAssessmentId: null,
  activeAttendanceDate: null,
  demoConfig: null,
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
  demoLoginButton: document.getElementById('demo-login-button'),
  demoLoginNote: document.getElementById('demo-login-note'),
  pin: document.getElementById('pin'),
  pinPad: document.getElementById('pin-pad'),
  teacherLabel: document.getElementById('teacher-label'),
  logoutButton: document.getElementById('logout-button'),
  workspaceFrame: document.getElementById('workspace-frame'),
  inspector: document.getElementById('inspector'),
  homePanel: document.getElementById('home-panel'),
  homeButton: document.getElementById('home-button'),
  helpButton: document.getElementById('help-button'),
  lessonAreaButton: document.getElementById('lesson-area-button'),
  classAreaButton: document.getElementById('class-area-button'),
  adminAreaButton: document.getElementById('admin-area-button'),
  adminHomeCard: document.getElementById('admin-home-card'),
  lessonNavGroup: document.getElementById('lesson-nav-group'),
  classNavGroup: document.getElementById('class-nav-group'),
  adminNavGroup: document.getElementById('admin-nav-group'),
  currentDraftButton: document.getElementById('current-draft-button'),
  teachingAidsButton: document.getElementById('teaching-aids-button'),
  assessmentButton: document.getElementById('assessment-button'),
  libraryButton: document.getElementById('library-button'),
  classRecordsButton: document.getElementById('class-records-button'),
  gradingButton: document.getElementById('grading-button'),
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
  helpPanel: document.getElementById('help-panel'),
  helpLanguage: document.getElementById('help-language'),
  helpAskForm: document.getElementById('help-ask-form'),
  helpQuestion: document.getElementById('help-question'),
  helpAskButton: document.getElementById('help-ask-button'),
  helpStatus: document.getElementById('help-status'),
  helpAnswer: document.getElementById('help-answer'),
  helpProviderDot: document.getElementById('help-provider-dot'),
  helpProviderLabel: document.getElementById('help-provider-label'),
  helpProviderDetail: document.getElementById('help-provider-detail'),
  helpCheckProvider: document.getElementById('help-check-provider'),
  helpSearchInput: document.getElementById('help-search-input'),
  helpSearchClear: document.getElementById('help-search-clear'),
  helpEmptyState: document.getElementById('help-empty-state'),
  helpAnswerToolbar: document.querySelector('.help-answer-toolbar'),
  helpCopyAnswer: document.getElementById('help-copy-answer'),
  helpClearAnswer: document.getElementById('help-clear-answer'),
  helpFollowupAnswer: document.getElementById('help-followup-answer'),
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
  resourcesField: document.getElementById('resources-field'),
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
  teachingAidTarget: document.getElementById('teaching-aid-target'),
  teachingAidTargetMeta: document.getElementById('teaching-aid-target-meta'),
  teachingAidRequest: document.getElementById('teaching-aid-request'),
  teachingAidsList: document.getElementById('teaching-aids-list'),
  teachingAidEditorPanel: document.getElementById('teaching-aid-editor-panel'),
  teachingAidTitle: document.getElementById('teaching-aid-title'),
  teachingAidEditor: document.getElementById('teaching-aid-editor'),
  teachingAidPreview: document.getElementById('teaching-aid-preview'),
  editTeachingAid: document.getElementById('edit-teaching-aid'),
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
  gradingPanel: document.getElementById('grading-panel'),
  refreshGrading: document.getElementById('refresh-grading'),
  gradingBatchForm: document.getElementById('grading-batch-form'),
  gradingClass: document.getElementById('grading-class'),
  gradingAssessment: document.getElementById('grading-assessment'),
  gradingPoints: document.getElementById('grading-points'),
  gradingStyle: document.getElementById('grading-style'),
  gradingQuestions: document.getElementById('grading-questions'),
  gradingAnswerKey: document.getElementById('grading-answer-key'),
  gradingRubric: document.getElementById('grading-rubric'),
  gradingActive: document.getElementById('grading-active'),
  gradingActiveTitle: document.getElementById('grading-active-title'),
  gradingActiveMeta: document.getElementById('grading-active-meta'),
  gradingUploadForm: document.getElementById('grading-upload-form'),
  gradingFiles: document.getElementById('grading-files'),
  gradingUploadButton: document.getElementById('grading-upload-button'),
  gradingStatus: document.getElementById('grading-status'),
  gradingImages: document.getElementById('grading-images'),
  gradingSubmissions: document.getElementById('grading-submissions'),
  gradingTransferReview: document.getElementById('grading-transfer-review'),
  gradingBatches: document.getElementById('grading-batches'),
  detectSubmissions: document.getElementById('detect-submissions'),
  gradeSubmissions: document.getElementById('grade-submissions'),
  previewScoreTransfer: document.getElementById('preview-score-transfer'),
  saveScoreTransfer: document.getElementById('save-score-transfer'),
  printGrading: document.getElementById('print-grading'),
  deleteGradingBatch: document.getElementById('delete-grading-batch'),
  classRecordsPanel: document.getElementById('class-records-panel'),
  refreshClassRecords: document.getElementById('refresh-class-records'),
  classRecordForm: document.getElementById('class-record-form'),
  classRecordName: document.getElementById('class-record-name'),
  classRecordGrade: document.getElementById('class-record-grade'),
  classRecordSection: document.getElementById('class-record-section'),
  classRecordSubject: document.getElementById('class-record-subject'),
  classRecordSchoolYear: document.getElementById('class-record-school-year'),
  classRecordsList: document.getElementById('class-records-list'),
  classRecordDetail: document.getElementById('class-record-detail'),
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

function setHelpStatus(message, isError = false) {
  if (!els.helpStatus) return;
  els.helpStatus.textContent = message;
  els.helpStatus.style.color = isError ? 'var(--danger)' : 'var(--accent-strong)';
}

function actionControlFromEvent(event) {
  if (!event) return null;
  if (event.submitter) return event.submitter;
  if (event.currentTarget?.matches?.('button')) return event.currentTarget;
  return event.currentTarget?.querySelector?.('button[type="submit"], button:not([type])') || null;
}

function setActionBusy(control, isBusy, busyText = 'Working...') {
  if (!control) return;
  if (isBusy) {
    if (!control.dataset.readyText) {
      control.dataset.readyText = control.textContent;
      control.dataset.readyHtml = control.innerHTML;
    }
    control.disabled = true;
    control.setAttribute('aria-busy', 'true');
    control.classList.add('is-busy');
    control.textContent = busyText;
    return;
  }
  control.disabled = false;
  control.removeAttribute('aria-busy');
  control.classList.remove('is-busy');
  if (control.dataset.readyHtml) {
    control.innerHTML = control.dataset.readyHtml;
    delete control.dataset.readyHtml;
    delete control.dataset.readyText;
  } else if (control.dataset.readyText) {
    control.textContent = control.dataset.readyText;
    delete control.dataset.readyText;
  }
}

function setRailBadge(button, text) {
  if (!button) return;
  let badge = button.querySelector('span');
  if (!badge) {
    const label = button.firstChild?.nodeType === Node.TEXT_NODE
      ? button.firstChild.textContent.trim()
      : button.textContent.replace(/\s+/g, ' ').trim().replace(/\s+(Open|\d+|New|Batch|Ready|Admin|Upload)$/i, '');
    button.textContent = label ? `${label} ` : '';
    badge = document.createElement('span');
    button.appendChild(badge);
  }
  badge.textContent = text;
}

async function runUserAction(eventOrControl, pendingMessage, action, options = {}) {
  const control = eventOrControl?.currentTarget ? actionControlFromEvent(eventOrControl) : eventOrControl;
  const busyText = options.busyText || 'Working...';
  const report = options.report || setStatus;
  if (pendingMessage) report(pendingMessage);
  setActionBusy(control, true, busyText);
  try {
    return await action();
  } catch (error) {
    report(error.message || 'Action failed.', true);
    return null;
  } finally {
    setActionBusy(control, false);
  }
}

function setGradingStatus(message, isError = false) {
  if (!els.gradingStatus) return;
  els.gradingStatus.textContent = message;
  els.gradingStatus.style.color = isError ? 'var(--danger)' : 'var(--accent-strong)';
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
  state.teachingAidTargetId = null;
  state.currentTeachingAid = null;
  state.teachingAidDraft = null;
  if (els.teachingAidRequest) els.teachingAidRequest.value = '';
  renderTeachingAids();
}

function setOllamaStatus(data) {
  const providerLabel = data.provider_label || (data.provider === 'vertex_gemma' ? 'Vertex Gemma' : 'Ollama');
  const dotClass = data.ok && data.model_available ? 'status-dot--ok' : data.ok ? 'status-dot--warn' : 'status-dot--bad';
  const label = data.ok && data.model_available
    ? 'Connected'
    : data.ok
      ? `${providerLabel} reachable, model unavailable`
      : 'Not connected';
  const detail = data.ok
    ? data.model_available
      ? `Ready to generate with ${data.model}`
      : `${providerLabel} is reachable at ${data.base_url}, but ${data.model} is unavailable`
    : `${data.model} at ${data.base_url}: ${data.error || 'unavailable'}`;

  els.ollamaState.innerHTML = `<span class="status-dot ${dotClass}"></span><strong>${label}</strong>`;
  els.ollamaDetail.textContent = detail;
  els.statusbarOllama.textContent = `${providerLabel} · ${label.toLowerCase()}`;
  els.statusbarOllamaDot.className = dotClass;
  els.systemModel.textContent = data.model || 'Unknown';
  const homeModelDot = document.getElementById('home-model-dot');
  const homeModelLabel = document.getElementById('home-model-label');
  if (homeModelDot) homeModelDot.className = `status-dot ${dotClass}`;
  if (homeModelLabel) homeModelLabel.textContent = data.model ? `${label} · ${data.model}` : label;
  if (els.helpProviderDot) els.helpProviderDot.className = `status-dot ${dotClass}`;
  if (els.helpProviderLabel) els.helpProviderLabel.textContent = label;
  if (els.helpProviderDetail) els.helpProviderDetail.textContent = detail;
}

async function checkOllamaStatus() {
  els.ollamaState.innerHTML = '<span class="status-dot status-dot--unknown"></span><strong>Checking...</strong>';
  els.ollamaDetail.textContent = 'Checking AI provider...';
  try {
    const data = await api('/api/ollama/status');
    setOllamaStatus(data);
    return data;
  } catch (error) {
    const data = {
      ok: false,
      base_url: 'unknown',
      model: 'unknown',
      error: error.message,
    };
    setOllamaStatus(data);
    return data;
  }
}

async function ensureHelpProviderReady() {
  setHelpStatus('Checking AI provider...');
  const data = await checkOllamaStatus();
  if (!data?.ok || !data?.model_available) {
    const providerLabel = data?.provider_label || data?.provider || 'AI provider';
    const reason = data?.error || (data?.ok ? `${data.model || 'Configured model'} is unavailable` : 'provider is not reachable');
    throw new Error(`${providerLabel} is not ready: ${reason}`);
  }
  return data;
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
  els.homePanel.classList.add('hidden');
  els.gradingPanel.classList.add('hidden');
  els.classRecordsPanel.classList.add('hidden');
  els.adminPanel.classList.add('hidden');
  els.curriculumPanel.classList.add('hidden');
  els.formatAdminPanel.classList.add('hidden');
  els.helpPanel.classList.add('hidden');
  els.adminAreaButton.classList.add('hidden');
  els.adminHomeCard.classList.add('hidden');
  els.adminToggle.classList.add('hidden');
  els.curriculumToggle.classList.add('hidden');
  els.formatAdminToggle.classList.add('hidden');
  els.teacherList.innerHTML = '';
  els.curriculumList.innerHTML = '';
  state.libraryOutputs = [];
  state.gradingBatches = [];
  state.gradingClasses = [];
  state.gradingAssessments = [];
  state.gradingTransferPreview = null;
  state.activeGradingBatch = null;
  state.classRecords = [];
  state.activeClassRecord = null;
  state.activeScoreAssessmentId = null;
  state.activeAttendanceDate = null;
  state.activeClassTab = 'dashboard';
}

function showApp() {
  els.loginView.classList.add('hidden');
  els.appView.classList.remove('hidden');
  els.teacherLabel.textContent = `${state.teacher.name}${state.teacher.is_admin ? ' | Admin' : ''}`;
  const isAdmin = Boolean(state.teacher.is_admin);
  els.adminAreaButton.classList.toggle('hidden', !isAdmin);
  els.adminHomeCard.classList.toggle('hidden', !isAdmin);
  els.adminToggle.classList.toggle('hidden', !isAdmin);
  els.curriculumToggle.classList.toggle('hidden', !isAdmin);
  els.formatAdminToggle.classList.toggle('hidden', !isAdmin);
  renderHelpRoleVisibility();
  if (!isAdmin) {
    els.adminPanel.classList.add('hidden');
    els.curriculumPanel.classList.add('hidden');
    els.formatAdminPanel.classList.add('hidden');
    els.teacherList.innerHTML = '';
    els.curriculumList.innerHTML = '';
    state.lessonPlanFormats = [];
  }
  switchWorkspace('home');
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
  updateResourcesVisibility();
  updateDocumentChrome(collectInputs());
}

function updateResourcesVisibility() {
  const showResources = els.kind.value === 'assessment';
  els.resourcesField?.classList.toggle('hidden', !showResources);
  if (!showResources) {
    els.resources.value = '';
  }
}

function renderHelpRoleVisibility() {
  const isAdmin = Boolean(state.teacher?.is_admin);
  document.querySelectorAll('.help-admin-only').forEach((node) => {
    node.classList.toggle('hidden', !isAdmin);
  });
}

function fillHelpQuestion(question) {
  switchWorkspace('help');
  els.helpQuestion.value = question || '';
  els.helpQuestion.focus();
  setHelpStatus('Question ready. Review it, then ask KlasBot.');
}

const HELP_ANSWER_EMPTY_TEXT = 'KlasBot Help answer appears here. Pick an example or type your own question above.';

function renderHelpAnswerEmpty(text = HELP_ANSWER_EMPTY_TEXT) {
  if (!els.helpAnswer) return;
  els.helpAnswer.replaceChildren();
  const empty = document.createElement('div');
  empty.className = 'draft-preview__empty';
  empty.textContent = text;
  els.helpAnswer.appendChild(empty);
}

function setHelpAnswerToolbarVisible(visible) {
  if (els.helpAnswerToolbar) {
    els.helpAnswerToolbar.hidden = !visible;
  }
}

function clearHelpAnswer() {
  renderHelpAnswerEmpty();
  setHelpAnswerToolbarVisible(false);
  setHelpStatus('');
}

async function generateClassInsights() {
  const panel = els.classRecordDetail.querySelector('.class-insights-panel');
  if (!panel) return;
  const output = panel.querySelector('.class-insights-output');
  const statusEl = panel.querySelector('.class-insights-status');
  output.innerHTML = '<div class="draft-preview__empty">Generating insights…</div>';
  statusEl.textContent = 'Generating…';
  const classId = state.activeClassRecord?.class?.id;
  const data = await api(`/api/class-records/classes/${classId}/insights`, { method: 'POST' });
  state.activeClassRecord = { ...state.activeClassRecord, insights: data };
  output.innerHTML = markdownToHtml(data.answer || '');
  statusEl.textContent = data.empty
    ? 'No insights yet — add students and scores first.'
    : `Generated with ${data.model}.`;
}

async function askHelpQuestion() {
  const question = els.helpQuestion.value.trim();
  if (!question) {
    setHelpStatus('Enter a help question first.', true);
    els.helpQuestion.focus();
    return;
  }
  await ensureHelpProviderReady();
  renderHelpAnswerEmpty('Asking KlasBot Help...');
  setHelpAnswerToolbarVisible(false);
  setHelpStatus('Asking KlasBot Help...');
  state.lastHelpQuestion = question;
  const data = await api('/api/help/ask', {
    method: 'POST',
    body: JSON.stringify({
      question,
      language: els.helpLanguage.value || 'en',
    }),
  });
  els.helpAnswer.innerHTML = markdownToHtml(data.answer || '');
  setHelpAnswerToolbarVisible(true);
  setHelpStatus(`Answered with ${data.model}.`);
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

function workspaceArea(workspace) {
  if (['draft', 'teaching-aids', 'library'].includes(workspace)) return 'lesson';
  if (['grading', 'class-records'].includes(workspace)) return 'class';
  if (['teacher-admin', 'curriculum', 'plan-formats'].includes(workspace)) return 'admin';
  if (workspace === 'help') return 'help';
  return 'home';
}

function setNavigationState(workspace) {
  const area = workspaceArea(workspace);
  const isHome = workspace === 'home';
  const isHelp = workspace === 'help';
  const isLesson = area === 'lesson';
  const isClass = area === 'class';
  const isAdmin = area === 'admin';

  els.workspaceFrame.dataset.area = area;
  els.homeButton.classList.toggle('rail-primary--active', isHome);
  els.helpButton.classList.toggle('rail-primary--active', isHelp);
  els.lessonAreaButton.classList.toggle('rail-item--on', isLesson);
  els.classAreaButton.classList.toggle('rail-item--on', isClass);
  els.adminAreaButton.classList.toggle('rail-item--on', isAdmin);
  els.lessonNavGroup.classList.toggle('hidden', !isLesson);
  els.classNavGroup.classList.toggle('hidden', !isClass);
  els.adminNavGroup.classList.toggle('hidden', !isAdmin || !state.teacher?.is_admin);
}

function setInspectorVisibility(workspace) {
  const showInspector = workspace === 'draft';
  els.inspector.classList.toggle('hidden', !showInspector);
  els.workspaceFrame.classList.toggle('workspace-frame--no-inspector', !showInspector);
}

function clearWorkspaceSelection() {
  els.currentDraftButton.classList.remove('rail-item--on');
  els.teachingAidsButton.classList.remove('rail-item--on');
  els.libraryButton.classList.remove('rail-item--on');
  els.gradingButton.classList.remove('rail-item--on');
  els.classRecordsButton.classList.remove('rail-item--on');
  els.adminToggle.classList.remove('rail-item--on');
  els.curriculumToggle.classList.remove('rail-item--on');
  els.formatAdminToggle.classList.remove('rail-item--on');
}

function setVisibleWorkspacePanel(panelName) {
  els.homePanel.classList.toggle('hidden', panelName !== 'home');
  els.draftPanel.classList.toggle('hidden', panelName !== 'draft');
  els.documentTabs.classList.toggle('hidden', panelName !== 'draft');
  els.helpPanel.classList.toggle('hidden', panelName !== 'help');
  els.teachingAidsPanel.classList.toggle('hidden', panelName !== 'teaching-aids');
  els.libraryPanel.classList.toggle('hidden', panelName !== 'library');
  els.gradingPanel.classList.toggle('hidden', panelName !== 'grading');
  els.classRecordsPanel.classList.toggle('hidden', panelName !== 'class-records');
  els.adminPanel.classList.toggle('hidden', panelName !== 'teacher-admin');
  els.curriculumPanel.classList.toggle('hidden', panelName !== 'curriculum');
  els.formatAdminPanel.classList.toggle('hidden', panelName !== 'plan-formats');
}

function openWorkArea(area) {
  const labels = {
    lesson: ['Lesson Planning', 'Choose a lesson planning action from the left menu.'],
    class: ['Class Management', 'Choose a class management action from the left menu.'],
    admin: ['Admin', 'Choose an admin action from the left menu.'],
  };
  if (area === 'admin' && !state.teacher?.is_admin) {
    switchWorkspace('home');
    return;
  }
  const [title, meta] = labels[area] || ['KlasBot Home', 'Choose a workspace.'];
  state.activeWorkspace = 'home';
  els.workspaceFrame.dataset.area = area;
  els.homeButton.classList.remove('rail-primary--active');
  els.helpButton.classList.remove('rail-primary--active');
  els.lessonAreaButton.classList.toggle('rail-item--on', area === 'lesson');
  els.classAreaButton.classList.toggle('rail-item--on', area === 'class');
  els.adminAreaButton.classList.toggle('rail-item--on', area === 'admin');
  els.lessonNavGroup.classList.toggle('hidden', area !== 'lesson');
  els.classNavGroup.classList.toggle('hidden', area !== 'class');
  els.adminNavGroup.classList.toggle('hidden', area !== 'admin' || !state.teacher?.is_admin);
  setInspectorVisibility('home');
  setVisibleWorkspacePanel('home');
  clearWorkspaceSelection();
  els.documentTitle.textContent = title;
  els.documentMeta.textContent = meta;
  document.querySelector('.breadcrumb').textContent = title;
}

function switchWorkspace(workspace) {
  if (workspaceArea(workspace) === 'admin' && !state.teacher?.is_admin) {
    workspace = 'home';
  }
  state.activeWorkspace = workspace;
  const isHome = workspace === 'home';
  const isHelp = workspace === 'help';
  const isDraft = workspace === 'draft';
  const isTeachingAids = workspace === 'teaching-aids';
  const isLibrary = workspace === 'library';
  const isGrading = workspace === 'grading';
  const isClassRecords = workspace === 'class-records';
  const isTeacherAdmin = workspace === 'teacher-admin';
  const isCurriculum = workspace === 'curriculum';
  const isPlanFormats = workspace === 'plan-formats';

  setNavigationState(workspace);
  setInspectorVisibility(workspace);

  setVisibleWorkspacePanel(workspace);

  clearWorkspaceSelection();
  els.currentDraftButton.classList.toggle('rail-item--on', isDraft);
  els.teachingAidsButton.classList.toggle('rail-item--on', isTeachingAids);
  els.libraryButton.classList.toggle('rail-item--on', isLibrary);
  els.gradingButton.classList.toggle('rail-item--on', isGrading);
  els.classRecordsButton.classList.toggle('rail-item--on', isClassRecords);
  els.adminToggle.classList.toggle('rail-item--on', isTeacherAdmin);
  els.curriculumToggle.classList.toggle('rail-item--on', isCurriculum);
  els.formatAdminToggle.classList.toggle('rail-item--on', isPlanFormats);
  setRailBadge(els.libraryButton, isLibrary ? 'Open' : `${state.libraryOutputs.length}`);
  setRailBadge(els.gradingButton, isGrading ? 'Open' : gradingRailBadge());

  if (isHome) {
    els.documentTitle.textContent = 'KlasBot Home';
    els.documentMeta.textContent = state.teacher?.is_admin
      ? 'Choose Lesson Planning, Class Management, or Admin.'
      : 'Choose Lesson Planning or Class Management.';
    document.querySelector('.breadcrumb').textContent = 'Home';
  } else if (isHelp) {
    els.documentTitle.textContent = 'Help';
    els.documentMeta.textContent = 'Offline instructions and grounded answers about using KlasBot.';
    document.querySelector('.breadcrumb').textContent = 'Help';
    renderHelpRoleVisibility();
  } else if (isLibrary) {
    els.documentTitle.textContent = 'My Library';
    els.documentMeta.textContent = 'Saved lesson plans, quizzes, exams, and teaching aids grouped by subject.';
    document.querySelector('.breadcrumb').textContent = 'Lesson Planning / My Library';
    renderLibraryView();
  } else if (isTeachingAids) {
    els.documentTitle.textContent = 'Teaching Aids';
    els.documentMeta.textContent = teachingAidTargetId()
      ? 'Generate, edit, copy into the lesson, print, or share attached classroom materials.'
      : 'Open or save a lesson plan before generating attached classroom materials.';
    document.querySelector('.breadcrumb').textContent = 'Lesson Planning / Teaching Aids';
    renderTeachingAids();
  } else if (isGrading) {
    els.documentTitle.textContent = 'Grade Quiz Photo';
    els.documentMeta.textContent = 'Upload worksheet photos, confirm submissions, and review item-level scores.';
    document.querySelector('.breadcrumb').textContent = 'Class Management / Grade Quiz Photo';
    renderGradingWorkspace();
  } else if (isClassRecords) {
    els.documentTitle.textContent = 'Class Management';
    els.documentMeta.textContent = 'Create classes, manage rosters, enter scores, and review performance.';
    document.querySelector('.breadcrumb').textContent = 'Class Management / All Classes';
    renderClassRecordsWorkspace();
  } else if (isTeacherAdmin) {
    els.documentTitle.textContent = 'Teacher Admin';
    els.documentMeta.textContent = 'Add teachers and manage shared kiosk access.';
    document.querySelector('.breadcrumb').textContent = 'Admin / Teacher Admin';
  } else if (isCurriculum) {
    els.documentTitle.textContent = 'Curriculum';
    els.documentMeta.textContent = 'Upload, activate, deactivate, and delete curriculum sources.';
    document.querySelector('.breadcrumb').textContent = 'Admin / Curriculum';
  } else if (isPlanFormats) {
    els.documentTitle.textContent = 'Plan Formats';
    els.documentMeta.textContent = 'Edit the lesson plan format requirements used in LLM prompts.';
    document.querySelector('.breadcrumb').textContent = 'Admin / Plan Formats';
  } else {
    document.querySelector('.breadcrumb').textContent = 'Lesson Planning / Current Draft';
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

function gradingRailBadge() {
  if (state.activeGradingBatch) return 'Ready';
  return state.gradingBatches.length ? `${state.gradingBatches.length}` : 'Batch';
}

function collectInputs() {
  const gradeLevels = els.gradeLevel.value ? [els.gradeLevel.value] : [];
  const resources = els.kind.value === 'assessment'
    ? els.resources.value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
    : [];
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
  updateResourcesVisibility();
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

function streamGenerate(inputs, control = null) {
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
  setActionBusy(control, true, 'Generating...');

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
    setActionBusy(control, false);
    setStatus('Draft ready. Edit, save, regenerate, or print.');
  });
  source.onerror = () => {
    source.close();
    state.generating = false;
    setActionBusy(control, false);
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
  if (state.activeWorkspace === 'teaching-aids') {
    renderTeachingAids();
  }
  if (els.libraryButton) {
    setRailBadge(els.libraryButton, state.activeWorkspace === 'library' ? 'Open' : `${data.outputs.length}`);
  }
}

async function loadGradingClassChoices() {
  const data = await api('/api/class-records/classes');
  state.gradingClasses = data.classes || [];
  els.gradingClass.innerHTML = '';
  if (!state.gradingClasses.length) {
    els.gradingClass.innerHTML = '<option value="">Create a class first</option>';
    els.gradingAssessment.innerHTML = '<option value="">No assessments</option>';
    els.gradingPoints.value = '';
    return;
  }
  state.gradingClasses.forEach((record) => {
    const option = document.createElement('option');
    option.value = String(record.id);
    option.textContent = `${record.name} | Grade ${record.grade_level}${record.section ? `-${record.section}` : ''} | ${record.subject}`;
    els.gradingClass.appendChild(option);
  });
  await loadGradingAssessmentChoices();
}

async function loadGradingAssessmentChoices() {
  const classId = Number(els.gradingClass.value);
  els.gradingAssessment.innerHTML = '';
  state.gradingAssessments = [];
  if (!classId) {
    els.gradingAssessment.innerHTML = '<option value="">Choose a class first</option>';
    els.gradingPoints.value = '';
    return;
  }
  const data = await api(`/api/class-records/classes/${classId}/assessments`);
  state.gradingAssessments = data.assessments || [];
  if (!state.gradingAssessments.length) {
    els.gradingAssessment.innerHTML = '<option value="">Create an assessment in this class first</option>';
    els.gradingPoints.value = '';
    return;
  }
  state.gradingAssessments.forEach((assessment) => {
    const option = document.createElement('option');
    option.value = String(assessment.id);
    option.textContent = `${assessment.title} | ${assessment.assessment_type} | Max ${assessment.max_score}`;
    els.gradingAssessment.appendChild(option);
  });
  syncGradingPointsFromAssessment();
}

function selectedGradingAssessment() {
  const assessmentId = Number(els.gradingAssessment.value);
  return state.gradingAssessments.find((assessment) => assessment.id === assessmentId) || null;
}

function syncGradingPointsFromAssessment() {
  const assessment = selectedGradingAssessment();
  els.gradingPoints.value = assessment ? assessment.max_score : '';
}

async function loadGradingBatches() {
  await loadGradingClassChoices();
  const data = await api('/api/grading/batches');
  state.gradingBatches = data.batches;
  if (state.activeGradingBatch) {
    const current = data.batches.find((batch) => batch.id === state.activeGradingBatch.id);
    if (current) {
      await selectGradingBatch(current.id);
    }
  }
  renderGradingWorkspace();
  setRailBadge(els.gradingButton, state.activeWorkspace === 'grading' ? 'Open' : gradingRailBadge());
}

async function createGradingBatch(event) {
  event.preventDefault();
  const answerKey = els.gradingAnswerKey.value.trim();
  const rubric = els.gradingRubric.value.trim();
  const questions = els.gradingQuestions.value.trim();
  const assessment = selectedGradingAssessment();
  if (!assessment) {
    setGradingStatus('Choose a class assessment before creating a batch.', true);
    return;
  }
  const data = await api('/api/grading/batches', {
    method: 'POST',
    body: JSON.stringify({
      class_id: Number(els.gradingClass.value),
      assessment_id: Number(els.gradingAssessment.value),
      total_points: Number(els.gradingPoints.value),
      grading_style: els.gradingStyle.value,
      questions,
      answer_key: answerKey,
      rubric,
    }),
  });
  els.gradingBatchForm.reset();
  state.gradingTransferPreview = null;
  state.activeGradingBatch = data.batch;
  await loadGradingBatches();
  setGradingStatus('Grading batch created. Choose quiz files and upload them.');
  setStatus('Grading batch created.');
}

async function selectGradingBatch(batchId) {
  const data = await api(`/api/grading/batches/${batchId}`);
  state.activeGradingBatch = data.batch;
  state.gradingTransferPreview = null;
  renderGradingWorkspace();
}

async function uploadGradingImages(event) {
  event.preventDefault();
  if (!state.activeGradingBatch) return;
  const files = [...els.gradingFiles.files];
  if (!files.length) {
    setGradingStatus('Choose at least one PNG, JPEG, or PDF quiz file.', true);
    return;
  }
  els.gradingUploadButton.disabled = true;
  els.gradingUploadButton.textContent = `Uploading ${files.length} file${files.length === 1 ? '' : 's'}...`;
  setGradingStatus(`Uploading ${files.length} quiz file${files.length === 1 ? '' : 's'}...`);
  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      const headers = {};
      if (state.csrfToken) headers['X-Klasbot-CSRF'] = state.csrfToken;
      const response = await fetch(`/api/grading/batches/${state.activeGradingBatch.id}/images`, {
        method: 'POST',
        body: formData,
        headers,
        credentials: 'same-origin',
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || response.statusText);
      }
    }
    els.gradingFiles.value = '';
    await selectGradingBatch(state.activeGradingBatch.id);
    await loadGradingBatches();
    const imageCount = state.activeGradingBatch?.images?.length || 0;
    setGradingStatus(`Upload complete. ${imageCount} file${imageCount === 1 ? '' : 's'} attached to this batch.`);
    setStatus('Quiz file upload complete.');
  } catch (error) {
    setGradingStatus(error.message, true);
    throw error;
  } finally {
    els.gradingUploadButton.disabled = false;
    els.gradingUploadButton.textContent = 'Upload files';
  }
}

async function detectGradingSubmissions() {
  if (!state.activeGradingBatch) return;
  await api(`/api/grading/batches/${state.activeGradingBatch.id}/detect-submissions`, { method: 'POST' });
  await selectGradingBatch(state.activeGradingBatch.id);
  setGradingStatus('Worksheet regions detected. Confirm names before final review.');
  setStatus('Worksheet regions detected. Confirm names before final review.');
}

async function gradeGradingSubmissions() {
  if (!state.activeGradingBatch) return;
  els.gradeSubmissions.disabled = true;
  els.gradeSubmissions.textContent = 'Grading...';
  setGradingStatus('Extracting answers with Ollama and proposing scores...');
  try {
    const data = await api(`/api/grading/batches/${state.activeGradingBatch.id}/grade`, { method: 'POST' });
    await selectGradingBatch(state.activeGradingBatch.id);
    const warnings = (data.submissions || []).flatMap((submission) => submission.grading_result?.warnings || []);
    const timeoutWarnings = warnings.filter((warning) => warning.toLowerCase().includes('ollama'));
    if (timeoutWarnings.length) {
      setGradingStatus('Ollama did not finish every submission. Manual-review rows were created with warnings.', true);
      setStatus('Grading finished with Ollama warnings.', true);
      return;
    }
    setGradingStatus('Model-extracted answers and proposed scores are ready for review.');
    setStatus('Model-extracted answers and proposed scores are ready for review.');
  } finally {
    els.gradeSubmissions.disabled = false;
    els.gradeSubmissions.textContent = 'Grade';
  }
}

async function saveGradingSubmission(submissionId) {
  const card = document.querySelector(`[data-submission-id="${submissionId}"]`);
  if (!card) return;
  const result = JSON.parse(card.querySelector('[data-field="grading-result"]').value || '{}');
  const response = await api(`/api/grading/submissions/${submissionId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      student_name: card.querySelector('[data-field="student-name"]').value.trim(),
      student_identifier: card.querySelector('[data-field="student-identifier"]').value.trim(),
      student_id: card.querySelector('[data-field="student-id"]').value ? Number(card.querySelector('[data-field="student-id"]').value) : null,
      extracted_answers: state.activeGradingBatch.submissions.find((item) => item.id === submissionId)?.extracted_answers || {},
      grading_result: result,
      score: card.querySelector('[data-field="score"]').value ? Number(card.querySelector('[data-field="score"]').value) : null,
      max_score: card.querySelector('[data-field="max-score"]').value ? Number(card.querySelector('[data-field="max-score"]').value) : null,
      confidence: card.querySelector('[data-field="confidence"]').value ? Number(card.querySelector('[data-field="confidence"]').value) : null,
      teacher_reviewed: card.querySelector('[data-field="teacher-reviewed"]').checked,
    }),
  });
  const index = state.activeGradingBatch.submissions.findIndex((item) => item.id === submissionId);
  if (index >= 0) state.activeGradingBatch.submissions[index] = response.submission;
  renderGradingWorkspace();
  setGradingStatus('Submission review saved.');
  setStatus('Submission review saved.');
}

async function previewScoreTransfer() {
  if (!state.activeGradingBatch) return;
  const data = await api(`/api/grading/batches/${state.activeGradingBatch.id}/transfer-preview`, { method: 'POST' });
  state.gradingTransferPreview = data;
  renderGradingTransferReview();
  const readyCount = (data.rows || []).filter((row) => row.status === 'ready').length;
  setGradingStatus(`${readyCount} reviewed score${readyCount === 1 ? '' : 's'} ready to save.`);
}

async function saveScoreTransfer() {
  if (!state.activeGradingBatch) return;
  const data = await api(`/api/grading/batches/${state.activeGradingBatch.id}/transfer-scores`, { method: 'POST' });
  state.gradingTransferPreview = data;
  await selectGradingBatch(state.activeGradingBatch.id);
  state.gradingTransferPreview = data;
  renderGradingTransferReview();
  setGradingStatus(`${data.saved_count || 0} score${data.saved_count === 1 ? '' : 's'} saved to the class assessment.`);
  if (state.activeClassRecord?.class?.id === data.assessment?.class_id) {
    await selectClassRecord(data.assessment.class_id);
  }
}

async function printGradingBatch() {
  if (!state.activeGradingBatch) return;
  const response = await fetch(`/api/grading/batches/${state.activeGradingBatch.id}/print`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: state.csrfToken ? { 'X-Klasbot-CSRF': state.csrfToken } : {},
  });
  if (!response.ok) throw new Error(response.statusText);
  const html = await response.text();
  const preview = window.open('', '_blank');
  preview.document.write(html);
  preview.document.close();
}

async function deleteActiveGradingBatch() {
  if (!state.activeGradingBatch) return;
  await api(`/api/grading/batches/${state.activeGradingBatch.id}`, { method: 'DELETE' });
  state.activeGradingBatch = null;
  await loadGradingBatches();
  setGradingStatus('Grading batch deleted.');
  setStatus('Grading batch deleted.');
}

function renderGradingWorkspace() {
  renderGradingBatches();
  renderActiveGradingBatch();
}

function renderGradingBatches() {
  if (!els.gradingBatches) return;
  if (!state.gradingBatches.length) {
    els.gradingBatches.innerHTML = '<p>No grading batches yet.</p>';
    return;
  }
  els.gradingBatches.innerHTML = state.gradingBatches.map((batch) => `
    <button class="list-item" type="button" data-batch-id="${batch.id}">
      <h3>${escapeHtml(batch.assessment_title || batch.topic || 'Untitled quiz')}</h3>
      <p>${escapeHtml(batch.class_name || 'No class')} | ${batch.submission_count} submission(s) | ${escapeHtml(batch.status)}</p>
    </button>
  `).join('');
  els.gradingBatches.querySelectorAll('[data-batch-id]').forEach((button) => {
    button.addEventListener('click', () => runUserAction(
      button,
      'Opening grading batch...',
      () => selectGradingBatch(Number(button.dataset.batchId)),
      { busyText: 'Opening...', report: setGradingStatus },
    ));
  });
}

function renderActiveGradingBatch() {
  const batch = state.activeGradingBatch;
  updateGradingSteps(batch);
  els.gradingActive.classList.toggle('hidden', !batch);
  if (!batch) {
    els.gradingImages.innerHTML = '';
  els.gradingSubmissions.innerHTML = '';
  els.gradingTransferReview.innerHTML = '';
    setGradingStatus('');
    return;
  }
  els.gradingActiveTitle.textContent = batch.assessment_title || batch.topic || 'Untitled quiz';
  els.gradingActiveMeta.textContent = `${batch.class_name || 'No class'} | ${batch.total_points} pts | ${batch.grading_style}`;
  els.gradingImages.innerHTML = (batch.images || []).map((image) => `
    <article class="grading-image-card">
      <img src="/api/grading/images/${image.id}/thumbnail" alt="Uploaded quiz worksheet preview" />
      <p>${image.width || 0} x ${image.height || 0}</p>
      ${(image.quality_warnings || []).length ? `<ul class="warning-list">${image.quality_warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join('')}</ul>` : ''}
    </article>
  `).join('');
  els.gradingSubmissions.innerHTML = (batch.submissions || []).map(renderGradingSubmissionCard).join('');
  els.gradingSubmissions.querySelectorAll('[data-save-submission]').forEach((button) => {
    button.addEventListener('click', () => runUserAction(
      button,
      'Saving submission review...',
      () => saveGradingSubmission(Number(button.dataset.saveSubmission)),
      { busyText: 'Saving...', report: setGradingStatus },
    ));
  });
  renderGradingTransferReview();
}

function updateGradingSteps(batch = state.activeGradingBatch) {
  const uploadedCount = batch?.images?.length || 0;
  const submissionCount = batch?.submissions?.length || 0;
  const reviewedCount = (batch?.submissions || []).filter((submission) => submission.teacher_reviewed).length;
  let activeStep = 'setup';
  if (batch && !uploadedCount) activeStep = 'upload';
  if (uploadedCount && !submissionCount) activeStep = 'detect';
  if (submissionCount) activeStep = 'review';
  document.querySelectorAll('[data-grading-step]').forEach((step) => {
    const stepName = step.dataset.gradingStep;
    const isActive = stepName === activeStep;
    step.classList.toggle('grading-step--on', isActive);
  });
  const reviewStep = document.querySelector('[data-grading-step="review"] span');
  if (reviewStep && submissionCount) {
    reviewStep.textContent = reviewedCount
      ? `Review scores (${reviewedCount}/${submissionCount})`
      : `Review scores (${submissionCount})`;
  } else if (reviewStep) {
    reviewStep.textContent = 'Review scores';
  }
}

function renderGradingSubmissionCard(submission) {
  const result = submission.grading_result || {};
  const warningItems = (result.warnings || []).map((warning) => `<li>${escapeHtml(warning)}</li>`).join('');
  const students = state.activeGradingBatch?.class_students || [];
  const studentOptions = ['<option value="">Needs match</option>'].concat(students.map((student) => {
    const selected = Number(submission.student_id || 0) === Number(student.id) ? ' selected' : '';
    return `<option value="${student.id}"${selected}>${escapeHtml(student.display_name || `${student.first_name} ${student.last_name}`)}</option>`;
  })).join('');
  return `
    <article class="grading-submission-card" data-submission-id="${submission.id}">
      <h4>${escapeHtml(submission.student_name || submission.student_identifier || `Submission ${submission.id}`)}</h4>
      <div class="workspace-form">
        <label>Student name <input data-field="student-name" type="text" value="${escapeHtml(submission.student_name || '')}" /></label>
        <label>Identifier <input data-field="student-identifier" type="text" value="${escapeHtml(submission.student_identifier || '')}" /></label>
        <label>Class student <select data-field="student-id">${studentOptions}</select></label>
        <label>Score <input data-field="score" type="number" step="0.5" value="${submission.score ?? ''}" /></label>
        <label>Max <input data-field="max-score" type="number" step="0.5" value="${submission.max_score ?? ''}" /></label>
        <label>Confidence <input data-field="confidence" type="number" min="0" max="1" step="0.01" value="${submission.confidence ?? ''}" /></label>
        <label class="checkbox"><input data-field="teacher-reviewed" type="checkbox" ${submission.teacher_reviewed ? 'checked' : ''} /> Teacher reviewed</label>
      </div>
      ${renderGradingItems(result.items || [])}
      ${warningItems ? `<ul class="warning-list">${warningItems}</ul>` : ''}
      <label>Structured result JSON <textarea data-field="grading-result" spellcheck="false">${escapeHtml(JSON.stringify(result, null, 2))}</textarea></label>
      <button class="primary compact" type="button" data-save-submission="${submission.id}">Save review</button>
    </article>
  `;
}

function renderGradingTransferReview() {
  if (!els.gradingTransferReview) return;
  const preview = state.gradingTransferPreview;
  if (!preview?.rows?.length) {
    els.gradingTransferReview.innerHTML = '';
    return;
  }
  els.gradingTransferReview.innerHTML = `
    <article class="grading-submission-card">
      <h4>Score transfer review</h4>
      <p class="microcopy">${escapeHtml(preview.assessment?.title || 'Assessment')} | Max ${escapeHtml(preview.assessment?.max_score ?? '')}</p>
      <table class="grading-items">
        <thead><tr><th>Submission</th><th>Student</th><th>Score</th><th>Status</th><th>Reason</th></tr></thead>
        <tbody>${preview.rows.map((row) => `
          <tr>
            <td>${escapeHtml(row.submission_name || row.student_identifier || `Submission ${row.submission_id}`)}</td>
            <td>${escapeHtml(row.student?.display_name || 'Needs match')}</td>
            <td>${escapeHtml(row.score ?? '')} / ${escapeHtml(row.max_score ?? '')}</td>
            <td>${escapeHtml(row.status)}</td>
            <td>${escapeHtml(row.reason || '')}</td>
          </tr>
        `).join('')}</tbody>
      </table>
    </article>
  `;
}

function renderGradingItems(items) {
  if (!items.length) return '<p class="microcopy">No item rows yet.</p>';
  return `
    <table class="grading-items">
      <thead><tr><th>Item</th><th>Student answer</th><th>Correct answer</th><th>Score</th><th>Feedback</th></tr></thead>
      <tbody>
        ${items.map((item) => `
          <tr>
            <td>${escapeHtml(item.item_number || '')}</td>
            <td>${escapeHtml(item.student_answer || '')}</td>
            <td>${escapeHtml(item.correct_answer || '')}</td>
            <td>${escapeHtml(item.score ?? '')} / ${escapeHtml(item.max_score ?? '')}</td>
            <td>${escapeHtml(item.feedback || '')}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

async function loadClassRecords() {
  const data = await api('/api/class-records/classes');
  state.classRecords = data.classes || [];
  if (state.activeClassRecord) {
    const current = state.classRecords.find((record) => record.id === state.activeClassRecord.class.id);
    if (current) {
      await selectClassRecord(current.id);
      return;
    }
    state.activeClassRecord = null;
  }
  renderClassRecordsWorkspace();
}

async function createClassRecord(event) {
  event.preventDefault();
  const data = await api('/api/class-records/classes', {
    method: 'POST',
    body: JSON.stringify({
      name: els.classRecordName.value.trim(),
      grade_level: els.classRecordGrade.value.trim(),
      section: els.classRecordSection.value.trim(),
      subject: els.classRecordSubject.value.trim(),
      school_year: els.classRecordSchoolYear.value.trim(),
    }),
  });
  els.classRecordForm.reset();
  await selectClassRecord(data.class.id);
  await loadClassRecords();
  setStatus('Class record created.');
}

async function selectClassRecord(classId) {
  const data = await api(`/api/class-records/classes/${classId}`);
  const attendanceDate = state.activeAttendanceDate || todayIsoDate();
  const [students, assessments, attendanceGrid, attendanceSummary] = await Promise.all([
    api(`/api/class-records/classes/${classId}/students`),
    api(`/api/class-records/classes/${classId}/assessments`),
    api(`/api/class-records/classes/${classId}/attendance?attendance_date=${encodeURIComponent(attendanceDate)}`),
    api(`/api/class-records/classes/${classId}/attendance/summary?days=220`),
  ]);
  state.activeClassRecord = {
    class: data.class,
    dashboard: data.dashboard,
    students: students.students || [],
    assessments: assessments.assessments || [],
    attendanceGrid,
    attendanceSummary: attendanceSummary.summary,
  };
  state.activeAttendanceDate = attendanceGrid.attendance_date || attendanceDate;
  state.activeClassTab = state.activeClassTab || 'dashboard';
  renderClassRecordsWorkspace();
}

async function addClassStudent(event) {
  event.preventDefault();
  const classId = state.activeClassRecord?.class?.id;
  if (!classId) return;
  const form = event.currentTarget;
  await api(`/api/class-records/classes/${classId}/students`, {
    method: 'POST',
    body: JSON.stringify({
      learner_reference_number: form.querySelector('[name="lrn"]').value.trim(),
      first_name: form.querySelector('[name="first_name"]').value.trim(),
      middle_name: form.querySelector('[name="middle_name"]').value.trim(),
      last_name: form.querySelector('[name="last_name"]').value.trim(),
      status: form.querySelector('[name="status"]').value,
    }),
  });
  form.reset();
  await selectClassRecord(classId);
  await loadClassRecords();
  setStatus('Student added.');
}

async function addClassAssessment(event) {
  event.preventDefault();
  const classId = state.activeClassRecord?.class?.id;
  if (!classId) return;
  const form = event.currentTarget;
  await api(`/api/class-records/classes/${classId}/assessments`, {
    method: 'POST',
    body: JSON.stringify({
      title: form.querySelector('[name="title"]').value.trim(),
      assessment_type: form.querySelector('[name="assessment_type"]').value,
      assessment_date: form.querySelector('[name="assessment_date"]').value,
      max_score: Number(form.querySelector('[name="max_score"]').value),
      weight: form.querySelector('[name="weight"]').value ? Number(form.querySelector('[name="weight"]').value) : null,
      notes: form.querySelector('[name="notes"]').value.trim(),
    }),
  });
  form.reset();
  await selectClassRecord(classId);
  await loadClassRecords();
  setStatus('Assessment created.');
}

async function openScoreEntry(assessmentId) {
  state.activeScoreAssessmentId = assessmentId;
  const grid = await api(`/api/class-records/assessments/${assessmentId}/scores`);
  renderScoreEntry(grid);
}

async function saveScoreEntry(event) {
  event.preventDefault();
  const assessmentId = state.activeScoreAssessmentId;
  if (!assessmentId) return;
  const scores = [...event.currentTarget.querySelectorAll('[data-score-row]')].map((row) => ({
    student_id: Number(row.dataset.studentId),
    score: row.querySelector('[name="score"]').value === '' ? null : Number(row.querySelector('[name="score"]').value),
    is_absent: row.querySelector('[name="is_absent"]').checked,
    notes: row.querySelector('[name="notes"]').value.trim(),
  }));
  const grid = await api(`/api/class-records/assessments/${assessmentId}/scores`, {
    method: 'PUT',
    body: JSON.stringify({ scores }),
  });
  await selectClassRecord(state.activeClassRecord.class.id);
  renderScoreEntry(grid);
  setStatus('Scores saved.');
}

async function loadAttendanceDate(attendanceDate) {
  const classId = state.activeClassRecord?.class?.id;
  if (!classId) return;
  const grid = await api(`/api/class-records/classes/${classId}/attendance?attendance_date=${encodeURIComponent(attendanceDate)}`);
  state.activeAttendanceDate = grid.attendance_date;
  state.activeClassRecord = {
    ...state.activeClassRecord,
    attendanceGrid: grid,
  };
  renderClassRecordsWorkspace();
}

async function saveAttendance(event) {
  event.preventDefault();
  const classId = state.activeClassRecord?.class?.id;
  if (!classId) return;
  const form = event.currentTarget;
  const attendanceDate = form.querySelector('[name="attendance_date"]').value || todayIsoDate();
  const rows = [...form.querySelectorAll('[data-attendance-row]')].map((row) => ({
    student_id: Number(row.dataset.studentId),
    status: row.querySelector('[name="attendance_status"]').value,
    notes: row.querySelector('[name="attendance_notes"]').value.trim(),
  }));
  const grid = await api(`/api/class-records/classes/${classId}/attendance`, {
    method: 'PUT',
    body: JSON.stringify({ attendance_date: attendanceDate, rows }),
  });
  const summary = await api(`/api/class-records/classes/${classId}/attendance/summary?days=220`);
  state.activeAttendanceDate = grid.attendance_date;
  state.activeClassRecord = {
    ...state.activeClassRecord,
    attendanceGrid: grid,
    attendanceSummary: summary.summary,
  };
  renderClassRecordsWorkspace();
  setStatus('Attendance saved.');
}

function renderClassRecordsWorkspace() {
  els.classRecordsPanel?.classList.toggle('class-records-panel--detail', Boolean(state.activeClassRecord));
  renderClassRecordList();
  renderClassRecordDetail();
}

function renderClassRecordList() {
  if (!els.classRecordsList) return;
  if (!state.classRecords.length) {
    els.classRecordsList.innerHTML = '<p>No class records yet.</p>';
    return;
  }
  els.classRecordsList.innerHTML = state.classRecords.map((record) => `
    <button class="list-item class-record-button" type="button" data-class-id="${record.id}">
      <h3>${escapeHtml(record.name)}</h3>
      <p>Grade ${escapeHtml(record.grade_level)}${record.section ? `-${escapeHtml(record.section)}` : ''} | ${escapeHtml(record.subject)} | ${record.student_count || 0} students</p>
      <p>Average ${formatPercent(record.latest_average)}</p>
    </button>
  `).join('');
  els.classRecordsList.querySelectorAll('[data-class-id]').forEach((button) => {
    button.addEventListener('click', () => runUserAction(
      button,
      'Opening class record...',
      () => selectClassRecord(Number(button.dataset.classId)),
      { busyText: 'Opening...' },
    ));
  });
}

function renderClassRecordDetail() {
  const active = state.activeClassRecord;
  if (!active) {
    els.classRecordDetail.innerHTML = '<div class="empty-state">Select or create a class to open its workspace.</div>';
    return;
  }
  const dashboard = active.dashboard || {};
  const activeTab = state.activeClassTab || 'dashboard';
  const classAverage = formatPercent(dashboard.class_average);
  const tabs = [
    ['dashboard', 'Dashboard'],
    ['students', 'Students'],
    ['attendance', 'Attendance'],
    ['attendance_performance', 'Attendance Performance'],
    ['assessments', 'Assessments'],
    ['performance', 'Student Performance'],
    ['insights', 'Insights'],
  ];
  const tabButtons = tabs.map(([value, label]) => `
    <button class="class-tab${activeTab === value ? ' class-tab--on' : ''}" type="button" data-class-tab="${value}">${label}</button>
  `).join('');
  const tabPanels = {
    dashboard: `
      <section class="class-tab-panel">
        <div class="metric-grid">
          <article><span>Class average</span><strong>${classAverage}</strong></article>
          <article><span>Students</span><strong>${dashboard.student_count || 0}</strong></article>
          <article><span>Assessments</span><strong>${dashboard.assessment_count || 0}</strong></article>
          <article><span>Missing/absent</span><strong>${dashboard.missing_or_absent_count || 0}</strong></article>
        </div>
        <div class="class-dashboard-grid">
          ${renderClassDashboardGraphs(dashboard, active.attendanceSummary)}
          <div class="class-dashboard-actions">
            <h4>Next actions</h4>
            <div class="button-row">
              <button class="secondary compact" type="button" data-jump-class-tab="students">Add Students</button>
              <button class="secondary compact" type="button" data-jump-class-tab="attendance">Take Attendance</button>
              <button class="secondary compact" type="button" data-jump-class-tab="attendance_performance">Review Attendance</button>
              <button class="secondary compact" type="button" data-jump-class-tab="assessments">Create Assessments</button>
              <button class="secondary compact" type="button" data-jump-class-tab="performance">Review Performance</button>
            </div>
          </div>
        </div>
      </section>
    `,
    students: `
      <section class="class-tab-panel">
        <div class="class-tab-panel__head">
          <h4>Add Students</h4>
          <p class="microcopy">Build the roster for this class before entering scores.</p>
        </div>
        ${renderStudentForm()}
        ${renderStudentTable(active.students || [])}
      </section>
    `,
    attendance: `
      <section class="class-tab-panel">
        <div class="class-tab-panel__head">
          <h4>Daily Attendance</h4>
          <p class="microcopy">Capture attendance for a selected date and review recent daily attendance in one view.</p>
        </div>
        ${renderAttendanceCapture(active.attendanceGrid)}
      </section>
    `,
    attendance_performance: `
      <section class="class-tab-panel">
        <div class="class-tab-panel__head">
          <h4>Attendance Performance</h4>
          <p class="microcopy">Review each student's daily attendance across saved class dates.</p>
        </div>
        ${renderAttendancePerformance(active.attendanceSummary)}
      </section>
    `,
    assessments: `
      <section class="class-tab-panel">
        <div class="class-tab-panel__head">
          <h4>Create Assessments</h4>
          <p class="microcopy">Add quizzes, exams, projects, or other score columns.</p>
        </div>
        ${renderAssessmentForm()}
        ${renderAssessmentTable(active.assessments || [])}
      </section>
    `,
    performance: `
      <section class="class-tab-panel">
        <div class="class-tab-panel__head">
          <h4>Student Performance</h4>
          <p class="microcopy">Use the indicators to spot learners who may need follow-up.</p>
        </div>
        ${renderPerformanceDashboard(dashboard)}
        ${renderPerformanceTable(dashboard.students || [], {
          assessments: dashboard.assessments || active.assessments || [],
          showAssessmentResults: true,
        })}
      </section>
    `,
    insights: `
      <section class="class-tab-panel">
        <div class="class-tab-panel__head">
          <h4>AI Insights</h4>
          <p class="microcopy">Generate an actionable briefing from current class data. Each click re-runs the AI model against the latest scores, attendance, and assessments.</p>
        </div>
        <div class="class-insights-panel">
          <div class="class-insights-toolbar">
            <button class="primary compact" type="button" data-class-insights-generate>Generate Insights</button>
            <span class="class-insights-status microcopy">${active.insights
              ? (active.insights.empty ? 'No insights yet — add students and scores first.' : `Generated with ${escapeHtml(active.insights.model || '')}.`)
              : ''
            }</span>
          </div>
          <div class="class-insights-output draft-preview">
            ${active.insights
              ? markdownToHtml(active.insights.answer || '')
              : '<div class="draft-preview__empty">Click <strong>Generate Insights</strong> to summarize this class with AI.</div>'
            }
          </div>
        </div>
      </section>
    `,
  };
  els.classRecordDetail.innerHTML = `
    <div class="class-detail-head">
      <div>
        <h3>${escapeHtml(active.class.name)}</h3>
        <p>${escapeHtml(active.class.subject)} | Grade ${escapeHtml(active.class.grade_level)}${active.class.section ? `-${escapeHtml(active.class.section)}` : ''} | ${escapeHtml(active.class.school_year || 'No school year')}</p>
      </div>
      <div class="button-row">
        <button class="ghost compact" type="button" data-close-active-class>Classes</button>
        <button class="ghost compact" type="button" data-refresh-active>Refresh</button>
      </div>
    </div>
    <div class="class-record-tabs" role="tablist" aria-label="Class workspace">
      ${tabButtons}
    </div>
    ${tabPanels[activeTab] || tabPanels.dashboard}
    <div id="score-entry-host"></div>
  `;
  els.classRecordDetail.querySelectorAll('[data-class-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      state.activeClassTab = button.dataset.classTab;
      state.activeScoreAssessmentId = null;
      renderClassRecordsWorkspace();
    });
  });
  els.classRecordDetail.querySelectorAll('[data-jump-class-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      state.activeClassTab = button.dataset.jumpClassTab;
      renderClassRecordsWorkspace();
    });
  });
  els.classRecordDetail.querySelector('[data-refresh-active]').addEventListener('click', (event) => runUserAction(
    event,
    'Refreshing class details...',
    () => selectClassRecord(active.class.id),
    { busyText: 'Refreshing...' },
  ));
  els.classRecordDetail.querySelector('[data-close-active-class]').addEventListener('click', () => {
    state.activeClassRecord = null;
    state.activeScoreAssessmentId = null;
    state.activeClassTab = 'dashboard';
    renderClassRecordsWorkspace();
    setStatus('Class workspace closed.');
  });
  els.classRecordDetail.querySelector('[data-student-form]')?.addEventListener('submit', (event) => {
    event.preventDefault();
    runUserAction(event, 'Adding student...', () => addClassStudent(event), { busyText: 'Adding...' });
  });
  els.classRecordDetail.querySelector('[data-assessment-form]')?.addEventListener('submit', (event) => {
    event.preventDefault();
    runUserAction(event, 'Creating assessment...', () => addClassAssessment(event), { busyText: 'Creating...' });
  });
  els.classRecordDetail.querySelectorAll('[data-score-assessment]').forEach((button) => {
    button.addEventListener('click', () => runUserAction(
      button,
      'Opening score entry...',
      () => openScoreEntry(Number(button.dataset.scoreAssessment)),
      { busyText: 'Opening...' },
    ));
  });
  els.classRecordDetail.querySelector('[data-attendance-form]')?.addEventListener('submit', (event) => {
    event.preventDefault();
    runUserAction(event, 'Saving attendance...', () => saveAttendance(event), { busyText: 'Saving...' });
  });
  els.classRecordDetail.querySelector('[data-attendance-date]')?.addEventListener('change', (event) => {
    runUserAction(event.currentTarget, 'Loading attendance...', () => loadAttendanceDate(event.currentTarget.value), { busyText: 'Loading...' });
  });
  els.classRecordDetail.querySelectorAll('[data-mark-attendance]').forEach((button) => {
    button.addEventListener('click', () => {
      const status = button.dataset.markAttendance;
      els.classRecordDetail.querySelectorAll('[name="attendance_status"]').forEach((select) => {
        select.value = status;
      });
    });
  });
  els.classRecordDetail.querySelector('[data-class-insights-generate]')?.addEventListener('click', (event) => {
    runUserAction(event, 'Generating insights…', generateClassInsights, { busyText: 'Generating…' });
  });
  syncAttendanceTableScrollers();
  syncPerformanceTableScrollers();
}

function renderClassDashboardGraphs(dashboard, attendanceSummary) {
  const attendanceStudents = attendanceSummary?.students || [];
  return `
    <section class="class-dashboard-section">
      <div class="class-tab-panel__head">
        <h4>Attendance Performance</h4>
      </div>
      ${renderAttendancePerformanceDashboard(attendanceStudents)}
    </section>
    <section class="class-dashboard-section">
      <div class="class-tab-panel__head">
        <h4>Student Performance</h4>
      </div>
      ${renderPerformanceDashboard(dashboard)}
    </section>
  `;
}

function renderStudentForm() {
  return `
    <form class="inline-record-form" data-student-form>
      <input class="record-field--main" name="first_name" type="text" placeholder="First name" required />
      <input name="middle_name" type="text" placeholder="Middle" />
      <input class="record-field--main" name="last_name" type="text" placeholder="Last name" required />
      <input name="lrn" type="text" placeholder="LRN" />
      <select name="status">
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
        <option value="transferred">Transferred</option>
      </select>
      <button class="primary compact" type="submit">Add</button>
    </form>
  `;
}

function renderAssessmentForm() {
  const today = todayIsoDate();
  return `
    <form class="inline-record-form assessment-form" data-assessment-form>
      <input class="record-field--title" name="title" type="text" placeholder="Quiz 1: Human Body Systems" required />
      <select name="assessment_type">
        <option value="quiz">Quiz</option>
        <option value="exam">Exam</option>
        <option value="project">Project</option>
        <option value="performance_task">Performance task</option>
        <option value="assignment">Assignment</option>
        <option value="other">Other</option>
      </select>
      <input name="assessment_date" type="date" value="${today}" required />
      <input name="max_score" type="text" inputmode="decimal" placeholder="Max" required />
      <input name="weight" type="text" inputmode="decimal" placeholder="Weight" />
      <input class="record-field--notes" name="notes" type="text" placeholder="Notes" />
      <button class="primary compact" type="submit">Create</button>
    </form>
  `;
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function renderStudentTable(students) {
  if (!students.length) return '<p class="microcopy">No students yet.</p>';
  return `
    <div class="table-scroll"><table class="records-table">
      <thead><tr><th>Name</th><th>Status</th><th>Average</th><th>Missing</th><th>Absent</th></tr></thead>
      <tbody>${students.map((student) => `
        <tr>
          <td>${escapeHtml(student.display_name || `${student.first_name} ${student.last_name}`)}</td>
          <td>${escapeHtml(student.status)}</td>
          <td>${formatPercent(student.average_percentage)}</td>
          <td>${student.missing_count || 0}</td>
          <td>${student.absent_count || 0}</td>
        </tr>
      `).join('')}</tbody>
    </table></div>
  `;
}

function renderAttendanceCapture(grid) {
  const attendanceDate = grid?.attendance_date || state.activeAttendanceDate || todayIsoDate();
  const rows = grid?.rows || [];
  const summary = grid?.summary || {};
  if (!rows.length) {
    return '<p class="microcopy">Add students before taking attendance.</p>';
  }
  return `
    <form class="attendance-panel" data-attendance-form>
      <div class="attendance-toolbar">
        <label>
          Date
          <input name="attendance_date" data-attendance-date type="date" value="${escapeHtml(attendanceDate)}" required />
        </label>
        <div class="attendance-actions">
          <button class="secondary compact" type="button" data-mark-attendance="present">Mark all present</button>
          <button class="secondary compact" type="button" data-mark-attendance="absent">Mark all absent</button>
          <button class="primary compact" type="submit">Save attendance</button>
        </div>
      </div>
      <div class="metric-grid attendance-metrics">
        <article><span>Present</span><strong>${summary.present || 0}</strong></article>
        <article><span>Late</span><strong>${summary.late || 0}</strong></article>
        <article><span>Absent</span><strong class="${summary.absent ? 'attendance-count--alert' : ''}">${summary.absent || 0}</strong></article>
        <article><span>Attendance rate</span><strong>${formatPercent(summary.attendance_rate)}</strong></article>
      </div>
      <div class="table-scroll"><table class="records-table attendance-entry-table">
        <thead><tr><th>Student</th><th>Status</th><th>Notes</th><th>Recorded</th></tr></thead>
        <tbody>${rows.map((row) => `
          <tr data-attendance-row data-student-id="${row.student.id}">
            <td>${escapeHtml(row.student.display_name || `${row.student.first_name} ${row.student.last_name}`)}</td>
            <td><select name="attendance_status">${attendanceStatusOptions(row.status)}</select></td>
            <td><input name="attendance_notes" type="text" value="${escapeHtml(row.notes || '')}" placeholder="Optional note" /></td>
            <td>${row.is_recorded ? '<span class="status-pill">Saved</span>' : '<span class="score-cell--muted">New</span>'}</td>
          </tr>
        `).join('')}</tbody>
      </table></div>
    </form>
  `;
}

function renderAttendancePerformance(summary) {
  const dates = summary?.dates || [];
  const students = summary?.students || [];
  const daySummaries = summary?.day_summaries || [];
  if (!dates.length) {
    return `
      <p class="microcopy">Save daily attendance to build the attendance performance view.</p>
    `;
  }
  return `
    ${renderAttendancePerformanceDashboard(students)}
    ${renderAttendancePerformanceTable(students, dates, daySummaries)}
  `;
}

function renderAttendancePerformanceDashboard(students) {
  return `
    <div class="attendance-performance-dashboard">
      <article>
        <h4>Student attendance bands</h4>
        ${renderAttendanceBandPie(students)}
      </article>
      <article>
        <h4>Present vs absent</h4>
        ${renderPresentAbsentPie(students)}
      </article>
    </div>
  `;
}

function renderAttendanceBandPie(students) {
  const summaries = students.map(studentAttendanceSummary);
  const buckets = [
    ['95-100%', summaries.filter((summary) => summary.rate !== null && summary.rate >= 95).length],
    ['90-94%', summaries.filter((summary) => summary.rate !== null && summary.rate >= 90 && summary.rate < 95).length],
    ['75-89%', summaries.filter((summary) => summary.rate !== null && summary.rate >= 75 && summary.rate < 90).length],
    ['0-74%', summaries.filter((summary) => summary.rate !== null && summary.rate < 75).length],
    ['No data', summaries.filter((summary) => summary.rate === null).length],
  ];
  return renderPieSummary(buckets, {
    emptyLabel: 'No student attendance data yet.',
    lowLabels: ['0-74%'],
  });
}

function renderPresentAbsentPie(students) {
  const summaries = students.map(studentAttendanceSummary);
  const present = summaries.reduce((total, summary) => total + summary.present + summary.late, 0);
  const absent = summaries.reduce((total, summary) => total + summary.absent, 0);
  return renderPieSummary([
    ['Present', present],
    ['Absent', absent],
  ], {
    emptyLabel: 'No present or absent marks yet.',
    lowLabels: ['Absent'],
  });
}

function renderPieSummary(items, options = {}) {
  const total = items.reduce((sum, [, count]) => sum + Number(count || 0), 0);
  if (!total) return `<p class="microcopy">${escapeHtml(options.emptyLabel || 'No data yet.')}</p>`;
  const colors = ['var(--green-700)', 'var(--danger)', 'var(--amber-700)', 'var(--slate-800)', 'var(--ink-500)'];
  let cursor = 0;
  const segments = items.map(([label, count], index) => {
    const value = Number(count || 0);
    const start = cursor;
    const end = cursor + (value / total) * 100;
    cursor = end;
    return `${colors[index % colors.length]} ${start}% ${end}%`;
  });
  return `
    <div class="pie-summary">
      <div class="pie-chart" style="background: conic-gradient(${segments.join(', ')})" role="img" aria-label="Distribution chart"></div>
      <div class="pie-legend">
        ${items.map(([label, count], index) => {
          const low = (options.lowLabels || []).includes(label) && count;
          const percent = total ? roundToOne((Number(count || 0) / total) * 100) : null;
          return `
            <div class="pie-legend-row">
              <span><i style="background: ${colors[index % colors.length]}"></i>${escapeHtml(label)}</span>
              <strong class="${low ? 'performance-value--low' : ''}">${count} <small>${formatPercent(percent)}</small></strong>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

function renderAttendancePerformanceTable(students, dates, daySummaries = []) {
  const tableMinWidth = Math.max(900, 520 + dates.length * 96);
  const daySummaryByDate = new Map(daySummaries.map((day) => [day.attendance_date, day]));
  return `
    <section class="attendance-performance">
      <div class="class-tab-panel__head">
        <h4>Daily Attendance by Student</h4>
        <p class="microcopy">Present and late count toward attendance rate; daily averages below 75% are highlighted.</p>
      </div>
      <div class="table-scroll-control" data-attendance-scroll-top>
        <input type="range" min="0" max="0" value="0" aria-label="Daily attendance horizontal scroll" />
      </div>
      <div class="table-scroll" data-attendance-scroll-main><table class="records-table attendance-performance-table" style="min-width: ${tableMinWidth}px">
        <thead>
          <tr>
            <th>Student</th>
            <th>Rate</th>
            <th>Present</th>
            <th>Late</th>
            <th>Absent</th>
            ${dates.map((date) => `<th>${escapeHtml(formatShortDate(date))}</th>`).join('')}
          </tr>
          <tr class="attendance-average-row">
            <th colspan="5">Daily average</th>
            ${dates.map((date) => {
              const rate = daySummaryByDate.get(date)?.attendance_rate ?? null;
              const low = rate !== null && Number(rate) < 75;
              return `<th class="${low ? 'performance-value--low' : ''}">${formatPercent(rate)}</th>`;
            }).join('')}
          </tr>
        </thead>
        <tbody>${students.map((student) => {
          const summary = studentAttendanceSummary(student);
          return `
            <tr>
              <td>${escapeHtml(student.display_name || `${student.first_name} ${student.last_name}`)}</td>
              <td class="${summary.rate !== null && summary.rate < 75 ? 'performance-value--low' : ''}">${formatPercent(summary.rate)}</td>
              <td>${summary.present}</td>
              <td>${summary.late}</td>
              <td class="${summary.absent ? 'performance-value--low' : ''}">${summary.absent}</td>
              ${(student.attendance_records || []).map((record) => renderAttendanceStatusCell(record)).join('')}
            </tr>
          `;
        }).join('')}</tbody>
      </table></div>
    </section>
  `;
}

function syncAttendanceTableScrollers() {
  const topScroller = els.classRecordDetail.querySelector('[data-attendance-scroll-top] input');
  const mainScroller = els.classRecordDetail.querySelector('[data-attendance-scroll-main]');
  if (!topScroller || !mainScroller) return;
  syncRangeTableScroller(topScroller, mainScroller);
}

function studentAttendanceSummary(student) {
  const records = student.attendance_records || [];
  const recorded = records.filter((record) => record?.is_recorded);
  const present = recorded.filter((record) => record.status === 'present').length;
  const late = recorded.filter((record) => record.status === 'late').length;
  const absent = recorded.filter((record) => record.status === 'absent').length;
  const excused = recorded.filter((record) => record.status === 'excused').length;
  const rate = recorded.length ? roundToOne((present + late) / recorded.length * 100) : null;
  return {
    present,
    late,
    absent,
    excused,
    recorded: recorded.length,
    rate,
  };
}

function attendanceStatusOptions(selectedStatus) {
  return [
    ['present', 'Present'],
    ['absent', 'Absent'],
    ['late', 'Late'],
    ['excused', 'Excused'],
  ].map(([value, label]) => `<option value="${value}" ${selectedStatus === value ? 'selected' : ''}>${label}</option>`).join('');
}

function renderAttendanceStatusCell(record, options = {}) {
  if (!record || !record.is_recorded) {
    return '<td><span class="attendance-status attendance-status--missing">No record</span></td>';
  }
  return `
    <td>
      <span class="attendance-status attendance-status--${escapeHtml(record.status)}">${escapeHtml(formatAttendanceStatus(record.status))}</span>
      ${options.showNotes && record.notes ? `<small>${escapeHtml(record.notes)}</small>` : ''}
    </td>
  `;
}

function formatAttendanceStatus(status) {
  return {
    present: 'Present',
    absent: 'Absent',
    late: 'Late',
    excused: 'Excused',
  }[status] || 'No record';
}

function formatShortDate(value) {
  if (!value) return '';
  const [, month = '', day = ''] = String(value).split('-');
  return `${month}/${day}`;
}

function renderAssessmentTable(assessments) {
  if (!assessments.length) return '<p class="microcopy">No assessments yet.</p>';
  return `
    <div class="table-scroll"><table class="records-table">
      <thead><tr><th>Assessment</th><th>Type</th><th>Date</th><th>Average</th><th>Done</th><th></th></tr></thead>
      <tbody>${assessments.map((assessment) => `
        <tr>
          <td>${escapeHtml(assessment.title)}</td>
          <td>${escapeHtml(assessment.assessment_type)}</td>
          <td>${escapeHtml(assessment.assessment_date)}</td>
          <td>${formatPercent(assessment.average_percentage)}</td>
          <td>${assessment.completion_count || 0}</td>
          <td><button class="secondary compact" type="button" data-score-assessment="${assessment.id}">Scores</button></td>
        </tr>
      `).join('')}</tbody>
    </table></div>
  `;
}

function renderPerformanceTable(students, options = {}) {
  if (!students.length) return '<p class="microcopy">Add scores to see performance indicators.</p>';
  const assessments = options.assessments || [];
  const showAssessmentResults = Boolean(options.showAssessmentResults && assessments.length);
  const tableMinWidth = showAssessmentResults ? Math.max(760, 380 + assessments.length * 150) : 620;
  const studentAverages = students
    .map((student) => student.average_percentage)
    .filter((value) => value !== null && value !== undefined)
    .map(Number);
  const classAverage = studentAverages.length
    ? roundToOne(studentAverages.reduce((total, value) => total + value, 0) / studentAverages.length)
    : null;
  return `
    <div class="table-scroll-control" data-performance-scroll-top>
      <input type="range" min="0" max="0" value="0" aria-label="Student performance horizontal scroll" />
    </div>
    <div class="table-scroll" data-performance-scroll-main><table class="records-table performance-table" style="min-width: ${tableMinWidth}px">
      <thead>
        <tr>
          <th>Student</th>
          <th>Average</th>
          ${showAssessmentResults ? assessments.map((assessment) => `
            <th>
              <span class="assessment-column-title">${escapeHtml(assessment.title)}</span>
              <small>Max ${formatNumber(assessment.max_score)}</small>
            </th>
          `).join('') : ''}
          <th>Indicator</th>
        </tr>
        <tr class="performance-average-row">
          <th>Assessment average</th>
          <th class="${isBelowTarget(classAverage) ? 'performance-value--low' : ''}">${formatPercent(classAverage)}</th>
          ${showAssessmentResults ? assessments.map((assessment) => {
            const low = isBelowTarget(assessment.average_percentage);
            return `<th class="${low ? 'performance-value--low' : ''}">${formatPercent(assessment.average_percentage)}</th>`;
          }).join('') : ''}
          <th></th>
        </tr>
      </thead>
      <tbody>${students.map((student) => `
        <tr>
          <td>${escapeHtml(student.display_name || `${student.first_name} ${student.last_name}`)}</td>
          <td class="${isBelowTarget(student.average_percentage) ? 'performance-value--low' : ''}">${formatPercent(student.average_percentage)}</td>
          ${showAssessmentResults ? assessments.map((assessment) => renderAssessmentResultCell(
            (student.assessment_results || []).find((result) => Number(result.assessment_id) === Number(assessment.id)),
          )).join('') : ''}
          <td><span class="status-pill">${escapeHtml(student.status_indicator)}</span></td>
        </tr>
      `).join('')}</tbody>
    </table></div>
  `;
}

function renderPerformanceDashboard(dashboard) {
  const students = dashboard.students || [];
  return `
    <div class="performance-dashboard">
      <article>
        <h4>Student average bands</h4>
        ${renderStudentDistributionPie(students)}
      </article>
      <article>
        <h4>Top 5 students</h4>
        ${renderStudentRankList(students, 'top')}
      </article>
      <article>
        <h4>Bottom 5 students</h4>
        ${renderStudentRankList(students, 'bottom')}
      </article>
    </div>
  `;
}

function renderStudentDistributionPie(students) {
  const buckets = [
    ['90-100%', students.filter((student) => Number(student.average_percentage) >= 90).length],
    ['75-89%', students.filter((student) => Number(student.average_percentage) >= 75 && Number(student.average_percentage) < 90).length],
    ['60-74%', students.filter((student) => Number(student.average_percentage) >= 60 && Number(student.average_percentage) < 75).length],
    ['0-59%', students.filter((student) => student.average_percentage !== null && student.average_percentage !== undefined && Number(student.average_percentage) < 60).length],
    ['No data', students.filter((student) => student.average_percentage === null || student.average_percentage === undefined).length],
  ];
  return renderPieSummary(buckets, {
    emptyLabel: 'No student performance data yet.',
    lowLabels: ['60-74%', '0-59%'],
  });
}

function renderStudentRankList(students, direction) {
  const ranked = students
    .filter((student) => student.average_percentage !== null && student.average_percentage !== undefined)
    .sort((a, b) => Number(b.average_percentage) - Number(a.average_percentage));
  const selected = direction === 'bottom' ? ranked.slice(-5).reverse() : ranked.slice(0, 5);
  if (!selected.length) return '<p class="microcopy">No student averages yet.</p>';
  return `
    <ol class="rank-list">
      ${selected.map((student) => {
        const average = Number(student.average_percentage);
        return `
          <li>
            <span>${escapeHtml(student.display_name || `${student.first_name} ${student.last_name}`)}</span>
            <strong class="${isBelowTarget(average) ? 'performance-value--low' : ''}">${formatPercent(average)}</strong>
          </li>
        `;
      }).join('')}
    </ol>
  `;
}

function syncPerformanceTableScrollers() {
  const topScroller = els.classRecordDetail.querySelector('[data-performance-scroll-top] input');
  const mainScroller = els.classRecordDetail.querySelector('[data-performance-scroll-main]');
  if (!topScroller || !mainScroller) return;
  syncRangeTableScroller(topScroller, mainScroller);
}

function syncRangeTableScroller(rangeInput, tableScroller) {
  const maxScroll = Math.max(0, tableScroller.scrollWidth - tableScroller.clientWidth);
  rangeInput.max = String(maxScroll);
  rangeInput.disabled = maxScroll === 0;
  rangeInput.value = String(Math.min(Number(rangeInput.value || 0), maxScroll));
  rangeInput.addEventListener('input', () => {
    tableScroller.scrollLeft = Number(rangeInput.value || 0);
  });
  tableScroller.addEventListener('scroll', () => {
    rangeInput.value = String(Math.round(tableScroller.scrollLeft));
  });
}

function renderAssessmentResultCell(result) {
  if (!result || result.is_missing) {
    return '<td class="score-cell score-cell--muted">No data</td>';
  }
  if (result.is_absent) {
    return '<td class="score-cell score-cell--muted">Absent</td>';
  }
  const low = Boolean(result.is_below_target);
  return `
    <td class="score-cell ${low ? 'score-cell--low' : ''}">
      <strong>${formatPercent(result.percentage)}</strong>
      <span>${formatNumber(result.score)} / ${formatNumber(result.max_score)}</span>
    </td>
  `;
}

function renderScoreEntry(grid) {
  const host = document.getElementById('score-entry-host');
  if (!host) return;
  host.innerHTML = `
    <section class="score-entry-panel">
      <div class="class-detail-head">
        <div>
          <h4>Score Entry</h4>
          <p>${escapeHtml(grid.assessment.title)} | Max ${grid.assessment.max_score}</p>
        </div>
      </div>
      <form data-score-form>
        <div class="table-scroll"><table class="records-table">
          <thead><tr><th>Student</th><th>Score</th><th>Absent</th><th>Notes</th></tr></thead>
          <tbody>${grid.rows.map((row) => `
            <tr data-score-row data-student-id="${row.student.id}">
              <td>${escapeHtml(row.student.display_name)}</td>
              <td><input name="score" type="text" inputmode="decimal" value="${row.score ?? ''}" /></td>
              <td><input name="is_absent" type="checkbox" ${row.is_absent ? 'checked' : ''} /></td>
              <td><input name="notes" type="text" value="${escapeHtml(row.notes || '')}" /></td>
            </tr>
          `).join('')}</tbody>
        </table></div>
        <button class="primary compact" type="submit">Save scores</button>
      </form>
    </section>
  `;
  host.querySelector('[data-score-form]').addEventListener('submit', (event) => {
    event.preventDefault();
    runUserAction(event, 'Saving scores...', () => saveScoreEntry(event), { busyText: 'Saving...' });
  });
  host.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function formatPercent(value) {
  return value === null || value === undefined ? 'No data' : `${Number(value).toFixed(Number(value) % 1 === 0 ? 0 : 1)}%`;
}

function roundToOne(value) {
  return Math.round(Number(value) * 10) / 10;
}

function formatNumber(value) {
  if (value === null || value === undefined || value === '') return 'No data';
  return Number(value).toFixed(Number(value) % 1 === 0 ? 0 : 1);
}

function isBelowTarget(value, target = 75) {
  return value !== null && value !== undefined && Number(value) < target;
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
  item.querySelector('[data-action="open"]').addEventListener('click', (event) => runUserAction(
    event,
    'Opening saved output...',
    () => openOutput(output),
    { busyText: 'Opening...' },
  ));
  item.querySelector('[data-action="share"]').addEventListener('click', (event) => runUserAction(event, 'Creating share link...', async () => {
      await openOutput(output);
      await shareOutput(output.id);
    }, { busyText: 'Sharing...' }));
  item.querySelector('[data-action="regenerate"]').addEventListener('click', (event) => runUserAction(event, 'Regenerating saved output...', async () => {
      switchWorkspace('draft');
      await streamRegenerate(output);
    }, { busyText: 'Regenerating...' }));
  item.querySelector('[data-action="delete"]').addEventListener('click', (event) => runUserAction(event, 'Deleting saved output...', async () => {
      await api(`/api/library/${output.id}`, { method: 'DELETE' });
      if (state.currentOutputId === output.id) {
        state.currentOutputId = null;
        state.currentOutput = null;
      }
      await loadLibrary();
      setStatus('Deleted saved output.');
    }, { busyText: 'Deleting...' }));
  return item;
}

async function openOutput(output) {
  switchWorkspace('draft');
  state.currentOutputId = output.id;
  state.currentOutput = output;
  state.currentInputs = output.inputs;
  setTeachingAidTarget(output);
  setFormFromInputs(output.inputs);
  setEditorValue(output.content_md);
  setDraftView('preview');
  if (output.kind === 'lesson_plan') {
    await loadTeachingAids(output.id);
  } else {
    resetTeachingAids();
  }
  setStatus('Saved output opened.');
}

function newLesson(kind = 'lesson_plan') {
  switchWorkspace('draft');
  state.currentInputs = null;
  state.currentOutputId = null;
  state.currentOutput = null;
  resetTeachingAids();
  els.generateForm.reset();
  els.kind.value = kind;
  updateFormats();
  setEditorValue('');
  setDraftView('preview');
  setStatus(kind === 'assessment' ? 'New assessment draft ready.' : 'New lesson plan draft ready.');
}

function openLessonWorkspace(kind = 'lesson_plan') {
  newLesson(kind);
  requestAnimationFrame(() => els.gradeLevel?.focus());
}

async function openTeachingAidsWorkspace() {
  switchWorkspace('teaching-aids');
  if (state.currentOutput?.kind === 'lesson_plan') {
    setTeachingAidTarget(state.currentOutput);
  }
  if (!state.libraryOutputs.length) {
    await loadLibrary();
  }
  const targetId = teachingAidTargetId();
  if (targetId) {
    await loadTeachingAids(targetId);
  } else {
    renderTeachingAids();
  }
  setStatus(targetId ? `Teaching Aids ready for ${teachingAidTargetLabel(teachingAidTargetOutput())}.` : 'Open or save a lesson before generating Teaching Aids.');
}

function openClassWorkspace(focusCreate = false) {
  switchWorkspace('class-records');
  runUserAction(els.classRecordsButton, 'Loading class records...', loadClassRecords, { busyText: 'Loading...' });
  if (focusCreate) {
    requestAnimationFrame(() => els.classRecordName?.focus());
  }
}

function openAdminWorkspace(workspace, loader, control) {
  switchWorkspace(workspace);
  if (state.teacher?.is_admin) {
    runUserAction(control, 'Loading admin workspace...', loader, { busyText: 'Loading...' });
  }
}

function handleHomeAction(action) {
  const actions = {
    'lesson-plan': () => openLessonWorkspace('lesson_plan'),
    assessment: () => openLessonWorkspace('assessment'),
    'teaching-aids': () => runUserAction(els.teachingAidsButton, 'Opening Teaching Aids...', openTeachingAidsWorkspace, { busyText: 'Opening...' }),
    library: () => {
      switchWorkspace('library');
      runUserAction(els.libraryButton, 'Loading library...', loadLibrary, { busyText: 'Loading...' });
    },
    'create-class': () => openClassWorkspace(true),
    'grade-quiz': () => {
      switchWorkspace('grading');
      runUserAction(els.gradingButton, 'Loading grading batches...', loadGradingBatches, { busyText: 'Loading...' });
    },
    'all-classes': () => openClassWorkspace(false),
    'teacher-admin': () => openAdminWorkspace('teacher-admin', loadTeachers, els.adminToggle),
    curriculum: () => openAdminWorkspace('curriculum', loadCurriculumDocuments, els.curriculumToggle),
    'plan-formats': () => openAdminWorkspace('plan-formats', loadLessonPlanFormats, els.formatAdminToggle),
    help: () => switchWorkspace('help'),
  };
  actions[action]?.();
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
      setTeachingAidTarget(data.output);
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
  setTeachingAidTarget(data.output);
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

function lessonPlanOutputs() {
  const outputs = [...state.libraryOutputs];
  if (state.currentOutput?.kind === 'lesson_plan' && !outputs.some((output) => output.id === state.currentOutput.id)) {
    outputs.unshift(state.currentOutput);
  }
  return outputs.filter((output) => output.kind === 'lesson_plan');
}

function teachingAidTargetOutput() {
  const targetId = state.teachingAidTargetId || (state.currentOutput?.kind === 'lesson_plan' ? state.currentOutput.id : null);
  if (!targetId) return null;
  if (state.currentOutput?.id === targetId) return state.currentOutput;
  return lessonPlanOutputs().find((output) => output.id === targetId) || null;
}

function teachingAidTargetId() {
  return teachingAidTargetOutput()?.id || null;
}

function teachingAidTargetLabel(output) {
  if (!output) return 'No target lesson';
  const grades = outputGrades(output).join(', ') || 'No grade';
  const updated = output.updated_at ? ` | Updated ${String(output.updated_at).slice(0, 16).replace('T', ' ')}` : '';
  return `${output.topic || 'Untitled lesson'} | ${output.subject || 'No subject'} | ${grades}${updated}`;
}

function setTeachingAidTarget(output) {
  if (output?.kind === 'lesson_plan') {
    state.teachingAidTargetId = output.id;
  }
}

function renderTeachingAidTargets() {
  if (!els.teachingAidTarget) return;
  const lessons = lessonPlanOutputs();
  const currentTarget = teachingAidTargetOutput();
  els.teachingAidTarget.innerHTML = '';
  if (!lessons.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No saved lessons';
    els.teachingAidTarget.appendChild(option);
    els.teachingAidTarget.disabled = true;
    if (els.teachingAidTargetMeta) {
      els.teachingAidTargetMeta.textContent = 'Open or save a lesson plan before generating Teaching Aids.';
    }
    return;
  }
  lessons.forEach((output) => {
    const option = document.createElement('option');
    option.value = String(output.id);
    option.textContent = teachingAidTargetLabel(output);
    els.teachingAidTarget.appendChild(option);
  });
  const target = currentTarget || lessons[0];
  state.teachingAidTargetId = target.id;
  els.teachingAidTarget.disabled = false;
  els.teachingAidTarget.value = String(target.id);
  if (els.teachingAidTargetMeta) {
    els.teachingAidTargetMeta.textContent = `Copy and saved aids will target: ${teachingAidTargetLabel(target)}.`;
  }
}

async function loadTeachingAids(outputId = teachingAidTargetId()) {
  if (!outputId) {
    resetTeachingAids();
    return;
  }
  state.teachingAidTargetId = Number(outputId);
  const data = await api(`/api/library/${outputId}/teaching-aids`);
  state.teachingAids = data.teaching_aids || [];
  renderTeachingAids();
}

function renderTeachingAids() {
  if (!els.teachingAidsPanel || !els.teachingAidsStatus || !els.teachingAidsList) {
    return;
  }
  renderTeachingAidTargets();
  const targetId = teachingAidTargetId();
  const savedLesson = Boolean(targetId);
  if (state.activeWorkspace === 'teaching-aids') {
    els.documentMeta.textContent = savedLesson
      ? 'Generate, edit, copy into the lesson, print, or share attached classroom materials.'
      : 'Open or save a lesson plan before generating attached classroom materials.';
  }
  els.teachingAidsStatus.textContent = savedLesson
    ? 'Choose an aid type, add an optional request, then edit the generated material before printing or sharing.'
    : 'Open or save a lesson plan to generate attached classroom materials.';
  document.querySelectorAll('[data-aid-type]').forEach((button) => {
    button.disabled = !savedLesson || state.generating;
  });
  els.teachingAidsList.innerHTML = '';
  if (!savedLesson) {
    els.teachingAidEditorPanel?.classList.add('hidden');
    return;
  }
  if (!state.teachingAids.length) {
    els.teachingAidsList.innerHTML = '<p class="microcopy">No saved Teaching Aids yet. Generate one above to start a reusable class material.</p>';
  } else {
    state.teachingAids.forEach((aid) => {
      const button = document.createElement('button');
      button.className = `teaching-aid-item${state.currentTeachingAid?.id === aid.id ? ' teaching-aid-item--on' : ''}`;
      button.type = 'button';
      button.innerHTML = `<strong>${escapeHtml(aid.title || teachingAidLabel(aid.aid_type))}</strong><span>${escapeHtml(teachingAidLabel(aid.aid_type))} | ${escapeHtml(aid.updated_at)}</span>`;
      button.addEventListener('click', () => openTeachingAid(aid));
      els.teachingAidsList.appendChild(button);
    });
  }
  if (state.currentTeachingAid || state.teachingAidDraft) {
    renderTeachingAidEditor();
  } else {
    els.teachingAidEditorPanel?.classList.add('hidden');
  }
}

function openTeachingAid(aid) {
  state.currentTeachingAid = aid;
  state.teachingAidDraft = null;
  state.teachingAidEditing = false;
  renderTeachingAidEditor();
}

async function selectTeachingAidTarget(outputId) {
  const targetId = Number(outputId);
  if (!targetId) return;
  state.teachingAidTargetId = targetId;
  state.currentTeachingAid = null;
  state.teachingAidDraft = null;
  state.teachingAidEditing = false;
  await loadTeachingAids(targetId);
  setStatus(`Teaching Aid target set to ${teachingAidTargetLabel(teachingAidTargetOutput())}.`);
}

function renderTeachingAidEditor() {
  if (!els.teachingAidEditorPanel || !els.teachingAidTitle || !els.teachingAidEditor || !els.teachingAidPreview) {
    return;
  }
  const aid = state.teachingAidDraft || state.currentTeachingAid;
  if (!aid) {
    els.teachingAidEditorPanel.classList.add('hidden');
    return;
  }
  els.teachingAidEditorPanel.classList.remove('hidden');
  els.teachingAidTitle.value = aid.title || teachingAidLabel(aid.aid_type);
  els.teachingAidEditor.value = normalizeLineEndings(aid.content_md || '');
  renderTeachingAidPreview();
  setTeachingAidEditMode(state.teachingAidEditing);
  els.deleteTeachingAid.disabled = !state.currentTeachingAid;
  els.shareTeachingAid.disabled = !state.currentTeachingAid;
}

function setTeachingAidEditMode(isEditing) {
  state.teachingAidEditing = Boolean(isEditing);
  els.teachingAidTitle?.classList.toggle('hidden', !state.teachingAidEditing);
  els.teachingAidEditor?.classList.toggle('hidden', !state.teachingAidEditing);
  els.saveTeachingAid?.classList.toggle('hidden', !state.teachingAidEditing);
  if (els.editTeachingAid) {
    els.editTeachingAid.textContent = state.teachingAidEditing ? 'Hide markdown' : 'Edit';
  }
}

function renderTeachingAidPreview() {
  if (!els.teachingAidEditor || !els.teachingAidPreview) {
    return;
  }
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
  if (!teachingAidTargetId() && state.currentInputs?.kind === 'lesson_plan') {
    await saveDraft();
  }
  const targetId = teachingAidTargetId();
  if (!targetId) {
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
  state.teachingAidEditing = true;
  renderTeachingAidEditor();
  setStatus(`Generating ${title}...`);
  const response = await fetch(`/api/library/${targetId}/teaching-aids/stream`, {
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
  els.teachingAidsStatus.textContent = `${title} ready. Review the preview, then save it to the lesson.`;
  setStatus(`${title} ready. Edit and save the aid.`);
}

async function saveTeachingAid() {
  const aid = state.currentTeachingAid || state.teachingAidDraft;
  const targetId = teachingAidTargetId();
  if (!aid || !els.teachingAidEditor.value.trim()) {
    setStatus('No Teaching Aid to save.', true);
    return;
  }
  if (!targetId) {
    setStatus('Choose a target lesson before saving the Teaching Aid.', true);
    return;
  }
  if (state.currentTeachingAid) {
    const data = await api(`/api/library/${targetId}/teaching-aids/${state.currentTeachingAid.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        title: els.teachingAidTitle.value.trim() || teachingAidLabel(aid.aid_type),
        content_md: normalizeLineEndings(els.teachingAidEditor.value),
      }),
    });
    state.currentTeachingAid = data.teaching_aid;
  } else {
    const data = await api(`/api/library/${targetId}/teaching-aids`, {
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
  setTeachingAidEditMode(false);
  setStatus(`Teaching Aid saved for ${teachingAidTargetLabel(teachingAidTargetOutput())}.`);
}

async function printTeachingAid() {
  const aid = state.currentTeachingAid || state.teachingAidDraft;
  const targetId = teachingAidTargetId();
  const content = normalizeLineEndings(els.teachingAidEditor.value || aid?.content_md || '').trim();
  if (!aid || !content) {
    setStatus('No Teaching Aid to print.', true);
    return;
  }
  if (!targetId) {
    setStatus('Choose a target lesson before printing.', true);
    return;
  }
  const payload = state.currentTeachingAid && !state.teachingAidEditing
    ? { output_id: targetId, teaching_aid_id: state.currentTeachingAid.id }
    : {
        content_md: content,
        metadata: { ...collectInputs(), format: 'Teaching Aid', title: els.teachingAidTitle.value.trim() || teachingAidLabel(aid.aid_type) },
      };
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    setStatus('Browser blocked the print preview window.', true);
    return;
  }
  printWindow.document.write('<!doctype html><title>Preparing Teaching Aid...</title><p>Preparing Teaching Aid preview...</p>');
  printWindow.document.close();
  const response = await fetch('/api/print/preview', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      ...(state.csrfToken ? { 'X-Klasbot-CSRF': state.csrfToken } : {}),
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    printWindow.close();
    throw new Error(error.detail || response.statusText);
  }
  const html = await response.text();
  printWindow.document.open();
  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
  setStatus('Teaching Aid print preview opened.');
}

async function shareTeachingAid() {
  if (!state.currentTeachingAid) {
    await saveTeachingAid();
  }
  const targetId = teachingAidTargetId();
  if (!state.currentTeachingAid) {
    setStatus('Save the Teaching Aid before sharing.', true);
    return;
  }
  if (!targetId) {
    setStatus('Choose a target lesson before sharing.', true);
    return;
  }
  const data = await api(`/api/library/${targetId}/teaching-aids/${state.currentTeachingAid.id}/share`, {
    method: 'POST',
    body: JSON.stringify({ expires_minutes: 15 }),
  });
  showShareResult(data);
}

async function copyTeachingAidIntoLesson() {
  const targetId = teachingAidTargetId();
  const title = els.teachingAidTitle.value.trim() || 'Teaching Aid';
  const content = normalizeLineEndings(els.teachingAidEditor.value).trim();
  if (!content) return;
  if (!targetId) {
    setStatus('Choose a target lesson before copying.', true);
    return;
  }
  const targetData = await api(`/api/library/${targetId}`);
  const target = targetData.output;
  const updatedContent = `${normalizeLineEndings(target.content_md).trim()}\n\n---\n\n# ${title}\n\n${content}\n`;
  const data = await api(`/api/library/${targetId}`, {
    method: 'PUT',
    body: JSON.stringify({ content_md: updatedContent }),
  });
  const updatedOutput = data.output;
  const existingIndex = state.libraryOutputs.findIndex((output) => output.id === updatedOutput.id);
  if (existingIndex >= 0) {
    state.libraryOutputs[existingIndex] = updatedOutput;
  } else {
    state.libraryOutputs.unshift(updatedOutput);
  }
  if (state.currentOutputId === targetId) {
    state.currentOutput = updatedOutput;
    state.currentInputs = updatedOutput.inputs;
    els.editor.value = updatedOutput.content_md;
    renderDraftPreview();
  }
  updateLibraryFilters();
  renderTeachingAidTargets();
  setStatus(`Teaching Aid copied and saved to ${teachingAidTargetLabel(updatedOutput)}.`);
}

async function deleteTeachingAid() {
  if (!state.currentTeachingAid) return;
  const targetId = teachingAidTargetId();
  if (!targetId) return;
  await api(`/api/library/${targetId}/teaching-aids/${state.currentTeachingAid.id}`, { method: 'DELETE' });
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
    item.querySelector('button').addEventListener('click', (event) => runUserAction(event, '', async () => {
      const pin = window.prompt(`New PIN for ${teacher.name}`);
      if (!pin) return;
      await api(`/api/admin/teachers/${teacher.id}/reset-pin`, {
        method: 'POST',
        body: JSON.stringify({ pin }),
      });
      setStatus('PIN reset.');
    }, { busyText: 'Resetting...' }));
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
    item.querySelector('[data-action="activate"]').addEventListener('click', (event) => runUserAction(event, 'Activating curriculum...', async () => {
        await api(`/api/admin/curriculum/${curriculumDocument.id}/activate`, { method: 'POST' });
        state.curriculumCache.clear();
        await loadCurriculumDocuments();
        await loadCurriculumGrades();
        setStatus('Curriculum activated.');
      }, { busyText: 'Activating...' }));
    item.querySelector('[data-action="deactivate"]').disabled = !curriculumDocument.active;
    item.querySelector('[data-action="deactivate"]').addEventListener('click', (event) => runUserAction(event, 'Deactivating curriculum...', async () => {
        await api(`/api/admin/curriculum/${curriculumDocument.id}/deactivate`, { method: 'POST' });
        state.curriculumCache.clear();
        await loadCurriculumDocuments();
        await loadCurriculumGrades();
        setStatus('Curriculum deactivated.');
      }, { busyText: 'Deactivating...' }));
    item.querySelector('[data-action="delete"]').disabled = curriculumDocument.active;
    item.querySelector('[data-action="delete"]').addEventListener('click', (event) => runUserAction(event, 'Deleting curriculum...', async () => {
        await api(`/api/admin/curriculum/${curriculumDocument.id}`, { method: 'DELETE' });
        state.curriculumCache.clear();
        await loadCurriculumDocuments();
        await loadCurriculumGrades();
        setStatus('Inactive curriculum deleted.');
      }, { busyText: 'Deleting...' }));
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

async function configureDemoLogin() {
  try {
    const data = await api('/api/demo/config');
    state.demoConfig = data;
    const showDemoLogin = Boolean(data.hosted_demo && data.prefill_pin && data.demo_pin);
    els.demoLoginButton?.classList.toggle('hidden', !showDemoLogin);
    els.demoLoginNote?.classList.toggle('hidden', !showDemoLogin);
    if (showDemoLogin) {
      els.pin.value = data.demo_pin;
      els.demoLoginNote.textContent = `${data.demo_teacher_name || 'Judge Demo'} is ready for reviewers.`;
    }
  } catch {
    state.demoConfig = null;
  }
}

async function completeLogin(pin) {
  const data = await api('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ pin }),
  });
  state.teacher = data.teacher;
  const session = await api('/api/me');
  state.csrfToken = session.csrf_token || '';
  els.pin.value = '';
  showApp();
  await Promise.all([
    loadLibrary(),
    loadCurriculumGrades(),
    loadGradingClassChoices(),
    configurePromptPreview(),
    checkOllamaStatus(),
  ]);
}

async function bootstrap() {
  buildPinPad();
  setupEditorBehavior();
  updateFormats();
  await configureDemoLogin();
  try {
    const data = await api('/api/me');
    state.teacher = data.teacher;
    state.csrfToken = data.csrf_token || '';
    showApp();
    await Promise.all([
      loadLibrary(),
      loadCurriculumGrades(),
      loadGradingClassChoices(),
      configurePromptPreview(),
      checkOllamaStatus(),
    ]);
  } catch {
    showLogin();
  }
}

els.loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  els.loginError.textContent = '';
  await runUserAction(event, 'Logging in...', async () => {
    await completeLogin(els.pin.value);
  }, {
    busyText: 'Logging in...',
    report: (message, isError = false) => {
      if (isError) {
        els.loginError.textContent = message;
      }
    },
  });
});

els.demoLoginButton?.addEventListener('click', async (event) => {
  els.loginError.textContent = '';
  await runUserAction(event, 'Logging in as judge demo...', async () => {
    await completeLogin(state.demoConfig?.demo_pin || els.pin.value);
  }, {
    busyText: 'Logging in...',
    report: (message, isError = false) => {
      if (isError) {
        els.loginError.textContent = message;
      }
    },
  });
});

els.logoutButton.addEventListener('click', (event) => {
  runUserAction(event, 'Logging out...', async () => {
    await api('/api/auth/logout', { method: 'POST' });
    state.teacher = null;
    state.csrfToken = '';
    state.lastHelpQuestion = '';
    if (els.helpQuestion) els.helpQuestion.value = '';
    if (els.helpSearchInput) els.helpSearchInput.value = '';
    if (typeof clearHelpAnswer === 'function') clearHelpAnswer();
    showLogin();
  }, { busyText: 'Logging out...' });
});

els.homeButton.addEventListener('click', () => switchWorkspace('home'));
els.helpButton.addEventListener('click', () => switchWorkspace('help'));
els.lessonAreaButton.addEventListener('click', () => openWorkArea('lesson'));
els.classAreaButton.addEventListener('click', () => openWorkArea('class'));
els.adminAreaButton.addEventListener('click', () => {
  if (state.teacher?.is_admin) {
    openWorkArea('admin');
  }
});
document.querySelectorAll('[data-home-action]').forEach((button) => {
  button.addEventListener('click', () => handleHomeAction(button.dataset.homeAction));
});
document.querySelectorAll('[data-help-example]').forEach((button) => {
  button.addEventListener('click', () => fillHelpQuestion(button.dataset.helpExample));
});

els.helpAskForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  await runUserAction(event, 'Asking KlasBot Help...', askHelpQuestion, {
    busyText: 'Asking...',
    report: setHelpStatus,
  });
});
els.helpCheckProvider.addEventListener('click', (event) => {
  runUserAction(event, 'Checking AI provider...', checkOllamaStatus, {
    busyText: 'Checking...',
    report: setHelpStatus,
  }).then((data) => {
    if (data?.ok && data?.model_available) {
      setHelpStatus(`AI ready: ${data.model}.`);
    } else if (data) {
      setHelpStatus(data.error || 'AI provider is not ready.', true);
    }
  });
});

// --- Help TOC chips: jump to a topic, open it, and flash it ---
document.querySelectorAll('[data-topic-jump]').forEach((chip) => {
  chip.addEventListener('click', () => {
    const key = chip.dataset.topicJump;
    const target = document.querySelector(`.help-topic[data-topic="${key}"]`);
    if (!target) return;
    target.open = true;
    target.classList.remove('help-topic--flash');
    void target.offsetWidth; // restart animation
    target.classList.add('help-topic--flash');
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => target.classList.remove('help-topic--flash'), 900);
  });
});

// --- Help search: filter topics by title + body text ---
function applyHelpSearch(rawQuery) {
  const query = (rawQuery || '').trim().toLowerCase();
  const topics = document.querySelectorAll('.help-topic');
  let visibleCount = 0;
  const adminVisible = Boolean(state.teacher?.is_admin);
  topics.forEach((topic) => {
    // Respect the admin-only gate even during search.
    if (topic.classList.contains('help-admin-only') && !adminVisible) {
      topic.classList.add('help-topic--hidden');
      return;
    }
    if (!query) {
      topic.classList.remove('help-topic--hidden');
      visibleCount += 1;
      return;
    }
    const haystack = (topic.textContent || '').toLowerCase();
    const matches = haystack.includes(query);
    topic.classList.toggle('help-topic--hidden', !matches);
    if (matches) {
      visibleCount += 1;
      topic.open = true;
    }
  });
  if (els.helpEmptyState) {
    els.helpEmptyState.hidden = visibleCount !== 0;
  }
  if (els.helpSearchClear) {
    els.helpSearchClear.hidden = !query;
  }
}

if (els.helpSearchInput) {
  els.helpSearchInput.addEventListener('input', (event) => {
    applyHelpSearch(event.target.value);
  });
}

if (els.helpSearchClear) {
  els.helpSearchClear.addEventListener('click', () => {
    if (!els.helpSearchInput) return;
    els.helpSearchInput.value = '';
    applyHelpSearch('');
    els.helpSearchInput.focus();
  });
}

// --- Help answer toolbar buttons ---
if (els.helpCopyAnswer) {
  els.helpCopyAnswer.addEventListener('click', async () => {
    const text = els.helpAnswer?.innerText?.trim();
    if (!text) {
      setHelpStatus('No answer to copy yet.', true);
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setHelpStatus('Answer copied to clipboard.');
    } catch (_err) {
      setHelpStatus('Copy failed. Select the answer text manually.', true);
    }
  });
}

if (els.helpClearAnswer) {
  els.helpClearAnswer.addEventListener('click', () => {
    clearHelpAnswer();
  });
}

if (els.helpFollowupAnswer) {
  els.helpFollowupAnswer.addEventListener('click', () => {
    const previous = state.lastHelpQuestion;
    const prefix = previous ? `Follow-up to: "${previous}"\n\n` : '';
    els.helpQuestion.value = prefix;
    els.helpQuestion.focus();
    const len = els.helpQuestion.value.length;
    els.helpQuestion.setSelectionRange(len, len);
    setHelpStatus('Type your follow-up, then ask KlasBot.');
  });
}

// --- Help language preference persistence ---
const HELP_LANG_KEY = 'klasbot:help:lang';
if (els.helpLanguage) {
  try {
    const savedLang = localStorage.getItem(HELP_LANG_KEY);
    if (savedLang && Array.from(els.helpLanguage.options).some((opt) => opt.value === savedLang)) {
      els.helpLanguage.value = savedLang;
    }
  } catch (_err) {
    // localStorage may be unavailable on some kiosks; ignore.
  }
  els.helpLanguage.addEventListener('change', () => {
    try {
      localStorage.setItem(HELP_LANG_KEY, els.helpLanguage.value);
    } catch (_err) {
      // Ignore storage failures.
    }
  });
}

els.adminToggle.addEventListener('click', () => {
  switchWorkspace('teacher-admin');
  runUserAction(els.adminToggle, 'Loading teacher admin...', loadTeachers, { busyText: 'Loading...' });
});

els.curriculumToggle.addEventListener('click', () => {
  switchWorkspace('curriculum');
  runUserAction(els.curriculumToggle, 'Loading curriculum...', loadCurriculumDocuments, { busyText: 'Loading...' });
});

els.formatAdminToggle.addEventListener('click', () => {
  switchWorkspace('plan-formats');
  runUserAction(els.formatAdminToggle, 'Loading lesson formats...', loadLessonPlanFormats, { busyText: 'Loading...' });
});

els.teacherForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  await runUserAction(event, 'Adding teacher...', async () => {
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
  }, {
    busyText: 'Adding...',
  });
});

els.refreshTeachers.addEventListener('click', (event) => runUserAction(event, 'Refreshing teachers...', loadTeachers, { busyText: 'Refreshing...' }));
els.refreshCurriculum.addEventListener('click', (event) => runUserAction(event, 'Refreshing curriculum...', loadCurriculumDocuments, { busyText: 'Refreshing...' }));
els.refreshFormats.addEventListener('click', (event) => runUserAction(event, 'Refreshing formats...', loadLessonPlanFormats, { busyText: 'Refreshing...' }));
els.formatAdminSelect.addEventListener('change', renderSelectedLessonPlanFormat);
els.formatAdminForm.addEventListener('submit', (event) => {
  event.preventDefault();
  runUserAction(event, 'Saving lesson format...', () => saveSelectedLessonPlanFormat(event), { busyText: 'Saving...' });
});
els.resetFormat.addEventListener('click', () => {
  runUserAction(els.resetFormat, 'Resetting format...', resetSelectedLessonPlanFormat, { busyText: 'Resetting...' });
});
els.curriculumUploadForm.addEventListener('submit', (event) => {
  event.preventDefault();
  runUserAction(event, 'Uploading and parsing curriculum...', () => uploadCurriculum(event), { busyText: 'Uploading...' });
});
if (els.pacingForm) {
  els.pacingForm.addEventListener('submit', (event) => {
    event.preventDefault();
    runUserAction(event, 'Saving weekly pacing...', () => savePacing(event), { busyText: 'Saving...' });
  });
}
if (els.resetPacing) {
  els.resetPacing.addEventListener('click', () => runUserAction(els.resetPacing, 'Resetting weekly pacing...', resetPacing, { busyText: 'Resetting...' }));
}
els.refreshLibrary.addEventListener('click', (event) => runUserAction(event, 'Refreshing library...', loadLibrary, { busyText: 'Refreshing...' }));
els.libraryFiltersToggle.addEventListener('click', () => {
  state.libraryFiltersCollapsed = !state.libraryFiltersCollapsed;
  updateLibraryFilterVisibility();
});
els.previewTab.addEventListener('click', () => setDraftView('preview'));
els.editTab.addEventListener('click', () => setDraftView('edit'));
els.currentDraftButton.addEventListener('click', () => switchWorkspace('draft'));
els.teachingAidsButton.addEventListener('click', (event) => runUserAction(event, 'Opening Teaching Aids...', openTeachingAidsWorkspace, { busyText: 'Opening...' }));
els.assessmentButton.addEventListener('click', () => openLessonWorkspace('assessment'));
els.gradingButton.addEventListener('click', () => {
  switchWorkspace('grading');
  runUserAction(els.gradingButton, 'Loading grading batches...', loadGradingBatches, { busyText: 'Loading...' });
});
els.classRecordsButton.addEventListener('click', () => {
  switchWorkspace('class-records');
  runUserAction(els.classRecordsButton, 'Loading class records...', loadClassRecords, { busyText: 'Loading...' });
});
els.libraryButton.addEventListener('click', () => {
  switchWorkspace('library');
  runUserAction(els.libraryButton, 'Loading library...', loadLibrary, { busyText: 'Loading...' }).catch((error) => {
    els.librarySummary.textContent = error.message;
  });
});
els.refreshGrading.addEventListener('click', (event) => runUserAction(event, 'Refreshing grading batches...', loadGradingBatches, { busyText: 'Refreshing...' }));
els.refreshClassRecords.addEventListener('click', (event) => runUserAction(event, 'Refreshing class records...', loadClassRecords, { busyText: 'Refreshing...' }));
els.classRecordForm.addEventListener('submit', (event) => {
  event.preventDefault();
  runUserAction(event, 'Creating class record...', () => createClassRecord(event), { busyText: 'Creating...' });
});
els.gradingBatchForm.addEventListener('submit', (event) => {
  event.preventDefault();
  runUserAction(event, 'Creating grading batch...', () => createGradingBatch(event), { busyText: 'Creating...' });
});
els.gradingClass.addEventListener('change', () => loadGradingAssessmentChoices().catch((error) => setStatus(error.message, true)));
els.gradingAssessment.addEventListener('change', syncGradingPointsFromAssessment);
els.gradingUploadForm.addEventListener('submit', (event) => {
  event.preventDefault();
  runUserAction(event, 'Uploading quiz files...', () => uploadGradingImages(event), {
    busyText: 'Uploading...',
    report: setGradingStatus,
  });
});
els.detectSubmissions.addEventListener('click', (event) => runUserAction(event, 'Detecting worksheet regions...', detectGradingSubmissions, {
  busyText: 'Detecting...',
  report: setGradingStatus,
}));
els.gradeSubmissions.addEventListener('click', (event) => runUserAction(event, 'Extracting answers with Ollama and proposing scores...', gradeGradingSubmissions, {
  busyText: 'Grading...',
  report: setGradingStatus,
}));
els.previewScoreTransfer.addEventListener('click', (event) => runUserAction(event, 'Preparing score transfer review...', previewScoreTransfer, {
  busyText: 'Reviewing...',
  report: setGradingStatus,
}));
els.saveScoreTransfer.addEventListener('click', (event) => runUserAction(event, 'Saving reviewed scores to assessment...', saveScoreTransfer, {
  busyText: 'Saving...',
  report: setGradingStatus,
}));
els.printGrading.addEventListener('click', (event) => runUserAction(event, 'Preparing grading print preview...', printGradingBatch, {
  busyText: 'Preparing...',
  report: setGradingStatus,
}));
els.deleteGradingBatch.addEventListener('click', (event) => runUserAction(event, 'Deleting grading batch...', deleteActiveGradingBatch, {
  busyText: 'Deleting...',
  report: setGradingStatus,
}));
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
els.newLessonButton.addEventListener('click', () => openLessonWorkspace('lesson_plan'));
els.previewPromptButton.addEventListener('click', () => {
  runUserAction(els.previewPromptButton, 'Building prompt preview...', previewPrompt, { busyText: 'Previewing...' });
});
if (els.checkOllamaButton) {
  els.checkOllamaButton.addEventListener('click', (event) => runUserAction(event, 'Checking Ollama...', checkOllamaStatus, { busyText: 'Checking...' }));
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
  streamGenerate(collectInputs(), event.submitter);
});
els.saveButton.addEventListener('click', (event) => runUserAction(event, 'Saving draft...', saveDraft, { busyText: 'Saving...' }));
els.printButton.addEventListener('click', (event) => runUserAction(event, 'Preparing print...', printDraft, { busyText: 'Preparing...' }));
els.shareButton.addEventListener('click', (event) => runUserAction(event, 'Creating share link...', shareDraft, { busyText: 'Sharing...' }));
document.querySelectorAll('[data-aid-type]').forEach((button) => {
  button.addEventListener('click', () => runUserAction(button, 'Generating Teaching Aid...', () => generateTeachingAid(button.dataset.aidType), { busyText: 'Generating...' }));
});
if (els.teachingAidEditor) {
  els.teachingAidEditor.addEventListener('input', () => {
    if (state.teachingAidDraft) {
      state.teachingAidDraft.content_md = normalizeLineEndings(els.teachingAidEditor.value);
    }
    renderTeachingAidPreview();
  });
}
els.saveTeachingAid?.addEventListener('click', (event) => runUserAction(event, 'Saving Teaching Aid...', saveTeachingAid, { busyText: 'Saving...' }));
els.editTeachingAid?.addEventListener('click', () => setTeachingAidEditMode(!state.teachingAidEditing));
els.printTeachingAid?.addEventListener('click', (event) => runUserAction(event, 'Printing Teaching Aid...', printTeachingAid, { busyText: 'Printing...' }));
els.shareTeachingAid?.addEventListener('click', (event) => runUserAction(event, 'Creating Teaching Aid share link...', shareTeachingAid, { busyText: 'Sharing...' }));
els.copyTeachingAid?.addEventListener('click', (event) => runUserAction(event, 'Copying Teaching Aid into lesson...', copyTeachingAidIntoLesson, { busyText: 'Copying...' }));
els.deleteTeachingAid?.addEventListener('click', (event) => runUserAction(event, 'Deleting Teaching Aid...', deleteTeachingAid, { busyText: 'Deleting...' }));
els.teachingAidTarget?.addEventListener('change', (event) => {
  runUserAction(event, 'Changing Teaching Aid target...', () => selectTeachingAidTarget(event.target.value), { busyText: 'Changing...' });
});
els.mobilePairButton.addEventListener('click', (event) => runUserAction(event, 'Creating mobile pairing code...', createMobilePairingToken, { busyText: 'Pairing...' }));

updateLibraryFilterVisibility();
renderDraftPreview();
renderTeachingAids();
setDraftView('preview');
bootstrap();
