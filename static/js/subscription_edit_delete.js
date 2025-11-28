document.addEventListener("DOMContentLoaded", function(){
    let subModal = new bootstrap.Modal(document.getElementById("subModal"));
    let billModal = new bootstrap.Modal(document.getElementById("billModal"));
    let deleteModal = new bootstrap.Modal(document.getElementById("deleteModal"));
    let saveBtn = document.getElementById("saveSubBtn");
    const config = document.getElementById("config");
    let subscriptions = JSON.parse(config.dataset.subscriptions);
    let poojas = JSON.parse(config.dataset.poojas);
    let csrf = config.dataset.csrf;
    let currentDeleteId = null;
    let currentBillData = null; // keep the bill data for printing

    // Filter handlers
    document.getElementById("nakshathra-filter").addEventListener("change", applyFilters);
    document.getElementById("status-filter").addEventListener("change", applyFilters);

    function applyFilters() {
        const nakshathra = document.getElementById("nakshathra-filter").value;
        const status = document.getElementById("status-filter").value;
        
        let query = "";
        const params = [];
        if (nakshathra) params.push("nakshathra=" + encodeURIComponent(nakshathra));
        if (status) params.push("status=" + encodeURIComponent(status));
        if (params.length) query = "?" + params.join("&");
        
        window.location.href = "/subscriptions/" + query;
    }

    window.clearFilters = function() {
        window.location.href = "/subscriptions/";
    }

    // Calculate total pooja amount
    function updateTotalPoojaAmount() {
        let total = 0;
        document.querySelectorAll(".pooja-checkbox:checked").forEach(cb => {
            total += parseFloat(cb.dataset.price || 0);
        });
        document.getElementById("totalPoojaAmount").textContent = total.toFixed(0);
    }

    document.querySelectorAll(".pooja-checkbox").forEach(cb => {
        cb.addEventListener("change", updateTotalPoojaAmount);
    });

    // Toggle subscription status
    document.querySelectorAll(".toggleStatus").forEach(switchBtn=>{
      switchBtn.addEventListener("change", ()=>{
        let id = switchBtn.dataset.id;
        fetch("/subscriptions/toggle/", {
          method:"POST",
          headers: {"Content-Type":"application/json","X-CSRFToken": csrf },
          body: JSON.stringify({id})
        }).then(res=>res.json()).then(data=>{
          if(data.success){
            switchBtn.nextElementSibling.innerText = data.status;
          } else {
            alert(data.error);
            switchBtn.checked = !switchBtn.checked;
          }
        });
      });
    });

    // Open Add Modal
    document.getElementById("addSubBtn").addEventListener("click", function(){
      document.getElementById("subModalLabel").innerText = "Add Subscription";
      resetForm();
      saveBtn.onclick = ()=>saveSub();
      subModal.show();
    });

    // View subscription bill
    document.querySelectorAll(".viewSubBtn").forEach(btn=>{
        btn.addEventListener("click", ()=>{
            let id = parseInt(btn.dataset.id);
            showBill(id, false);
        });
    });

    // Edit subscription
    document.querySelectorAll(".editSubBtn").forEach(btn=>{
      btn.addEventListener("click", ()=>{
        let id = parseInt(btn.dataset.id);
        console.log(id)
        let sub = subscriptions.find(s=>s.id===id);
        if(!sub) return;

        document.getElementById("subModalLabel").innerText = "Edit Subscription";
        resetForm();

        document.querySelector("[name='customer_name']").value = sub.customer.name;
        document.querySelector("[name='customer_phone']").value = sub.customer.phone_number;
        document.querySelector("[name='nakshathra']").value = sub.nakshathra;
        document.querySelector("[name='start_date']").value = sub.start_date;
        document.querySelector("[name='end_date']").value = sub.end_date;
        document.querySelectorAll("[name='poojas']").forEach(cb=>{
          cb.checked = sub.poojas.includes(parseInt(cb.value));
        });
        updateTotalPoojaAmount();

        saveBtn.onclick = ()=>saveSub(id);
        subModal.show();
      });
    });

    // Delete subscription
    document.querySelectorAll(".deleteSubBtn").forEach(btn=>{
        btn.addEventListener("click", ()=>{
            currentDeleteId = parseInt(btn.dataset.id);
            deleteModal.show();
        });
    });

    document.getElementById("confirmDeleteBtn").addEventListener("click", ()=>{
        if(currentDeleteId) {
            fetch("/subscriptions/delete/", {
                method:"POST",
                headers: {"Content-Type":"application/json","X-CSRFToken": csrf},
                body: JSON.stringify({id: currentDeleteId})
            }).then(res=>res.json()).then(data=>{
                if(data.success) {
                    location.reload();
                } else {
                    alert(data.error);
                }
                deleteModal.hide();
                currentDeleteId = null;
            });
        }
    });

    // Show bill in modal (preview)
    window.showBill = function(id, isNewSubscription = false) {
        const sub = subscriptions.find(s => s.id === id);
        if (!sub) return;

        const selectedPoojas = poojas.filter(p => sub.poojas.includes(p.id));
        const totalPoojaAmount = selectedPoojas.reduce((sum, p) => sum + parseFloat(p.price), 0);
        const totalDays = sub.total_days;
        const cycles = Math.ceil(totalDays / 28);
        const totalBillAmount = totalPoojaAmount * cycles;

        currentBillData = { sub, selectedPoojas, totalPoojaAmount, cycles, totalBillAmount, totalDays };

        // Preview inside modal
        const billContent = `
            <div class="bill-header text-center">
                <h4 class="mb-1">🕉️ Temple Subscription Bill</h4>
                <p class="text-muted mb-0">Sacred Pooja Services</p>
            </div>
            <hr>
            <div>
                <strong>പേര്:</strong> ${sub.customer.name}<br>
                <strong>നക്ഷത്രം:</strong> ${sub.nakshathra}<br>
                <strong>തീയതി:</strong> ${new Date().toLocaleDateString()}
            </div>
            <table class="table table-sm mt-3">
                <thead>
                    <tr>
                        <th>വഴിപാടു</th>
                        <th>അളവ് (Cycles)</th>
                        <th>തുക</th>
                    </tr>
                </thead>
                <tbody>
                    ${selectedPoojas.map(p => `
                        <tr>
                            <td>${p.pooja_name}</td>
                            <td>${cycles}</td>
                            <td>₹${(parseFloat(p.price) * cycles).toFixed(0)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div class="text-end fw-bold">ആകെ തുക : ₹${totalBillAmount.toFixed(0)}</div>
        `;

        document.getElementById("billContent").innerHTML = billContent;
        billModal.show();
    };

    // Proper print bill
    window.printBill = function() {
        if (!currentBillData) {
            alert("No bill to print!");
            return;
        }
        const { sub, selectedPoojas, cycles, totalBillAmount } = currentBillData;

        const billHtml = `
        <div class="print-bill-container">
          <!-- Header -->
          <div class="bill-header-print">
            <img src="/static/logo.png" alt="Ganapathi"><br>
            <span>തഴുതല ശ്രീ മഹാഗണപതി ക്ഷേത്രം</span><br>
            <span>Thazhuthala, Phone: 9496363989</span><br>
            <span>web: www.thazhuthalasreemahaganapathi.com</span><br>
            <span>e-mail: thazhuthalaganapathy@gmail.com</span>
          </div>
          <hr>
          <!-- Customer Info -->
          <div class="bill-info">
            <div>പേര് : <strong>${sub.customer.name}</strong></div>
            <div>നക്ഷത്രം : <strong>${sub.nakshathra}</strong></div>
            <div>തീയതി : <strong>${new Date().toLocaleDateString()}</strong></div>
          </div>
          <!-- Items Table -->
          <table class="bill-items-table">
            <thead>
              <tr>
                <th>വഴിപാടു</th>
                <th>അളവ്</th>
                <th>തുക</th>
              </tr>
            </thead>
            <tbody>
              ${selectedPoojas.map(p => `
                <tr>
                  <td>${p.pooja_name}</td>
                  <td>${cycles}</td>
                  <td>₹${(parseFloat(p.price) * cycles).toFixed(0)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          <!-- Total -->
          <div class="bill-total-print">
            ആകെ തുക : ₹${totalBillAmount.toFixed(0)}
          </div>
          <!-- Secretary -->
          <div class="bill-signature">
            <span>സെക്രട്ടറി</span>
          </div>
        </div>
        `;

        const printWindow = window.open('', '', 'width=800,height=600');
        printWindow.document.write(`
          <html>
            <head>
              <title>Subscription Bill</title>
              <style>
                @page { size: 15.5cm auto; margin: 0.5cm; }
                body { font-family: 'Noto Sans Malayalam', sans-serif; font-size:12px; }
                table { border-collapse: collapse; width:100%; }
                table, th, td { border:1px solid black; }
                th, td { padding:3px; text-align:center; }
              </style>
            </head>
            <body>${billHtml}</body>
          </html>
        `);
        printWindow.document.close();
        printWindow.print();
        printWindow.close();
    };

    // Save subscription with bill display
    window.saveSub = function(id=null){
      let form = document.getElementById("subForm");
      let data = Object.fromEntries(new FormData(form).entries());
      data.poojas = Array.from(form.querySelectorAll("[name='poojas']:checked")).map(cb=>parseInt(cb.value));
      if(id) data.id = id;

      fetch("/subscriptions/save/", {
        method:"POST",
        headers: {"Content-Type":"application/json","X-CSRFToken": csrf},
        body: JSON.stringify(data)
      }).then(r=>r.json()).then(d=>{
        if(d.success) {
            subModal.hide();
            location.reload(); // reload to refresh subscriptions
        } else {
            alert(d.error);
        }
      });
    }

    function resetForm(){
      document.getElementById("subForm").reset();
      document.querySelectorAll("[name='poojas']").forEach(cb=>cb.checked=false);
      updateTotalPoojaAmount();
    }
});