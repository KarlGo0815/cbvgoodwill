function checkBalance() {
    const lender = document.querySelector("#id_lender")?.value;
    const apartment = document.querySelector("#id_apartment")?.value;
    const start = document.querySelector("#id_start_date")?.value;
    const end = document.querySelector("#id_end_date")?.value;

    console.log("🔁 Prüfe Buchungsbedingungen ...", lender, apartment, start, end);

    const warningDiv = document.querySelector("#saldo-warning");
    if (!warningDiv) {
        console.warn("⚠️ Kein #saldo-warning Element gefunden!");
        return;
    }

    if (!lender || !apartment || !start || !end) {
        warningDiv.innerHTML = "";
        return;
    }

    fetch("/lenders/check_booking_warnings/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]')?.value || "",
        },
        body: new URLSearchParams({
            lender,
            apartment,
            start_date: start,
            end_date: end
        }),
    })
    .then((res) => res.json())
    .then((data) => {
        console.log("📥 Antwort vom Server:", data);

        if (data.status === "ok" && Array.isArray(data.warnings) && data.warnings.length > 0) {
            const html = data.warnings.map(w => `<p style="margin: 0 0 5px;">${w}</p>`).join("");
            warningDiv.innerHTML = `
                <div style="border: 2px solid red; background-color: #ffe5e5; color: black; padding: 10px; margin-bottom: 10px;">
                    ${html}
                </div>`;
        } else {
            warningDiv.innerHTML = "";
        }
    })
    .catch((err) => {
        console.error("❌ Fehler bei der Guthabenprüfung:", err);
        warningDiv.innerHTML = `
            <div style="border: 2px solid orange; background-color: #fff3cd; color: black; padding: 10px;">
                ⚠️ Fehler beim Abrufen der Buchungswarnungen.
            </div>`;
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
                const val = el.value;
                if (lastValues[selector] !== val) {
                    lastValues[selector] = val;
                    changed = true;
                }
            }
        });

        if (changed) {
            checkBalance();
        }
    }

    setInterval(monitorFields, 1000);
});
