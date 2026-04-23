const state = {
  activeTab: "products",
  month: new Date().toISOString().slice(0, 7),
  dashboard: null,
  selectedQuickCosts: [],
};

const colors = ["#0f9d84", "#ff8c61", "#3bb6a1", "#f4b15d", "#317b6b", "#f06e56", "#7ec7bb"];

const el = {
  tabs: document.getElementById("tabs"),
  pages: [...document.querySelectorAll(".page")],
  title: document.getElementById("page-title"),
  kicker: document.getElementById("page-kicker"),
  monthInput: document.getElementById("month-input"),
  refreshButton: document.getElementById("refresh-button"),
  todaySalesCard: document.getElementById("today-sales-card"),
  openProductModal: document.getElementById("open-product-modal"),
  heroSellButton: document.getElementById("hero-sell-button"),
  quickProductForm: document.getElementById("quick-product-form"),
  productCostSelector: document.getElementById("product-cost-selector"),
  selectedCosts: document.getElementById("selected-costs"),
  productGrid: document.getElementById("product-grid"),
  productMetrics: document.getElementById("product-metrics"),
  variableTotal: document.getElementById("variable-total"),
  fixedTotal: document.getElementById("fixed-total"),
  variableDonut: document.getElementById("variable-donut"),
  fixedDonut: document.getElementById("fixed-donut"),
  variableLegend: document.getElementById("variable-legend"),
  fixedLegend: document.getElementById("fixed-legend"),
  variableList: document.getElementById("variable-list"),
  fixedList: document.getElementById("fixed-list"),
  statsCards: document.getElementById("stats-cards"),
  lineChart: document.getElementById("line-chart"),
  barChart: document.getElementById("bar-chart"),
  activityStrip: document.getElementById("activity-strip"),
  modalBackdrop: document.getElementById("modal-backdrop"),
  modalContent: document.getElementById("modal-content"),
  productModalTemplate: document.getElementById("product-modal-template"),
  costModalTemplate: document.getElementById("cost-modal-template"),
};

function currency(value) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function percentage(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function safeValue(value) {
  return value === "" || value === undefined ? null : value;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "No se pudo completar la accion.");
  }
  return data;
}

async function loadDashboard() {
  const data = await api(`/api/dashboard?month=${state.month}`);
  state.dashboard = data;
  renderAll();
}

function renderAll() {
  renderHeader();
  renderSidebar();
  renderQuickForm();
  renderProductMetrics();
  renderProducts();
  renderCosts("variable");
  renderCosts("fixed");
  renderStats();
}

function renderHeader() {
  const meta = {
    products: ["Catalogo", "Productos"],
    variable: ["Estructura", "Gastos variables"],
    fixed: ["Estructura", "Gastos fijos"],
    stats: ["Panel", "Estadisticas"],
  };
  el.kicker.textContent = meta[state.activeTab][0];
  el.title.textContent = meta[state.activeTab][1];
  el.monthInput.value = state.month;
}

function renderSidebar() {
  const today = state.dashboard.stats.today_sales;
  el.todaySalesCard.innerHTML = `
    <p class="eyebrow">Hoy</p>
    <strong>${today.count}</strong>
    <p class="muted">ventas registradas</p>
    <strong>${currency(today.revenue)}</strong>
    <p class="muted">ingresos del dia</p>
  `;
}

function renderQuickForm() {
  const options = state.dashboard.variable_costs.map(
    (cost) => `<option value="${cost.id}">${cost.name} · ${currency(cost.amount)}</option>`
  );
  el.productCostSelector.innerHTML = [
    `<option value="">Selecciona un coste variable</option>`,
    ...options,
  ].join("");

  el.selectedCosts.innerHTML = state.selectedQuickCosts.length
    ? state.selectedQuickCosts.map((costId) => {
        const cost = state.dashboard.variable_costs.find((item) => item.id === costId);
        return `<span class="chip">${cost.name}<button type="button" data-remove-cost="${costId}">&times;</button></span>`;
      }).join("")
    : `<div class="empty-state">Asigna costes variables desde el desplegable para no escribir de mas.</div>`;
}

