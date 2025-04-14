function checkBalance() {
    const lender = document.querySelector("#id_lender")?.value;
    const apartment = document.querySelector("#id_apartment")?.value;
    const start = document.querySelector("#id_start_date")?.value;
    const end = document.querySelector("#id_end_date")?.value;

    console.log("🔁 Prüfe Guthaben ...", lender, apartment, start, end);  // NEU!

    const warningDiv = document.querySelector("#saldo-warning");
    if (!lender || !apartment || !start || !end) {
        warningDiv.innerHTML = "";
        return;
    }

    fetch("/lenders/check_balance/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: new URLSearchParams({ lender, apartment, start_date: start, end_date: end }),
    })
        .then((response) => response.json())
        .then((data) => {
            console.log("📥 Antwort vom Server:", data);  // NEU!

            if (!warningDiv) return;
            if (data.status === "warning") {
                warningDiv.innerHTML = `
                    <div style="border:2px solid red; background:#ffe5e5; color:black; padding:10px;">
                        ⚠️ Guthaben zu gering: <strong>${data.saldo} €</strong><br>
                        Buchungskosten: <strong>${data.kosten} €</strong>
                    </div>`;
            } else {
                warningDiv.innerHTML = "";
            }
        });
}

document.addEventListener("DOMContentLoaded", () => {
    const fields = ["#id_lender", "#id_apartment", "#id_start_date", "#id_end_date"];

    let lastValues = {};

    function monitorFields() {
        let changed = false;

        fields.forEach((selector) => {
            const el = document.querySelector(selector);
            if (el) {
                const currentValue = el.value;
                if (lastValues[selector] !== currentValue) {
                    lastValues[selector] = currentValue;
                    changed = true;
                }
            }
        });

        if (changed) {
            checkBalance();
        }
    }

    setInterval(monitorFields, 1000);  // alle 1 Sekunde prüfen
});
