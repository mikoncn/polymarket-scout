// API 基础路径
const API_BASE = "";

// DOM 元素
const elements = {
  // 配置输入
  minVolume: document.getElementById("minVolume"),
  minProb: document.getElementById("minProb"),
  maxProb: document.getElementById("maxProb"),
  tag: document.getElementById("tag"),
  minLiquidity: document.getElementById("minLiquidity"),
  maxDays: document.getElementById("maxDays"),
  search: document.getElementById("search"),
  orderBy: document.getElementById("orderBy"),
  fetchLimit: document.getElementById("fetchLimit"),
  runtimeLimit: document.getElementById("runtimeLimit"),

  // 按钮
  saveBtn: document.getElementById("saveBtn"),
  scoutBtn: document.getElementById("scoutBtn"),
  resetBtn: document.getElementById("resetBtn"),

  // 结果展示
  resultsContainer: document.getElementById("resultsContainer"),
  loadingOverlay: document.getElementById("loadingOverlay"),
  notification: document.getElementById("notification"),
  
  // 新增字段和按钮
  exclude: document.getElementById("exclude"),
  presetSelect: document.getElementById("presetSelect"),
  savePresetBtn: document.getElementById("savePresetBtn"),
};

// 页面加载时获取当前配置、标签和预设列表
window.addEventListener("DOMContentLoaded", async () => {
  await loadTags();
  await loadPresets(); // 加载预设列表
  await loadConfig();
});

// 加载预设列表
async function loadPresets() {
  try {
    const response = await fetch(`${API_BASE}/api/presets`);
    const presets = await response.json();
    
    // 清空现有选项
    elements.presetSelect.innerHTML = '<option value="">-- 选择预设方案 --</option>';
    
    // 添加预设选项
    presets.forEach(name => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      elements.presetSelect.appendChild(option);
    });
  } catch (error) {
    console.error("预设加载失败:", error);
  }
}

// 切换预设方案
elements.presetSelect.addEventListener("change", async (e) => {
  const presetName = e.target.value;
  if (!presetName) return;

  try {
    const response = await fetch(`${API_BASE}/api/presets/${presetName}`);
    const config = await response.json();
    
    // 填充表单
    fillForm(config);
    showNotification(`已加载方案: ${presetName}`, "success");
    
    // 自动保存加载的配置到 .env (可选，这里先不自动保存，让用户确认)
    // await saveConfigToEnv(config); 
  } catch (error) {
    showNotification("加载方案失败: " + error.message, "error");
  }
});

