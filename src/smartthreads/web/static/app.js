const provider = document.querySelector("#provider");
const model = document.querySelector("#model");
const baseUrl = document.querySelector("#baseUrl");
const internetModel = document.querySelector("#internetModel");
const internetBaseUrl = document.querySelector("#internetBaseUrl");
const apiKey = document.querySelector("#apiKey");
const timeout = document.querySelector("#timeout");
const systemPrompt = document.querySelector("#systemPrompt");
const thread = document.querySelector("#thread");
const form = document.querySelector("#chatForm");
const promptInput = document.querySelector("#prompt");
const sendButton = document.querySelector("#sendButton");
const internetButton = document.querySelector("#internetButton");
const runtimeStatus = document.querySelector("#runtimeStatus");
const connectionPill = document.querySelector("#connectionPill");
const resetDefaults = document.querySelector("#resetDefaults");

const defaults = {
  auto: {
    model: "qwen3.5:0.8b",
    base_url: "http://localhost:11434",
    internet_model: "gpt-4o-mini",
    internet_base_url: "https://api.openai.com/v1",
  },
  local: {
    model: "qwen3.5:0.8b",
    base_url: "http://localhost:11434",
  },
  internet: {
    model: "gpt-4o-mini",
    base_url: "https://api.openai.com/v1",
  },
};

function setRuntimeStatus(text, tone = "neutral") {
  runtimeStatus.textContent = text;
  runtimeStatus.dataset.tone = tone;
}

function applyProviderDefaults() {
  const selected = provider.value;
  model.value = defaults[selected].model;
  baseUrl.value = defaults[selected].base_url;
  internetModel.value = defaults[selected].internet_model || defaults.internet.internet_model || defaults.internet.model;
  internetBaseUrl.value = defaults[selected].internet_base_url || defaults.internet.internet_base_url || defaults.internet.base_url;
  updateProviderView();
}

function updateProviderView() {
  const selected = provider.value;
  connectionPill.textContent = selected === "auto" ? "Auto" : selected === "local" ? "Local" : "Internet";
  connectionPill.dataset.provider = selected;
  document.body.dataset.provider = selected;
  sendButton.textContent = selected === "auto" ? "Auto Send" : "Send";
}

function addMessage(role, text, meta, note = "") {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const metaLine = document.createElement("div");
  metaLine.className = "message-meta";
  metaLine.textContent = meta;

  const body = document.createElement("p");
  body.textContent = text;

  article.append(metaLine, body);
  if (note) {
    const routeNote = document.createElement("div");
    routeNote.className = "route-note";
    routeNote.textContent = note;
    article.append(routeNote);
  }
  thread.append(article);
  thread.scrollTop = thread.scrollHeight;
}

function requestPayload(prompt, forceProvider = "") {
  return {
    provider: provider.value,
    force_provider: forceProvider,
    model: model.value,
    base_url: baseUrl.value,
    internet_model: internetModel.value,
    internet_base_url: internetBaseUrl.value,
    api_key: apiKey.value,
    timeout: timeout.value,
    system: systemPrompt.value,
    prompt,
  };
}

async function loadConfig() {
  const response = await fetch("/api/config");
  if (!response.ok) {
    throw new Error("Could not load server config");
  }
  const config = await response.json();
  provider.value = config.provider || "auto";
  model.value = config.model || defaults[provider.value].model;
  baseUrl.value = config.base_url || defaults[provider.value].base_url;
  internetModel.value = config.internet_model || defaults.auto.internet_model;
  internetBaseUrl.value = config.internet_base_url || defaults.auto.internet_base_url;
  timeout.value = config.timeout || 120;
  updateProviderView();
}

async function sendPrompt(event, forceProvider = "") {
  if (event) {
    event.preventDefault();
  }

  const prompt = promptInput.value.trim();
  if (!prompt) {
    return;
  }

  addMessage("user", prompt, "You");
  promptInput.value = "";
  promptInput.style.height = "";
  sendButton.disabled = true;
  internetButton.disabled = true;
  setRuntimeStatus(forceProvider === "internet" ? "Internet model" : "Thinking", "busy");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload(prompt, forceProvider)),
    });
    const body = await response.json();

    if (!response.ok) {
      throw new Error(body.error || "Request failed");
    }

    addMessage("assistant", body.text, `${body.provider} · ${body.model}`, body.route_reason || "");
    setRuntimeStatus("Ready", "ok");
  } catch (error) {
    addMessage("error", error.message, "Error");
    setRuntimeStatus("Needs attention", "error");
  } finally {
    sendButton.disabled = false;
    internetButton.disabled = false;
    promptInput.focus();
  }
}

function autosizePrompt() {
  promptInput.style.height = "auto";
  promptInput.style.height = `${Math.min(promptInput.scrollHeight, 180)}px`;
}

provider.addEventListener("change", applyProviderDefaults);
resetDefaults.addEventListener("click", applyProviderDefaults);
form.addEventListener("submit", sendPrompt);
internetButton.addEventListener("click", () => sendPrompt(null, "internet"));
promptInput.addEventListener("input", autosizePrompt);
promptInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    form.requestSubmit();
  }
});

loadConfig().catch((error) => {
  setRuntimeStatus("Config error", "error");
  addMessage("error", error.message, "Error");
});