function renderProductMetrics() {
  const products = state.dashboard.products;
  const totals = {
    products: products.length,
    avgSalePrice: products.length ? products.reduce((sum, item) => sum + item.sale_price, 0) / products.length : 0,
    avgMargin: products.length ? products.reduce((sum, item) => sum + item.margin_per_sale, 0) / products.length : 0,
    mappedCosts: products.reduce((sum, item) => sum + item.variable_costs.length, 0),
  };
  const cards = [
    ["Productos activos", totals.products, "catalogo disponible"],
    ["Precio medio", currency(totals.avgSalePrice), "media de venta"],
    ["Margen medio", currency(totals.avgMargin), "por unidad"],
    ["Costes vinculados", totals.mappedCosts, "asignaciones activas"],
  ];
  el.productMetrics.innerHTML = cards.map(([label, value, copy]) => `
    <article class="metric-card">
      <p class="eyebrow">${label}</p>
      <strong>${value}</strong>
      <p class="muted">${copy}</p>
    </article>
  `).join("");
}

function renderProducts() {
  if (!state.dashboard.products.length) {
    el.productGrid.innerHTML = `<div class="empty-state">Todavia no hay productos. Empieza arriba con el alta rapida.</div>`;
    return;
  }

  el.productGrid.innerHTML = state.dashboard.products.map((product) => `
    <article class="product-card">
      <div class="product-header">
        <div>
          <p class="eyebrow">Producto</p>
          <h3>${product.name}</h3>
        </div>
        <div class="action-menu">
          <button class="action-pill" data-toggle-menu="${product.id}">•••</button>
          <div class="action-menu-panel" id="menu-${product.id}" hidden>
            <button type="button" data-edit-product="${product.id}">Modificar</button>
            <button type="button" data-delete-product="${product.id}">Eliminar</button>
          </div>
        </div>
      </div>
      <div class="product-meta">
        <div>
          <p class="eyebrow">Venta</p>
          <strong>${currency(product.sale_price)}</strong>
        </div>
        <div>
          <p class="eyebrow">Coste</p>
          <strong>${currency(product.cost_price)}</strong>
        </div>
        <div>
          <p class="eyebrow">Margen</p>
          <strong>${currency(product.margin_per_sale)}</strong>
        </div>
      </div>
      <div class="selected-costs">
        ${product.variable_costs.length
          ? product.variable_costs.map((cost) => `<span class="chip">${cost.name}</span>`).join("")
          : `<span class="muted">Sin costes variables vinculados</span>`}
      </div>
      <div class="product-actions">
        <button class="primary-button" data-sell-product="${product.id}">Vender</button>
        <button class="ghost-button" data-edit-product="${product.id}">Editar</button>
      </div>
    </article>
  `).join("");
}

function renderCosts(type) {
  const statsKey = type === "fixed" ? "fixed_breakdown" : "variable_breakdown";
  const listKey = type === "fixed" ? "fixed_costs" : "variable_costs";
  const totalKey = type === "fixed" ? "total_fixed_costs" : "total_variable_costs";
  const donut = type === "fixed" ? el.fixedDonut : el.variableDonut;
  const legend = type === "fixed" ? el.fixedLegend : el.variableLegend;
  const list = type === "fixed" ? el.fixedList : el.variableList;
  const total = state.dashboard.stats[totalKey];
  const breakdown = state.dashboard.stats[statsKey];
  const items = state.dashboard[listKey];

  if (type === "fixed") {
    el.fixedTotal.textContent = `Total del mes: ${currency(total)}`;
  } else {
    el.variableTotal.textContent = `Total del mes: ${currency(total)}`;
  }

  renderDonut(donut, legend, breakdown, total, type === "fixed" ? "Gastos fijos" : "Gastos variables");

  list.innerHTML = items.length ? items.map((cost) => `
    <article class="cost-item">
      <div>
        <p class="eyebrow">${type === "fixed" ? "Fijo" : "Variable"}</p>
        <strong>${cost.name}</strong>
        <p class="muted">${new Date(cost.recorded_at).toLocaleDateString("es-ES")}</p>
      </div>
      <div>
        <strong>${currency(cost.amount)}</strong>
        <div class="product-actions">
          <button class="ghost-button" data-edit-cost="${cost.id}" data-cost-type="${type}">Editar</button>
          <button class="soft-button" data-delete-cost="${cost.id}">Eliminar</button>
        </div>
      </div>
    </article>
  `).join("") : `<div class="empty-state">No hay gastos en esta categoria todavia.</div>`;
}

