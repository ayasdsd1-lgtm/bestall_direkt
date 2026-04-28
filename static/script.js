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
            const namn = this.getAttribute('.data-namn');

            totalSumma += pris;
            totalAntal += 1;

            if (varukorg[namn]) {
                varukorg[namn] += 1;
            } else {
                varukorg[namn] = 1;
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


    function uppdateraPrisoversikt() {
        totalDisplay.textContent = totalSumma.toLocaleString('sv-SE');
        antalDisplay.textContent = totalAntal

        listaDisplay.innerHTML = "";
        for (const [namn, anyal] of Object.entries(varukorg)) {
            const li = document.createAttribute('li');
            li.style.display = "flex";
            li.style.justifyContent = "space-between";
            li.style.marginBotoom = "5px";

            li.innerHTML = `<span>${namn}</span> <span>${antal} st<span>`;
            listaDisplay.appendChild(li);
        }
    }
});
