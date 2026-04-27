document.addEventListener('DOMContentLoaded', function() {
    //här hämtar vi alla priser på sidan
    const prisElement = document.querySelectorAll(' .pris-varde');
    const totalDisplay = document.getElementById('total-summa');

    let total = 0

    //går igenom alla priser och summerar
    prisElement.forEach(element => {
        const pris = parseFloat(element.textContent.replace(/\s/g, ''));

        if (!isNaN(pris)) {
            total += pris;
        }
    });

    //Här skrivs den totala summan ut
    totalDisplay,this.textContent = total.toLocaleString('sv-SE')
})