function renderDonut(target, legend, breakdown, total, label) {
  if (!breakdown.length || !total) {
    target.style.setProperty("--segments", "rgba(15, 157, 132, 0.14) 0deg 360deg");
    target.dataset.total = `${label}\n${currency(total)}`;
    legend.innerHTML = `<div class="empty-state">No hay datos suficientes para el reparto de este mes.</div>`;
    return;
  }

  let angle = 0;
  const segments = breakdown.map((item, index) => {
    const start = angle;
    const segmentAngle = Math.round((item.value / total) * 3600) / 10;
    angle += segmentAngle;
    return `${colors[index % colors.length]} ${start}deg ${angle}deg`;
  });

  target.style.setProperty("--segments", segments.join(", "));
  target.dataset.total = `${label}\n${currency(total)}`;
  legend.innerHTML = breakdown.map((item, index) => `
    <div class="legend-item">
      <div>
        <span class="legend-swatch" style="background:${colors[index % colors.length]}"></span>
        <strong>${item.name}</strong>
      </div>
      <div>
        <strong>${percentage(item.percentage)}</strong>
        <p class="muted">${currency(item.value)}</p>
      </div>
    </div>
  `).join("");
}

function renderStats() {
  const { stats } = state.dashboard;
  const income = Number(stats.total_income || 0);
  const marginRate = income ? (Number(stats.total_margin || 0) / income) * 100 : 0;
  const netRate = income ? (Number(stats.profitability || 0) / income) * 100 : 0;
  const cards = [
    ["Ingresos", currency(stats.total_income), "facturacion del mes"],
    ["Margen bruto", percentage(marginRate), "peso del margen sobre ingresos"],
    ["Resultado neto", currency(stats.profitability), `${percentage(netRate)} sobre ingresos`],
    ["Cobertura fija", percentage(stats.fixed_cost_coverage.coverage_percentage), "margen cubriendo gastos fijos"],
  ];
  el.statsCards.innerHTML = cards.map(([label, value, copy]) => `
    <article class="stat-card">
      <p class="eyebrow">${label}</p>
      <strong>${value}</strong>
      <p class="muted">${copy}</p>
    </article>
  `).join("");

  renderLineChart(stats.profitability_series);
  renderBarChart(stats.top_products);
  renderActivityStrip(stats.daily_sales);
}

function renderLineChart(series) {
  if (!series.length) {
    el.lineChart.innerHTML = `<div class="empty-state">Aun no hay evolucion suficiente para dibujar la rentabilidad.</div>`;
    return;
  }

  const width = 700;
  const height = 280;
  const padding = 28;
  const values = series.map((item) => Number(item.profitability || 0));
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = max - min || 1;
  const stepX = (width - padding * 2) / Math.max(series.length - 1, 1);
  const points = series.map((item, index) => {
    const x = padding + index * stepX;
    const y = height - padding - ((Number(item.profitability || 0) - min) / range) * (height - padding * 2);
    return [x, y, item];
  });
  const line = points.map(([x, y]) => `${x},${y}`).join(" ");
  const area = [`${padding},${height - padding}`, ...points.map(([x, y]) => `${x},${y}`), `${width - padding},${height - padding}`].join(" ");

  el.lineChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      <defs>
        <linearGradient id="area-fill" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="rgba(15,157,132,0.32)"></stop>
          <stop offset="100%" stop-color="rgba(15,157,132,0.04)"></stop>
        </linearGradient>
      </defs>
      <polygon points="${area}" fill="url(#area-fill)"></polygon>
      <polyline points="${line}" fill="none" stroke="#0f9d84" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>
      ${points.map(([x, y, item]) => `
        <g>
          <circle cx="${x}" cy="${y}" r="6" fill="#ff8c61"></circle>
          <text x="${x}" y="${height - 8}" text-anchor="middle" font-size="12" fill="#6f7d78">${item.month.slice(2)}</text>
        </g>
      `).join("")}
    </svg>
  `;
}

function renderBarChart(items) {
  if (!items.length) {
    el.barChart.innerHTML = `<div class="empty-state">Todavia no hay ventas suficientes para comparar productos.</div>`;
    return;
  }

  const max = Math.max(...items.map((item) => item.revenue), 1);
  el.barChart.innerHTML = items.map((item, index) => `
    <div class="bar-row">
      <div>
        <strong>${item.name}</strong>
        <p class="muted">${item.sales_count} ventas</p>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="--target-width:${(item.revenue / max) * 100}%; --delay:${index * 80}ms"></div>
      </div>
      <strong>${currency(item.revenue)}</strong>
    </div>
  `).join("");
}

function renderActivityStrip(items) {
  if (!items.length) {
    el.activityStrip.innerHTML = `<div class="empty-state">No hay actividad registrada en este mes todavia.</div>`;
    return;
  }

  const width = 900;
  const height = 240;
  const padding = 20;
  const max = Math.max(...items.map((item) => item.revenue), 1);
  const barWidth = (width - padding * 2) / items.length - 10;

  el.activityStrip.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      ${items.map((item, index) => {
        const x = padding + index * ((width - padding * 2) / items.length);
        const barHeight = (item.revenue / max) * (height - 56);
        const y = height - padding - barHeight;
        return `
          <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="12" fill="${colors[index % colors.length]}" opacity="0.88">
            <animate attributeName="height" from="0" to="${barHeight}" dur="0.8s" begin="${index * 0.08}s" fill="freeze"></animate>
            <animate attributeName="y" from="${height - padding}" to="${y}" dur="0.8s" begin="${index * 0.08}s" fill="freeze"></animate>
          </rect>
          <text x="${x + barWidth / 2}" y="${height - 6}" text-anchor="middle" font-size="11" fill="#6f7d78">${item.day.slice(8)}</text>
        `;
      }).join("")}
    </svg>
  `;
}

