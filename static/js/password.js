const ADMIN_PASSWORD = "admin@123"; // Change this to your desired password

function showPasswordPrompt(action, itemId = null, deleteUrl = null) {
    const password = prompt("🔐 Enter Admin Password:");
    
    if (password === null) {
        return; // User cancelled
    }
    
    if (password !== ADMIN_PASSWORD) {
        alert("❌ Incorrect password! Access denied.");
        return;
    }
    
    // Password is correct, proceed with the action
    switch (action) {
        case 'addEvent':
            $('#addEventModal').modal('show');
            break;
        case 'addPooja':
            $('#addPoojaModal').modal('show');
            break;
        case 'editEvent':
            $(`#editEventModal${itemId}`).modal('show');
            break;
        case 'editPooja':
            $(`#editPoojaModal${itemId}`).modal('show');
            break;
        case 'deleteEvent':
        case 'deletePooja':
            // Set up the delete confirmation modal
            var confirmBtn = document.getElementById('confirmDeleteBtn');
            confirmBtn.setAttribute('href', deleteUrl);
            $('#confirmDeleteModal').modal('show');
            break;
    }
}

// Malayalam IME setup
$(document).ready(function() {
    $('.malayalam-input').ime({ imePath: '{% static "js/jquery.ime.js" %}' });
    $('.malayalam-input').ime('disable');
    $('.malayalam-input').on('focus', function() {
        $(this).ime('enable');
        $(this).ime('setLanguage', 'ml');
        $(this).ime('setIM', 'itrans');
    });
});

// Festival bills filter
function applyFilter() {
    const eventId = $('#filterEvent').val();
    const poojaId = $('#filterPooja').val();
    const paymentStatus = $('#filterPayment').val();

    $.ajax({
        url: window.location.href,
        method: 'GET',
        data: {
            event: eventId,
            pooja: poojaId,
            payment: paymentStatus
        },
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        success: function(response) {
            const tbody = $('table tbody');
            tbody.empty();

            if(response.bills.length === 0) {
                tbody.append('<tr><td colspan="6" class="text-center">No Festival Bills</td></tr>');
                return;
            }

            response.bills.forEach(bill => {
                const poojas = bill.poojas.join(', ');
                let paymentHtml = '';
                if (bill.payment_status === 'Paid') {
                    paymentHtml = `
                        <span class="badge bg-success">✅ Paid</span>
                        <button class="btn btn-sm btn-outline-danger toggle-payment"
                                data-id="${bill.id}" data-action="mark_unpaid">
                            Mark as Unpaid
                        </button>
                    `;
                } else {
                    paymentHtml = `
                        <span class="badge bg-warning text-dark">❌ Pending</span>
                        <button class="btn btn-sm btn-outline-success toggle-payment"
                                data-id="${bill.id}" data-action="mark_paid">
                            Mark as Paid
                        </button>
                    `;
                }

                const row = `
                    <tr data-poojas="${poojas}">
                        <td>${bill.id}</td>
                        <td>${bill.customer_name}</td>
                        <td>${bill.event_name}</td>
                        <td>₹${bill.total_amount}</td>
                        <td>${paymentHtml}</td>
                    </tr>
                `;

                tbody.append(row);
            });
        },
        error: function() {
            alert('Error fetching filtered bills.');
        }
    });
}

function resetFilter() {
    $('#filterEvent').val('');
    $('#filterPooja').val('');
    $('#filterPayment').val('');
    applyFilter();
}

    let cart = [];
const ORG = {
  name_ml: "വെൺകുളം ശ്രീസരസ്വതി ക്ഷേത്രം",    // change if needed
  place_ml: "സരസ്വതിപുരം, ഇടവ",
  phone: "9946538926",
  volume: "2025"  // shown like your sample (Vol: 2025)
};

function updateCartFromSelection() {
    cart = []; // clear previous
    const poojaSelect = document.getElementById("poojaSelect");
    const selectedOptions = Array.from(poojaSelect.selectedOptions);
    selectedOptions.forEach(opt => {
        cart.push({
            id: opt.value,
            name: opt.text.split(' (₹')[0], // get pooja name without price
            price: parseFloat(opt.dataset.price),
            qty: 1 // default quantity 1, you can extend for custom qty
        });
    });
}

function makeBillNo(date) {
    // Example: BILL-20250922-1523
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    const h = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    const sec = String(date.getSeconds()).padStart(2, '0');
    return `BILL-${y}${m}${d}-${h}${min}${sec}`;
}

