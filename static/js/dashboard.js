  let currentBillId = null;
  let currentBillIsFamily = false;
  let currentFamilyMembers = [];
  const ORG = {
    name_ml: "വെൺകുളം ശ്രീസരസ്വതി ക്ഷേത്രം",    // change if needed
    place_ml: "സരസ്വതിപുരം, ഇടവ",
    phone: "9946538926",
    volume: "2025"  // shown like your sample (Vol: 2025)
  };

  function makeBillNo(d=new Date()){
    // YY MM DD HH(am/pm code) mm ss  -> ex: 25120304125956
    let yy = String(d.getFullYear()).slice(-2);
    let mm = String(d.getMonth()+1).padStart(2,"0");
    let dd = String(d.getDate()).padStart(2,"0");
    let hours = d.getHours(); // 0..23
    let ap = hours < 12 ? "1" : "2";          // AM=1, PM=2
    let h12 = hours % 12; if (h12 === 0) h12 = 12;
    let hh = String(h12).padStart(2,"0");
    let mi = String(d.getMinutes()).padStart(2,"0");
    let ss = String(d.getSeconds()).padStart(2,"0");
    return `${yy}${mm}${dd}${hh}${ap}${mi}${ss}`;
  }

function buildReceiptHTML({cust, nak, cart, createdAt, billId}) {
  const billNo = billId;
  const dateStr = createdAt.toLocaleDateString('en-GB'); // DD/MM/YYYY
  let total = cart.reduce((s,p)=>s + p.price*p.qty, 0);
  if (Array.isArray(cust)) {
    total = total * cust.length;  // multiply by number of members
  }

  // Customers rows
  let customerRows = "";
  if (Array.isArray(cust)) {
    cust.forEach(m => {
      customerRows += `<tr><td>${m.name}</td><td>${m.nakshathra}</td></tr>`;
    });
  } else {
    customerRows = `<tr><td>${cust}</td><td>${nak}</td></tr>`;
  }

  // Pooja rows
  const poojaRows = cart.map(p => `
    <tr>
      <td>${p.name}</td>
      <td style="width:18%; text-align:center;">${p.qty}</td>
      <td style="width:22%; text-align:right;">₹${(p.price*p.qty).toFixed(2)}</td>
    </tr>
  `).join("");

  return `
    <div class="receipt-wrap" style="font-size:14px;">
      <div class="receipt-title" style="font-size:18px;">${ORG.name_ml}</div>
      <div class="receipt-sub" style="font-size:14px;">${ORG.place_ml}, ഫോൺ : ${ORG.phone}</div>
      <div class="receipt-bar">
        <div class="receipt-meta" style="font-size:13px;">Vol : ${ORG.volume}&nbsp;&nbsp;<span class="billno">${billNo}</span></div>
        <div class="receipt-heading" style="font-size:14px;">രസീത്</div>
        <div class="receipt-meta" style="font-size:13px;">തീയതി : ${dateStr}</div>
      </div>

      <!-- Poojas Table -->
      <div style="margin-top:5px;">
        <table class="items" style="font-size:19px;">
          <thead>
            <tr>
              <th>വഴിപാടു</th>
              <th>അളവ്</th>
              <th>തുക</th>
            </tr>
          </thead>
          <tbody>${poojaRows}</tbody>
        </table>
      </div>

      <!-- Customers Table -->
      <div style="margin-top:3px;">
        <table class="items" style="font-size:19px;">
          <thead>
            <tr>
              <th>പേര്</th>
              <th>നക്ഷത്രം</th>
            </tr>
          </thead>
          <tbody>${customerRows}</tbody>
        </table>
      </div>

      <!-- Bottom Row: Total and Receiver -->
      <div style="display:flex; justify-content:space-between; font-size:15px; font-weight:700; margin-top:5px;">
        <div>ആകെ തുക : ₹${total.toFixed(2)}</div>
        <div>റീസിവർ- 9846076654</div>
      </div>
    </div>
  `;
}






  let cart = [];
  
    function addProduct(id, name, price) {
      let item = cart.find(p => p.id === id);
      if (item) {
        item.qty++;
      } else {
        cart.push({ id, name, price, qty: 1 });
      }
      renderCart();
    }


  function updateQty(name, change) {
    let item = cart.find(p => p.name === name);
    if(item) {
      item.qty += change;
      if(item.qty <= 0) cart = cart.filter(p => p.name !== name);
    }
    renderCart();
  }

  function removeProduct(name) {
    cart = cart.filter(p => p.name !== name);
    renderCart();
  }