function setActiveTab(tab) {
  state.activeTab = tab;
  [...el.tabs.querySelectorAll(".tab")].forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === tab);
  });
  el.pages.forEach((page) => page.classList.toggle("is-visible", page.dataset.page === tab));
  renderHeader();
}

function openModal(template) {
  el.modalContent.innerHTML = "";
  el.modalContent.appendChild(template.content.cloneNode(true));
  el.modalBackdrop.classList.remove("hidden");
}

function closeModal() {
  el.modalBackdrop.classList.add("hidden");
  el.modalContent.innerHTML = "";
}

function openProductModal(product = null) {
  openModal(el.productModalTemplate);
  document.getElementById("product-modal-title").textContent = product ? "Modificar producto" : "Anadir producto";
  const form = document.getElementById("product-modal-form");
  const picker = document.getElementById("product-modal-costs");
  const selected = new Set(product ? product.variable_costs.map((cost) => cost.id) : []);

  form.querySelector('[name="product_id"]').value = product?.id || "";
  form.querySelector('[name="name"]').value = product?.name || "";
  form.querySelector('[name="sale_price"]').value = product?.sale_price || "";
  picker.innerHTML = state.dashboard.variable_costs.map((cost) => `
    <label>
      <input type="checkbox" value="${cost.id}" ${selected.has(cost.id) ? "checked" : ""}>
      ${cost.name} · ${currency(cost.amount)}
    </label>
  `).join("");
}

function openCostModal(type, cost = null) {
  openModal(el.costModalTemplate);
  document.getElementById("cost-modal-title").textContent = cost ? "Modificar gasto" : "Anadir gasto";
  const form = document.getElementById("cost-modal-form");
  form.querySelector('[name="cost_id"]').value = cost?.id || "";
  form.querySelector('[name="cost_type"]').value = type;
  form.querySelector('[name="name"]').value = cost?.name || "";
  form.querySelector('[name="amount"]').value = cost?.amount || "";
  form.addEventListener("submit", handleCostSubmit);
}

function getProduct(productId) {
  return state.dashboard.products.find((item) => item.id === Number(productId));
}

function getCost(costId) {
  return [...state.dashboard.fixed_costs, ...state.dashboard.variable_costs].find((item) => item.id === Number(costId));
}

async function handleProductSubmit(event) {
  event.preventDefault();
  try {
    const form = event.target;
    const nameField = form.id === "product-modal-form"
      ? form.querySelector('[name="name"]')
      : document.getElementById("product-name");
    const priceField = form.id === "product-modal-form"
      ? form.querySelector('[name="sale_price"]')
      : document.getElementById("product-price");
    const productId = form.id === "product-modal-form"
      ? form.querySelector('[name="product_id"]').value
      : "";
    const payload = {
      name: nameField?.value || "",
      sale_price: safeValue(priceField?.value),
      variable_cost_ids: form.id === "product-modal-form"
        ? [...form.querySelectorAll('input[type="checkbox"]:checked')].map((input) => Number(input.value))
        : state.selectedQuickCosts,
    };

    if (form.id === "product-modal-form" && productId) {
      await api(`/api/products/${productId}`, { method: "PATCH", body: JSON.stringify(payload) });
      closeModal();
    } else {
      await api("/api/products", { method: "POST", body: JSON.stringify(payload) });
      form.reset();
      state.selectedQuickCosts = [];
    }

    await loadDashboard();
  } catch (error) {
    console.error(error);
    alert(error.message || "No se pudo guardar el producto.");
  }
}

