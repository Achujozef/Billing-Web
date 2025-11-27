function confirmPassword() {
  return new Promise((resolve) => {
    const entered = prompt("Enter admin password to continue:");
    if (entered === "admin@123") {
      resolve(true);  
    } else {
      alert("❌ Invalid password");
      resolve(false);
    }
  });
}

let poojaModal;

document.addEventListener("DOMContentLoaded", function() {
  poojaModal = new bootstrap.Modal(document.getElementById("poojaModal"));
});

function openPoojaModal() {
  document.getElementById("poojaModalLabel").innerText = "Add Pooja";
  document.getElementById("pooja-id").value = "";
  document.getElementById("pooja-name").value = "";
  document.getElementById("pooja-price").value = "";
  poojaModal.show();
}

function editPooja(id, name, price) {
  document.getElementById("poojaModalLabel").innerText = "Edit Pooja";
  document.getElementById("pooja-id").value = id;
  document.getElementById("pooja-name").value = name;
  document.getElementById("pooja-price").value = price;
  poojaModal.show();
}

async function savePooja() {
  if (!(await confirmPassword())) return;

  let id = document.getElementById("pooja-id").value;
  let name = document.getElementById("pooja-name").value.trim();
  let price = parseFloat(document.getElementById("pooja-price").value);
  if (!name || isNaN(price)) {
    alert("Please fill all fields correctly");
    return;
  }

  fetch("/poojas/save/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": "{{ csrf_token }}"
    },
    body: JSON.stringify({ id, pooja_name: name, price })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        location.reload();
      } else {
        alert("Error: " + data.error);
      }
    })
    .catch(err => alert("AJAX Error: " + err));
}

async function deletePooja(id){
  if(!confirm("Are you sure you want to delete this pooja?")) return;
  if (!(await confirmPassword())) return;
  fetch(`/poojas/delete/${id}/`, {method: "POST", headers: {"X-CSRFToken": "{{ csrf_token }}"}})
    .then(res => res.json())
    .then(data => {
      if(data.success) location.reload();
      else alert("Error: " + data.error);
    });
}