function buildReceiptHTML({cust, nak, address, cart, createdAt}) {
  const billNo = makeBillNo(createdAt);
  const dateStr = createdAt.toLocaleDateString('en-GB');
  const total = cart.reduce((s,p)=>s + p.price*p.qty, 0);

  const poojaRows = cart.map(p => `
    <tr>
      <td style="text-align:left;">${p.name}</td>
      <td style="width:18%; text-align:center;">${p.qty}</td>
      <td style="width:22%; text-align:right;">₹${(p.price*p.qty).toFixed(2)}</td>
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

    <div class="receipt-grid">
      <div class="box">
        <span class="label">പേര്</span>
        <div>${cust}</div>
      </div>
      <div class="box">
        <span class="label">നക്ഷത്രം</span>
        <div>${nak}</div>
      </div>
      <div class="box" style="grid-column:1 / span 2;">
        <span class="label">വിലാസം</span>
        <div>${address}</div>
      </div>
      <div class="box" style="grid-column:1 / span 2;">
        <span class="label">വഴിപാടു വിവരം</span>
        <table class="items">
          <thead>
            <tr><th style="text-align:left;">വഴിപാടു</th><th style="width:18%;">അളവ്</th><th style="width:22%;">തുക</th></tr>
          </thead>
          <tbody>${poojaRows}</tbody>
        </table>
        <div class="total-row">ആകെ തുക : ₹${total.toFixed(2)}</div>
      </div>
    </div>

    <div class="sign">റീസിവർ- 9846076654</div>
  </div>`;
}


function generateBill() {
  const cust = document.getElementById("cust-name").value.trim();
  const nak  = document.getElementById("nakshathra").value.trim();
  const address = document.getElementById("address").value.trim();

  updateCartFromSelection()


  if (!cust || !nak || !address || cart.length === 0) {
    alert("Please fill all details and select products.");
    return;
  }
  const createdAt = new Date();
  const html = buildReceiptHTML({cust, nak, address, cart, createdAt});
  document.getElementById("bill-body").innerHTML = html;

  const billModal = new bootstrap.Modal(document.getElementById('billModal'));
  billModal.show();
}

function generateAndPrint() {
    const cust = document.getElementById("cust-name").value.trim();
    const nak  = document.getElementById("nakshathra").value.trim();
    const address = document.getElementById("address").value.trim();
    updateCartFromSelection()

    if (!cust || !nak || !address || cart.length === 0) {
        alert("Please fill all details and select products before printing.");
        return;
    }

    // Prepare form data
    const form = document.getElementById('billForm');
    const formData = new FormData(form);

    // Add selected poojas to FormData manually
    const poojaSelect = document.getElementById('poojaSelect');
    const selectedOptions = Array.from(poojaSelect.selectedOptions);
    selectedOptions.forEach(opt => {
        formData.append('poojas', opt.value);
    });

    // If payment checkbox is checked, add it
    formData.set('payment_status', document.getElementById('payment_status').checked ? 'on' : '');

    // Submit via AJAX
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}', // Ensure CSRF token is set
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Backend saved successfully, now generate bill HTML for print
            const createdAt = new Date(data.created_at); // you can return the bill timestamp from backend
            const html = buildReceiptHTML({cust, nak, address, cart, createdAt});

            const w = window.open('', '', 'width=900,height=650');
            w.document.write(`
                <html>
                    <head>
                        <title>Receipt</title>
                        <meta charset="utf-8">
                        <link rel="stylesheet" href="/static/css/festival_dashboard.css">
                    </head>
                    <body>${html}</body>
                </html>
            `);
            w.document.close();
            w.focus();
            w.print();
            w.close();

            cart = [];
            // Close the modal
            const addBillModalEl = document.getElementById('addBillModal');
            const addBillModal = bootstrap.Modal.getInstance(addBillModalEl);
            addBillModal.hide();

            // Optionally, reload the table or page to show the new bill
            location.reload();
        } else {
            alert(data.error || "Failed to save the bill.");
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error saving the bill.");
    });
}

$(document).on("click", ".toggle-payment", function () {
    const billId = $(this).data("id");
    const action = $(this).data("action"); // mark_paid / mark_unpaid
    const row = $(this).closest("tr");
    const amount = row.find("td:nth-child(4)").text().replace("₹", "").trim();

    // Fill modal hidden fields
    $("#billId").val(billId);
    $("#billAmount").val(amount);
    $("#billAction").val(action);
    $("#enteredAmount").val("");

    // Show modal
    $("#paymentConfirmModal").modal("show");
});

$("#paymentConfirmForm").on("submit", function (e) {
    e.preventDefault();

    const entered = parseFloat($("#enteredAmount").val());
    const correct = parseFloat($("#billAmount").val());
    const billId = $("#billId").val();
    const action = $("#billAction").val();

    if (entered !== correct) {
        alert("❌ Amount mismatch! Please try again.");
        return;
    }

    // ✅ Proceed with AJAX request (correct URL + data)
    $.ajax({
        url: `/bill/${billId}/toggle-payment/`,
        method: "POST",
        data: {
            action: action,
            csrfmiddlewaretoken: "{{ csrf_token }}"
        },
        success: function (response) {
            $("#paymentConfirmModal").modal("hide");

            // if you want to refresh only filtered table:
            if (typeof applyFilter === "function") {
                applyFilter();
            } else {
                location.reload();
            }
        },
        error: function () {
            alert("⚠️ Error updating payment status. Try again.");
        }
    });
});