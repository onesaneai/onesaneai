from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid
from django.contrib.auth import get_user_model
User = get_user_model()

# ---------- 1️⃣ COMPANY INFO ----------
class CompanyInfo(models.Model):
    name = models.CharField(max_length=200, default="Onesane AI")
    logo = models.ImageField(upload_to="company/", blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(default="info@onesane.com")
    phone = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)

    # Payment / Banking info
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=50, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_id = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name


# ---------- 2️⃣ CLIENT ----------
class Client(models.Model):
    client_name = models.CharField(max_length=200)
    client_profession = models.CharField(max_length=200, blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    company_logo = models.ImageField(upload_to="clients/", blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, default="INR")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_name} ({self.company_name or 'Individual'})"


# ---------- 3️⃣ INVOICE ----------
class Invoice(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="invoices")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    currency = models.CharField(max_length=10, default="INR")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True, null=True)
    public_message = models.TextField(blank=True, null=True)
    internal_notes = models.TextField(blank=True, null=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    additional_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client.client_name}"


    def generate_invoice_number(self):
        prefix = "INV"
        date_part = self.created_at.strftime("%Y%m%d") if self.created_at else ""
        unique_id = str(uuid.uuid4().int)[:6]  # Or use a sequence, or max + 1 logic
        return f"{prefix}-{date_part}-{unique_id}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Ensure date_created is set for use in generate_invoice_number
            if not self.created_at:
                from django.utils.timezone import now
                self.created_at = now()
            self.invoice_number = self.generate_invoice_number()
        
        items = self.items.all()
        self.subtotal = sum(item.total for item in items)
        print("The subtotal is:", self.subtotal)
        tax_amount = (self.subtotal - self.discount) * (self.tax / 100)
        print("The tax amount is:", tax_amount)

        # ---------------------
        
        self.total = (self.subtotal - self.discount + self.additional_charges) + tax_amount
        print("Total amount is:", self.total)
        self.balance_due = self.total - self.amount_paid
            
            
        super().save(*args, **kwargs)

    def update_totals(self):
        items = self.items.all()
        self.subtotal = sum(item.total for item in items)
        self.total = (
            self.subtotal - self.discount + self.tax + self.additional_charges
        )
        self.balance_due = self.total - self.amount_paid
        self.save()


# ---------- 4️⃣ INVOICE ITEM ----------
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)  # percentage
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        base = self.quantity * self.unit_price
        tax_amount = base * (self.tax_rate / 100)
        self.total = base + tax_amount - self.discount
        super().save(*args, **kwargs)
        self.invoice.update_totals()

    def __str__(self):
        return f"{self.description} ({self.invoice.invoice_number})"


# ---------- 5️⃣ PAYMENT (optional) ----------
class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="payments", on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50, default="Bank Transfer")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        total_paid = sum(p.amount for p in self.invoice.payments.all())
        self.invoice.amount_paid = total_paid
        self.invoice.balance_due = self.invoice.total - total_paid
        self.invoice.save()


# ---------- 6️⃣ EMAIL LOG (for sent invoices) ----------
class EmailLog(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="emails", on_delete=models.CASCADE)
    sent_to = models.EmailField()
    cc = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Email to {self.sent_to} ({self.invoice.invoice_number})"
