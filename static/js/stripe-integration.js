// Stripe integration JavaScript

let stripe;
let elements;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Stripe
    stripe = Stripe('YOUR_STRIPE_PUBLIC_KEY'); // Replace with your actual public key

    // Handle subscription button clicks
    const subscribeButtons = document.querySelectorAll('.subscribe-btn');
    subscribeButtons.forEach(button => {
        button.addEventListener('click', handleSubscription);
    });
});

async function handleSubscription(event) {
    const priceId = event.target.dataset.priceId;
    
    try {
        const response = await fetch('/create-checkout-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ priceId: priceId }),
        });

        const session = await response.json();
        
        const result = await stripe.redirectToCheckout({
            sessionId: session.sessionId,
        });

        if (result.error) {
            alert(result.error.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
}
