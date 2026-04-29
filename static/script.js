
//-----------------------------------View.html-----------------------------------//
document.addEventListener('DOMContentLoaded', function() {
    let totalSumma = 0;
    let totalAntal = 0;
    const varukorg = {}; 

    const totalDisplay = document.getElementById('total-summa');
    const antalDisplay = document.getElementById('antal-produkter');
    const listaDisplay = document.getElementById('produkt-lista');

    function laggTillVara(namn, pris) {
            totalSumma += pris;
            totalAntal += 1;

            if (varukorg[namn]) {
                varukorg[namn].antal += 1;
            } else {
                varukorg[namn] = {
                    antal: 1,
                    pris: pris
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
                delete varukorg[namn];
            }
            uppdateraAllt();
        }
    }

    // plus knappen//
    document.querySelectorAll(' .add-btn').forEach(button => {
        button.addEventListener('click', function() {
            const pris = parseFloat(this.getAttribute('data-pris'));
            const namn = this.getAttribute('data-namn');
            laggTillVara(namn, pris);
        });
    });

    // minus knappen//
    document.querySelectorAll('.remove-btn-small').forEach(button => {
        button.addEventListener('click', function() {
            const namn = this.getAttribute('data-namn');
            taBortVara(namn)
        });
    });


    function uppdateraAllt() {
        totalDisplay.textContent = totalSumma.toLocaleString('sv-SE');
        antalDisplay.textContent = totalAntal;

        document.querySelectorAll('.item-count').forEach(span => span.textContent = "0");

        for (const [namn, data] of Object.entries(varukorg)) {
            const countSpan = document.getElementById(`count-${namn}`);
            if (countSpan) {
                countSpan.textContent = data.antal;
            }
        }

        listaDisplay.innerHTML = "";
        for (const [namn, data] of Object.entries(varukorg)) {
            const li= document.createElement('li');
            li.style.display = "flex";
            li.style.justifyContent = "space-between";
            li.style.marginBottom = "8px";

            li.innerHTML = `
            <span>${namn} (${data.antal} st)</span>
            <button class="remoce-btn-list" style="background:#8f512b; color:white, border:none; padding: 2px 8px; cursor:pointer;">Ta bort</button>
            `;

            li.querySelector('.remove-btn-list').addEventListener('click', () => taBortVara(namn));
            listaDisplay.appendChild(li);
        }
    }
});







//---------------------------------------Annat??--------------------------------------//


