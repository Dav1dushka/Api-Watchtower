const $ = (selector) => document.querySelector(selector);

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}
function statusClass(value) {
  return String(value || "").toLowerCase();
}
function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value.replace(" ", "T") + "Z");
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json(); message = body.detail || message; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}
function updateStats(targets, checks) {
  $("#target-count").textContent = targets.length;
  $("#healthy-count").textContent = targets.filter(t => t.last_health === "HEALTHY").length;
  $("#attention-count").textContent = targets.filter(t => t.last_health && t.last_health !== "HEALTHY").length;
  $("#check-count").textContent = checks.length;
}
function renderTargets(items) {
  const host = $("#targets");
  host.replaceChildren();
  if (!items.length) {
    host.append(make("p", "muted", "No targets yet. Add an endpoint above to start monitoring."));
    return;
  }
  for (const item of items) {
    const row = make("article", "target");
    const main = make("div", "target-main");
    main.append(make("p", "target-name", item.name));
    main.append(make("p", "target-url", item.url));
    const meta = make("div", "target-meta");
    meta.append(make("span", `status ${statusClass(item.last_health)}`, item.last_health || "NOT CHECKED"));
    if (item.last_latency_ms !== null && item.last_latency_ms !== undefined) {
      meta.append(make("span", "muted", `${item.last_latency_ms} ms`));
    }
    const run = make("button", "small-btn", "Run check");
    run.addEventListener("click", async () => {
      run.disabled = true; run.textContent = "Checking…";
      try { await api(`/api/targets/${item.id}/check`, { method: "POST" }); await refresh(); }
      catch (error) { alert(error.message); }
      finally { run.disabled = false; run.textContent = "Run check"; }
    });
    const remove = make("button", "small-btn delete-btn", "Remove");
    remove.addEventListener("click", async () => {
      if (!confirm(`Remove ${item.name} and its check history?`)) return;
      try { await api(`/api/targets/${item.id}`, { method: "DELETE" }); await refresh(); }
      catch (error) { alert(error.message); }
    });
    meta.append(run, remove);
    row.append(main, meta);
    host.append(row);
  }
}
function renderHistory(items) {
  const body = $("#history");
  body.replaceChildren();
  if (!items.length) {
    const row = make("tr");
    const cell = make("td", "muted", "No checks yet.");
    cell.colSpan = 6; row.append(cell); body.append(row); return;
  }
  for (const item of items) {
    const row = make("tr");
    const values = [
      item.target_name, item.health, item.status_code ?? "—",
      item.latency_ms === null ? "—" : `${item.latency_ms} ms`,
      `${item.security_score}/100`, formatDate(item.checked_at),
    ];
    values.forEach((value, index) => {
      const cell = make("td");
      if (index === 1) cell.append(make("span", `status ${statusClass(item.health)}`, value));
      else cell.textContent = value;
      row.append(cell);
    });
    body.append(row);
  }
}
async function refresh() {
  const [targets, checks] = await Promise.all([api("/api/targets"), api("/api/checks?limit=30")]);
  renderTargets(targets);
  renderHistory(checks);
  updateStats(targets, checks);
}
$("#target-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  button.disabled = true;
  $("#form-message").textContent = "Adding target…";
  try {
    await api("/api/targets", {
      method: "POST",
      body: JSON.stringify({ name: $("#target-name").value, url: $("#target-url").value }),
    });
    event.currentTarget.reset();
    $("#form-message").textContent = "Target added. Run a check when ready.";
    await refresh();
  } catch (error) {
    $("#form-message").textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
$("#refresh-btn").addEventListener("click", () => refresh().catch(error => alert(error.message)));
refresh().catch(error => { $("#targets").textContent = error.message; });
