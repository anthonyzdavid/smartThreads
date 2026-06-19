const provider = document.querySelector("#provider");
const model = document.querySelector("#model");
const baseUrl = document.querySelector("#baseUrl");
const apiKey = document.querySelector("#apiKey");
const timeout = document.querySelector("#timeout");
const systemPrompt = document.querySelector("#systemPrompt");
const thread = document.querySelector("#thread");
const form = document.querySelector("#chatForm");
const promptInput = document.querySelector("#prompt");
const sendButton = document.querySelector("#sendButton");
const runtimeStatus = document.querySelector("#runtimeStatus");
const connectionPill = document.querySelector("#connectionPill");
const resetDefaults = document.querySelector("#resetDefaults");

const defaults = {
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
  updateProviderView();
}

function updateProviderView() {
  const selected = provider.value;
  connectionPill.textContent = selected === "local" ? "Local" : "Internet";
  connectionPill.dataset.provider = selected;
  document.body.dataset.provider = selected;
}

function addMessage(role, text, meta) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const metaLine = document.createElement("div");
  metaLine.className = "message-meta";
  metaLine.textContent = meta;

  const body = document.createElement("p");
  body.textContent = text;

  article.append(metaLine, body);
  thread.append(article);
  thread.scrollTop = thread.scrollHeight;
}

function requestPayload(prompt) {
  return {
    provider: provider.value,
    model: model.value,
    base_url: baseUrl.value,
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
  provider.value = config.provider || "local";
  model.value = config.model || defaults[provider.value].model;
  baseUrl.value = config.base_url || defaults[provider.value].base_url;
  timeout.value = config.timeout || 120;
  updateProviderView();
}

async function sendPrompt(event) {
  event.preventDefault();

  const prompt = promptInput.value.trim();
  if (!prompt) {
    return;
  }

  addMessage("user", prompt, "You");
  promptInput.value = "";
  promptInput.style.height = "";
  sendButton.disabled = true;
  setRuntimeStatus("Thinking", "busy");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload(prompt)),
    });
    const body = await response.json();

    if (!response.ok) {
      throw new Error(body.error || "Request failed");
    }

    addMessage("assistant", body.text, `${body.provider} · ${body.model}`);
    setRuntimeStatus("Ready", "ok");
  } catch (error) {
    addMessage("error", error.message, "Error");
    setRuntimeStatus("Needs attention", "error");
  } finally {
    sendButton.disabled = false;
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
