/* 功耗计算器 — shared calculation model (no DOM dependencies) */
(function (global) {
  'use strict';

  var MODEL = {
    body: {
      kcalPerKwh: 860.421,
      // 1 kcal/day = 4184 J / 86400 s ≈ 0.0484259 W
      kcalPerDayToWatt: 4184 / 86400,
      // Mifflin-St Jeor 男女平均，按实际年龄：
      // 10W + 6.25H - 5A - 78 kcal/day（男女常数 +5 / -161 的平均）
      bmrSexAverageConstant: -78,
      bmrAgeCoefficient: 5,
      strideHeightFactor: 0.00413,
      stepsPerMinute: 100
    },
    battery: {
      voltage: 3.7,
      efficiency: 0.85,
      cyclesMax: 3,
      cyclesStep: 0.25
    },
    equivalence: {
      kgcePerKwh: 0.12284,
      // Tesla Model X 按约 20.8 kWh/100km 折算
      teslaModelXKmPerKwh: 4.8
    },
    gradeLevels: [
      { max: 5, label: '省电模式', text: '点几块炭够你活一天，牛逼' },
      { max: 15, label: '节能模式', text: '控制全球变暖有你一份功劳' },
      { max: 25, label: '均衡模式', text: '试着把空调固定在26度，指不定会少花几块钱' },
      { max: 40, label: '性能模式', text: '耗能有点高，是不是需要注意下账单...' },
      { max: Infinity, label: '高耗能模式', text: '你知道你带得动几张GPU吗...不告诉你！' }
    ],
    fixed: {
      wifi: { name: 'WiFi 路由器', icon: 'wifi', watts: 8, hours: 24 },
      baseStation: { name: '通信基站', icon: 'tower', kwhPerDay: 0.25 },
      cloud: { name: '云服务器及传输', icon: 'cloud', kwhPerDay: 0.25 }
    },
    devices: {
      phone: {
        name: '手机', icon: 'phone', mode: 'battery', unit: 'mAh',
        capacityMin: 800, capacityMax: 10000, capacityStep: 100,
        defaultCapacity: 5000, defaultCycles: 1,
        meta: '日常主力设备'
      },
      tablet: {
        name: '平板电脑', icon: 'tablet', mode: 'battery', unit: 'mAh',
        capacityMin: 3000, capacityMax: 15000, capacityStep: 500,
        defaultCapacity: 8000, defaultCycles: 0.75,
        meta: '大屏娱乐与轻办公'
      },
      laptop: {
        name: '笔记本电脑', icon: 'laptop', mode: 'battery', unit: 'Wh',
        capacityMin: 40, capacityMax: 120, capacityStep: 5,
        defaultCapacity: 60, defaultCycles: 1,
        meta: '电池能量 40–120 Wh'
      },
      powerbank: {
        name: '移动电源', icon: 'powerbank', mode: 'battery', unit: 'mAh',
        capacityMin: 5000, capacityMax: 27000, capacityStep: 500,
        defaultCapacity: 10000, defaultCycles: 0.5,
        meta: '给手机 / 耳机补电'
      },
      earbuds: {
        name: '真无线耳机', icon: 'earbuds', mode: 'battery', unit: 'mAh',
        capacityMin: 200, capacityMax: 1000, capacityStep: 50,
        defaultCapacity: 500, defaultCycles: 1,
        meta: '耳机 + 充电盒'
      },
      headphones: {
        name: '头戴式耳机', icon: 'headphones', mode: 'battery', unit: 'mAh',
        capacityMin: 100, capacityMax: 1800, capacityStep: 50,
        defaultCapacity: 800, defaultCycles: 0.75,
        meta: '包耳式无线耳机'
      },
      actioncam: {
        name: '运动相机', icon: 'actioncam', mode: 'battery', unit: 'mAh',
        capacityMin: 800, capacityMax: 5000, capacityStep: 100,
        defaultCapacity: 1800, defaultCycles: 0.5,
        meta: '户外拍摄'
      },
      camera: {
        name: '相机', icon: 'camera', mode: 'battery', unit: 'mAh',
        capacityMin: 800, capacityMax: 5000, capacityStep: 100,
        defaultCapacity: 2400, defaultCycles: 0.25,
        meta: '卡片机 / 可换镜头机'
      },
      instax: {
        name: '拍立得', icon: 'instant', mode: 'battery', unit: 'mAh',
        capacityMin: 800, capacityMax: 3000, capacityStep: 100,
        defaultCapacity: 1200, defaultCycles: 0.25,
        meta: '即时成像相机'
      },
      desktop: {
        name: '台式主机', icon: 'desktop', mode: 'power',
        powerMin: 150, powerMax: 1000, powerStep: 10,
        defaultPower: 300,
        hoursMin: 0, hoursMax: 24, hoursStep: 0.5,
        defaultHours: 2,
        meta: '按主机功率与使用时长'
      }
    },
    appliances: {
      fridge: {
        name: '冰箱', icon: 'fridge', powerMin: 50, powerMax: 300, powerStep: 10,
        defaultPower: 80, defaultHours: 24,
        meta: '全天运行'
      },
      ac: {
        name: '空调', icon: 'snow', powerMin: 700, powerMax: 3500, powerStep: 100,
        defaultPower: 1200, defaultHours: 0,
        meta: '制冷 / 制热平均功率'
      },
      heater: {
        name: '电热水器', icon: 'heater', powerMin: 1000, powerMax: 3000, powerStep: 100,
        defaultPower: 2000, defaultHours: 0,
        meta: '储水式热水器'
      },
      washer: {
        name: '洗衣机', icon: 'washer', powerMin: 200, powerMax: 1200, powerStep: 50,
        defaultPower: 500, defaultHours: 0,
        meta: '按一次标准洗涤'
      },
      tv: {
        name: '电视', icon: 'tv', powerMin: 50, powerMax: 400, powerStep: 10,
        defaultPower: 120, defaultHours: 0,
        meta: '按屏幕平均功率'
      }
    },
    transit: {
      subway: {
        name: '地铁', icon: 'train', form: 'slider', unit: 'min', unitLabel: '分钟',
        min: 0, max: 120, step: 5, defaultValue: 30,
        speedKmh: 35, kwhPerKm: 0.060, perPerson: true,
        meta: '人均 · 按 35 km/h 估算'
      },
      ebike: {
        name: '电动车', icon: 'bike', form: 'slider', unit: 'min', unitLabel: '分钟',
        min: 0, max: 120, step: 5, defaultValue: 30,
        speedKmh: 20, kwhPerKm: 0.018, perPerson: false,
        meta: '两轮电动自行车 · 20 km/h'
      },
      taxiEv: {
        name: '打车 · 电车', icon: 'evcar', form: 'slider', unit: 'km', unitLabel: '公里',
        min: 0, max: 80, step: 1, defaultValue: 0,
        kwhPerKm: 0.150, perPerson: false,
        meta: '纯电出租车 · 0.15 kWh/km'
      },
      taxi: {
        name: '打车 · 油车', icon: 'fuelcar', form: 'slider', unit: 'km', unitLabel: '公里',
        min: 0, max: 80, step: 1, defaultValue: 0,
        kwhPerKm: 0.55, perPerson: false,
        meta: '燃油出租车 · 0.55 kWh/km'
      },
      cityBus: {
        name: '公交车', icon: 'bus', form: 'slider', unit: 'km', unitLabel: '公里',
        min: 0, max: 200, step: 5, defaultValue: 0,
        kwhPerKm: 0.035, perPerson: true,
        meta: '人均 · 0.035 kWh/km'
      },
      evCar: {
        name: '电车', icon: 'evcar', form: 'slider', unit: 'km', unitLabel: '公里',
        min: 0, max: 500, step: 5, defaultValue: 0,
        kwhPerKm: 0.150, perPerson: false,
        meta: '纯电私家车 · 0.15 kWh/km'
      },
      iceCar: {
        name: '油车', icon: 'fuelcar', form: 'slider', unit: 'km', unitLabel: '公里',
        min: 0, max: 500, step: 5, defaultValue: 0,
        kwhPerKm: 0.600, perPerson: false,
        meta: '燃油私家车 · 0.60 kWh/km'
      },
      coach: {
        name: '大巴', icon: 'bus', form: 'input', unit: 'km', unitLabel: '公里',
        min: 0, max: 2000, step: 10, defaultValue: 0,
        kwhPerKm: 0.050, perPerson: true,
        meta: '人均 · 0.050 kWh/km'
      },
      train: {
        name: '火车', icon: 'train', form: 'input', unit: 'km', unitLabel: '公里',
        min: 0, max: 5000, step: 10, defaultValue: 0,
        kwhPerKm: 0.045, perPerson: true,
        meta: '人均 · 0.045 kWh/km'
      },
      hsr: {
        name: '高铁', icon: 'train', form: 'input', unit: 'km', unitLabel: '公里',
        min: 0, max: 5000, step: 10, defaultValue: 0,
        kwhPerKm: 0.065, perPerson: true,
        meta: '人均 · 0.065 kWh/km'
      },
      plane: {
        name: '飞机', icon: 'plane', form: 'input', unit: 'km', unitLabel: '公里',
        min: 0, max: 10000, step: 10, defaultValue: 0,
        kwhPerKm: 0.300, perPerson: true,
        meta: '人均 · 0.300 kWh/km'
      }
    }
  };

  // These are the items shown on the first screen. Everything else lives
  // behind an expander and starts unchecked, so a new install only includes
  // the core devices/routes until the user opts in.
  var DEFAULT_ON_DEVICES = ['phone', 'earbuds', 'tablet', 'desktop'];
  var DEFAULT_ON_APPLIANCES = ['fridge'];
  var DEFAULT_ON_TRIPS = ['subway', 'ebike'];

  var DEFAULTS = {
    day: '',
    configLocked: false,
    age: 30,
    height: 170,
    weight: 68,
    steps: 8000,
    met: 4.2,
    devices: {},
    appliances: {},
    trips: {},
    tripEnabled: {},
    tab: 'body'
  };

  Object.keys(MODEL.devices).forEach(function (key) {
    var def = MODEL.devices[key];
    DEFAULTS.devices[key] = def.mode === 'power'
      ? { watts: def.defaultPower, hours: def.defaultHours, enabled: DEFAULT_ON_DEVICES.indexOf(key) >= 0 }
      : { capacity: def.defaultCapacity, cycles: def.defaultCycles, enabled: DEFAULT_ON_DEVICES.indexOf(key) >= 0 };
  });

  Object.keys(MODEL.appliances).forEach(function (key) {
    var def = MODEL.appliances[key];
    DEFAULTS.appliances[key] = {
      watts: def.defaultPower,
      hours: def.defaultHours,
      enabled: DEFAULT_ON_APPLIANCES.indexOf(key) >= 0
    };
  });

  Object.keys(MODEL.transit).forEach(function (key) {
    DEFAULTS.trips[key] = MODEL.transit[key].defaultValue;
    DEFAULTS.tripEnabled[key] = DEFAULT_ON_TRIPS.indexOf(key) >= 0;
  });

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function numberOr(value, fallback) {
    var n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function roundTo(value, step) {
    return Math.round(value / step) * step;
  }

  function normalizeState(raw) {
    var source = raw && typeof raw === 'object' ? raw : {};
    var defaults = DEFAULTS;
    var state = {
      day: /^\d{4}-\d{2}-\d{2}$/.test(String(source.day || '')) ? String(source.day) : defaults.day,
      configLocked: source.configLocked === true,
      age: Math.round(clamp(numberOr(source.age, defaults.age), 16, 80)),
      height: Math.round(clamp(numberOr(source.height, defaults.height), 140, 210)),
      weight: Math.round(clamp(numberOr(source.weight, defaults.weight), 40, 120)),
      steps: roundTo(clamp(numberOr(source.steps, defaults.steps), 0, 30000), 50),
      met: clamp(numberOr(source.met, defaults.met), 1, 12),
      devices: {},
      appliances: {},
      trips: {},
      tripEnabled: {},
      tab: ['body', 'device', 'transit', 'overview'].indexOf(source.tab) >= 0 ? source.tab : defaults.tab
    };

    Object.keys(MODEL.devices).forEach(function (key) {
      var def = MODEL.devices[key];
      var fallback = defaults.devices[key];
      var rawItem = source.devices && source.devices[key] && typeof source.devices[key] === 'object'
        ? source.devices[key]
        : null;
      var item = rawItem || {};
      var enabled = fallback.enabled;
      if (rawItem) {
        if (typeof rawItem.enabled === 'boolean') {
          enabled = rawItem.enabled;
        } else if (def.mode === 'power') {
          // Migrate pre-toggle saved states: an item that used to contribute
          // at >0 h stays checked; a deliberately 0 h item stays unchecked.
          enabled = numberOr(rawItem.hours, fallback.hours) > 0;
        } else {
          enabled = numberOr(rawItem.cycles, fallback.cycles) > 0;
        }
      }

      if (def.mode === 'power') {
        state.devices[key] = {
          // Fixed ratings are user-entered exact values; sliders stay coarse,
          // but reloading must not snap 437 W back to 440 W.
          watts: Math.round(
            clamp(numberOr(item.watts, fallback.watts), def.powerMin, def.powerMax)
          ),
          hours: roundTo(
            clamp(numberOr(item.hours, fallback.hours), def.hoursMin, def.hoursMax),
            def.hoursStep
          ),
          enabled: enabled
        };
      } else {
        state.devices[key] = {
          capacity: Math.round(
            clamp(numberOr(item.capacity, fallback.capacity), def.capacityMin, def.capacityMax)
          ),
          cycles: roundTo(
            clamp(numberOr(item.cycles, fallback.cycles), 0, MODEL.battery.cyclesMax),
            MODEL.battery.cyclesStep
          ),
          enabled: enabled
        };
      }
    });

    Object.keys(MODEL.appliances).forEach(function (key) {
      var def = MODEL.appliances[key];
      var fallback = defaults.appliances[key];
      var rawItem = source.appliances && source.appliances[key] && typeof source.appliances[key] === 'object'
        ? source.appliances[key]
        : null;
      var item = rawItem || {};
      var enabled = fallback.enabled;
      if (rawItem) {
        if (typeof rawItem.enabled === 'boolean') {
          enabled = rawItem.enabled;
        } else {
          enabled = numberOr(rawItem.hours, fallback.hours) > 0;
        }
      }
      state.appliances[key] = {
        watts: Math.round(
          clamp(numberOr(item.watts, fallback.watts), def.powerMin, def.powerMax)
        ),
        hours: roundTo(
          clamp(numberOr(item.hours, fallback.hours), 0, 24),
          0.5
        ),
        enabled: enabled
      };
    });

    Object.keys(MODEL.transit).forEach(function (key) {
      var def = MODEL.transit[key];
      var hasRawTrip = !!(source.trips && Object.prototype.hasOwnProperty.call(source.trips, key));
      var rawValue = hasRawTrip ? source.trips[key] : undefined;
      state.trips[key] = clamp(numberOr(rawValue, def.defaultValue), def.min, def.max);
      if (source.tripEnabled && typeof source.tripEnabled[key] === 'boolean') {
        state.tripEnabled[key] = source.tripEnabled[key];
      } else if (hasRawTrip) {
        state.tripEnabled[key] = numberOr(rawValue, def.defaultValue) > 0;
      } else {
        state.tripEnabled[key] = defaults.tripEnabled[key];
      }
    });

    return state;
  }

  function activityLabel(met) {
    if (met < 1.5) return '静坐';
    if (met < 2.2) return '站立';
    if (met < 3.2) return '散步';
    if (met < 4.6) return '快走';
    if (met < 6.2) return '慢跑';
    if (met < 7.6) return '骑行';
    if (met < 8.6) return '跑步';
    return '高强度';
  }

  function bmiLabel(bmi) {
    if (bmi < 18.5) return '偏轻';
    if (bmi < 24) return '正常';
    if (bmi < 28) return '偏高';
    return '肥胖';
  }

  function equivalentsFor(kwh) {
    var n = Math.max(0, Number(kwh) || 0);
    return {
      coalKg: n * MODEL.equivalence.kgcePerKwh,
      teslaKm: n * MODEL.equivalence.teslaModelXKmPerKwh
    };
  }

  function evaluateGrade(kwh) {
    var n = Math.max(0, Number(kwh) || 0);
    var levels = MODEL.gradeLevels;
    for (var i = 0; i < levels.length; i += 1) {
      var level = levels[i];
      if (n <= level.max || i === levels.length - 1) {
        return {
          level: i + 1,
          total: levels.length,
          label: level.label,
          text: level.text,
          max: isFinite(level.max) ? level.max : null
        };
      }
    }
    return {
      level: levels.length,
      total: levels.length,
      label: levels[levels.length - 1].label,
      text: levels[levels.length - 1].text,
      max: null
    };
  }

  function calc(rawState) {
    var state = normalizeState(rawState);

    // 自体：年龄、身高、体重决定基础代谢，步数决定活动时长，MET 决定活动强度。
    var bmrKcal = 10 * state.weight + 6.25 * state.height -
      MODEL.body.bmrAgeCoefficient * state.age + MODEL.body.bmrSexAverageConstant;
    var restPowerW = bmrKcal * MODEL.body.kcalPerDayToWatt;
    var activePowerW = restPowerW * state.met;
    var walkMinutes = state.steps / MODEL.body.stepsPerMinute;
    var activeHours = walkMinutes / 60;
    var activityKwh = restPowerW * (state.met - 1) * activeHours / 1000;
    var bodyKwh = restPowerW * 24 / 1000 + activityKwh;
    var bodyKcal = bodyKwh * MODEL.body.kcalPerKwh;
    var stepLengthM = state.height * MODEL.body.strideHeightFactor;
    var distanceKm = state.steps * stepLengthM / 1000;
    var bmi = state.weight / Math.pow(state.height / 100, 2);

    var deviceItems = Object.keys(MODEL.devices).map(function (key) {
      var def = MODEL.devices[key];
      var values = state.devices[key];
      var enabled = values.enabled !== false;
      if (def.mode === 'power') {
        var powerKwh = enabled ? values.watts * values.hours / 1000 : 0;
        return {
          key: key,
          name: def.name,
          icon: def.icon,
          meta: def.meta,
          mode: 'power',
          enabled: enabled,
          watts: values.watts,
          hours: values.hours,
          capacity: 0,
          capacityUnit: '',
          cycles: 0,
          wallWhPerCharge: 0,
          kwh: powerKwh,
          averageW: powerKwh * 1000 / 24
        };
      }

      var capacityWh = def.unit === 'Wh'
        ? values.capacity
        : values.capacity * MODEL.battery.voltage / 1000;
      var wallWhPerCharge = capacityWh / MODEL.battery.efficiency;
      var batteryKwh = enabled ? wallWhPerCharge * values.cycles / 1000 : 0;
      return {
        key: key,
        name: def.name,
        icon: def.icon,
        meta: def.meta,
        mode: 'battery',
        enabled: enabled,
        capacity: values.capacity,
        capacityUnit: def.unit,
        cycles: values.cycles,
        watts: 0,
        hours: 0,
        wallWhPerCharge: wallWhPerCharge,
        kwh: batteryKwh,
        averageW: batteryKwh * 1000 / 24
      };
    });
    var deviceKwh = deviceItems.reduce(function (sum, item) { return sum + item.kwh; }, 0);

    var applianceItems = Object.keys(MODEL.appliances).map(function (key) {
      var def = MODEL.appliances[key];
      var values = state.appliances[key];
      var enabled = values.enabled !== false;
      var kwh = enabled ? values.watts * values.hours / 1000 : 0;
      return {
        key: key,
        name: def.name,
        icon: def.icon,
        meta: def.meta,
        enabled: enabled,
        watts: values.watts,
        hours: values.hours,
        kwh: kwh,
        averageW: kwh * 1000 / 24
      };
    });
    var applianceKwh = applianceItems.reduce(function (sum, item) { return sum + item.kwh; }, 0);

    var wifiKwh = MODEL.fixed.wifi.watts * MODEL.fixed.wifi.hours / 1000;
    var baseKwh = MODEL.fixed.baseStation.kwhPerDay;
    var cloudKwh = MODEL.fixed.cloud.kwhPerDay;
    var fixedKwh = wifiKwh + baseKwh + cloudKwh;

    var transitItems = Object.keys(MODEL.transit).map(function (key) {
      var def = MODEL.transit[key];
      var value = state.trips[key];
      var enabled = state.tripEnabled[key] !== false;
      var tripDistanceKm = def.unit === 'min' ? value / 60 * def.speedKmh : value;
      var kwh = enabled ? tripDistanceKm * def.kwhPerKm : 0;
      return {
        key: key,
        name: def.name,
        icon: def.icon,
        meta: def.meta,
        form: def.form,
        unit: def.unit,
        unitLabel: def.unitLabel,
        enabled: enabled,
        value: value,
        perPerson: !!def.perPerson,
        distanceKm: tripDistanceKm,
        kwhPerKm: def.kwhPerKm,
        kwh: kwh,
        liters: key === 'taxi' || key === 'iceCar' ? kwh / 9.1 : 0
      };
    });
    var tripsKwh = transitItems.reduce(function (sum, item) { return sum + item.kwh; }, 0);
    var transitKwh = fixedKwh + applianceKwh + tripsKwh;

    var totalKwh = bodyKwh + deviceKwh + transitKwh;
    var averageW = totalKwh * 1000 / 24;

    return {
      state: state,
      body: {
        bmrKcal: bmrKcal,
        restPowerW: restPowerW,
        activePowerW: activePowerW,
        walkMinutes: walkMinutes,
        activeHours: activeHours,
        stepLengthM: stepLengthM,
        distanceKm: distanceKm,
        activityKwh: activityKwh,
        activityKcal: activityKwh * MODEL.body.kcalPerKwh,
        bmi: bmi,
        bmiLabel: bmiLabel(bmi),
        kwh: bodyKwh,
        kcal: bodyKcal,
        averageW: bodyKwh * 1000 / 24,
        label: activityLabel(state.met)
      },
      device: {
        items: deviceItems,
        kwh: deviceKwh,
        averageW: deviceKwh * 1000 / 24
      },
      appliance: {
        items: applianceItems,
        kwh: applianceKwh,
        averageW: applianceKwh * 1000 / 24
      },
      transit: {
        items: transitItems,
        fixed: {
          wifiKwh: wifiKwh,
          baseKwh: baseKwh,
          cloudKwh: cloudKwh,
          kwh: fixedKwh
        },
        appliances: applianceItems,
        appliancesKwh: applianceKwh,
        tripsKwh: tripsKwh,
        kwh: transitKwh,
        averageW: transitKwh * 1000 / 24
      },
      totalKwh: totalKwh,
      averageW: averageW
    };
  }

  global.PowerModel = {
    MODEL: MODEL,
    DEFAULTS: DEFAULTS,
    clone: clone,
    normalizeState: normalizeState,
    activityLabel: activityLabel,
    bmiLabel: bmiLabel,
    equivalentsFor: equivalentsFor,
    evaluateGrade: evaluateGrade,
    calc: calc
  };
}(typeof window !== 'undefined' ? window : this));
