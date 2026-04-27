document.addEventListener('DOMContentLoaded', function() {
    let total = 0;
    const buttons = document.querySelectorAll(' .add-btn');
    const totalDisplay = document.getElementById('total-summa');


    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const pris = parseFloat(this.getAttribute('data-pris'));
            const namn = this.getAttribute('.data-namn');
            total += pris;
            totalDisplay.textContent = total.toLocaleString('sv-SE');
            console.log(`${namn} lades till för ${pris}kr`);
            this.style.backgroundColor = "#4CAF50";
            this.textContent = "Tillagd!";
            setTimeout (() => {
                this.style.backgroundColor = "";
                this.textContent = "Lägg till";
            }, 1000);
        })
    });
})