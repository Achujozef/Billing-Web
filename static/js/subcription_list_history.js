document.addEventListener("DOMContentLoaded", function(){
  const config = document.getElementById("config");
  let csrf = config.dataset.csrf;
  const historyModalHtml = `
    <div class="modal fade" id="historyModal" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content bg-white text-dark">
          <div class="modal-header border-bottom">
            <h5 class="modal-title">📜 Subscription Cycle History</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" style="max-height:500px; overflow-y:auto;">
            <div id="cycleCards" class="d-flex flex-column gap-3"></div>
          </div>
          <div class="modal-footer border-top">
            <button class="btn btn-dark" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>`;
  
  document.body.insertAdjacentHTML('beforeend', historyModalHtml);
  const historyModalEl = document.getElementById("historyModal");
  const historyModal = new bootstrap.Modal(historyModalEl);
  const cycleCardsEl = document.getElementById("cycleCards");

  document.querySelectorAll(".historySubBtn").forEach(btn=>{
    btn.addEventListener("click", async ()=>{
      const subId = btn.dataset.id;
      const res = await fetch(`/subscription/${subId}/history/`);
      const data = await res.json();
      if(!data.success) return alert("Failed to fetch history");

      cycleCardsEl.innerHTML = "";

      // Enable cycles based on backend data
      let enableNext = true;
      data.cycles.forEach((cycle, idx)=>{
        const card = document.createElement("div");
        card.className = "card p-2 bg-white text-dark border";
        card.style.cursor = "pointer";

        if(!cycle.done && !enableNext) card.classList.add("disabled-cycle");
            card.innerHTML = `
              <strong>Cycle ${cycle.cycle_number}</strong>
              <span class="text-success">
                ${cycle.done ? "✔️ Done at " + formatDateTime(cycle.done_at) : "Pending"}
              </span>
            `;


        card.addEventListener("click", ()=>{
          if(card.classList.contains("disabled-cycle")) return;
          showCyclePoojas(card, subId, cycle.cycle_number, data.poojas, cycle.poojas_done);
        });

        cycleCardsEl.appendChild(card);
        enableNext = cycle.done;
      });

      historyModal.show();
    });
  });

  function showCyclePoojas(cardEl, subId, cycleNumber, poojas, donePoojas){
    cycleCardsEl.querySelectorAll(".cycle-poojas")?.forEach(el=>el.remove());

    const poojaList = poojas.map(p=>{
      const checked = donePoojas.includes(p.id) ? "checked" : "";
      return `<div class="form-check mb-1">
                <input class="form-check-input pooja-cycle-checkbox" type="checkbox" value="${p.id}" ${checked} id="poojaCycle${p.id}">
                <label class="form-check-label" for="poojaCycle${p.id}">${p.pooja_name}</label>
              </div>`;
    }).join('');

    const content = `
      <div id="cyclePoojaContainer">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h6>Cycle ${cycleNumber} Poojas</h6>
          <button class="btn btn-sm btn-outline-dark" id="closePoojaList" title="Close">&times;</button>
        </div>
        <div class="mb-2">
          <button class="btn btn-sm btn-outline-dark" id="checkAllPoojas">Check All</button>
        </div>
        <div>${poojaList}</div>
        <button class="btn btn-dark mt-3" id="markDoneBtn">Done</button>
      </div>
    `;

    const div = document.createElement("div");
    div.className = "cycle-poojas mt-2 p-2 border rounded bg-white text-dark";
    div.innerHTML = content;

    cardEl.insertAdjacentElement('afterend', div);

    div.querySelector("#checkAllPoojas").addEventListener("click", ()=>{
      div.querySelectorAll(".pooja-cycle-checkbox").forEach(cb=>cb.checked=true);
    });

    div.querySelector("#markDoneBtn").addEventListener("click", async ()=>{
      const selectedPoojas = Array.from(div.querySelectorAll(".pooja-cycle-checkbox:checked")).map(cb=>parseInt(cb.value));
      const resp = await fetch("/subscription/mark_cycle_done/", {
        method:"POST",
        headers: {"Content-Type":"application/json","X-CSRFToken":csrf},
        body: JSON.stringify({subscription_id: subId, cycle_number: cycleNumber, pooja_ids: selectedPoojas})
      });
      const result = await resp.json();
      if(result.success){
        alert(result.message);
        document.querySelector(`.historySubBtn[data-id="${subId}"]`).click();
      } else {
        alert(result.error || "Failed to mark done");
      }
    });

    // Close button
    div.querySelector("#closePoojaList").addEventListener("click", ()=>{ div.remove(); });
  }
});

function formatDateTime(dateString) {
  if (!dateString) return "";
  const d = new Date(dateString);

  const day = d.getDate().toString().padStart(2, "0");
  const month = d.toLocaleString("en-US", { month: "long" });
  const year = d.getFullYear();

  let hours = d.getHours();
  const minutes = d.getMinutes().toString().padStart(2, "0");
  const ampm = hours >= 12 ? "pm" : "am";
  hours = hours % 12 || 12;

  return `${day} - ${month} - ${year} (${hours}:${minutes} ${ampm})`;
}
