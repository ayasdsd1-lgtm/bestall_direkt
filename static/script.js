
//-----------------------------------View.html-----------------------------------//
        //===========Prisöversikt och lägg till knapparna===========//
document.addEventListener('DOMContentLoaded', function() {
    let totalSumma = 0;
    let totalAntal = 0;
    const varukorg = {}; 

    const totalDisplay = document.getElementById('total-summa');
    const antalDisplay = document.getElementById('antal-produkter');
    const listaDisplay = document.getElementById('produkt-lista');

    const checkoutForm = document.getElementById('checkout-form');
    const orderDataInput = document.getElementById('order_data_input');
    const totalPrisInput = document.getElementById('total_pris_input');


    function laggTillVara(namn, pris, index) {
            totalSumma += pris;
            totalAntal += 1;

            if (varukorg[namn]) {
                varukorg[namn].antal += 1;
            } else {
                varukorg[namn] = {
                    antal: 1,
                    pris: pris,
                    index: index
                };
            }
            uppdateraAllt();  
    }


    function taBortVara(namn) {
        if (varukorg[namn]) {
            const prisPerEnhet = varukorg[namn].pris;

            totalSumma -= prisPerEnhet;
            totalAntal -= 1;
            varukorg[namn].antal -=1;

            if (totalSumma < 0) totalSumma = 0;
            if (totalAntal < 0) totalSumma = 0;

            if (varukorg[namn].antal <= 0) {
                const countSpan = document.getElementById(`count-${varukorg[namn].index}`);
                if(countSpan) countSpan.textContent = "0";
                delete varukorg[namn];
            }
            uppdateraAllt();
        }
    }

    // plus knappen för tjänstrkort//
    document.querySelectorAll(' .add-btn-stepper').forEach(button => {
        button.addEventListener('click', function() {
            const pris = parseFloat(this.getAttribute('data-pris'));
            const namn = this.getAttribute('data-namn');
            const index = this.getAttribute('data-index');
            laggTillVara(namn, pris, index);
        });
    });

    // minus knappen för tjänstekort//
    document.querySelectorAll('.remove-btn-small').forEach(button => {
        button.addEventListener('click', function() {
            const namn = this.getAttribute('data-namn');
            taBortVara(namn)
        });
    });


    function uppdateraAllt() {
        totalDisplay.textContent = totalSumma.toLocaleString('sv-SE');
        antalDisplay.textContent = totalAntal;

        document.querySelectorAll('.item-count').forEach(span => {
            span.textContent = "0";
            span.style.opacity = "0.5";
        });

        listaDisplay.innerHTML = "";

        for (const [namn, data] of Object.entries(varukorg)) {
            const countSpan = document.getElementById(`count-${data.index}`);
            if (countSpan) {
                countSpan.textContent = data.antal;
                countSpan.style.color = "#ffffff"; 
                countSpan.style.opacity = data.antal > 0 ? "1" : "0.5"
            }
            const li= document.createElement('li');
            li.style.display = "flex";
            li.style.justifyContent = "space-between";
            li.style.marginBottom = "10px";
            li.style.borderBottom = "1px solid #eee"
            li.style.paddingBottom= "5px";

            li.innerHTML = `
                <span>${namn} (${data.antal} st)</span>
                <button class="remove-btn-list" style="background: #8f512b; color:white; border:none; padding: 2px 8px; cursor:pointer;">Ta bort</button>
            `;

            li.querySelector('.remove-btn-list').addEventListener('click', () => taBortVara(namn));
            listaDisplay.appendChild(li);

        }
        //===========formuäret===========//
    }
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if(Object.keys(varukorg).length === 0) {
                alert("Din Varukorg är tom!");
                return;
            }

            let cartDataText= "";
            for (const [namn, data] of Object.entries(varukorg)) {
                cartDataText += `${namn} (${data.antal} st), `;
            }
            orderDataInput.value = cartDataText;
            totalPrisInput.value = totalSumma;

            const formData = new FormData(this);

            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then( response => response.json())
            .then(data => {

                if(data.success) {
                    document.getElementById('order-form-container').innerHTML = `
                        <div class="success-message">
                            <h4>Skickat!</h4>
                            <p>${data.message}</p>
                            <button onclick="location.reload()" class="submit-btn" style="width:100%">Gör en ny beställning</button>
                        </div>
                    `;
                } else {
                    alert("Ett fel uppstod")
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert("Kunde inte kontakta servern. ");
            });
        });
    }    

    // Visar fler kategorier när användaren klickar på "Visa alla kategorier"
    const visaFler = document.getElementById("visa-fler");
    const extraKategorier = document.querySelectorAll(".extra-kategori");

    if (visaFler) {
        visaFler.addEventListener("click", function() {
            extraKategorier.forEach(function(kategori) {
                kategori.style.display = "block";
            });

            visaFler.style.display = "none";
        });
    }
});




//-----------------------------------register.html-----------------------------------//
const registerForm = document.getElementById("register-form");

if (registerForm) {
    registerForm.addEventListener("submit", function(e) {
        let harFel = false;

        document.querySelectorAll(".klient-fel").forEach(el => el.remove());
        document.querySelectorAll(".fel-border").forEach(el => el.classList.remove("fel-border"));

        const namn = document.getElementById("namn");
        const personnummer = document.getElementById("personnummer");
        const email = document.getElementById("email");
        const tel = document.getElementById("tel");
        const losenord = document.getElementById("losenord");

        function visaFel(input, meddelande) {
            input.classList.add("fel-border");
            const span = document.createElement("span");
            span.className = "falt-fel klient-fel";
            span.textContent = meddelande;
            input.insertAdjacentElement("afterend", span);
            harFel = true;
        }

        if (!namn.value.trim() || namn.value.trim().length < 2)
            visaFel(namn, "Namn är obligatoriskt och måste vara minst 2 tecken.");

        if (!personnummer.value.trim() || !/^\d{8}-?\d{4}$/.test(personnummer.value.trim()))
            visaFel(personnummer, "Ange personnummer i format YYYYMMDD-XXXX.");

        if (!email.value.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim()))
            visaFel(email, "Ange en giltig e-postadress.");

        if (!tel.value.trim() || !/^(\+46|0)\d{9}$/.test(tel.value.replace(/[\s-]/g, "")))
            visaFel(tel, "Ange ett giltigt mobilnummer (t.ex. 0701234567).");

        if (!losenord.value || losenord.value.length < 8)
            visaFel(losenord, "Lösenordet måste vara minst 8 tecken.");

        if (harFel) e.preventDefault();
    });
}