//   function renderCart() {
//     let tbody = document.getElementById("selected-products");
//     tbody.innerHTML = "";
//     let total = 0;
//     cart.forEach(p => {
//       total += p.price * p.qty;
//       tbody.innerHTML += `
//         <tr>
//           <td>${p.name}</td>
//           <td>₹${p.price}</td>
//           <td>
//             <button class="btn btn-sm btn-outline-secondary" onclick="updateQty('${p.name}',-1)">-</button>
//             <span class="px-2">${p.qty}</span>
//             <button class="btn btn-sm btn-outline-secondary" onclick="updateQty('${p.name}',1)">+</button>
//           </td>
//           <td><button class="btn btn-sm btn-outline-danger" onclick="removeProduct('${p.name}')">🗑</button></td>
//         </tr>
//       `;
//     });
//     document.getElementById("total").innerText = total;
//     document.getElementById("calc-total").innerText = total;
//     calculateBalance();
//   }
function renderCart() {
  let tbody = document.getElementById("selected-products");
  tbody.innerHTML = "";
  let total = 0;
  cart.forEach(p => {
    total += p.price * p.qty;
    tbody.innerHTML += `
      <tr>
        <td>${p.name}</td>
        <td>₹${p.price}</td>
        <td>
          <button class="btn btn-sm btn-outline-secondary" onclick="updateQty('${p.name}',-1)">-</button>
          <span class="px-2">${p.qty}</span>
          <button class="btn btn-sm btn-outline-secondary" onclick="updateQty('${p.name}',1)">+</button>
        </td>
        <td><button class="btn btn-sm btn-outline-danger" onclick="removeProduct('${p.name}')">🗑</button></td>
      </tr>
    `;
  });

  let memberCount = currentBillIsFamily ? currentFamilyMembers.length : 1;
  total = total * memberCount;

  document.getElementById("total").innerText = total;
  document.getElementById("calc-total").innerText = total;
  calculateBalance();
}

  function calculateBalance() {
    let paid = parseFloat(document.getElementById("paid").value || 0);
    let total = parseFloat(document.getElementById("total").innerText);
    document.getElementById("balance").innerText = (paid - total).toFixed(2);
  }

    function generateBill() {
      const cust = document.getElementById("cust-name").value.trim();
      const nak  = document.getElementById("nakshathra").value.trim();
      if (!cust || !nak || cart.length === 0) {
        alert("Please fill all details and select products.");
        return;
      }

      const createdAt = new Date();
      const total = cart.reduce((s,p)=>s + p.price*p.qty, 0);

      // ✅ Save immediately
      fetch("generate-bill/", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": "{{ csrf_token }}" },
        body: JSON.stringify({
          customer_name: cust,
          nakshathra: nak,
          bill_no: makeBillNo(createdAt),
          datetime_iso: createdAt.toISOString(),
          cart: cart.map(p => ({ id: p.id, name: p.name, price: p.price, qty: p.qty })),
          total: total
        })
      })
      .then(r=>r.json()).then(data=>{
        if(data.success){
          currentBillId = data.bill_id;

          // ✅ Build bill HTML using backend bill_id
          const html = buildReceiptHTML({cust, nak, cart, createdAt, billId: currentBillId});
          document.getElementById("bill-body").innerHTML = html;

          // ✅ Show modal
          const billModal = new bootstrap.Modal(document.getElementById('billModal'));
          billModal.show();
        } else {
          alert("Error saving bill: " + data.error);
        }
      })
      .catch(err => alert("AJAX Error: " + err));
    }

