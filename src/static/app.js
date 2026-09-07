const form = document.querySelector("#food-form");
const button = document.querySelector("#start-btn");
const timeline = document.querySelector("#timeline");
const statusBox = document.querySelector("#status");
const reportBox = document.querySelector("#report");
const agentsBox = document.querySelector("#agents");

function formToPayload(formElement) {
  const data = new FormData(formElement);
  return {
    taste: data.get("taste"),
    budget: Number(data.get("budget")),
    weather: data.get("weather"),
    avoid: data.get("avoid"),
    scene: data.get("scene"),
    mood: data.get("mood"),
    agents: {
      agent_a: {
        name: data.get("agentAName"),
        style: data.get("agentAStyle"),
      },
      agent_b: {
        name: data.get("agentBName"),
        style: data.get("agentBStyle"),
      },
    },
  };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderAgents(agents, signatureDishes = {}) {
  const dishA = signatureDishes.agent_a || {};
  const dishB = signatureDishes.agent_b || {};
  agentsBox.innerHTML = `
    <article class="agent agent-a">
      <span class="avatar">A</span>
      <div>
        <h2>${escapeHtml(agents.agent_a.name)}</h2>
        <p>主推：${escapeHtml(dishA.name || "待定")} · ${escapeHtml(dishA.source || "校园档口")}</p>
      </div>
    </article>
    <article class="agent agent-b">
      <span class="avatar">B</span>
      <div>
        <h2>${escapeHtml(agents.agent_b.name)}</h2>
        <p>主推：${escapeHtml(dishB.name || "待定")} · ${escapeHtml(dishB.source || "校园档口")}</p>
      </div>
    </article>
  `;
}

function appendSpeech(item) {
  const source = item.source === "deepseek" ? "DeepSeek" : "本地兜底";
  const wrapper = document.createElement("article");
  wrapper.className = `speech ${item.agent_key}`;
  wrapper.innerHTML = `
      <div class="speech-head">
        <span>第 ${item.round} 轮 · ${escapeHtml(item.agent)}</span>
        <span>主推 ${escapeHtml(item.dish_name || "")} · ${escapeHtml(source)} · ${escapeHtml(item.time)}</span>
      </div>
    <p>${escapeHtml(item.content)}</p>
  `;
  timeline.appendChild(wrapper);
  wrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderReport(report) {
  const scoreRows = Object.entries(report.score || {})
    .map(([name, value]) => {
      const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
      return `
        <div class="score-row">
          <div class="score-label"><span>${escapeHtml(name)}</span><span>${safeValue}</span></div>
          <div class="bar"><span style="width:${safeValue}%"></span></div>
        </div>
      `;
    })
    .join("");

  const reasons = (report.reasons || [])
    .map((reason) => `<li>${escapeHtml(reason)}</li>`)
    .join("");

  reportBox.innerHTML = `
    <div class="report-grid">
      <div>
        <span class="eyebrow">最终战报 · ${escapeHtml(report.source || "local")}</span>
        <h2 class="winner">${escapeHtml(report.recommended_dish || "待定")}</h2>
        <ul class="reasons">${reasons}</ul>
        <p class="meta">${escapeHtml(report.summary || "")}</p>
        <p class="meta">备选方案：${escapeHtml(report.backup_dish || "无")}。风险提示：${escapeHtml(report.risk || "以实际供应为准。")}</p>
      </div>
      <aside class="scores">
        <div class="score-label"><span>获胜阵营</span><span>${escapeHtml(report.winner_agent || "裁判判定")}</span></div>
        ${scoreRows}
      </aside>
    </div>
  `;
  reportBox.classList.remove("hidden");
}

async function handleStream(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();

    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line);
      if (event.type === "start") {
        renderAgents(event.agents, event.signature_dishes);
      } else if (event.type === "status") {
        statusBox.textContent = event.message;
      } else if (event.type === "speech") {
        appendSpeech(event.speech);
      } else if (event.type === "report") {
        renderReport(event.report);
      } else if (event.type === "done") {
        statusBox.textContent = "已出战报";
      } else if (event.type === "error") {
        throw new Error(event.error || "流式运行失败");
      }
    }
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = formToPayload(form);
  button.disabled = true;
  statusBox.textContent = "准备开赛";
  timeline.classList.remove("empty");
  timeline.innerHTML = "";
  reportBox.classList.add("hidden");

  try {
    const response = await fetch("/api/debate-stream", {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(payload),
    });
    if (!response.ok || !response.body) {
      throw new Error("请求失败");
    }
    await handleStream(response);
  } catch (error) {
    statusBox.textContent = "运行失败";
    timeline.innerHTML = `<article class="speech"><p>${escapeHtml(error.message)}</p></article>`;
  } finally {
    button.disabled = false;
  }
});
