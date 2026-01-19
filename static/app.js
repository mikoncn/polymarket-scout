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

// 页面加载时统一初始化 (串行执行避免竞争)
window.addEventListener("DOMContentLoaded", async () => {
    try {
        elements.loadingOverlay.classList.remove("hidden");
        const loadingText = elements.loadingOverlay.querySelector('p');
        loadingText.textContent = "正在同步前线情报...";

        // 1. 先加载基础数据 (并发加载)
        const [tagsLoaded, presetsLoaded] = await Promise.all([
            loadTags(),
            loadPresets()
        ]);

        // 2. 基础数据到位后，加载当前配置并回填
        await loadConfig();
        
        // 3. 特殊回填: 自动化配置 (因为它是独立变量)
        await loadAutomationConfig();

        elements.loadingOverlay.classList.add("hidden");
    } catch (e) {
        console.error("初始化失败:", e);
        showNotification("系统初始化失败", "error");
    }
});

// 加载自动化配置并回填 UI
async function loadAutomationConfig() {
    try {
        const res = await fetch(`${API_BASE}/api/config`);
        const config = await res.json();
        
        const webhookElem = document.getElementById("webhookUrl");
        const autoSelectElem = document.getElementById("autoPreset");

        if (config.SCOUT_WEBHOOK_URL && webhookElem) {
            webhookElem.value = config.SCOUT_WEBHOOK_URL;
        }

        if (config.SCOUT_AUTO_PRESET && autoSelectElem) {
            // 处理可能存在的引号问题
            const targetValue = config.SCOUT_AUTO_PRESET.replace(/['"]/g, '');
            console.log("回填自动化预设:", targetValue);
            
            // 确保选项已存在
            let found = false;
            for (let i = 0; i < autoSelectElem.options.length; i++) {
                if (autoSelectElem.options[i].value === targetValue) {
                    autoSelectElem.selectedIndex = i;
                    found = true;
                    break;
                }
            }
            if (!found) console.warn("未能在预设列表中找到:", targetValue);
        }
    } catch (e) {
        console.error("加载自动化配置失败:", e);
    }
}

// 加载预设列表
async function loadPresets() {
  try {
    const response = await fetch(`${API_BASE}/api/presets`);
    const presets = await response.json();
    
    // 1. 常规预设下拉框
    elements.presetSelect.innerHTML = '<option value="">-- 选择预设方案 --</option>';
    presets.forEach(name => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      elements.presetSelect.appendChild(option);
    });

    // 2. [Automation] 自动化预设下拉框 (如果存在)
    const autoSelect = document.getElementById("autoPreset");
    if (autoSelect) {
        autoSelect.innerHTML = '<option value="">-- 跟随当前手动配置 --</option>';
        presets.forEach(name => {
            const option = document.createElement("option");
            option.value = name;
            option.textContent = name;
            autoSelect.appendChild(option);
        });
    }

  } catch (error) {
    console.error("预设加载失败:", error);
  }
}

// [Automation] 绑定自动化配置按钮
const saveAutoBtn = document.getElementById("saveAutoBtn");
const testWebhookBtn = document.getElementById("testWebhookBtn");

if (saveAutoBtn) {
    // 保存
    saveAutoBtn.addEventListener("click", async () => {
        const webhookElem = document.getElementById("webhookUrl");
        const autoSelectElem = document.getElementById("autoPreset");
        
        const config = {
            SCOUT_WEBHOOK_URL: webhookElem.value,
            SCOUT_AUTO_PRESET: autoSelectElem.value
        };
        try {
            await fetch(`${API_BASE}/api/config`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config),
            });
            showNotification("✅ 自动化配置已保存", "success");
        } catch (e) {
            showNotification("❌ 保存失败: " + e.message, "error");
        }
    });

    // 测试 Webhook
    testWebhookBtn.addEventListener("click", async () => {
        if (!webhookInput.value) {
            showNotification("⚠️ 请先输入 Webhook URL", "warning");
            return;
        }
        try {
            const res = await fetch(`${API_BASE}/api/test_webhook`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: webhookInput.value }), 
            });
            const result = await res.json();
            if (result.success) showNotification("✅ 测试消息发送成功!", "success");
            else showNotification("❌ 发送失败: " + result.message, "error");
        } catch (e) {
             showNotification("❌ 请求错误: " + e.message, "error");
        }
    });
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
// 保存当前为新方案
console.log("Binding SavePresetBtn...");
// 保存当前为新方案
console.log("Binding SavePresetBtn...");
if (elements.savePresetBtn) {
    // 1. 点击保存，显示弹窗
    elements.savePresetBtn.addEventListener("click", () => {
        const modal = document.getElementById("savePresetModal");
        const input = document.getElementById("newPresetName");
        modal.classList.remove("hidden");
        // 自动聚焦输入框
        setTimeout(() => input.focus(), 100); 
    });
    
    // 2. 绑定弹窗内的按钮
    const confirmBtn = document.getElementById("confirmPresetBtn");
    const cancelBtn = document.getElementById("cancelPresetBtn");
    const modal = document.getElementById("savePresetModal");
    const input = document.getElementById("newPresetName");
    
    // 取消
    cancelBtn.addEventListener("click", () => {
        modal.classList.add("hidden");
    });
    
    // 确认保存
    const performSave = async () => {
        const name = input.value.trim();
        if (!name) {
            showNotification("请输入方案名称", "error");
            return;
        }
        
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
              modal.classList.add("hidden"); // 关闭弹窗
              input.value = ""; // 清空输入
            } else {
              showNotification("❌ " + result.message, "error");
            }
        } catch (error) {
            showNotification("保存失败: " + error.message, "error");
        }
    };

    confirmBtn.addEventListener("click", performSave);
    
    // 允许回车提交
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") performSave();
    });

} else {
    console.error("CRITICAL: savePresetBtn not found in DOM!");
}

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