// 保存当前为新方案
elements.savePresetBtn.addEventListener("click", async () => {
  const name = prompt("请输入新方案名称 (例如: 激进短线):");
  if (!name) return;
  
  const config = getConfigFromForm();
  
  try {
    const response = await fetch(`${API_BASE}/api/presets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, config }),
    });
    
    const result = await response.json();
    if (result.success) {
      showNotification("✅ 方案保存成功", "success");
      await loadPresets(); // 刷新列表
      elements.presetSelect.value = name; // 选中新方案
    } else {
      showNotification("❌ " + result.message, "error");
    }
  } catch (error) {
    showNotification("保存失败: " + error.message, "error");
  }
});

// 从表单获取配置对象
function getConfigFromForm() {
  return {
    SCOUT_MIN_VOLUME: elements.minVolume.value,
    SCOUT_MIN_PROB: elements.minProb.value,
    SCOUT_MAX_PROB: elements.maxProb.value,
    SCOUT_TAG: elements.tag.value,
    SCOUT_MIN_LIQUIDITY: elements.minLiquidity.value,
    SCOUT_MAX_DAYS_TO_END: elements.maxDays.value,
    SCOUT_SEARCH: elements.search.value,
    SCOUT_EXCLUDE_KEYWORDS: elements.exclude.value,
    SCOUT_ORDER_BY: elements.orderBy.value,
    SCOUT_FETCH_LIMIT: elements.fetchLimit.value,
    SCOUT_RUNTIME_LIMIT: elements.runtimeLimit.value,
  };
}

// 填充表单
function fillForm(config) {
    elements.minVolume.value = config.SCOUT_MIN_VOLUME || '5000';
    elements.minProb.value = config.SCOUT_MIN_PROB || '0.15';
    elements.maxProb.value = config.SCOUT_MAX_PROB || '0.85';
    elements.tag.value = config.SCOUT_TAG || '';
    elements.minLiquidity.value = config.SCOUT_MIN_LIQUIDITY || '';
    elements.maxDays.value = config.SCOUT_MAX_DAYS_TO_END || '';
    elements.search.value = config.SCOUT_SEARCH || '';
    elements.exclude.value = config.SCOUT_EXCLUDE_KEYWORDS || '';
    elements.orderBy.value = config.SCOUT_ORDER_BY || 'volume';
    elements.fetchLimit.value = config.SCOUT_FETCH_LIMIT || '200';
    elements.runtimeLimit.value = config.SCOUT_RUNTIME_LIMIT || '30';
}

// 加载品类标签列表
async function loadTags() {
  try {
    const response = await fetch(`${API_BASE}/api/tags`);
    const tags = await response.json();
    
    // 获取 datalist 元素
    const tagDatalist = document.getElementById("tagList");
    
    // 添加所有标签到 datalist
    tags.forEach(tag => {
      const option = document.createElement("option");
      option.value = tag.label;
      tagDatalist.appendChild(option);
    });
  } catch (error) {
    console.error("标签加载失败:", error);
    // 静默失败，使用默认的空列表
  }
}

// 加载配置
async function loadConfig() {
  try {
    const response = await fetch(`${API_BASE}/api/config`);
    const config = await response.json();

    // 填充表单
    fillForm(config);

    showNotification("配置加载成功", "success");
  } catch (error) {
    showNotification("配置加载失败: " + error.message, "error");
  }
}

// 保存配置
elements.saveBtn.addEventListener("click", async () => {
  const config = getConfigFromForm();

  try {
    const response = await fetch(`${API_BASE}/api/config`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
    });

    const result = await response.json();

    if (result.success) {
      showNotification("✅ 配置已保存", "success");
    } else {
      showNotification("❌ " + result.message, "error");
    }
  } catch (error) {
    showNotification("保存失败: " + error.message, "error");
  }
});
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
    });

    const result = await response.json();

    if (result.success) {
      showNotification("✅ 配置已保存", "success");
    } else {
      showNotification("❌ " + result.message, "error");
    }
  } catch (error) {
    showNotification("保存失败: " + error.message, "error");
  }
});

// 启动侦察
elements.scoutBtn.addEventListener("click", async () => {
  // 显示加载动画
  elements.loadingOverlay.classList.remove("hidden");
  elements.scoutBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/scout`, {
      method: "POST",
    });

    const result = await response.json();

    if (result.success) {
      // 显示结果
      displayResults(result.markets);
      showNotification("🎯 侦察完成", "success");
    } else {
      showNotification("❌ " + result.message, "error");
    }
  } catch (error) {
    showNotification("侦察失败: " + error.message, "error");
  } finally {
    // 隐藏加载动画
    elements.loadingOverlay.classList.add("hidden");
    elements.scoutBtn.disabled = false;
  }
});

// 重置默认配置
elements.resetBtn.addEventListener("click", () => {
  if (confirm("确定要重置为默认配置吗？")) {
    elements.minVolume.value = "5000";
    elements.minProb.value = "0.15";
    elements.maxProb.value = "0.85";
    elements.tag.value = "";
    elements.minLiquidity.value = "";
    elements.maxDays.value = "";
    elements.search.value = "";
    elements.orderBy.value = "volume";
    elements.fetchLimit.value = "200";
    elements.runtimeLimit.value = "30";

    showNotification("已重置为默认配置", "success");
  }
});

// 显示结果
function displayResults(marketsData) {
  elements.resultsContainer.innerHTML = `
        <div class="results-content">${marketsData}</div>
    `;
}

// 显示通知
function showNotification(message, type = "success") {
  elements.notification.textContent = message;
  elements.notification.className = `notification ${type}`;
  elements.notification.classList.remove("hidden");

  setTimeout(() => {
    elements.notification.classList.add("hidden");
  }, 3000);
}
