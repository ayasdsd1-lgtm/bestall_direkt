
//-----------------------------------View.html-----------------------------------//
        //===========Prisöversikt och lägg till knapparna===========//
document.addEventListener('DOMContentLoaded', function() {
    let totalAmount = 0;
    let totalItems = 0;
    const cart = {}; 

    const totalDisplay = document.getElementById('total-summa');
    const itemCountDisplay = document.getElementById('antal-produkter');
    const productListDisplay = document.getElementById('produkt-lista');

    const checkoutForm = document.getElementById('checkout-form');
    const orderDataInput = document.getElementById('order_data_input');
    const totalPriceInput = document.getElementById('total_pris_input');


    function addItem(name, price, index) {
            totalAmount += price;
            totalItems += 1;

            if (cart[name]) {
                cart[name].quantity += 1;
            } else {
                cart[name] = {
                    quantity: 1,
                    price: price,
                    index: index
                };
            }
            updateCart();  
    }


    function removeItem(name) {
        if (cart[name]) {
            const unitPrice = cart[name].price;

            totalAmount -= unitPrice;
            totalItems -= 1;
            cart[name].quantity -=1;

            if (totalAmount < 0) totalAmount = 0;
            if (totalItems < 0) totalAmount = 0;

            if (cart[name].quantity <= 0) {
                const countSpan = document.getElementById(`count-${cart[name].index}`);
                if(countSpan) countSpan.textContent = "0";
                delete cart[name];
            }
            updateCart();
        }
    }

    // plus knappen för tjänstrkort//
    document.querySelectorAll(' .add-btn-stepper').forEach(button => {
        button.addEventListener('click', function() {
            const price = parseFloat(this.getAttribute('data-pris'));
            const name = this.getAttribute('data-namn');
            const index = this.getAttribute('data-index');
            addItem(name, price, index);
        });
    });

    // minus knappen för tjänstekort//
    document.querySelectorAll('.remove-btn-small').forEach(button => {
        button.addEventListener('click', function() {
            const name = this.getAttribute('data-namn');
            removeItem(name)
        });
    });


    function updateCart() {
        totalDisplay.textContent = totalAmount.toLocaleString('sv-SE');
        itemCountDisplay.textContent = totalItems;

        document.querySelectorAll('.item-count').forEach(span => {
            span.textContent = "0";
            span.style.opacity = "0.5";
        });

        productListDisplay.innerHTML = "";

        for (const [name, data] of Object.entries(cart)) {
            const countSpan = document.getElementById(`count-${data.index}`);
            if (countSpan) {
                countSpan.textContent = data.quantity;
                countSpan.style.color = "#ffffff"; 
                countSpan.style.opacity = data.quantity > 0 ? "1" : "0.5"
            }
            const li= document.createElement('li');
            li.style.display = "flex";
            li.style.justifyContent = "space-between";
            li.style.marginBottom = "10px";
            li.style.borderBottom = "1px solid #eee"
            li.style.paddingBottom= "5px";

            li.innerHTML = `
                <span>${name} (${data.quantity} st)</span>
                <button class="remove-btn-list" style="background: #8f512b; color:white; border:none; padding: 2px 8px; cursor:pointer;">Ta bort</button>
            `;

            li.querySelector('.remove-btn-list').addEventListener('click', () => removeItem(name));
            productListDisplay.appendChild(li);

        }
        //===========formuäret===========//
    }
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if(Object.keys(cart).length === 0) {
                alert("Din Varukorg är tom!");
                return;
            }

            let cartDataText= "";
            for (const [name, data] of Object.entries(cart)) {
                cartDataText += `${name} (${data.quantity} st), `;
            }
            orderDataInput.value = cartDataText;
            totalPriceInput.value = totalAmount;

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
    const showMoreButton = document.getElementById("show-more");
    const extraCategories = document.querySelectorAll(".extra-category");

    if (showMoreButton) {
        showMoreButton.addEventListener("click", function() {
            extraCategories.forEach(function(category) {
                category.style.display = "block";
            });

            showMoreButton.style.display = "none";
        });
    }
});




//-----------------------------------register.html-----------------------------------//
const registerForm = document.getElementById("register-form");

if (registerForm) {
    registerForm.addEventListener("submit", function(e) {
        let hasError = false;

        document.querySelectorAll(".klient-fel").forEach(el => el.remove());
        document.querySelectorAll(".fel-border").forEach(el => el.classList.remove("fel-border"));

        const name = document.getElementById("name");
        const personnummer = document.getElementById("personnummer");
        const email = document.getElementById("email");
        const tel = document.getElementById("tel");
        const password = document.getElementById("password");

        function showError(input, message) {
            input.classList.add("fel-border");
            const span = document.createElement("span");
            span.className = "falt-fel klient-fel";
            span.textContent = message;
            input.insertAdjacentElement("afterend", span);
            hasError = true;
        }

        if (!name.value.trim() || name.value.trim().length < 2)
            showError(name, "Namn är obligatoriskt och måste vara minst 2 tecken.");

        if (!personnummer.value.trim() || !/^\d{8}-?\d{4}$/.test(personnummer.value.trim()))
            showError(personnummer, "Ange personnummer i format YYYYMMDD-XXXX.");

        if (!email.value.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim()))
            showError(email, "Ange en giltig e-postadress.");

        if (!tel.value.trim() || !/^(\+46|0)\d{9}$/.test(tel.value.replace(/[\s-]/g, "")))
            showError(tel, "Ange ett giltigt mobilnummer (t.ex. 0701234567).");

        if (!password.value || password.value.length < 8)
            showError(password, "Lösenordet måste vara minst 8 tecken.");

        if (hasError) e.preventDefault();
    });
}