async function handleCostSubmit(event) {
  event.preventDefault();
  try {
    const form = event.currentTarget;
    console.log("Submitting cost form", {
      costId: form.querySelector('[name="cost_id"]').value,
      costType: form.querySelector('[name="cost_type"]').value,
    });
    const costId = form.querySelector('[name="cost_id"]').value;
    const payload = {
      name: form.querySelector('[name="name"]').value,
      amount: form.querySelector('[name="amount"]').value,
      cost_type: form.querySelector('[name="cost_type"]').value,
    };

    if (costId) {
      await api(`/api/costs/${costId}`, { method: "PATCH", body: JSON.stringify(payload) });
    } else {
      await api("/api/costs", { method: "POST", body: JSON.stringify(payload) });
    }

    closeModal();
    await loadDashboard();
  } catch (error) {
    console.error(error);
    alert(error.message || "No se pudo guardar el gasto.");
  }
}

function bindEvents() {
  el.tabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tab]");
    if (!button) return;
    setActiveTab(button.dataset.tab);
  });

  el.monthInput.addEventListener("change", async (event) => {
    state.month = event.target.value;
    await loadDashboard();
  });

  el.refreshButton.addEventListener("click", loadDashboard);
  el.openProductModal.addEventListener("click", () => openProductModal());
  el.heroSellButton.addEventListener("click", async () => {
    const firstProduct = state.dashboard.products[0];
    if (!firstProduct) return;
    await api(`/api/products/${firstProduct.id}/sell`, { method: "POST" });
    await loadDashboard();
  });

  document.addEventListener("click", async (event) => {
    if (!event.target.closest(".action-menu")) {
      document.querySelectorAll(".action-menu-panel").forEach((panel) => {
        panel.hidden = true;
      });
    }

    const removeChip = event.target.closest("[data-remove-cost]");
    if (removeChip) {
      state.selectedQuickCosts = state.selectedQuickCosts.filter((id) => id !== Number(removeChip.dataset.removeCost));
      renderQuickForm();
      return;
    }

    const toggleMenu = event.target.closest("[data-toggle-menu]");
    if (toggleMenu) {
      const panel = document.getElementById(`menu-${toggleMenu.dataset.toggleMenu}`);
      if (panel) panel.hidden = !panel.hidden;
      return;
    }

    const sellButton = event.target.closest("[data-sell-product]");
    if (sellButton) {
      await api(`/api/products/${sellButton.dataset.sellProduct}/sell`, { method: "POST" });
      await loadDashboard();
      return;
    }

    const editProduct = event.target.closest("[data-edit-product]");
    if (editProduct) {
      openProductModal(getProduct(editProduct.dataset.editProduct));
      return;
    }

    const deleteProduct = event.target.closest("[data-delete-product]");
    if (deleteProduct && confirm("Eliminar este producto?")) {
      await api(`/api/products/${deleteProduct.dataset.deleteProduct}`, { method: "DELETE" });
      await loadDashboard();
      return;
    }

    const openCostModalButton = event.target.closest("[data-open-cost-modal]");
    if (openCostModalButton) {
      openCostModal(openCostModalButton.dataset.openCostModal);
      return;
    }

    const editCost = event.target.closest("[data-edit-cost]");
    if (editCost) {
      openCostModal(editCost.dataset.costType, getCost(editCost.dataset.editCost));
      return;
    }

    const deleteCost = event.target.closest("[data-delete-cost]");
    if (deleteCost && confirm("Eliminar este gasto?")) {
      await api(`/api/costs/${deleteCost.dataset.deleteCost}`, { method: "DELETE" });
      await loadDashboard();
      return;
    }

    if (event.target.matches("[data-close-modal]") || event.target === el.modalBackdrop) {
      closeModal();
    }
  });

  el.productCostSelector.addEventListener("change", (event) => {
    const costId = Number(event.target.value);
    if (!costId || state.selectedQuickCosts.includes(costId)) return;
    state.selectedQuickCosts.push(costId);
    event.target.value = "";
    renderQuickForm();
  });

  el.quickProductForm.addEventListener("submit", handleProductSubmit);
  el.modalBackdrop.addEventListener("submit", async (event) => {
    if (event.target.id === "product-modal-form") {
      await handleProductSubmit(event);
    }
  });

}

bindEvents();
loadDashboard().catch((error) => {
  console.error(error);
  alert(error.message);
});
