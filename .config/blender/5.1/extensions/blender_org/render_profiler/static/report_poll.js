(function () {
  var currentMode = '';
  var currentTab = 'modifiers';
  var lastAppliedUpdateTime = null;

  function relativeTime(timeSec) {
    if (timeSec == null) return '';
    if (timeSec === 0) return 'waiting for update…';
    var sec = Math.floor(Date.now() / 1000 - timeSec);
    if (sec < 1) return 'just now';
    if (sec < 60) return sec + ' seconds ago';
    var min = Math.floor(sec / 60);
    if (min === 1) return '1 minute ago';
    if (min < 60) return min + ' minutes ago';
    var hr = Math.floor(min / 60);
    if (hr === 1) return '1 hour ago';
    if (hr < 24) return hr + ' hours ago';
    var day = Math.floor(hr / 24);
    if (day === 1) return '1 day ago';
    if (day < 7) return day + ' days ago';
    return Math.floor(day / 7) + ' weeks ago';
  }

  function setMode(mode) {
    document.querySelectorAll('.mode-btn').forEach(function(btn) {
      btn.classList.toggle('active', btn.dataset.mode === mode);
      var elMod = document.getElementById('tab-content-modifiers');
      var elHeavy = document.getElementById('tab-content-heavy');
      var elTextures = document.getElementById('tab-content-textures');
      var elStatistics = document.getElementById('tab-content-statistics');
      var elMemory = document.getElementById('tab-content-memory');
      if (elMod) elMod.innerHTML = '';
      if (elHeavy) elHeavy.innerHTML = '';
      if (elTextures) elTextures.innerHTML = '';
      if (elStatistics) elStatistics.innerHTML = '';
      if (elMemory) elMemory.innerHTML = '';
    });
  }
  
  function setTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll('.report-tab').forEach(function(btn) {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-pane').forEach(function(pane) {
      pane.style.display = pane.dataset.tab === tabId ? 'block' : 'none';
    });
  }

  function showError(msg) {
    var el = document.getElementById('report-error');
    if (el) {
      var textEl = el.querySelector('.report-error-text');
      if (textEl) textEl.textContent = msg;
      el.classList.add('visible');
    }
  }

  function hideError() {
    var el = document.getElementById('report-error');
    if (el) el.classList.remove('visible');
  }

  function refresh() {
    fetch('/state.json').then(function(r) {
      if (!r.ok) throw new Error('Server error');
      return r.json();
    }).then(function(s) {
      hideError();
      var mode = s.mode || 'viewport';
      var hasData = s.modifiers_html && s.modifiers_html.length > 0;
      var updateTime = s.last_update_time;
      var contentChanged = (updateTime !== lastAppliedUpdateTime) || (mode !== currentMode);


      if (contentChanged) {
        lastAppliedUpdateTime = updateTime;
        if (s.mode !== undefined && s.mode !== currentMode) setMode(s.mode);
        currentMode = mode;
        var elMod = document.getElementById('tab-content-modifiers');
        var elHeavy = document.getElementById('tab-content-heavy');
        var elTextures = document.getElementById('tab-content-textures');
        var elStatistics = document.getElementById('tab-content-statistics');
        var elMemory = document.getElementById('tab-content-memory');
        var disabled_message = '<p class="report-message">Profiler is disabled.</p>';
        var viewport_message = '<p class="report-message">Profiler is in viewport mode. It will get data on any scene update.</p>';
        var render_message = '<p class="report-message">Profiler is in render mode. To get data, render the scene.</p>';
        if (mode === 'off') {
          if (elMod) elMod.innerHTML = disabled_message;
          if (elHeavy) elHeavy.innerHTML = disabled_message;
          if (elTextures) elTextures.innerHTML = disabled_message;
          if (elStatistics) elStatistics.innerHTML = disabled_message;
          if (elMemory) elMemory.innerHTML = disabled_message;
        } else if (mode === 'viewport') {
          if (!hasData) {
            if (elMod) elMod.innerHTML = viewport_message;
            if (elHeavy) elHeavy.innerHTML = viewport_message;
            if (elTextures) elTextures.innerHTML = viewport_message;
            if (elStatistics) elStatistics.innerHTML = viewport_message;
            if (elMemory) elMemory.innerHTML = viewport_message;
          } else {
            if (elMod) elMod.innerHTML = s.modifiers_html;
            if (elHeavy) elHeavy.innerHTML = s.heavy_meshes_html || '';
            if (elTextures) elTextures.innerHTML = s.textures_html || '';
            if (elStatistics) elStatistics.innerHTML = s.statistics_html || '';
            if (elMemory) elMemory.innerHTML = s.memory_html || '';
          }
        } else if (mode === 'render') {
          if (!hasData) {
            if (elMod) elMod.innerHTML = render_message;
            if (elHeavy) elHeavy.innerHTML = render_message;
            if (elTextures) elTextures.innerHTML = render_message;
            if (elStatistics) elStatistics.innerHTML = render_message;
            if (elMemory) elMemory.innerHTML = render_message;
          } else {
            if (elMod) elMod.innerHTML = s.modifiers_html;
            if (elHeavy) elHeavy.innerHTML = s.heavy_meshes_html || '';
            if (elTextures) elTextures.innerHTML = s.textures_html || '';
            if (elStatistics) elStatistics.innerHTML = s.statistics_html || '';
            if (elMemory) elMemory.innerHTML = s.memory_html || '';
          }
        }

        var elLastUpdate = document.getElementById('last-update-block');
        if (elLastUpdate) elLastUpdate.innerHTML = (mode !== 'off' && hasData && s.last_update_html) ? (s.last_update_html || '') : '';
        if (s.title !== undefined) document.title = s.title;
        var elFile = document.getElementById('context-file-name');
        if (elFile && s.file_name !== undefined) elFile.textContent = s.file_name;
        var elScene = document.getElementById('context-scene-name');
        if (elScene && s.scene_name !== undefined) elScene.textContent = s.scene_name;
        var elViewLayer = document.getElementById('context-view-layer-name');
        if (elViewLayer && s.view_layer_name !== undefined) elViewLayer.textContent = s.view_layer_name;
      }
      if (s.last_update_time != null) {
        var ago = relativeTime(s.last_update_time);
        document.querySelectorAll('.last-update-ago').forEach(function(el) { el.textContent = ago; });
      }
    }).catch(function() {
      showError('Failed to update. The connection to Blender was lost — Blender may have been closed. This page will retry when Blender is running again with the add-on enabled.');
    });
  }

  document.querySelectorAll('.mode-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var m = this.dataset.mode;
      fetch('/mode', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'mode=' + m }).then(function() { setMode(m); });
    });
  });

  document.querySelectorAll('.report-tab').forEach(function(btn) {
    btn.addEventListener('click', function() { setTab(this.dataset.tab); });
  });

  var warningEl = document.getElementById('report-warning');
  var closeBtn = warningEl && warningEl.querySelector('.report-warning-close');
  if (closeBtn && warningEl) {
    try {
      if (localStorage.getItem('reportWarningDismissed') === '1') warningEl.classList.add('report-warning-dismissed');
    } catch (e) {}
    closeBtn.addEventListener('click', function() {
      warningEl.classList.add('report-warning-dismissed');
      try { localStorage.setItem('reportWarningDismissed', '1'); } catch (e) {}
    });
  }

  setInterval(refresh, __POLL_INTERVAL_MS__);
  setTab('modifiers');
  refresh();
})();
