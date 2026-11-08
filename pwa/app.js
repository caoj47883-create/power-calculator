/* 功耗计算器 — app shell & interactions */
(function () {
  'use strict';

  var Model = window.PowerModel;
  if (!Model) return;

  var STORAGE_KEY = 'powercalc.state.v2';
  var HISTORY_KEY = 'powercalc.history.v1';
  var PROFILE_KEY = 'powercalc.profile.v1';
  var ITEM_LOCKS_KEY = 'powercalc.itemLocks.v1';
  var HISTORY_LIMIT = 730;
  var TABS = ['body', 'device', 'transit', 'overview'];
  var CORE_DEVICE_KEYS = ['phone', 'earbuds', 'tablet', 'desktop'];
  var EXTRA_DEVICE_KEYS = ['laptop', 'powerbank', 'headphones', 'actioncam', 'camera', 'instax'];
  var CORE_TRIP_KEYS = ['subway', 'ebike'];
  var EXTRA_TRIP_KEYS = ['taxiEv', 'taxi', 'cityBus', 'evCar', 'iceCar'];
  var INTERCITY_KEYS = ['coach', 'train', 'hsr', 'plane'];
  var HERO_LABELS = {
    body: '自体功耗',
    device: '设备功耗',
    transit: '周边功耗',
    overview: '今日总功耗'
  };
  var MOOD_STOPS = [
    { at: 0, rgb: [198, 222, 184] },
    { at: 1.5, rgb: [174, 213, 232] },
    { at: 4, rgb: [246, 209, 160] },
    { at: 8, rgb: [242, 183, 166] },
    { at: 14, rgb: [231, 184, 174] }
  ];
  var state = loadState();
  var profile = loadProfile();
  if (profile.complete) {
    state.age = profile.age;
    state.height = profile.height;
    state.weight = profile.weight;
  }
  var history = loadHistory();
  var itemLocks = loadItemLocks();
  var currentTab = 'body';
  var latestData = null;
  var toastTimer = 0;
  var modalCloseTimer = 0;
  var profileCloseTimer = 0;
  var lastFocused = null;
  var isModalOpen = false;
  var isProfileOpen = false;
  var profileMode = 'settings';
  var prefersReduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  var root = document.documentElement;
  var stage = document.getElementById('stage');
  var infoModal = document.getElementById('infoModal');
  var infoSheet = document.getElementById('infoSheet');
  var infoButton = document.getElementById('infoButton');
  var closeInfoButton = document.getElementById('closeInfo');
  var profileModal = document.getElementById('profileModal');
  var profileSheet = document.getElementById('profileSheet');
  var profileTitle = document.getElementById('profileTitle');
  var profileKicker = document.getElementById('profileKicker');
  var profileLead = document.getElementById('profileLead');
  var profileAge = document.getElementById('profileAge');
  var profileHeight = document.getElementById('profileHeight');
  var profileWeight = document.getElementById('profileWeight');
  var closeProfileButton = document.getElementById('closeProfileButton');
  var saveProfileButton = document.getElementById('saveProfileButton');
  var profileSettingsExtra = document.getElementById('profileSettingsExtra');
  var configLockToggle = document.getElementById('configLockToggle');
  var settingsButton = document.getElementById('settingsButton');
  var editProfileButton = document.getElementById('editProfileButton');
  var resetButton = document.getElementById('resetButton');
  var toast = document.getElementById('toast');
  var stepsInput = document.getElementById('stepsInput');
  var metInput = document.getElementById('metInput');
  var deviceList = document.getElementById('deviceList');
  var deviceExtraList = document.getElementById('deviceExtraList');
  var deviceExpandButton = document.getElementById('deviceExpandButton');
  var deviceExpandMeta = document.getElementById('deviceExpandMeta');
  var applianceList = document.getElementById('applianceList');
  var transitList = document.getElementById('transitList');
  var transitExtraList = document.getElementById('transitExtraList');
  var transitInputList = document.getElementById('transitInputList');
  var tripExtra = document.getElementById('tripExtra');
  var tripExpandButton = document.getElementById('tripExpandButton');
  var tripExpandMeta = document.getElementById('tripExpandMeta');
  var heroOverview = document.getElementById('heroOverview');
  var legendButtons = Array.prototype.slice.call(document.querySelectorAll('.legend-item[data-go-tab]'));
  var tabButtons = Array.prototype.slice.call(document.querySelectorAll('.tab'));

  function loadState() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return Model.normalizeState(Model.DEFAULTS);
      return Model.normalizeState(JSON.parse(raw));
    } catch (error) {
      return Model.normalizeState(Model.DEFAULTS);
    }
  }

  function saveState() {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      /* 本地存储不可用时，应用仍然可以正常计算。 */
    }
  }

  function loadProfile() {
    try {
      var raw = window.localStorage.getItem(PROFILE_KEY);
      if (!raw) return { complete: false, age: 30, height: 170, weight: 68 };
      var parsed = JSON.parse(raw);
      if (!parsed || parsed.complete !== true) {
        return { complete: false, age: 30, height: 170, weight: 68 };
      }
      return {
        complete: true,
        age: Math.round(Math.min(80, Math.max(16, Number(parsed.age) || 30))),
        height: Math.round(Math.min(210, Math.max(140, Number(parsed.height) || 170))),
        weight: Math.round(Math.min(120, Math.max(40, Number(parsed.weight) || 68)))
      };
    } catch (error) {
      return { complete: false, age: 30, height: 170, weight: 68 };
    }
  }

  function saveProfile() {
    try {
      window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    } catch (error) {
      /* 本地存储不可用时，本次资料仍然有效。 */
    }
  }

  function loadItemLocks() {
    var result = { device: {}, appliance: {}, trip: {} };
    try {
      var parsed = JSON.parse(window.localStorage.getItem(ITEM_LOCKS_KEY) || '{}');
      ['device', 'appliance', 'trip'].forEach(function (kind) {
        var source = parsed && parsed[kind];
        if (!source || typeof source !== 'object') return;
        Object.keys(source).forEach(function (key) {
          if (source[key] === true) result[kind][key] = true;
        });
      });
    } catch (error) {
      /* 没有固定状态也可以正常使用。 */
    }
    return result;
  }

  function saveItemLocks() {
    try {
      window.localStorage.setItem(ITEM_LOCKS_KEY, JSON.stringify(itemLocks));
    } catch (error) {
      /* 固定状态只影响本机交互。 */
    }
  }

  function isItemLocked(kind, key) {
    return !!(itemLocks[kind] && itemLocks[kind][key]);
  }

  function setItemLock(kind, key, value) {
    if (!itemLocks[kind]) itemLocks[kind] = {};
    if (value) {
      itemLocks[kind][key] = true;
    } else {
      delete itemLocks[kind][key];
    }
    saveItemLocks();
  }

  function loadHistory() {
    try {
      var raw = window.localStorage.getItem(HISTORY_KEY);
      if (!raw) return [];
      var parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.map(function (entry) {
        if (!entry || typeof entry.date !== 'string') return null;
        var total = Number(entry.total);
        if (!isFinite(total) || total < 0) return null;
        return {
          date: entry.date,
          total: total,
          body: Math.max(0, Number(entry.body) || 0),
          device: Math.max(0, Number(entry.device) || 0),
          transit: Math.max(0, Number(entry.transit) || 0)
        };
      }).filter(Boolean).sort(function (a, b) {
        return a.date < b.date ? 1 : -1;
      }).slice(0, HISTORY_LIMIT);
    } catch (error) {
      return [];
    }
  }

  function saveHistory() {
    try {
      window.localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (error) {
      /* 历史只保存在本机；存储不可用时本次会话仍可查看。 */
    }
  }

  function localDateKey(date) {
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2);
    var day = ('0' + date.getDate()).slice(-2);
    return year + '-' + month + '-' + day;
  }

  function recordHistory(data, dateOverride) {
    var dateKey = localDateKey(new Date());
    if (dateOverride && /^\d{4}-\d{2}-\d{2}$/.test(String(dateOverride))) {
      dateKey = String(dateOverride);
    }
    var entry = {
      date: dateKey,
      total: Number(data.totalKwh.toFixed(3)),
      body: Number(data.body.kwh.toFixed(3)),
      device: Number(data.device.kwh.toFixed(3)),
      transit: Number(data.transit.kwh.toFixed(3))
    };
    var found = false;
    for (var i = 0; i < history.length; i += 1) {
      if (history[i].date === dateKey) {
        history[i] = entry;
        found = true;
        break;
      }
    }
    if (!found) history.push(entry);
    history.sort(function (a, b) {
      return a.date < b.date ? 1 : -1;
    });
    if (history.length > HISTORY_LIMIT) history = history.slice(0, HISTORY_LIMIT);
    saveHistory();
  }

  function clearDailyUsage(dayKey) {
    Object.keys(Model.MODEL.devices).forEach(function (key) {
      var def = Model.MODEL.devices[key];
      if (def.mode === 'power') {
        state.devices[key].hours = 0;
      } else {
        state.devices[key].cycles = 0;
      }
    });
    Object.keys(Model.MODEL.appliances).forEach(function (key) {
      state.appliances[key].hours = 0;
    });
    Object.keys(Model.MODEL.transit).forEach(function (key) {
      state.trips[key] = 0;
    });
    state.steps = 0;
    state.met = 1.3;
    state.day = dayKey;
    itemLocks = { device: {}, appliance: {}, trip: {} };
    saveItemLocks();
    latestData = null;
  }

  function rolloverDayIfNeeded() {
    var today = localDateKey(new Date());
    if (!state.day) {
      // Existing installs predate the day marker. Clear once on the first
      // launch after this update. A brand-new install (no profile/history)
      // keeps the sample values until the user finishes onboarding.
      if (history.length > 0 || profile.complete) {
        clearDailyUsage(today);
        saveState();
        return true;
      }
      state.day = today;
      saveState();
      return false;
    }
    if (state.day === today) return false;

    // Save the previous day's numbers under the previous day first, then
    // clear only the adjustable daily usage. Profile, selected items, device
    // capacities and fixed daily items stay.
    recordHistory(latestData || Model.calc(state), state.day);
    clearDailyUsage(today);
    saveState();
    return true;
  }

  function syncDailyUI() {
    applyBodyInputs();
    applyDeviceInputs();
    applyApplianceInputs();
    applyTransitInputs();
    render();
    saveState();
  }

  function handleDayRollover() {
    if (!rolloverDayIfNeeded()) return;
    syncDailyUI();
    showToast('新的一天：昨日用量已归档，今日可调用量已归零');
  }

  function renderGrade(data) {
    var card = document.getElementById('gradeCard');
    if (!card) return;
    var grade = Model.evaluateGrade(data.transit.kwh);
    setText('gradeIndex', ('0' + grade.level).slice(-2));
    setText('gradeLabel', '今日评价 · ' + grade.label);
    setText('gradeText', grade.text);
    setText('gradeMetric', '按周边 ' + formatEnergy(data.transit.kwh) + ' kWh 评定');
    card.setAttribute('data-level', String(grade.level));
    card.setAttribute('aria-label', '今日周边功耗评价：' + grade.label + '，' + grade.text);
    Array.prototype.forEach.call(card.querySelectorAll('.grade-scale i'), function (dot, index) {
      dot.classList.toggle('is-on', index < grade.level);
    });
  }

  function renderHistory(data) {
    var container = document.getElementById('historyBars');
    if (!container) return;
    var today = new Date();
    today.setHours(12, 0, 0, 0);
    var recordByDate = {};
    history.forEach(function (entry) {
      recordByDate[entry.date] = entry;
    });

    var days = [];
    var max = Math.max(data.totalKwh, 1);
    for (var offset = 6; offset >= 0; offset -= 1) {
      var date = new Date(today.getTime());
      date.setDate(date.getDate() - offset);
      var key = localDateKey(date);
      var record = recordByDate[key] || null;
      if (record) max = Math.max(max, record.total);
      days.push({ date: date, key: key, record: record, isToday: offset === 0 });
    }

    var weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    var labels = [];
    container.innerHTML = days.map(function (day) {
      var total = day.record ? day.record.total : 0;
      var transit = day.record ? day.record.transit : 0;
      var grade = day.record ? Model.evaluateGrade(transit) : null;
      var height = day.record ? Math.max(8, Math.round(total / max * 100)) : 0;
      var label = day.isToday ? '今天' : weekdays[day.date.getDay()];
      var aria = day.isToday
        ? '今天周边 ' + formatEnergy(transit) + ' 千瓦时' + (grade ? '，' + grade.label : '，暂无记录')
        : (day.date.getMonth() + 1) + '月' + day.date.getDate() + '日，' +
          (day.record ? '周边 ' + formatEnergy(transit) + ' 千瓦时，' + grade.label : '暂无记录');
      labels.push(aria);
      return '<div class="history-day' +
        (day.record ? ' has-record' : '') +
        (day.isToday ? ' is-today' : '') +
        '" data-level="' + (grade ? grade.level : 0) + '" aria-label="' + aria + '">' +
        '<div class="history-bar-track"><span class="history-bar-fill" style="height:' + height + '%"></span></div>' +
        '<span class="history-date">' + label + '</span>' +
        '</div>';
    }).join('');
    container.setAttribute('aria-label', labels.join('；'));

    var currentGrade = Model.evaluateGrade(data.transit.kwh);
    setText('historyCaption', '今天周边 ' + formatEnergy(data.transit.kwh) + ' kWh · ' +
      currentGrade.label + '；总 ' + formatEnergy(data.totalKwh) + ' kWh，本机已保存 ' + history.length + ' 天。');
  }

  function icon(name, className) {
    return '<svg class="' + (className || 'icon') + '" aria-hidden="true"><use href="#i-' + name + '"></use></svg>';
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function formatEnergy(value) {
    var n = Math.max(0, Number(value) || 0);
    if (n >= 100) return n.toFixed(1);
    return n.toFixed(2);
  }

  function formatDeviceEnergy(value) {
    var n = Math.max(0, Number(value) || 0);
    if (n >= 100) return n.toFixed(1);
    if (n >= 0.1) return n.toFixed(2);
    return n.toFixed(3);
  }

  function formatPower(value) {
    var n = Math.max(0, Number(value) || 0);
    if (n >= 1000) return (n / 1000).toFixed(2) + ' kW';
    if (n >= 10) return Math.round(n) + ' W';
    if (n >= 1) return n.toFixed(1) + ' W';
    return n.toFixed(2) + ' W';
  }

  function formatInteger(value) {
    return Math.round(Number(value) || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  function formatCycles(value) {
    return String(parseFloat((Number(value) || 0).toFixed(2)));
  }

  function formatCoal(kg) {
    var n = Math.max(0, Number(kg) || 0);
    if (n >= 0.1) return n.toFixed(2);
    if (n >= 0.01) return n.toFixed(3);
    return n.toFixed(4);
  }

  function formatTeslaKm(km) {
    var n = Math.max(0, Number(km) || 0);
    if (n >= 100) return n.toFixed(0);
    return n.toFixed(1);
  }

  function formatPercent(value, total) {
    if (!total || total <= 0 || value <= 0) return '0%';
    var pct = value / total * 100;
    if (pct < 1) return '<1%';
    return Math.round(pct) + '%';
  }

  function formatDate() {
    var date = new Date();
    var weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    setText('dateLabel', (date.getMonth() + 1) + '月' + date.getDate() + '日 · ' + weekdays[date.getDay()]);
  }

  function setRangeFill(input) {
    if (!input) return;
    var min = Number(input.min) || 0;
    var max = Number(input.max) || 100;
    var value = Number(input.value) || 0;
    var pct = max === min ? 0 : (value - min) / (max - min) * 100;
    pct = Math.max(0, Math.min(100, pct));
    input.style.setProperty('--pct', pct + '%');
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function moodColor(kwh) {
    var value = Math.max(0, Number(kwh) || 0);
    if (value >= MOOD_STOPS[MOOD_STOPS.length - 1].at) {
      return MOOD_STOPS[MOOD_STOPS.length - 1].rgb.slice();
    }
    for (var i = 1; i < MOOD_STOPS.length; i += 1) {
      if (value <= MOOD_STOPS[i].at) {
        var prev = MOOD_STOPS[i - 1];
        var next = MOOD_STOPS[i];
        var t = (value - prev.at) / (next.at - prev.at);
        return [
          Math.round(prev.rgb[0] + (next.rgb[0] - prev.rgb[0]) * t),
          Math.round(prev.rgb[1] + (next.rgb[1] - prev.rgb[1]) * t),
          Math.round(prev.rgb[2] + (next.rgb[2] - prev.rgb[2]) * t)
        ];
      }
    }
    return MOOD_STOPS[0].rgb.slice();
  }

  function mixRgb(base, color, ratio) {
    return [
      Math.round(base[0] + (color[0] - base[0]) * ratio),
      Math.round(base[1] + (color[1] - base[1]) * ratio),
      Math.round(base[2] + (color[2] - base[2]) * ratio)
    ];
  }

  function applyMood(kwh) {
    var color = moodColor(kwh);
    // Keep the whole page in warm, high-key tints. High energy should feel
    // sun-baked rather than "lights out": never interpolate toward black.
    var pageTop = mixRgb([250, 248, 243], color, 0.22);
    var pageBg = mixRgb([247, 244, 238], color, 0.06);
    root.style.setProperty('--mood-rgb', color.join(', '));
    root.style.setProperty('--page-top', 'rgb(' + pageTop.join(', ') + ')');
    root.style.setProperty('--page-bg', 'rgb(' + pageBg.join(', ') + ')');
  }

  function itemToggleMarkup(kind, key, enabled, label) {
    var locked = enabled && isItemLocked(kind, key);
    var state = locked ? 'fixed' : (enabled ? 'on' : 'off');
    var action = locked ? '已固定，点击取消计入' : (enabled ? '已计入，点击固定' : '未计入，点击勾选');
    return '<button class="item-toggle' + (enabled ? ' is-checked' : '') + (locked ? ' is-locked' : '') + '" type="button" data-state="' + state + '" aria-label="' + label + '：' + action + '" data-toggle-' + kind + '="' + key + '">' +
      '<svg class="icon" aria-hidden="true"><use href="' + (locked ? '#i-lock' : '#i-check') + '"></use></svg>' +
      '</button>';
  }

  function deviceCardMarkup(key) {
    var def = Model.MODEL.devices[key];
    var values = state.devices[key];
    var enabled = values.enabled !== false;
    var top = '' +
      '<div class="device-top">' +
        '<span class="device-icon">' + icon(def.icon) + '</span>' +
        '<div class="device-copy">' +
          '<h3>' + def.name + '</h3>' +
          '<p>' + def.meta + '</p>' +
        '</div>' +
        '<div class="device-energy"><span data-device-kwh="' + key + '">0.000</span><small>kWh</small></div>' +
        itemToggleMarkup('device', key, enabled, def.name) +
      '</div>';
    var controls = '';

    if (def.mode === 'power') {
      controls += '' +
        '<div class="slider-head device-slider-head">' +
          '<label class="slider-label" for="device-power-' + key + '">主机功率</label>' +
          '<output class="slider-output" for="device-power-' + key + '" id="device-power-out-' + key + '">' + formatInteger(values.watts) + ' W</output>' +
        '</div>' +
        '<input class="range" id="device-power-' + key + '" type="range" min="' + def.powerMin + '" max="' + def.powerMax + '" step="' + def.powerStep + '" value="' + values.watts + '" data-device-power="' + key + '" aria-label="' + def.name + '功率，单位瓦">' +
        '<div class="range-ends"><span>' + def.powerMin + ' W</span><span>' + def.powerMax + ' W</span></div>' +
        '<div class="slider-head device-slider-head second">' +
          '<label class="slider-label" for="device-hours-' + key + '">每日使用</label>' +
          '<output class="slider-output" for="device-hours-' + key + '" id="device-hours-out-' + key + '">' + formatCycles(values.hours) + ' 小时</output>' +
        '</div>' +
        '<input class="range" id="device-hours-' + key + '" type="range" min="' + def.hoursMin + '" max="' + def.hoursMax + '" step="' + def.hoursStep + '" value="' + values.hours + '" data-device-hours="' + key + '" aria-label="' + def.name + '每日使用时长，单位小时">' +
        '<div class="range-ends"><span>0 小时</span><span>24 小时</span></div>' +
        '<div class="device-foot"><span>功率 × 时长</span><span data-device-avg="' + key + '">平均 0.00 W</span></div>';
    } else {
      controls += '' +
        '<div class="slider-head device-slider-head">' +
          '<label class="slider-label" for="device-cap-' + key + '">电池容量</label>' +
          '<output class="slider-output" for="device-cap-' + key + '" id="device-cap-out-' + key + '">' + formatInteger(values.capacity) + ' ' + def.unit + '</output>' +
        '</div>' +
        '<input class="range" id="device-cap-' + key + '" type="range" min="' + def.capacityMin + '" max="' + def.capacityMax + '" step="' + def.capacityStep + '" value="' + values.capacity + '" data-device-capacity="' + key + '" aria-label="' + def.name + '电池容量，单位' + (def.unit === 'Wh' ? '瓦时' : '毫安时') + '">' +
        '<div class="range-ends"><span>' + formatInteger(def.capacityMin) + ' ' + def.unit + '</span><span>' + formatInteger(def.capacityMax) + ' ' + def.unit + '</span></div>' +
        '<div class="slider-head device-slider-head second">' +
          '<label class="slider-label" for="device-cycles-' + key + '">每日完整充电</label>' +
          '<output class="slider-output" for="device-cycles-' + key + '" id="device-cycles-out-' + key + '">' + formatCycles(values.cycles) + ' 次</output>' +
        '</div>' +
        '<input class="range" id="device-cycles-' + key + '" type="range" min="0" max="' + Model.MODEL.battery.cyclesMax + '" step="' + Model.MODEL.battery.cyclesStep + '" value="' + values.cycles + '" data-device-cycles="' + key + '" aria-label="' + def.name + '每日完整充电次数">' +
        '<div class="range-ends"><span>0 次</span><span>3 次</span></div>' +
        '<div class="device-foot"><span data-device-per-charge="' + key + '">每次 0 Wh</span><span data-device-avg="' + key + '">平均 0.00 W</span></div>';
    }

    return '<article class="device-card' + (enabled ? '' : ' is-off') + '" data-device-card="' + key + '">' + top + controls + '</article>';
  }

  function buildDeviceList() {
    deviceList.innerHTML = CORE_DEVICE_KEYS.map(deviceCardMarkup).join('');
    deviceExtraList.innerHTML = EXTRA_DEVICE_KEYS.map(deviceCardMarkup).join('');
    updateExpandMeta();
  }

  function buildApplianceList() {
    var html = Object.keys(Model.MODEL.appliances).map(function (key) {
      var def = Model.MODEL.appliances[key];
      var values = state.appliances[key];
      var enabled = values.enabled !== false;
      return '' +
        '<article class="device-card appliance-card' + (enabled ? '' : ' is-off') + '" data-appliance-card="' + key + '">' +
          '<div class="device-top">' +
            '<span class="device-icon">' + icon(def.icon) + '</span>' +
            '<div class="device-copy">' +
              '<h3>' + def.name + '</h3>' +
              '<p>' + def.meta + '</p>' +
            '</div>' +
            '<div class="device-energy"><span data-appliance-kwh="' + key + '">0.000</span><small>kWh</small></div>' +
            itemToggleMarkup('appliance', key, enabled, def.name) +
          '</div>' +
          '<div class="slider-head device-slider-head">' +
            '<label class="slider-label" for="appliance-power-' + key + '">电器功率</label>' +
            '<output class="slider-output" for="appliance-power-' + key + '" id="appliance-power-out-' + key + '">' + formatInteger(values.watts) + ' W</output>' +
          '</div>' +
          '<input class="range" id="appliance-power-' + key + '" type="range" min="' + def.powerMin + '" max="' + def.powerMax + '" step="' + def.powerStep + '" value="' + values.watts + '" data-appliance-power="' + key + '" aria-label="' + def.name + '功率，单位瓦">' +
          '<div class="range-ends"><span>' + def.powerMin + ' W</span><span>' + def.powerMax + ' W</span></div>' +
          '<div class="slider-head device-slider-head second">' +
            '<label class="slider-label" for="appliance-hours-' + key + '">每日使用</label>' +
            '<output class="slider-output" for="appliance-hours-' + key + '" id="appliance-hours-out-' + key + '">' + formatCycles(values.hours) + ' 小时</output>' +
          '</div>' +
          '<input class="range" id="appliance-hours-' + key + '" type="range" min="0" max="24" step="0.5" value="' + values.hours + '" data-appliance-hours="' + key + '" aria-label="' + def.name + '每日使用时长，单位小时">' +
          '<div class="range-ends"><span>0 小时</span><span>24 小时</span></div>' +
          '<div class="device-foot"><span>功率 × 时长</span><span data-appliance-avg="' + key + '">平均 0.00 W</span></div>' +
        '</article>';
    }).join('');
    applianceList.innerHTML = html;
  }

  function tripActionLabel(key, unit) {
    if (unit === 'min') return key === 'subway' ? '乘坐时长' : '行驶时长';
    return key === 'cityBus' ? '乘坐里程' : '行驶里程';
  }

  function tripCardMarkup(key) {
    var def = Model.MODEL.transit[key];
    var value = state.trips[key];
    var enabled = state.tripEnabled[key] !== false;
    var mid = Math.round(def.max / 2);
    var action = tripActionLabel(key, def.unit);
    var rateLabel = (def.perPerson ? '人均 ' : '') + def.kwhPerKm.toFixed(3) + ' kWh/km';
    return '' +
      '<article class="trip-card' + (enabled ? '' : ' is-off') + '" data-trip-card="' + key + '">' +
        '<div class="trip-top">' +
          '<span class="trip-icon">' + icon(def.icon) + '</span>' +
          '<div class="trip-copy">' +
            '<h3>' + def.name + '</h3>' +
            '<p>' + def.meta + '</p>' +
          '</div>' +
          '<div class="trip-energy"><span data-trip-kwh="' + key + '">0.00</span><small>kWh</small></div>' +
          itemToggleMarkup('trip', key, enabled, def.name) +
        '</div>' +
        '<div class="slider-head">' +
          '<label class="slider-label" for="trip-' + key + '">' + action + '</label>' +
          '<output class="slider-output" for="trip-' + key + '" id="trip-out-' + key + '">' + value + ' ' + def.unitLabel + '</output>' +
        '</div>' +
        '<input class="range" id="trip-' + key + '" type="range" min="' + def.min + '" max="' + def.max + '" step="' + def.step + '" value="' + value + '" data-trip="' + key + '" aria-label="' + def.name + action + '，单位' + def.unitLabel + '">' +
        '<div class="range-ends"><span>0</span><span>' + mid + '</span><span>' + def.max + ' ' + def.unitLabel + '</span></div>' +
        '<div class="trip-foot">' +
          '<strong data-trip-distance="' + key + '">≈ 0.0 km</strong>' +
          '<span data-trip-rate="' + key + '">' + rateLabel + '</span>' +
        '</div>' +
      '</article>';
  }

  function tripInputCardMarkup(key) {
    var def = Model.MODEL.transit[key];
    var value = state.trips[key];
    var enabled = state.tripEnabled[key] !== false;
    return '' +
      '<article class="trip-input-card' + (enabled ? '' : ' is-off') + '" data-trip-card="' + key + '">' +
        '<div class="trip-input-top">' +
          '<span class="trip-icon">' + icon(def.icon) + '</span>' +
          '<div class="trip-copy">' +
            '<h3>' + def.name + '</h3>' +
            '<p>' + (def.perPerson ? '人均 ' : '') + def.kwhPerKm.toFixed(3) + ' kWh/km</p>' +
          '</div>' +
          itemToggleMarkup('trip', key, enabled, def.name) +
        '</div>' +
        '<div class="trip-input-controls">' +
          '<label class="trip-number">' +
            '<input type="number" min="' + def.min + '" max="' + def.max + '" step="' + def.step + '" value="' + value + '" data-trip-number="' + key + '" inputmode="decimal" enterkeyhint="done" aria-label="' + def.name + '里程，单位公里">' +
            '<span>km</span>' +
          '</label>' +
          '<strong data-trip-kwh="' + key + '">0.00 kWh</strong>' +
        '</div>' +
      '</article>';
  }

  function buildTransitList() {
    transitList.innerHTML = CORE_TRIP_KEYS.map(tripCardMarkup).join('');
    transitExtraList.innerHTML = EXTRA_TRIP_KEYS.map(tripCardMarkup).join('');
    transitInputList.innerHTML = INTERCITY_KEYS.map(tripInputCardMarkup).join('');
    updateExpandMeta();
  }

  function countExtraEnabled(keys, getter) {
    return keys.filter(function (key) { return getter(key); }).length;
  }

  function setToggleState(kind, key, enabled, label) {
    var button = document.querySelector('[data-toggle-' + kind + '="' + key + '"]');
    if (!button) return;
    var locked = enabled && isItemLocked(kind, key);
    button.classList.toggle('is-checked', enabled);
    button.classList.toggle('is-locked', locked);
    button.setAttribute('data-state', locked ? 'fixed' : (enabled ? 'on' : 'off'));
    var action = locked ? '已固定，点击取消计入' : (enabled ? '已计入，点击固定' : '未计入，点击勾选');
    button.setAttribute('aria-label', (label || '这个项目') + '：' + action);
    var use = button.querySelector('use');
    if (use) use.setAttribute('href', locked ? '#i-lock' : '#i-check');
  }

  function itemLabel(kind, key) {
    if (kind === 'device') return (Model.MODEL.devices[key] || {}).name || key;
    if (kind === 'appliance') return (Model.MODEL.appliances[key] || {}).name || key;
    return (Model.MODEL.transit[key] || {}).name || key;
  }

  function isItemEnabled(kind, key) {
    if (kind === 'device') return state.devices[key].enabled !== false;
    if (kind === 'appliance') return state.appliances[key].enabled !== false;
    return state.tripEnabled[key] !== false;
  }

  function setItemEnabled(kind, key, value) {
    if (kind === 'device') state.devices[key].enabled = value;
    else if (kind === 'appliance') state.appliances[key].enabled = value;
    else state.tripEnabled[key] = value;
  }

  function cycleItemState(kind, key) {
    var enabled = isItemEnabled(kind, key);
    var locked = enabled && isItemLocked(kind, key);
    var label = itemLabel(kind, key);
    if (!enabled) {
      setItemEnabled(kind, key, true);
      setItemLock(kind, key, false);
      showToast('已计入' + label);
    } else if (!locked) {
      setItemLock(kind, key, true);
      showToast('已固定' + label);
    } else {
      setItemEnabled(kind, key, false);
      setItemLock(kind, key, false);
      showToast('已取消计入' + label);
    }
    saveState();
    render();
  }

  function renderConfigLockToggle() {
    if (!configLockToggle) return;
    var locked = state.configLocked === true;
    configLockToggle.classList.toggle('is-on', locked);
    configLockToggle.setAttribute('aria-checked', locked ? 'true' : 'false');
  }

  function applyConfigLockState() {
    if (state.configLocked !== true) return;
    Array.prototype.forEach.call(document.querySelectorAll(
      '[data-device-capacity], [data-device-power], [data-appliance-power]'
    ), function (control) {
      control.disabled = true;
    });
  }

  function toggleConfigLock() {
    state.configLocked = state.configLocked !== true;
    saveState();
    renderConfigLockToggle();
    applyItemCardLocks();
    applyConfigLockState();
    showToast(state.configLocked ? '已锁定设备容量和电器功率' : '已解除容量和功率锁定');
  }

  function applyItemCardLocks() {
    Object.keys(Model.MODEL.devices).forEach(function (key) {
      var card = document.querySelector('[data-device-card="' + key + '"]');
      var locked = isItemEnabled('device', key) && isItemLocked('device', key);
      setToggleState('device', key, isItemEnabled('device', key), itemLabel('device', key));
      if (!card) return;
      card.classList.toggle('is-fixed', locked);
      Array.prototype.forEach.call(card.querySelectorAll('input[type="range"]'), function (control) {
        control.disabled = locked;
      });
    });

    Object.keys(Model.MODEL.appliances).forEach(function (key) {
      var card = document.querySelector('[data-appliance-card="' + key + '"]');
      var locked = isItemEnabled('appliance', key) && isItemLocked('appliance', key);
      setToggleState('appliance', key, isItemEnabled('appliance', key), itemLabel('appliance', key));
      if (!card) return;
      card.classList.toggle('is-fixed', locked);
      Array.prototype.forEach.call(card.querySelectorAll('input[type="range"]'), function (control) {
        control.disabled = locked;
      });
    });

    Object.keys(Model.MODEL.transit).forEach(function (key) {
      var card = document.querySelector('[data-trip-card="' + key + '"]');
      var locked = isItemEnabled('trip', key) && isItemLocked('trip', key);
      setToggleState('trip', key, isItemEnabled('trip', key), itemLabel('trip', key));
      if (!card) return;
      card.classList.toggle('is-fixed', locked);
      Array.prototype.forEach.call(card.querySelectorAll('input[type="range"], [data-trip-number]'), function (control) {
        control.disabled = locked;
      });
    });
  }

  function toggleExpand(button, target, closedLabel, openLabel) {
    if (!button || !target) return;
    var expanded = target.hidden;
    target.hidden = !expanded;
    button.classList.toggle('is-open', expanded);
    button.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    var label = button.querySelector('span');
    if (label) label.textContent = expanded ? openLabel : closedLabel;
  }

  function updateExpandMeta() {
    var deviceSelected = countExtraEnabled(EXTRA_DEVICE_KEYS, function (key) {
      return state.devices[key].enabled !== false;
    });
    var tripSelected = countExtraEnabled(EXTRA_TRIP_KEYS.concat(INTERCITY_KEYS), function (key) {
      return state.tripEnabled[key] !== false;
    });
    if (deviceExpandMeta) {
      deviceExpandMeta.textContent = deviceSelected
        ? '已选 ' + deviceSelected + ' / ' + EXTRA_DEVICE_KEYS.length
        : EXTRA_DEVICE_KEYS.length + ' 项可选';
    }
    if (tripExpandMeta) {
      tripExpandMeta.textContent = tripSelected
        ? '已选 ' + tripSelected + ' / ' + (EXTRA_TRIP_KEYS.length + INTERCITY_KEYS.length)
        : (EXTRA_TRIP_KEYS.length + INTERCITY_KEYS.length) + ' 项可选';
    }
  }

  function applyBodyInputs() {
    stepsInput.value = state.steps;
    metInput.value = state.met;
    [stepsInput, metInput].forEach(setRangeFill);
    stepsInput.setAttribute('aria-valuetext', state.steps + ' 步');
    metInput.setAttribute('aria-valuetext', Model.activityLabel(state.met) + '，' + state.met.toFixed(2) + ' MET');
  }

  function applyDeviceInputs() {
    Object.keys(Model.MODEL.devices).forEach(function (key) {
      var def = Model.MODEL.devices[key];
      var values = state.devices[key];
      if (def.mode === 'power') {
        var powerInput = document.getElementById('device-power-' + key);
        var hoursInput = document.getElementById('device-hours-' + key);
        if (powerInput) {
          powerInput.value = values.watts;
          setRangeFill(powerInput);
        }
        if (hoursInput) {
          hoursInput.value = values.hours;
          setRangeFill(hoursInput);
        }
      } else {
        var capacityInput = document.getElementById('device-cap-' + key);
        var cyclesInput = document.getElementById('device-cycles-' + key);
        if (capacityInput) {
          capacityInput.value = values.capacity;
          setRangeFill(capacityInput);
        }
        if (cyclesInput) {
          cyclesInput.value = values.cycles;
          setRangeFill(cyclesInput);
        }
      }
    });
  }

  function applyApplianceInputs() {
    Object.keys(Model.MODEL.appliances).forEach(function (key) {
      var values = state.appliances[key];
      var powerInput = document.getElementById('appliance-power-' + key);
      var hoursInput = document.getElementById('appliance-hours-' + key);
      if (powerInput) {
        powerInput.value = values.watts;
        setRangeFill(powerInput);
      }
      if (hoursInput) {
        hoursInput.value = values.hours;
        setRangeFill(hoursInput);
      }
    });
  }

  function applyTransitInputs() {
    Object.keys(Model.MODEL.transit).forEach(function (key) {
      var def = Model.MODEL.transit[key];
      if (def.form === 'slider') {
        var slider = document.getElementById('trip-' + key);
        if (slider) {
          slider.value = state.trips[key];
          setRangeFill(slider);
        }
      } else {
        var numberInput = document.querySelector('[data-trip-number="' + key + '"]');
        if (numberInput) numberInput.value = state.trips[key];
      }
    });
  }

  function updateHero(data) {
    var tab = currentTab;
    var energy = tab === 'overview' ? data.totalKwh : data[tab].kwh;
    var equivalents = Model.equivalentsFor(energy);
    setText('heroLabel', HERO_LABELS[tab]);
    setText('heroKwh', formatDeviceEnergy(energy));
    setText('heroAverage', formatPower(energy * 1000 / 24));
    setText('coalEquivalent', formatCoal(equivalents.coalKg));
    setText('teslaEquivalent', formatTeslaKm(equivalents.teslaKm));
    heroOverview.hidden = tab !== 'overview';
    applyMood(energy);
  }

  function setTab(tab, options) {
    if (TABS.indexOf(tab) < 0) tab = 'body';
    var changed = tab !== currentTab;
    currentTab = tab;
    state.tab = tab;
    root.setAttribute('data-tab', tab);

    tabButtons.forEach(function (button) {
      var active = button.getAttribute('data-tab') === tab;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-selected', active ? 'true' : 'false');
      button.setAttribute('tabindex', active ? '0' : '-1');
    });

    TABS.forEach(function (key) {
      var panel = document.getElementById('panel-' + key);
      if (!panel) return;
      var active = key === tab;
      panel.classList.toggle('is-active', active);
      if (active) panel.removeAttribute('hidden');
      else panel.setAttribute('hidden', '');
    });

    legendButtons.forEach(function (button) {
      button.classList.toggle('is-active', button.getAttribute('data-go-tab') === tab);
    });

    if (changed || (options && options.resetScroll)) stage.scrollTop = 0;

    if (!latestData) latestData = Model.calc(state);
    updateHero(latestData);

    try {
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, '', '#' + tab);
      }
    } catch (error) {
      /* file:// WebView 中个别版本不允许改写 history，不影响使用。 */
    }

    saveState();
  }

  function render() {
    var data = Model.calc(state);
    latestData = data;
    var total = data.totalKwh;
    var shares = {
      body: total > 0 ? data.body.kwh / total * 100 : 0,
      device: total > 0 ? data.device.kwh / total * 100 : 0,
      transit: total > 0 ? data.transit.kwh / total * 100 : 0
    };

    ['body', 'device', 'transit'].forEach(function (key) {
      var segment = document.querySelector('[data-seg="' + key + '"]');
      if (!segment) return;
      segment.style.width = (shares[key] > 0 ? Math.max(shares[key], 1.1) : 0) + '%';
      segment.classList.toggle('is-empty', data[key].kwh <= 0);
    });
    document.getElementById('energyBar').setAttribute(
      'aria-label',
      '自体 ' + formatEnergy(data.body.kwh) + ' kWh，占 ' + Math.round(shares.body) +
      '%；设备 ' + formatEnergy(data.device.kwh) + ' kWh，占 ' + Math.round(shares.device) +
      '%；周边 ' + formatEnergy(data.transit.kwh) + ' kWh，占 ' + Math.round(shares.transit) + '%。'
    );
    setText('bodyLegendKwh', formatEnergy(data.body.kwh));
    setText('deviceLegendKwh', formatEnergy(data.device.kwh));
    setText('transitLegendKwh', formatEnergy(data.transit.kwh));

    setText('restPower', Math.round(data.body.restPowerW));
    setText('activePower', Math.round(data.body.activePowerW));
    setText('activeState', data.body.label + '时 · ' + state.met.toFixed(2) + ' MET');
    setText('profileSummary', state.age + ' 岁 · ' + state.height + ' cm · ' + state.weight + ' kg');
    setText('bmiOut', data.body.bmi.toFixed(1));
    setText('bmiText', data.body.bmiLabel);
    setText('stepsOut', formatInteger(state.steps));
    setText('stepDistance', data.body.distanceKm.toFixed(1));
    setText('stepMinutes', Math.round(data.body.walkMinutes));
    setText('stepEnergy', formatEnergy(data.body.activityKwh));
    setText('activityMinutesHint', Math.round(data.body.walkMinutes));
    setText('metOut', state.met.toFixed(2));

    stepsInput.setAttribute('aria-valuetext', formatInteger(state.steps) + ' 步，约 ' + data.body.distanceKm.toFixed(1) + ' 公里，活动 ' + Math.round(data.body.walkMinutes) + ' 分钟');
    metInput.setAttribute('aria-valuetext', data.body.label + '，' + state.met.toFixed(2) + ' MET');
    [stepsInput, metInput].forEach(setRangeFill);
    Array.prototype.forEach.call(document.querySelectorAll('[data-met]'), function (button) {
      var active = Math.abs(Number(button.getAttribute('data-met')) - state.met) < 0.001;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-steps]'), function (button) {
      var active = state.steps === Number(button.getAttribute('data-steps'));
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });

    data.device.items.forEach(function (item) {
      var card = document.querySelector('[data-device-card="' + item.key + '"]');
      var kwhEl = document.querySelector('[data-device-kwh="' + item.key + '"]');
      var avgEl = document.querySelector('[data-device-avg="' + item.key + '"]');
      if (kwhEl) kwhEl.textContent = formatDeviceEnergy(item.kwh);
      if (avgEl) avgEl.textContent = '平均 ' + formatPower(item.averageW);
      setToggleState('device', item.key, item.enabled, item.name);

      if (item.mode === 'power') {
        var powerInput = document.getElementById('device-power-' + item.key);
        var hoursInput = document.getElementById('device-hours-' + item.key);
        var powerOut = document.getElementById('device-power-out-' + item.key);
        var hoursOut = document.getElementById('device-hours-out-' + item.key);
        if (powerOut) powerOut.textContent = formatInteger(item.watts) + ' W';
        if (hoursOut) hoursOut.textContent = formatCycles(item.hours) + ' 小时';
        if (card) card.classList.toggle('is-off', !item.enabled);
        if (powerInput) {
          if (powerInput.value !== String(item.watts)) powerInput.value = item.watts;
          setRangeFill(powerInput);
          powerInput.setAttribute('aria-valuetext', formatInteger(item.watts) + ' 瓦');
        }
        if (hoursInput) {
          if (hoursInput.value !== String(item.hours)) hoursInput.value = item.hours;
          setRangeFill(hoursInput);
          hoursInput.setAttribute('aria-valuetext', formatCycles(item.hours) + ' 小时，每日 ' + formatDeviceEnergy(item.kwh) + ' 千瓦时');
        }
      } else {
        var capacityInput = document.getElementById('device-cap-' + item.key);
        var cyclesInput = document.getElementById('device-cycles-' + item.key);
        var capacityOut = document.getElementById('device-cap-out-' + item.key);
        var cyclesOut = document.getElementById('device-cycles-out-' + item.key);
        var perChargeEl = document.querySelector('[data-device-per-charge="' + item.key + '"]');
        if (capacityOut) capacityOut.textContent = formatInteger(item.capacity) + ' ' + item.capacityUnit;
        if (cyclesOut) cyclesOut.textContent = formatCycles(item.cycles) + ' 次';
        if (perChargeEl) perChargeEl.textContent = '每次 ' + item.wallWhPerCharge.toFixed(1) + ' Wh';
        if (card) card.classList.toggle('is-off', !item.enabled);
        if (capacityInput) {
          if (capacityInput.value !== String(item.capacity)) capacityInput.value = item.capacity;
          setRangeFill(capacityInput);
          capacityInput.setAttribute('aria-valuetext', formatInteger(item.capacity) + ' ' + (item.capacityUnit === 'Wh' ? '瓦时' : '毫安时'));
        }
        if (cyclesInput) {
          if (cyclesInput.value !== String(item.cycles)) cyclesInput.value = item.cycles;
          setRangeFill(cyclesInput);
          cyclesInput.setAttribute('aria-valuetext', formatCycles(item.cycles) + ' 次完整充电，每日 ' + formatDeviceEnergy(item.kwh) + ' 千瓦时');
        }
      }
    });

    data.appliance.items.forEach(function (item) {
      var card = document.querySelector('[data-appliance-card="' + item.key + '"]');
      var kwhEl = document.querySelector('[data-appliance-kwh="' + item.key + '"]');
      var avgEl = document.querySelector('[data-appliance-avg="' + item.key + '"]');
      var powerInput = document.getElementById('appliance-power-' + item.key);
      var hoursInput = document.getElementById('appliance-hours-' + item.key);
      var powerOut = document.getElementById('appliance-power-out-' + item.key);
      var hoursOut = document.getElementById('appliance-hours-out-' + item.key);
      if (kwhEl) kwhEl.textContent = formatDeviceEnergy(item.kwh);
      if (avgEl) avgEl.textContent = '平均 ' + formatPower(item.averageW);
      if (powerOut) powerOut.textContent = formatInteger(item.watts) + ' W';
      if (hoursOut) hoursOut.textContent = formatCycles(item.hours) + ' 小时';
      setToggleState('appliance', item.key, item.enabled, item.name);
      if (card) card.classList.toggle('is-off', !item.enabled);
      if (powerInput) {
        if (powerInput.value !== String(item.watts)) powerInput.value = item.watts;
        setRangeFill(powerInput);
        powerInput.setAttribute('aria-valuetext', formatInteger(item.watts) + ' 瓦');
      }
      if (hoursInput) {
        if (hoursInput.value !== String(item.hours)) hoursInput.value = item.hours;
        setRangeFill(hoursInput);
        hoursInput.setAttribute('aria-valuetext', formatCycles(item.hours) + ' 小时，每日 ' + formatDeviceEnergy(item.kwh) + ' 千瓦时');
      }
    });

    data.transit.items.forEach(function (item) {
      var card = document.querySelector('[data-trip-card="' + item.key + '"]');
      var kwhEl = document.querySelector('[data-trip-kwh="' + item.key + '"]');
      if (kwhEl) kwhEl.textContent = item.form === 'input' ? formatEnergy(item.kwh) + ' kWh' : formatEnergy(item.kwh);
      setToggleState('trip', item.key, item.enabled, item.name);
      if (item.form === 'input') {
        var numberInput = document.querySelector('[data-trip-number="' + item.key + '"]');
        if (numberInput && document.activeElement !== numberInput) numberInput.value = item.value;
        if (card) card.classList.toggle('is-off', !item.enabled);
        return;
      }

      var input = document.getElementById('trip-' + item.key);
      var outEl = document.getElementById('trip-out-' + item.key);
      var distanceEl = document.querySelector('[data-trip-distance="' + item.key + '"]');
      var rateEl = document.querySelector('[data-trip-rate="' + item.key + '"]');
      if (outEl) outEl.textContent = item.value + ' ' + item.unitLabel;
      if (distanceEl) {
        if (item.key === 'taxi' || item.key === 'iceCar') {
          distanceEl.textContent = '≈ ' + item.liters.toFixed(2) + ' L 汽油';
        } else {
          distanceEl.textContent = '≈ ' + item.distanceKm.toFixed(1) + ' km';
        }
      }
      if (rateEl) rateEl.textContent = (item.perPerson ? '人均 ' : '') + item.kwhPerKm.toFixed(3) + ' kWh/km';
      if (card) card.classList.toggle('is-off', !item.enabled);
      if (input) {
        if (input.value !== String(item.value)) input.value = item.value;
        setRangeFill(input);
        input.setAttribute('aria-valuetext', item.value + ' ' + item.unitLabel + '，约 ' + formatEnergy(item.kwh) + ' 千瓦时');
      }
    });

    setText('wifiFixedKwh', formatEnergy(data.transit.fixed.wifiKwh));
    setText('baseFixedKwh', formatEnergy(data.transit.fixed.baseKwh));
    setText('cloudFixedKwh', formatEnergy(data.transit.fixed.cloudKwh));
    setText('fixedSubtotal', formatEnergy(data.transit.fixed.kwh) + ' kWh/天');
    setText('applianceSubtotal', formatEnergy(data.transit.appliancesKwh) + ' kWh/天');
    setText('travelSubtotal', formatEnergy(data.transit.tripsKwh) + ' kWh');

    var categories = [
      { key: 'body', name: '自体功耗', kwh: data.body.kwh },
      { key: 'device', name: '设备功耗', kwh: data.device.kwh },
      { key: 'transit', name: '周边功耗', kwh: data.transit.kwh }
    ];
    categories.forEach(function (item) {
      var cap = item.key.charAt(0).toUpperCase() + item.key.slice(1);
      setText('overview' + cap + 'Kwh', formatDeviceEnergy(item.kwh));
      setText('overview' + cap + 'Pct', formatPercent(item.kwh, total));
    });
    var largest = categories.slice().sort(function (a, b) { return b.kwh - a.kwh; })[0];
    var largestPct = total > 0 ? Math.round(largest.kwh / total * 100) : 0;
    var insight = document.getElementById('overviewInsightText');
    if (insight) {
      insight.innerHTML = '今天<b>' + largest.name + '</b>是最大的能量开销，占总能耗的<b>' +
        largestPct + '%</b>。';
    }

    updateExpandMeta();
    applyItemCardLocks();
    applyConfigLockState();
    renderConfigLockToggle();
    recordHistory(data);
    renderGrade(data);
    renderHistory(data);
    renderTransitInsight(data);
    updateHero(data);
  }

  function renderTransitInsight(data) {
    var insightText = document.getElementById('transitInsightText');
    if (!insightText) return;
    var groups = [
      { key: 'fixed', label: '固定项', kwh: data.transit.fixed.kwh },
      { key: 'appliance', label: '电器', kwh: data.transit.appliancesKwh },
      { key: 'trip', label: '出行', kwh: data.transit.tripsKwh }
    ];
    var largest = groups.slice().sort(function (a, b) { return b.kwh - a.kwh; })[0];
    var share = data.transit.kwh > 0 ? Math.round(largest.kwh / data.transit.kwh * 100) : 0;
    insightText.innerHTML = '周边共 <b>' + formatEnergy(data.transit.kwh) + ' kWh</b>：固定项 ' +
      formatEnergy(data.transit.fixed.kwh) + '、电器 ' + formatEnergy(data.transit.appliancesKwh) +
      '、出行 ' + formatEnergy(data.transit.tripsKwh) + '；<b>' + largest.label + '</b>占比最高（' + share + '%）。';
  }

  function showToast(message) {
    if (!toast) return;
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add('is-visible');
    toastTimer = window.setTimeout(function () {
      toast.classList.remove('is-visible');
    }, 1900);
  }

  function setRangeState(input) {
    var value = Number(input.value);
    if (!isFinite(value)) return;
    if (state.configLocked === true && (
      input.hasAttribute('data-device-capacity') ||
      input.hasAttribute('data-device-power') ||
      input.hasAttribute('data-appliance-power')
    )) {
      return;
    }
    if (input === stepsInput) {
      state.steps = value;
    } else if (input === metInput) {
      state.met = value;
    } else if (input.getAttribute('data-device-capacity')) {
      state.devices[input.getAttribute('data-device-capacity')].capacity = value;
    } else if (input.getAttribute('data-device-cycles')) {
      state.devices[input.getAttribute('data-device-cycles')].cycles = value;
    } else if (input.getAttribute('data-device-power')) {
      state.devices[input.getAttribute('data-device-power')].watts = value;
    } else if (input.getAttribute('data-device-hours')) {
      state.devices[input.getAttribute('data-device-hours')].hours = value;
    } else if (input.getAttribute('data-appliance-power')) {
      state.appliances[input.getAttribute('data-appliance-power')].watts = value;
    } else if (input.getAttribute('data-appliance-hours')) {
      state.appliances[input.getAttribute('data-appliance-hours')].hours = value;
    } else if (input.getAttribute('data-trip')) {
      state.trips[input.getAttribute('data-trip')] = value;
    }
    setRangeFill(input);
    render();
    saveState();
  }

  function updateTripNumber(input) {
    var key = input.getAttribute('data-trip-number');
    var def = Model.MODEL.transit[key];
    if (!def) return;
    var raw = input.value.trim();
    var value = raw === '' ? 0 : Number(raw);
    if (!isFinite(value)) value = 0;
    state.trips[key] = clamp(value, def.min, def.max);
    render();
    saveState();
  }

  function handleInput(event) {
    var input = event.target;
    if (!input || !input.getAttribute) return;
    if (input.getAttribute('data-trip-number')) {
      updateTripNumber(input);
      return;
    }
    if (input.type !== 'range') return;
    setRangeState(input);
  }

  function handleChange(event) {
    var input = event.target;
    if (!input || !input.getAttribute || !input.getAttribute('data-trip-number')) return;
    input.value = state.trips[input.getAttribute('data-trip-number')];
    render();
  }

  function handleDocumentClick(event) {
    var stepPreset = event.target.closest ? event.target.closest('[data-steps]') : null;
    if (stepPreset) {
      var stepValue = Number(stepPreset.getAttribute('data-steps'));
      if (isFinite(stepValue)) {
        stepsInput.value = stepValue;
        stepsInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
      return;
    }

    var metPreset = event.target.closest ? event.target.closest('[data-met]') : null;
    if (metPreset) {
      var metValue = Number(metPreset.getAttribute('data-met'));
      if (isFinite(metValue)) {
        metInput.value = metValue;
        metInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
      return;
    }

    var deviceToggle = event.target.closest ? event.target.closest('[data-toggle-device]') : null;
    if (deviceToggle) {
      cycleItemState('device', deviceToggle.getAttribute('data-toggle-device'));
      return;
    }

    var applianceToggle = event.target.closest ? event.target.closest('[data-toggle-appliance]') : null;
    if (applianceToggle) {
      cycleItemState('appliance', applianceToggle.getAttribute('data-toggle-appliance'));
      return;
    }

    var tripToggle = event.target.closest ? event.target.closest('[data-toggle-trip]') : null;
    if (tripToggle) {
      cycleItemState('trip', tripToggle.getAttribute('data-toggle-trip'));
      return;
    }

    if (event.target.closest && event.target.closest('#deviceExpandButton')) {
      toggleExpand(deviceExpandButton, deviceExtraList, '展开更多设备', '收起更多设备');
      return;
    }

    if (event.target.closest && event.target.closest('#tripExpandButton')) {
      toggleExpand(tripExpandButton, tripExtra, '展开更多出行', '收起更多出行');
      return;
    }

    var profileBackdrop = event.target.closest ? event.target.closest('[data-close-profile]') : null;
    if (profileBackdrop) {
      closeProfile();
      return;
    }

    var goTab = event.target.closest ? event.target.closest('[data-go-tab]') : null;
    if (goTab) {
      setTab(goTab.getAttribute('data-go-tab'), { resetScroll: true });
      return;
    }

    var tab = event.target.closest ? event.target.closest('.tab') : null;
    if (tab) {
      setTab(tab.getAttribute('data-tab'), { resetScroll: true });
      return;
    }

    var closeTrigger = event.target.closest ? event.target.closest('[data-close-modal]') : null;
    if (closeTrigger) {
      closeModal();
    }
  }

  function handleTabKeydown(event) {
    var key = event.key;
    if (!event.target.classList.contains('tab')) return;
    if (key !== 'ArrowLeft' && key !== 'ArrowRight' && key !== 'Home' && key !== 'End') return;
    event.preventDefault();
    var index = TABS.indexOf(currentTab);
    if (key === 'ArrowLeft') index = (index + TABS.length - 1) % TABS.length;
    else if (key === 'ArrowRight') index = (index + 1) % TABS.length;
    else if (key === 'Home') index = 0;
    else if (key === 'End') index = TABS.length - 1;
    var nextTab = TABS[index];
    setTab(nextTab, { resetScroll: true });
    var target = document.getElementById('tab-' + nextTab);
    if (target) target.focus();
  }

  function fillProfileForm() {
    profileAge.value = state.age;
    profileHeight.value = state.height;
    profileWeight.value = state.weight;
  }

  function openProfile(mode) {
    if (isProfileOpen) return;
    if (isModalOpen) closeModal();
    profileMode = mode === 'onboarding' ? 'onboarding' : 'settings';
    isProfileOpen = true;
    window.clearTimeout(profileCloseTimer);
    fillProfileForm();
    var onboarding = profileMode === 'onboarding';
    profileModal.classList.toggle('is-onboarding', onboarding);
    profileKicker.textContent = onboarding ? 'BEFORE WE START' : 'PROFILE';
    profileTitle.textContent = onboarding ? '先认识一下你' : '身体资料';
    profileLead.textContent = onboarding
      ? '身高、体重和年龄只录入一次，之后在「身体资料」里修改。基础代谢会按你的实际年龄计算。'
      : '修改后会立刻重新计算基础代谢与今天的账本；资料只保存在本机。';
    saveProfileButton.textContent = onboarding ? '保存并开始' : '保存修改';
    closeProfileButton.hidden = onboarding;
    profileSettingsExtra.hidden = onboarding;
    renderConfigLockToggle();
    lastFocused = document.activeElement;
    profileModal.hidden = false;
    if (!prefersReduced) void profileModal.offsetWidth;
    profileModal.classList.add('is-open');
    window.setTimeout(function () {
      if (!isProfileOpen) return;
      try { profileAge.focus({ preventScroll: true }); } catch (error) { profileAge.focus(); }
    }, 80);
  }

  function hideProfileModal() {
    isProfileOpen = false;
    profileModal.classList.remove('is-open');
    window.clearTimeout(profileCloseTimer);
    profileCloseTimer = window.setTimeout(function () {
      if (!isProfileOpen) profileModal.hidden = true;
      if (lastFocused && lastFocused.focus) {
        try { lastFocused.focus({ preventScroll: true }); } catch (error) { lastFocused.focus(); }
      }
    }, prefersReduced ? 0 : 240);
  }

  function closeProfile() {
    if (profileMode === 'onboarding') return;
    hideProfileModal();
  }

  function saveProfileFromForm() {
    var nextAge = Math.round(clamp(Number(profileAge.value) || state.age, 16, 80));
    var nextHeight = Math.round(clamp(Number(profileHeight.value) || state.height, 140, 210));
    var nextWeight = Math.round(clamp(Number(profileWeight.value) || state.weight, 40, 120));
    profileAge.value = nextAge;
    profileHeight.value = nextHeight;
    profileWeight.value = nextWeight;
    profile = {
      complete: true,
      age: nextAge,
      height: nextHeight,
      weight: nextWeight
    };
    state.age = nextAge;
    state.height = nextHeight;
    state.weight = nextWeight;
    saveProfile();
    saveState();
    render();
    hideProfileModal();
    showToast('身体资料已保存');
  }

  function openModal() {
    if (isModalOpen || isProfileOpen) return;
    isModalOpen = true;
    window.clearTimeout(modalCloseTimer);
    lastFocused = document.activeElement;
    infoModal.hidden = false;
    if (!prefersReduced) {
      void infoModal.offsetWidth;
    }
    infoModal.classList.add('is-open');
    window.setTimeout(function () {
      if (!isModalOpen) return;
      try { closeInfoButton.focus({ preventScroll: true }); } catch (error) { closeInfoButton.focus(); }
    }, 80);
  }

  function closeModal() {
    if (!isModalOpen && infoModal.hidden) return;
    isModalOpen = false;
    infoModal.classList.remove('is-open');
    window.clearTimeout(modalCloseTimer);
    modalCloseTimer = window.setTimeout(function () {
      if (!isModalOpen) infoModal.hidden = true;
      if (lastFocused && lastFocused.focus) {
        try { lastFocused.focus({ preventScroll: true }); } catch (error) { lastFocused.focus(); }
      }
    }, prefersReduced ? 0 : 240);
  }

  function trapModalFocus(event) {
    if ((!isModalOpen && !isProfileOpen) || event.key !== 'Tab') return;
    var sheet = isProfileOpen ? profileSheet : infoSheet;
    var focusables = Array.prototype.slice.call(
      sheet.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
    ).filter(function (el) {
      return !el.disabled && el.offsetParent !== null;
    });
    if (!focusables.length) return;
    var first = focusables[0];
    var last = focusables[focusables.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function resetAll() {
    var keepConfigLocked = state.configLocked === true;
    state = Model.normalizeState(Model.DEFAULTS);
    if (profile.complete) {
      state.age = profile.age;
      state.height = profile.height;
      state.weight = profile.weight;
    }
    state.configLocked = keepConfigLocked;
    state.day = localDateKey(new Date());
    itemLocks = { device: {}, appliance: {}, trip: {} };
    saveItemLocks();
    currentTab = 'body';
    applyBodyInputs();
    applyDeviceInputs();
    applyApplianceInputs();
    applyTransitInputs();
    render();
    setTab('body', { resetScroll: true });
    saveState();
    closeModal();
    showToast('已恢复示例值，身体资料保留');
  }

  function handleBack() {
    if (isProfileOpen) {
      if (profileMode === 'onboarding') return true;
      closeProfile();
      return true;
    }
    if (!infoModal.hidden) {
      closeModal();
      return true;
    }
    if (currentTab !== 'body') {
      setTab('body', { resetScroll: true });
      return true;
    }
    return false;
  }

  function bindEvents() {
    document.addEventListener('input', handleInput);
    document.addEventListener('change', handleChange);
    document.addEventListener('click', handleDocumentClick);
    infoButton.addEventListener('click', openModal);
    closeInfoButton.addEventListener('click', closeModal);
    settingsButton.addEventListener('click', function () { openProfile('settings'); });
    editProfileButton.addEventListener('click', function () { openProfile('settings'); });
    closeProfileButton.addEventListener('click', closeProfile);
    saveProfileButton.addEventListener('click', saveProfileFromForm);
    configLockToggle.addEventListener('click', toggleConfigLock);
    resetButton.addEventListener('click', resetAll);
    document.querySelectorAll('.tab').forEach(function (tab) {
      tab.addEventListener('keydown', handleTabKeydown);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        if (isProfileOpen) {
          event.preventDefault();
          if (profileMode !== 'onboarding') closeProfile();
          return;
        }
        if (isModalOpen) {
          event.preventDefault();
          closeModal();
          return;
        }
      }
      trapModalFocus(event);
    });
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') {
        saveState();
        saveHistory();
        saveProfile();
        saveItemLocks();
      } else {
        handleDayRollover();
      }
    });
    window.addEventListener('pageshow', handleDayRollover);
    window.addEventListener('focus', handleDayRollover);
    window.setInterval(handleDayRollover, 60000);
    window.addEventListener('beforeunload', function () {
      saveState();
      saveProfile();
      saveItemLocks();
    });
  }

  function initialTab() {
    var hash = (window.location.hash || '').replace('#', '');
    if (TABS.indexOf(hash) >= 0) return hash;
    return state.tab;
  }

  function init() {
    var rolledOverOnLoad = rolloverDayIfNeeded();
    formatDate();
    buildDeviceList();
    buildApplianceList();
    buildTransitList();
    applyBodyInputs();
    applyDeviceInputs();
    applyApplianceInputs();
    applyTransitInputs();
    render();
    setTab(initialTab(), { resetScroll: true });
    bindEvents();
    applyItemCardLocks();
    applyConfigLockState();
    renderConfigLockToggle();
    if (!profile.complete) {
      window.setTimeout(function () { openProfile('onboarding'); }, 120);
    }
    if (rolledOverOnLoad) {
      window.setTimeout(function () {
        showToast('新的一天：昨日用量已归档，今日可调用量已归零');
      }, 650);
    }
    window.requestAnimationFrame(function () {
      window.setTimeout(function () {
        root.classList.add('is-ready');
      }, prefersReduced ? 0 : 40);
    });
    window.setTimeout(function () {
      Array.prototype.forEach.call(document.querySelectorAll('.range'), setRangeFill);
    }, 80);
  }

  window.PowerApp = {
    handleBack: handleBack,
    getState: function () { return Model.clone(state); },
    getHistory: function () { return Model.clone(history); },
    setTab: setTab
  };

  init();
}());
