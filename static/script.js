

document.addEventListener('DOMContentLoaded', function() {
    let totalSumma = 0;
    let totalAntal = 0;
    const varukorg = {}; 

    const buttons = document.querySelectorAll(' .add-btn');
    const totalDisplay = document.getElementById('total-summa')
    const antalDisplay = document.getElementById('antal-produkter')
    const listaDisplay = document.getElementById('produkt-lista')


    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const pris = parseFloat(this.getAttribute('data-pris'));
            const namn = this.getAttribute('data-namn');

            totalSumma += pris;
            totalAntal += 1;

            if (varukorg[namn]) {
                varukorg[namn] += 1;
            } else {
                varukorg[namn] = {
                    antal: 1,
                    pris: pris
                };
            }

            uppdateraPrisoversikt();
            this.style.backgroundColor = "#4CAF50";
            this.textContent = "Tillagd!";
            setTimeout (() => {
                this.style.backgroundColor = "";
                this.textContent = "Lägg till";
            }, 800);
        });
    });

    function taBortVara(namn) {
        if (varukorg[namn]) {
            const prisPerEnhet = varukorg[namn].pris;

            totalSumma -= prisPerEnhet;
            totalAntal -= 1;
            varukorg[namn].antal -=1;

            if (varukorg[namn].antal <= 0) {
                delete varukorg[namn];
            }
            uppdateraPrisoversikt();
        }
    }



    function uppdateraPrisoversikt() {
        totalDisplay.textContent = totalSumma.toLocaleString('sv-SE');
        antalDisplay.textContent = totalAntal

        listaDisplay.innerHTML = "";
        for (const [namn, data] of Object.entries(varukorg)) {
            const li = document.createElement('li');
            li.style.display = "flex";
            li.style.justifyContent = "space-between";
            li.style.alignItems = "center"
            li.style.marginBotoom = "8px";

            li.innerHTML = `
                <span>${namn} (${data.antal} st) </span>
                <button class="remove-btn" style="background: #ff4d4d; color: white; border: none; border-radius: 4px; padding: 2px 8px; cusor: pointer;">
                Ta bort
                </button>                
                `;
                li.querySelector(' .remove-btn').addEventListener('click', () => {
                    taBortVara(namn);
                }); 
                
            listaDisplay.appendChild(li);
        }
    }
});
