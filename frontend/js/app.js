const BASE = "https://sub-shi-qubipay-backend.hf.space";


function showTab(tab, el) {
  document.getElementById("merchant").style.display = tab === "merchant" ? "block" : "none";
  document.getElementById("user").style.display = tab === "user" ? "block" : "none";

  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  el.classList.add("active");
}

// 🔹 Utility
function setLoading(el, state) {
  el.disabled = state;
  el.style.opacity = state ? 0.6 : 1;
}

// ✅ Merchant APIs

async function createResource() {
  const btn = document.getElementById("createResourceBtn");

  const api_key = apiKey.value;
  const name = rName.value;
  const description = rDesc.value;
  const price_qubic = parseInt(rPrice.value);

  if (!api_key || !name || !price_qubic) {
    resourceOut.textContent = "❌ Missing fields";
    return;
  }

  resourceOut.textContent = "⏳ Creating resource...";
  setLoading(btn, true);

  try {
    const res = await fetch(BASE + "/api/resources", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_key,
        name,
        description,
        price_qubic
      })
    });

    const text = await res.text();
    resourceOut.textContent = JSON.stringify(JSON.parse(text), null, 2);

    // ✅ Clear fields
    rName.value = "";
    rDesc.value = "";
    rPrice.value = "";

    // ✅ Reload resources
    loadResources();

  } catch (err) {
    resourceOut.textContent = "❌ Network error while creating resource";
    console.error(err);
  }

  // ✅ GUARANTEED re-enable
  setLoading(btn, false);
  setTimeout(updateAnalytics, 500);
}


async function loadResources() {
  const api_key = apiKey.value;

  resourceList.textContent = "⏳ Loading resources...";

  const res = await fetch(BASE + "/api/resources?api_key=" + api_key);
  const text = await res.text();
  resourceList.textContent = JSON.stringify(JSON.parse(text), null, 2);

  try {
    const parsed = JSON.parse(text);
    if (parsed.length > 0) {
      payResourceId.value = parsed[0].id; // auto-fill for demo
    }
  } catch {}
}

// ✅ User APIs

async function createSession() {
  const api_key = apiKey.value;
  const resource_id = parseInt(payResourceId.value);
  const user_wallet = userWallet.value;

  if (!api_key || !resource_id || !user_wallet) {
    sessionOut.textContent = "❌ Missing fields";
    return;
  }

  sessionOut.textContent = "⏳ Creating payment session...";
  setLoading(event.target, true);

  const res = await fetch(BASE + "/api/pay-per-use", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key, resource_id, user_wallet })
  });

  const text = await res.text();
  sessionOut.textContent = JSON.stringify(JSON.parse(text), null, 2);

  try {
    const parsed = JSON.parse(text);

    // ✅ NEW: Read from standardized backend format
    const newSessionId = parsed.data?.session_id;

    if (newSessionId) {
      // ✅ AUTO-FILL confirm payment field
      sessionId.value = newSessionId;

      // ✅ AUTO-COPY for safety
      navigator.clipboard.writeText(newSessionId);

      // ✅ Visual feedback
      paymentBadge.innerHTML = "📋 Session ID auto-filled & copied";
    }

  } catch (e) {
    console.error("Session parse error:", e);
  }

  setLoading(event.target, false);
  setTimeout(updateAnalytics, 500);
}


async function markPaid() {
  const id = sessionId.value;
  statusOut.textContent = "⏳ Marking paid...";

  setLoading(event.target, true);

  const res = await fetch(BASE + "/api/sessions/" + id + "/mock-paid", { method: "POST" });
  const text = await res.text();
  statusOut.textContent = text;

  try {
    const parsed = JSON.parse(text);
    if (parsed.success === true) {
      paymentBadge.innerHTML = "<span class='status-badge status-paid'>✅ PAID</span>";
    }
  } catch {}

  setLoading(event.target, false);
  setTimeout(updateAnalytics, 500);
}

async function checkStatus() {
  const id = sessionId.value;
  statusOut.textContent = "⏳ Checking status...";

  const res = await fetch(BASE + "/api/sessions/" + id);
  const text = await res.text();
  statusOut.textContent = JSON.stringify(JSON.parse(text), null, 2);

  try {
    const parsed = JSON.parse(text);

    // ✅ NEW: Read from parsed.data.status
    const realStatus = parsed.data?.status;

    if (realStatus === "paid") {
      paymentBadge.innerHTML = "<span class='status-badge status-paid'>✅ PAID</span>";
    } else {
      paymentBadge.innerHTML = "<span class='status-badge status-pending'>⏳ PENDING</span>";
    }

  } catch (e) {
    paymentBadge.innerHTML = "<span class='status-badge status-pending'>⚠️ ERROR</span>";
  }
}

async function updateAnalytics() {
  try {
    const api_key = apiKey.value;
    if (!api_key) return;

    const resResources = await fetch(BASE + "/api/resources?api_key=" + api_key);
    const resourcesData = await resResources.json();

    const resSessions = await fetch(BASE + "/api/sessions/all"); // we’ll add this next
    const sessionsData = await resSessions.json();

    let revenue = 0;
    let paid = 0;

    sessionsData.forEach(s => {
      if (s.status === "paid") {
        revenue += s.amount_qubic;
        paid += 1;
      }
    });

    totalRevenue.innerText = revenue;
    totalSessions.innerText = sessionsData.length;
    paidSessions.innerText = paid;

  } catch (e) {
    console.log("Analytics error:", e);
  }
}
