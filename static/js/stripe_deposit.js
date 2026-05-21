// Stripe Elements initialization
const stripe = Stripe(STRIPE_PUBLIC_KEY);
const elements = stripe.elements({
    appearance: {
        theme: 'night',
        variables: {
            colorPrimary: '#6c63ff',
            colorBackground: '#13161f',
            colorText: '#e8e9f0',
            colorDanger: '#ef4444',
            fontFamily: 'Manrope, sans-serif',
            borderRadius: '8px',
        }
    }
});

const cardElement = elements.create('card', {
    style: {
        base: {
            fontSize: '15px',
            color: '#e8e9f0',
            '::placeholder': { color: '#7b7f96' }
        }
    }
});
cardElement.mount('#stripe-card-element');

// Show card errors
cardElement.on('change', ({ error }) => {
    document.getElementById('card-errors').textContent = error ? error.message : '';
});

// Quick amount preset buttons
const presets = document.querySelectorAll('.preset-btn');
const amountInput = document.getElementById('amount-input');

presets.forEach(btn => {
    btn.addEventListener('click', () => {
        presets.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        amountInput.value = btn.dataset.amount;
    });
});

amountInput.addEventListener('input', () => {
    presets.forEach(b => b.classList.remove('active'));
});

// Submit payment
document.getElementById('submit-btn').addEventListener('click', async () => {
    const amount = parseFloat(amountInput.value);

    if (!amount || amount < 1) {
        document.getElementById('card-errors').textContent = 'Please enter an amount (minimum 1)';
        return;
    }

    setLoading(true);

    try {
        // 1. Get client_secret from server
        const res = await fetch(CREATE_INTENT_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify({ amount })
        });

        const data = await res.json();

        if (data.error) {
            document.getElementById('card-errors').textContent = data.error;
            setLoading(false);
            return;
        }

        // 2. Confirm payment via Stripe
        const { error, paymentIntent } = await stripe.confirmCardPayment(data.client_secret, {
            payment_method: { card: cardElement }
        });

        if (error) {
            document.getElementById('card-errors').textContent = error.message;
            setLoading(false);
        } else if (paymentIntent.status === 'succeeded') {
            // 3. Redirect to success page
            window.location.href = `${SUCCESS_URL}?payment_intent=${paymentIntent.id}`;
        }

    } catch (err) {
        document.getElementById('card-errors').textContent = 'Network error. Please try again.';
        setLoading(false);
    }
});

function setLoading(isLoading) {
    const btn = document.getElementById('submit-btn');
    btn.disabled = isLoading;
    document.getElementById('spinner').style.display = isLoading ? 'block' : 'none';
    document.getElementById('btn-text').textContent = isLoading ? 'Processing...' : 'Top Up Wallet';
}
