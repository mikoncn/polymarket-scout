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
};

// 页面加载时获取当前配置和标签列表
window.addEventListener("DOMContentLoaded", async () => {
  await loadTags();
  await loadConfig();
});

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
    elements.minVolume.value = config.SCOUT_MIN_VOLUME;
    elements.minProb.value = config.SCOUT_MIN_PROB;
    elements.maxProb.value = config.SCOUT_MAX_PROB;
    elements.tag.value = config.SCOUT_TAG;
    elements.minLiquidity.value = config.SCOUT_MIN_LIQUIDITY;
    elements.maxDays.value = config.SCOUT_MAX_DAYS_TO_END;
    elements.search.value = config.SCOUT_SEARCH;
    elements.orderBy.value = config.SCOUT_ORDER_BY;
    elements.fetchLimit.value = config.SCOUT_FETCH_LIMIT;
    elements.runtimeLimit.value = config.SCOUT_RUNTIME_LIMIT;

    showNotification("配置加载成功", "success");
  } catch (error) {
    showNotification("配置加载失败: " + error.message, "error");
  }
}

// 保存配置
elements.saveBtn.addEventListener("click", async () => {
  const config = {
    SCOUT_MIN_VOLUME: elements.minVolume.value,
    SCOUT_MIN_PROB: elements.minProb.value,
    SCOUT_MAX_PROB: elements.maxProb.value,
    SCOUT_TAG: elements.tag.value,
    SCOUT_MIN_LIQUIDITY: elements.minLiquidity.value,
    SCOUT_MAX_DAYS_TO_END: elements.maxDays.value,
    SCOUT_SEARCH: elements.search.value,
    SCOUT_ORDER_BY: elements.orderBy.value,
    SCOUT_FETCH_LIMIT: elements.fetchLimit.value,
    SCOUT_RUNTIME_LIMIT: elements.runtimeLimit.value,
  };

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
