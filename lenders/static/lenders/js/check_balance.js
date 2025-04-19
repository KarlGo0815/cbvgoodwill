function checkBookingWarnings() {
    const lender = document.querySelector("#id_lender")?.value;
    const apartment = document.querySelector("#id_apartment")?.value;
    const start = document.querySelector("#id_start_date")?.value;
    const end = document.querySelector("#id_end_date")?.value;

    const warningDiv = document.querySelector("#saldo-warning");

    if (!lender || !apartment || !start || !end) {
        if (warningDiv) warningDiv.innerHTML = "";
        return;
    }

    console.log("🔁 Sende Anfrage an /lenders/check_booking_warnings/ ...");

    fetch("/lenders/check_booking_warnings/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: new URLSearchParams({
            lender,
            apartment,
            start_date: start,
            end_date: end,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            console.log("📥 Antwort vom Server:", data);

            if (!warningDiv) return;

            if (data.status === "ok" && data.warnings.length > 0) {
                let html = `
                    <div style="border:2px solid red; background:#ffe5e5; color:black; padding:10px;">`;
                data.warnings.forEach((warn) => {
                    html += `<p style="margin:5px 0;">${warn}</p>`;
                });
                html += `</div>`;
                warningDiv.innerHTML = html;
            } else {
                warningDiv.innerHTML = "";
            }
        })
        .catch((err) => {
            console.error("❌ Fehler bei der Anfrage:", err);
            if (warningDiv) {
                warningDiv.innerHTML = "<div style='color:red;'>⚠️ Fehler bei der Prüfung</div>";
            }
        });
}

// Überwache Felder für Änderungen
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
            checkBookingWarnings();
        }
    }

    setInterval(monitorFields, 1000);
});