function printBill() {
  if (!currentBillId) {
    alert("Bill not generated yet.");
    return;
  }

  const createdAt = new Date();
  const total = cart.reduce((s,p)=>s + p.price*p.qty, 0);

  let cust, nak;
  if (currentBillIsFamily) {
    cust = currentFamilyMembers;  // use array of members
    nak = "";                      // optional
  } else {
    cust = document.getElementById("cust-name").value.trim();
    nak  = document.getElementById("nakshathra").value.trim();
  }

  const html = buildReceiptHTML({cust, nak, cart, createdAt, billId: currentBillId});

  const w = window.open('', '', 'width=900,height=650');
  w.document.write(`
    <html>
      <head>
        <title>Receipt</title>
        <meta charset="utf-8">
        <link rel="stylesheet" href="/static/css/dashboard.css">
      </head>
      <body>
        <div class="receipt-container">${html}</div>
      </body>
    </html>
  `);
  w.document.close();
  w.focus();
  w.print();
  w.close();

    // ✅ Close the bill modal immediately
  const billModalEl = document.getElementById('billModal');
  const billModalInstance = bootstrap.Modal.getInstance(billModalEl);
  if(billModalInstance) billModalInstance.hide();

  cart = [];
  renderCart();
  currentBillIsFamily = false;
  currentFamilyMembers = [];
}




const familyBillBtn = document.getElementById("family-bill-btn");
const familyModalEl = document.getElementById("familyBillModal");
const familyContainer = document.getElementById("family-members-container");

document.addEventListener("DOMContentLoaded", function() {
  const familyModal = new bootstrap.Modal(familyModalEl);

  familyBillBtn.addEventListener("click", () => {
    const familyModal = new bootstrap.Modal(document.getElementById("familyBillModal"));
    familyModal.show();
  });

  document.getElementById("generate-family-bill-btn").addEventListener("click", () => {
    const members = [];
    const names = document.querySelectorAll(".member-name");
    const naks = document.querySelectorAll(".member-nakshathra");

    for (let i = 0; i < names.length; i++) {
      const name = names[i].value.trim();
      const nak = naks[i].value.trim();
      if (name && nak) {
        members.push({ name, nakshathra: nak });
      }
    }

    if (!members.length) {
      alert("Please enter at least one member with Nakshathra.");
      return;
    }

    if (cart.length === 0) {
      alert("Please select at least one pooja.");
      return;
    }

    const familyModalEl = document.getElementById("familyBillModal");
    const familyModalInstance = bootstrap.Modal.getInstance(familyModalEl);
    if(familyModalInstance) familyModalInstance.hide();

    const createdAt = new Date();

    fetch("generate-family-bill/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": "{{ csrf_token }}" },
      body: JSON.stringify({
        bill_no: makeBillNo(createdAt),
        members: members,
        cart: cart.map(p => ({ id: p.id, name: p.name, price: p.price, qty: p.qty }))
      })
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        currentBillId = data.bill_id;
        currentBillIsFamily = true;
        currentFamilyMembers = members;

        const html = buildReceiptHTML({cust: members, nak:"", cart, createdAt, billId: currentBillId});
        document.getElementById("bill-body").innerHTML = html;

        const billModalInstance = new bootstrap.Modal(document.getElementById('billModal'));
        billModalInstance.show();
        names.forEach(input => input.value = "");
        naks.forEach(select => select.value = "");
      } else {
        alert("Error saving family bill: " + data.error);
      }
    })
    .catch(err => alert("AJAX Error: " + err));
  });
});




document.addEventListener("DOMContentLoaded", function() {
  const poojaModalEl = document.getElementById("poojaModal");
  const poojaModal = new bootstrap.Modal(poojaModalEl);
  const searchInput = document.getElementById("pooja-search");

  // Open modal on spacebar
  document.addEventListener("keydown", function(e) {
    if ((e.code === "Space" || e.key === " ") &&
        !["INPUT","TEXTAREA"].includes(e.target.tagName)) {
      e.preventDefault();
      poojaModal.show();

      // Wait for modal to fully show, then focus input
      poojaModalEl.addEventListener('shown.bs.modal', function () {
        searchInput.focus();
      }, { once: true });
    }
  });
});

