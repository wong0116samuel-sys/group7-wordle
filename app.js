const usernameInput = document.querySelector("#register-username");
const usernameStatus = document.querySelector("#username-status");

if (usernameInput && usernameStatus) {
    let timer = null;

    usernameInput.addEventListener("input", () => {
        clearTimeout(timer);
        const username = usernameInput.value.trim();

        if (username.length < 2) {
            usernameStatus.textContent = "至少 2 個字";
            usernameStatus.dataset.state = "invalid";
            return;
        }

        timer = setTimeout(async () => {
            const response = await fetch(`/api/check-username?username=${encodeURIComponent(username)}`);
            const payload = await response.json();
            usernameStatus.textContent = payload.message;
            usernameStatus.dataset.state = payload.available ? "valid" : "invalid";
        }, 250);
    });
}

const guessInput = document.querySelector("#guess-input");
const guessForm = document.querySelector(".guess-form");
const keyboard = document.querySelector(".keyboard");

if (guessInput && guessForm && keyboard) {
    keyboard.addEventListener("click", (event) => {
        const key = event.target.closest(".key");
        if (!key) {
            return;
        }

        const action = key.dataset.action;
        if (action === "backspace") {
            guessInput.value = guessInput.value.slice(0, -1);
            guessInput.focus();
            return;
        }

        if (action === "enter") {
            if (guessInput.reportValidity()) {
                guessForm.requestSubmit();
            }
            return;
        }

        const letter = key.dataset.key;
        if (letter && guessInput.value.length < Number(guessInput.maxLength)) {
            guessInput.value += letter.toLowerCase();
            guessInput.focus();
        }
    });
}
