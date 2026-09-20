---
doc_id: "ofn-seller-refunds"
title: "Refunds and Adjusting Payments"
source_url: "https://guide.openfoodnetwork.org/basic-features/orders/refunds-and-adjusting-payments"
retrieved_at: "2026-09-20"
document_version: "not-stated"
audience: "seller"
category: "refunds-policy"
language: "en"
license_or_permission: "CC-BY-SA-4.0"
attribution: "Open Food Network contributors"
license_url: "https://creativecommons.org/licenses/by-sa/4.0/"
permission_source: "https://ofn-user-guide.gitbook.io/ofn-handbook/white-label-users"
source_format: "official-markdown"
extraction_scope: "Full article text; image assets omitted"
changes: "Removed documentation navigation and image assets; retained captions and warnings; converted tabs to headings; resolved links"
---

# Refunds and Adjusting Payments

From time to time, a customer may request that their order is adjusted such as adding or removing an item.

On other occasions you as a business manager may need to change an order. Common scenarios include:

1. A product was not delivered by a supplier
2. A product was of lower quality than expected
3. An order contains products with variable weights such as [meat or large vegetables](https://guide.openfoodnetwork.org/basic-features/products-1/pricing-irregular-items-kg.md#option-one-set-an-average-weight-price-and-reimburse) (i.e. whole items priced by weight).

The process of issuing a refund or requesting further payment depends on the [payment method](https://guide.openfoodnetwork.org/basic-features/shopfront/payment-methods.md) employed.

**warning:**
On the OFN platform, refunds and additional payments can only be made **automatically** using the [Payment Method](https://guide.openfoodnetwork.org/basic-features/shopfront/payment-methods.md) Provider **Stripe/Stripe SCA**.

## Refunds

Using the OFN Platform you can process a [total refund](#total-refund), which refunds the entirety of the order, or a [partial refund](#partial-refund), which you might use when an item was not available for example.

**warning:**
If you have integrated with Stripe as a Payment Method, you can log in to your Stripe account and issue an invoice to the customer via Stripe. The customer will be sent an email asking them to pay with a Credit or Debit Card, but be aware that OFN will not be notified of this transaction and you will still need to manually capture the payment as received in OFN.

### Total Refund

To issue a *total refund*, select the relevant payment method from the tabs below:

#### Cash/BACS
For non-automated payment methods (such as cash on collection or BACS), there are two scenarios:

**The customer has not yet paid for the item.**
If a customer places an order, selecting a payment method such as cash on collection or BACS and the payment has not been captured on the system it will appear as 'payment state: balance due':

You can [cancel the order](https://guide.openfoodnetwork.org/basic-features/orders/refunds-and-adjusting-payments.md#marking-an-order-as-cancelled) straight away following the steps below for 'Marking an order as cancelled'.

**The customer has paid for the item.**

When [viewing orders](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#listing-orders) the order appears as 'payment state: paid' and the 'Shipment State: Ready':

1. Arrange for the customer to be reimbursed independently of the OFN platform.
2. Record this action by [**Orders -> Edit**](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#editing-an-order) and select the ‘Payments’ tab from the right hand menu.
   Select the ‘X’ to the right hand side of the payment to void it.

Before marking the payment as void

After marking the payment as void, the payment status changes to 'void'

Then [mark the order as ‘cancelled'](https://guide.openfoodnetwork.org/basic-features/orders/refunds-and-adjusting-payments.md#marking-an-order-as-cancelled) using the steps below.

#### Stripe
Order payment is collected automatically on creation (except for [subscriptions](https://guide.openfoodnetwork.org/basic-features/subscriptions.md)) and so in [listing Orders](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#listing-orders) the order appears as:

'Payment state = paid'

To process the total refund, visit [**Orders -> Edit**](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#editing-an-order) and select ‘Payments’ from the right hand menu.
Click on the ‘**X**’ to the right of the payment to void it.

This will automatically send the payment back to the credit or debit card used by the customer.

**info:**
Note that Stripe payments can take 3-5 working days to appear on a customer’s bank statement.

Once you have issued a refund, follow the steps below to [cancel the order](https://guide.openfoodnetwork.org/basic-features/orders/refunds-and-adjusting-payments.md#marking-an-order-as-cancelled).

#### PayPal
Payment is collected automatically on checkout from the customer and so in [listing Orders](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#listing-orders) the order appears as:

'Payment state = paid'

Going to the 'payments' screen from Orders -> Edit will show the payment method used:

**danger:**
**Orders placed and paid for via PayPal can not be refunded through the OFN platform.**

To refund the customer you will need to log into your [PayPal account](https://www.paypal.com/uk/home) and issue the money back to the customer’s account through Paypal's interface.

Once this has been done, you can [mark the order as cancelled](https://guide.openfoodnetwork.org/basic-features/orders/refunds-and-adjusting-payments.md#marking-an-order-as-cancelled) using the steps below.

#### Marking an order as cancelled

Once you have issued a refund, you can now cancel the order. [Edit the order](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#editing-an-order) and select ‘Cancel Order’ under ‘Actions’ (top right hand blue button).

**success:**
The customer will receive an email to state that their order has been cancelled.

**info:**
Cancelling an order will **automatically** **update stock levels**. For example, if a shop had five loaves of bread in stock and a customer ordered three, stock levels would show two in stock. Cancelling the customer's order automatically updates stock levels, such that five will again show as in stock.

**danger:**
Note that you cannot cancel an order which has been marked as ‘Shipped’

### Partial Refund

To issue a partial refund, you must first edit the order to change the balance owing. There are two main ways to [edit an order](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#editing-an-order) when you want to issue a partial refund. You can adjust item quantities, or make an adjustment:

**1. Edit the quantity of an item** by going to[ Orders -> edit ](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#adding-and-removing-products-from-an-order)order and clicking on the ‘edit’ icon next to the item (highlighted in red below) or delete the item completely using the 'bin' icon (highlighted in green below):

Or you can *reduce* the quantity by editing the quantity value, remembering to click the 'tick' button to save your changes:

Select **‘Update and Recalculate Fees’** at the bottom of the page to save your changes.

**danger:**
If the product has been deleted by the supplier from their master [product](https://guide.openfoodnetwork.org/basic-features/products-1.md) list then it will not be possible to edit this page. In which case, use the ‘adjustments’ method below.

**2. Edit by adding a new Adjustment** to the [**order**](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#modify-an-order) by visiting **Orders -> Edit -> Adjustments** from the right hand menu and selecting **+ New Adjustment**  at the top right.

Add the relevant details, remembering that for **a refund**,  the value needs to be a **negative number**. When finished, click ‘continue’:

**success:**
You can use ‘Adjustments’ to partially refund a customer for a substandard product.

Once the order has been amended to reflect either the missing/adjusted products or the new adjustment, the order will appear with the payment state of **‘Credit Owing’** for the amount the customer no longer needs to pay.

**Process the Partial Refund**
To process a partial refund of the amount that is now owed, see instructions by choosing the payment method from the following tabs:

#### Cash/BACS

1. Arrange for the refund to be made to the customer independently of the platform.
2. Record this action by going to **Orders -> Edit** and selecting ‘Payments’ from the right hand menu, then '**+ New Payment**':

Enter a **negative value** in the ‘Amount’ field to record the refund as having been made.

**info:**
The button for **+ New Payment** will only be visible if you have already added an adjustment (e.g. the payment state is 'credit owed')

#### Stripe
Using the OFN platform you can automatically refund a customer who paid by Stripe. This will directly process the refund to their credit or debit card.

1. Visit **Orders -> Edit Order** and then select ‘Payments’ from the right hand menu.
2. As you created the adjustment in the previous step, the payment screen will now say '**Credit Owed**' with the amount you specified. By clicking the tick next to the payment any credit owed to the customer will be automatically refunded.

**danger:**
Clicking the 'X' will **void the whole payment** and issue a **full refund** to the customer.

**warning:**
Note that Stripe payments can take 3-5 working days to appear on a customer’s bank statement.

#### PayPal
**You can not issue a partial refund to a customer who paid by PayPal automatically via the OFN platform at present.**

1. You will need to log into your business [PayPal account](https://www.paypal.com/uk/home) and refund the customer the correct amount through their interface.
2. To record this action you will need to set up a new [Payment Method](https://guide.openfoodnetwork.org/basic-features/shopfront/payment-methods.md) as follows:
   Name= ‘Paypal refunds’
   Display = ‘Back Office Only’
   Payment provider = ‘cash/EFT/etc’.
3. Visit **Orders - > Edit Order-> Payments** (found in the right hand menu).
4. Select **+New Payment** and select ‘Paypal refunds’.

A negative value in the ‘Amount’ field means that a refund is recorded.

**danger:**
If you opt to add a new payment with the payment method provider ‘Paypal’ this will not be possible:

## Collecting Additional Payments

Follow the steps above for [Partial refunds](https://guide.openfoodnetwork.org/basic-features/orders/refunds-and-adjusting-payments.md#partial-refund) to add extra items to a customer's order or make adjustments via the [Bulk Order Management](https://guide.openfoodnetwork.org/basic-features/products-1/group-buy-for-bulk-ordering.md#adjusting-orders-to-make-complete-batches) page.

Orders will now display with the Payment State = ‘Balance Due’:

To record payment of the extra monies due visit [Orders -> Edit Order](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#editing-an-order) and then ‘Payments’.
Select **+ New Payment** (top right hand blue button)

1. If customer has given your business the money owing in **cash or BACS** payment then record this in the same manner as detailed for a refund, but use a positive value in the ‘Amount’ field.
2. If the customer is present or on the end of the phone you can take the extra payment by **Stripe**. You will need the customer’s credit/debit card details to do this. You can also log in to your Stripe account and issue an invoice to the customer via Stripe. The customer will be sent an email asking them to pay with a Credit or Debit Card, but be aware that OFN will not be notified of this transaction and you will still need to manually capture the payment as received in OFN.

**warning:**
Collection of additional payments through PayPal is not possible at present

**warning:**
If a payment method has an associated fee attached then the fee will be recorded by the system every time you collect extra money from the customer or issue them a refund.

## Keeping Track of Customer Payment Balances

Monies owing (credit) or due (debit) for **individual orders** can be viewed on your [listing orders admin](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md) page.

**warning:**
Remember that only payments for integrated payment methods (PayPal and Stripe) are automatically captured by the platform. If a customer pays your business by cash or BACS (or similar) you will need to [capture this payment](https://guide.openfoodnetwork.org/basic-features/orders/view-orders.md#capturing-a-payment) manually to keep your records up to date.

You may wish to allow your trusted customers to pay (by BACS) once a month for all their orders in that time period, or give those who have cash flow one week a bit of lee-way with their payments.  To keep track of individual **customer balances** with your business, visit your [Customer](https://guide.openfoodnetwork.org/basic-features/shopfront/customer-management-and-conditional-displays-prices/customers.md) list.  The amount of credit/debit due is displayed to the right of each customer's entry.