// 加载品类标签列表 (Custom Dropdown Logic)
async function loadTags() {
  try {
    const response = await fetch(`${API_BASE}/api/tags`);
    const tags = await response.json();
    
    // 获取元素
    const tagOptions = document.getElementById("tagOptions");
    const tagInput = document.getElementById("tag");
    const wrapper = document.getElementById("tagSelectWrapper");
    
    // 1. 渲染列表
    // 保留"全局扫描"选项，添加新选项
    tagOptions.innerHTML = '<li data-value="">全局扫描</li>';
    
    tags.forEach(tag => {
      const li = document.createElement("li");
      li.dataset.value = tag.label;
      li.textContent = tag.label;
      tagOptions.appendChild(li);
    });

    // 2. 绑定交互事件
    
    // 打开下拉框
    tagInput.addEventListener('focus', () => {
        wrapper.classList.add('open');
        filterOptions(); // 聚焦时也进行一次过滤（显示全部或当前匹配项）
    });
    
    // 点击箭头切换
    wrapper.querySelector('.arrow').addEventListener('click', (e) => {
        e.stopPropagation(); // 阻止冒泡
        if (wrapper.classList.contains('open')) {
            wrapper.classList.remove('open');
        } else {
            wrapper.classList.add('open');
            tagInput.focus();
        }
    });

    // 输入筛选
    tagInput.addEventListener('input', () => {
        filterOptions();
        wrapper.classList.add('open'); // 输入时确保展开
    });

    // 选择选项
    tagOptions.addEventListener('click', (e) => {
        if (e.target.tagName === 'LI') {
            const value = e.target.dataset.value;
            tagInput.value = value;
            wrapper.classList.remove('open');
            
            // 触发 input 事件以通知其他监听器（如果有）
            tagInput.dispatchEvent(new Event('input'));
        }
    });

    // 点击外部关闭
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
            wrapper.classList.remove('open');
        }
    });

    // 筛选逻辑函数
    function filterOptions() {
        const query = tagInput.value.toLowerCase();
        const options = tagOptions.querySelectorAll('li');
        let hasVisible = false;

        options.forEach(li => {
            const text = li.textContent.toLowerCase();
            if (text.includes(query)) {
                li.classList.remove('hidden-option');
                hasVisible = true;
            } else {
                li.classList.add('hidden-option');
            }
        });

        // 如果没有匹配项，可以在这里显示"无结果"（可选）
    }

  } catch (error) {
    console.error("标签加载失败:", error);
    showNotification("标签列表加载失败", "error");
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

// 保存配置 (同时更新 .env 和当前选中的预设)
elements.saveBtn.addEventListener("click", async () => {
  const config = getConfigFromForm();
  const currentPreset = elements.presetSelect.value;

  try {
    // 1. 保存到 .env (运行时生效)
    const responseEnv = await fetch(`${API_BASE}/api/config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    const resultEnv = await responseEnv.json();

    if (!resultEnv.success) {
        showNotification("❌ 运行时配置保存失败: " + resultEnv.message, "error");
        return;
    }

    // 2. 如果当前选了预设，同步更新预设文件 (持久化生效)
    if (currentPreset) {
        const responsePreset = await fetch(`${API_BASE}/api/presets`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: currentPreset, config }),
        });
        const resultPreset = await responsePreset.json();
        
        if (resultPreset.success) {
            showNotification(`✅ 配置已保存 (同步更新预设: ${currentPreset})`, "success");
        } else {
            showNotification("⚠️ .env 已保存，但预设更新失败: " + resultPreset.message, "warning");
        }
    } else {
        showNotification("✅ 运行时配置已保存 (未选中预设)", "success");
    }

  } catch (error) {
    showNotification("保存失败: " + error.message, "error");
  }
});
// 启动侦察
elements.scoutBtn.addEventListener("click", async () => {
    // 锁定按钮并显示状态
    elements.loadingOverlay.classList.remove("hidden");
    elements.scoutBtn.disabled = true;
    const loadingText = elements.loadingOverlay.querySelector('p');
    const originalText = loadingText.textContent;

    try {
        // 1. 先保存当前配置!
        loadingText.textContent = "正在保存作战方案...";
        const config = getConfigFromForm();
        
        await fetch(`${API_BASE}/api/config`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(config),
        });

        // 2. 执行侦察 (直接把当前配置传给后端，避免后端环境更新延迟)
        loadingText.textContent = "侦察兵出击中...";
        const response = await fetch(`${API_BASE}/api/scout`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(config), // payload-driven execution
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
        // 恢复状态
        elements.loadingOverlay.classList.add("hidden");
        loadingText.textContent = originalText;
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