// Filter poojas by search input
function filterPoojas() {
  const search = document.getElementById("pooja-search").value.toLowerCase();
  const items = document.querySelectorAll("#pooja-modal-list .pooja-item");
  items.forEach(item => {
    const name = item.dataset.name;
    item.style.display = name.includes(search) ? "block" : "none";
  });
}
function attachManglishSuggestions(inputId, boxId) {
    const input = document.getElementById(inputId);
    const box = document.getElementById(boxId);
    if (!input || !box) return;

    let activeIndex = 0;
    let items = [];
    let debounceTimer = null;
    let abortController = null;
    const cache = new Map();
    const DEBOUNCE_MS = 120;
    const MAX_SUGGESTIONS = 11;
    let skipSuggestions = false; // <--- new flag

    const showBox = () => box.classList.remove("d-none");
    const hideBox = () => box.classList.add("d-none");
    const clearBox = () => { box.innerHTML = ""; items = []; activeIndex = 0; };

    function getLastWord(txt) {
        if (!txt) return "";
        const parts = txt.trim().split(/\s+/);
        return parts.length ? parts[parts.length - 1] : "";
    }

    function replaceLastWord(txt, replacement) {
        const parts = (txt || "").trim().split(/\s+/);
        if (!parts.length) return (replacement || "") + " ";
        parts[parts.length - 1] = (replacement || "");
        return parts.join(" ") + " ";
    }

    function renderSuggestions(list) {
        clearBox();
        if (!Array.isArray(list) || list.length === 0 || skipSuggestions) return hideBox();
        const slice = list.slice(0, MAX_SUGGESTIONS);
        slice.forEach((s, i) => {
            const div = document.createElement("div");
            div.className = "list-group-item list-group-item-action" + (i === 0 ? " active" : "");
            div.setAttribute("role", "option");
            div.textContent = s;
            div.addEventListener("mousedown", (evt) => {
                evt.preventDefault();
                commitSuggestion(s);
            });
            box.appendChild(div);
        });
        items = Array.from(box.querySelectorAll(".list-group-item"));
        activeIndex = 0;
        showBox();
    }

    function setActive(index) {
        if (!items.length) return;
        items[activeIndex]?.classList.remove("active");
        activeIndex = ((index % items.length) + items.length) % items.length;
        items[activeIndex]?.classList.add("active");
        items[activeIndex]?.scrollIntoView({ block: "nearest", inline: "nearest" });
    }

    function commitSuggestion(choice) {
        if (!choice) return;
        input.value = replaceLastWord(input.value, choice);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        clearBox();
        hideBox();
        skipSuggestions = true; // <--- prevent suggestions until next word
    }

    async function fetchSuggestionsFor(word) {
        if (!word) return [];
        if (cache.has(word)) return cache.get(word);

        if (abortController) {
            try { abortController.abort(); } catch (e) {}
        }
        abortController = new AbortController();
        try {
            const url = `/api/transliterate/?q=${encodeURIComponent(word)}`;
            const res = await fetch(url, { method: "GET", credentials: "same-origin", signal: abortController.signal });
            if (!res.ok) throw new Error("Network response not ok");
            const data = await res.json();
            const result = Array.isArray(data.suggestions) ? data.suggestions : [];
            cache.set(word, result);
            return result;
        } catch (err) {
            if (err.name === "AbortError") return [];
            console.warn("Transliteration fetch error:", err);
            return [];
        }
    }

    async function handleInputEvent() {
        const last = getLastWord(input.value);
        if (!last) { clearBox(); hideBox(); return; }

        if (skipSuggestions) {
            skipSuggestions = false; // <--- reset flag when user types a new word
        }

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(async () => {
            const qAtCall = last;
            const suggestions = await fetchSuggestionsFor(qAtCall);
            if (getLastWord(input.value) !== qAtCall) return;
            renderSuggestions(suggestions);
        }, DEBOUNCE_MS);
    }

    function handleKeyDown(e) {
        if (box.classList.contains("d-none") || !items.length) return;

        if (e.key === "Enter" || e.key === "Tab" || e.key === " ") {
            e.preventDefault();
            const choice = items[activeIndex]?.textContent || items[0]?.textContent;
            if (choice) commitSuggestion(choice);
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive(activeIndex + 1);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive(activeIndex - 1);
        } else if (e.key === "Escape") {
            hideBox();
            clearBox();
        }
    }

    function handleBlur() {
        setTimeout(() => { hideBox(); clearBox(); }, 150);
    }

    input.addEventListener("input", handleInputEvent);
    input.addEventListener("keydown", handleKeyDown);
    input.addEventListener("blur", handleBlur);
}

  // Initialize both inputs
  attachManglishSuggestions("cust-name", "customer_suggestions");
  attachManglishSuggestions("pooja-search", "product_suggestions");
  // Family members (0 to 7)
  for (let i = 0; i < 8; i++) {
    attachManglishSuggestions(`cust-name-fam-${i}`, `customer_suggestions_fam_${i}`);
  }