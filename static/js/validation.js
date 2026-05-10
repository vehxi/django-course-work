document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('register-form');
    
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Получаем поля
            const usernameInput = registerForm.querySelector('input[name="username"]');
            const emailInput = registerForm.querySelector('input[name="email"]');
            const passwordInput = registerForm.querySelector('input[name="password"]');
            const passwordConfirmInput = registerForm.querySelector('input[name="password_confirm"]');
            
            // Очистка старых ошибок
            document.querySelectorAll('.js-error').forEach(el => el.remove());
            
            // Функция показа ошибки
            function showError(input, message) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'js-error';
                errorDiv.style.color = '#ff4757';
                errorDiv.style.fontSize = '12px';
                errorDiv.style.marginTop = '4px';
                errorDiv.innerText = message;
                input.parentNode.insertBefore(errorDiv, input.nextSibling);
                isValid = false;
            }
            
            // Валидация Username
            if (usernameInput && usernameInput.value.trim().length < 3) {
                showError(usernameInput, 'Имя пользователя должно содержать не менее 3 символов');
            }
            
            // Валидация Email
            if (emailInput) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(emailInput.value)) {
                    showError(emailInput, 'Пожалуйста, введите корректный email адрес');
                }
            }
            
            // Валидация пароля
            if (passwordInput && passwordInput.value.length < 6) {
                showError(passwordInput, 'Пароль должен содержать не менее 6 символов');
            }
            
            // Совпадение паролей
            if (passwordInput && passwordConfirmInput && passwordInput.value !== passwordConfirmInput.value) {
                showError(passwordConfirmInput, 'Пароли не совпадают');
            }
            
            // Если есть ошибки, останавливаем отправку (клиентская валидация сработала)
            if (!isValid) {
                event.preventDefault();
                console.log('Client-side validation failed.');
            }
        });
    }
});
