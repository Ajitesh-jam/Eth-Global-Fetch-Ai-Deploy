import razorpay
import os
import uuid
import logging
import time
import json
from dotenv import load_dotenv
load_dotenv()
import webbrowser
# --- Setup Logging ---
# Sets up a logger to provide clear, timestamped output about the script's operations.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RazorpayGateway:
    """
    A class to handle Razorpay payment initiation and status confirmation.
    """
    def __init__(self):
        """
        Initializes the Razorpay client using credentials from environment variables.
        """
        self.client = self._initialize_client()

    def _initialize_client(self):
        """
        Safely retrieves credentials and sets u22p the Razorpay client.
        Returns:
            razorpay.Client object or None if initialization fails.
        """
        key_id = os.getenv("RAZORPAY_KEY_ID")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        if not key_id or not key_secret:
            logging.error("Razorpay credentials (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET) are not set in environment variables.")
            return None

        try:
            client = razorpay.Client(auth=(key_id, key_secret))
            logging.info("Razorpay client initialized successfully.")
            return client
        except Exception as e:
            logging.error(f"Failed to initialize Razorpay client: {e}")
            return None

    def initiate_payment(self, amount_inr: float, description: str = "Payment Request") -> dict:
        """
        Creates a new Razorpay payment link and returns its details.

        Args:
            amount_inr (float): The amount to be charged in Indian Rupees (e.g., 10.50).
            description (str): A brief description for the payment.

        Returns:
            dict: A dictionary containing the status and, on success, the
                  'payment_url' and 'payment_link_id'.
        """
        if not self.client:
            return {'status': 'error', 'message': 'Razorpay client not initialized.'}

        if not isinstance(amount_inr, (int, float)) or amount_inr <= 0:
            return {'status': 'error', 'message': 'Invalid amount. Must be a positive number.'}

        # Razorpay API requires the amount in the smallest currency unit (paise for INR)
        amount_in_paise = int(amount_inr * 100)

        try:
            payment_link_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "accept_partial": False,
                "description": description,
                # A unique reference ID for your records
                "reference_id": f"agent_{uuid.uuid4().hex[:10]}"
            }
            logging.info(f"Creating payment link for INR {amount_inr:.2f}")
            link = self.client.payment_link.create(payment_link_data)

            return {
                'status': 'success',
                'message': 'Payment link created successfully.',
                'payment_url': link['short_url'],
                'payment_link_id': link['id']
            }

        except Exception as e:
            logging.error(f"Razorpay API Error during link creation: {e}")
            return {'status': 'error', 'message': str(e)}

    def is_payment_confirmed(self, payment_link_id: str) -> dict:
        """
        Checks the status of a specific payment link.

        Args:
            payment_link_id (str): The ID of the payment link to check.

        Returns:
            dict: A dictionary containing the payment status. Possible statuses include
                  'paid', 'pending', 'expired', or 'error'.
        """
        if not self.client:
            return {'status': 'error', 'message': 'Razorpay client not initialized.'}

        try:
            logging.info(f"Fetching status for payment link: {payment_link_id}")
            link_status = self.client.payment_link.fetch(payment_link_id)

            if link_status['status'] == 'paid':
                # Attempt to get the specific payment ID from the list of payments
                payment_id = None
                if link_status.get('payments'):
                    payment_id = link_status['payments'][0].get('payment_id')

                logging.info(f"Payment successful! Status: 'paid'. Payment ID: {payment_id}")
                return {
                    'status': 'paid',
                    'message': 'Payment confirmed successfully.',
                    'payment_id': payment_id,
                    'amount_paid': link_status['amount_paid'] / 100
                }
            elif link_status['status'] == 'expired':
                logging.warning("Payment link has expired.")
                return {'status': 'expired', 'message': 'Payment link expired.'}
            else:
                # For any other status ('created', etc.), we consider it pending.
                logging.info(f"Payment is pending. Current status: '{link_status['status']}'")
                return {'status': 'pending', 'message': f"Payment is not yet complete. Current status: {link_status['status']}"}

        except Exception as e:
            logging.error(f"Razorpay API Error during status check: {e}")
            return {'status': 'error', 'message': str(e)}
        
        

def pay_inr(from_currency: str, to_currency: str, from_address: str, to_address: str, amount: float) -> str:
    """
    Initiates a payment for a transaction, waits for confirmation, and then simulates a transfer.
    This function is designed to be used as a tool by an AI agent.
    """
    # For Razorpay, the payment must be in INR.
    if from_currency.upper() != 'INR':
        return json.dumps({
            "status": "error",
            "message": f"Payment failed. Razorpay gateway only supports payments in INR, but from_currency was {from_currency}."
        })

    # 1. Initialize the gateway
    gateway = RazorpayGateway()
    if not gateway.client:
        return json.dumps({
            "status": "error",
            "message": "Payment failed due to Razorpay gateway initialization error. Check credentials."
        })

    # 2. Initiate the payment to get the URL
    logging.info(f"Initiating payment of INR {amount:.2f} for transfer to {to_address}")
    initiation_result = gateway.initiate_payment(amount_inr=amount, description=f"Payment for {amount} {from_currency} to {to_currency}")

    if initiation_result['status'] != 'success':
        return json.dumps({
            "status": "error",
            "message": f"Failed to create payment link: {initiation_result.get('message', 'Unknown error')}"
        })

    payment_url = initiation_result['payment_url']
    payment_link_id = initiation_result['payment_link_id']

    # 3. Inform the user/agent runner to complete the payment
    # open the payment URL in the default web browser
    
    webbrowser.open(payment_url)
    

    # 4. Poll for confirmation
    logging.info(f"Waiting for payment confirmation for link ID: {payment_link_id}")
    start_time = time.time()
    timeout_seconds = 180  # Wait for 3 minutes
    payment_confirmed = False
    final_payment_details = {}

    while time.time() - start_time < timeout_seconds:
        confirmation_result = gateway.is_payment_confirmed(payment_link_id)
        if confirmation_result['status'] == 'paid':
            logging.info("Payment confirmed successfully.")
            payment_confirmed = True
            final_payment_details = confirmation_result
            break
        elif confirmation_result['status'] in ['expired', 'error']:
            logging.error(f"Payment failed or link expired: {confirmation_result.get('message')}")
            return json.dumps({
                "status": "error",
                "message": f"Payment failed: {confirmation_result.get('message')}"
            })
        
        # If pending, wait and poll again
        time.sleep(10)

    if not payment_confirmed:
        logging.warning("Payment timed out.")
        return json.dumps({
            "status": "error",
            "message": "Payment was not completed within the time limit."
        })

    # 5. If payment is confirmed, simulate the transfer
    print(f"\n[TOOL LOG] Payment confirmed. Simulating transfer of {amount:.2f} {from_currency} to {to_currency} for address {to_address}...")
    
    return json.dumps({
        "status": "success",
        "message": "Payment confirmed and transfer processed.",
        "payment_id": final_payment_details.get('payment_id'),
        "amount_paid_inr": final_payment_details.get('amount_paid'),
        "transfer_details": {
            "from": from_address,
            "to": to_address,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount_in": amount
        }
    })
        