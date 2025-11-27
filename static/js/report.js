// Organization data - same as dashboard
const ORG = {
  name_ml: "വെൺകുളം ശ്രീസരസ്വതി ക്ഷേത്രം",
  place_ml: "സരസ്വതിപുരം..., ഇടവ",
  phone: "9946538926",
  volume: "2025"
};

// Helper: create bill number exactly as requested (YYMMDDHHapMMSS with AM=1 PM=2)
function makeBillNo(d=new Date()){
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

// Build receipt HTML (same structure as dashboard)
function buildReceiptHTML({cust, nak, family, cart, createdAt, bill_id, total_amount, is_family}) {
  const created = createdAt ? new Date(createdAt) : new Date();
  const billNo = bill_id;
  const dateStr = created.toLocaleDateString('en-GB'); 
  const total = total_amount ? parseFloat(total_amount) 
                             : (cart || []).reduce((s,p)=>s + (parseFloat(p.price||0) * parseInt(p.qty||1)), 0);

  // Customers
// Customers
let customerRows = "";
if (is_family && Array.isArray(family) && family.length > 0) {
  family.forEach(m => {
    customerRows += `<tr>
                       <td>${m.name}</td>
                       <td>${m.nakshathra}</td>
                     </tr>`;
  });
} else {
  customerRows = `<tr>
                    <td>${cust}</td>
                    <td>${nak}</td>
                  </tr>`;
}


  // Poojas
  const poojaRows = (cart || []).map(p => `
    <tr>
      <td style="text-align:left;">${p.name} (₹${parseFloat(p.price||0).toFixed(2)})</td>
      <td style="width:18%; text-align:center;">${p.qty}</td>
      <td style="width:22%; text-align:right;">₹${(parseFloat(p.price||0)*p.qty).toFixed(2)}</td>
    </tr>
  `).join("");

  return `
    <div class="receipt-wrap">
      <div class="receipt-title">${ORG.name_ml}</div>
      <div class="receipt-sub">${ORG.place_ml}, ഫോൺ : ${ORG.phone}</div>
      <div class="receipt-bar">
        <div class="receipt-meta">Vol : ${ORG.volume}&nbsp;&nbsp;<span class="billno">${billNo}</span></div>
        <div class="receipt-heading">രസീത്</div>
        <div class="receipt-meta">തീയതി : ${dateStr}</div>
      </div>
      
      <!-- Pooja Table -->
      <table class="items">
        <thead><tr><th>വഴിപാടു</th><th>അളവ്</th><th>തുക</th></tr></thead>
        <tbody>${poojaRows}</tbody>
      </table>

      <!-- Customers Table -->
      <table class="items" style="margin-top:6px;">
        <thead>
          <tr>
            <th>പേര്</th>
            <th>നക്ഷത്രം</th>
          </tr>
        </thead>
        <tbody>
          ${customerRows}
        </tbody>
      </table>


      <!-- Total -->
      <div style="display:flex; justify-content:space-between; font-size:15px; font-weight:700; margin-top:5px;">
        <div>ആകെ തുക : ₹${total.toFixed(2)}</div>
        <div>റീസിവർ- 9846076654</div>
      </div>
    </div>
  `;
}


// Parse a poojas text from backend into [{name, qty, price}, ...]
// expected format per row: "Pooja A (₹100), Pooja B (₹50)" or just "Pooja A"
function parsePoojasString(s) {
  if (!s) return [];
  try {
    return JSON.parse(s); // don't wrap in [ ]
  } catch (e) {
    console.error("Parse error:", e, s);
    return [];
  }
}


// Toggle date inputs
function toggleDateInput(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("d-none");
}

// Print whole report area (improved: open new window and inject styles)
function printReport(){
  const printContents = document.getElementById("printArea").innerHTML;
  // collect all stylesheets and inline styles from current page to preserve layout
  const headContent = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
                    .map(node => node.outerHTML).join('\n');

  const w = window.open('', '', 'width=900,height=650');
  w.document.write(`
    <html>
      <head>
        <meta charset="utf-8">
        ${headContent}
        <title>Report</title>
        <style>
          /* ensure A4-friendly printing defaults for the report */
          @page { size: A4; margin: 1cm; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; margin: 0.5cm; }
        </style>
      </head>
      <body>
        ${printContents}
      </body>
    </html>
  `);
  w.document.close();
  w.focus();
  // small timeout to allow styles to load
  setTimeout(()=> { w.print(); w.close(); }, 300);
}

// Modal & View button wiring
document.addEventListener("DOMContentLoaded", function(){
  const billModalEl = document.getElementById("billModal");
  const billModal = new bootstrap.Modal(billModalEl);

  // Attach click to all view buttons
  document.querySelectorAll(".viewBillBtn").forEach(btn => {
    btn.addEventListener("click", () => {
      const family = JSON.parse(btn.dataset.family || "[]");
      const poojas = JSON.parse(btn.dataset.poojas || "[]");

      const html = buildReceiptHTML({
        cust: btn.dataset.customer,
        nak: btn.dataset.nakshathra,
        family: family,
        cart: poojas,
        createdAt: btn.dataset.date,
        bill_id: btn.dataset.bill_id,
        total_amount: btn.dataset.total,
        is_family: btn.dataset.is_family === "true"
      });

      document.getElementById("bill-body").innerHTML = html;
      new bootstrap.Modal(document.getElementById("billModal")).show();
    });
  });


  // Print from modal (ensures same CSS used)
  const printBtn = document.getElementById("printBillBtn");
  printBtn && printBtn.addEventListener("click", function(){
    const css = document.getElementById("receipt-style").innerHTML;
    const html = document.getElementById("bill-body").innerHTML;
    // open print window
    const w = window.open('', '', 'width=900,height=650');
    w.document.write(`
      <html>
        <head>
          <meta charset="utf-8">
          <title>Receipt</title>
          <style>${css}</style>
        </head>
        <body>${html}</body>
      </html>
    `);
    w.document.close();
    w.focus();
    // small delay to ensure content rendered
    setTimeout(() => { w.print(); w.close(); }, 250);
  });
});