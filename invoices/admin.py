from django.contrib import admin
from .models import (
    CompanyInfo, Client, Invoice, InvoiceItem, Payment, EmailLog
)
from django.utils.html import format_html
# ---------- 1️⃣ COMPANY INFO ----------
@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "website")
    fieldsets = (
        ("Company Identity", {
            "fields": ("name", "logo", "address", "email", "phone", "website")
        }),
        ("Tax & Legal", {
            "fields": ("gst_number", "tax_id")
        }),
        ("Banking / Payment Details", {
            "fields": (
                "bank_name", "account_name", "account_number",
                "ifsc_code", "upi_id", "paypal_id"
            )
        }),
    )
    search_fields = ("name", "email", "phone")
    list_per_page = 10


# ---------- 2️⃣ CLIENT ----------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("client_name","client_profession", "company_name","company_logo", "email", "phone", "country", "currency", "created_at")
    search_fields = ("client_name", "company_name", "email", "phone", "country")
    list_filter = ("country", "currency")
    ordering = ("-created_at",)
    fieldsets = (
        ("Client Info", {
            "fields": ("client_name","client_profession", "company_name","company_logo", "email", "phone", "address")
        }),
        ("Tax / Billing", {
            "fields": ("gst_number", "country", "currency")
        }),
    )
    readonly_fields = ("created_at",)


# ---------- 3️⃣ INVOICE ITEM INLINE ----------
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ("description", "quantity", "unit_price", "tax_rate", "discount", "total")
    readonly_fields = ("total",)
    autocomplete_fields = []
    show_change_link = False


# ---------- 4️⃣ PAYMENT INLINE ----------
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("date", "amount", "method", "transaction_id", "notes")
    readonly_fields = ("created_at",)
    show_change_link = False


# ---------- 5️⃣ EMAIL LOG INLINE ----------
class EmailLogInline(admin.TabularInline):
    model = EmailLog
    extra = 0
    readonly_fields = ("sent_at", "viewed", "viewed_at")
    fields = ("sent_to", "subject", "sent_at", "viewed", "viewed_at")
    can_delete = False


# ---------- 6️⃣ INVOICE ----------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number", "client", "status",
        "invoice_date", "due_date", "total", "balance_due","Preview_Invoice"
    )
    list_filter = ("status", "currency", "invoice_date")
    search_fields = ("invoice_number", "client__client_name", "client__email","client__company_name",)
    date_hierarchy = "invoice_date"
    ordering = ("-invoice_date",)

    fieldsets = (
        ("Invoice Info", {
            "fields": (
                "client", "created_by", "invoice_date",
                "due_date", "status", "payment_terms", "currency", "exchange_rate"
            )
        }),
        ("Amounts", {
            "fields": ("discount","additional_charges","tax",
                "subtotal", 
                "total","amount_paid", "balance_due"
            )
        }),
        ("Notes & Messages", {
            "fields": ("notes", "public_message", "internal_notes")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    readonly_fields = ("subtotal", "total", "balance_due","amount_paid", "created_at", "updated_at")
    inlines = [InvoiceItemInline, PaymentInline, EmailLogInline]
    list_per_page = 15

    def save_model(self, request, obj, form, change):
        """Auto-assign current user as creator on new invoices"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def Preview_Invoice(self, obj):
        return format_html(f'<a class="button" href="/api/invoices/{obj.invoice_number}/preview/" target="_blank">👁 Preview</a>')
    Preview_Invoice.short_description = 'Preview'


# ---------- 7️⃣ PAYMENT ----------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "date", "amount", "method", "transaction_id")
    list_filter = ("method", "date")
    search_fields = ("invoice__invoice_number", "transaction_id")
    readonly_fields = ("created_at",)
    ordering = ("-date",)


# ---------- 8️⃣ EMAIL LOG ----------
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("invoice", "sent_to", "subject", "sent_at", "viewed", "viewed_at")
    search_fields = ("invoice__invoice_number", "sent_to", "subject")
    list_filter = ("viewed", "sent_at")
    readonly_fields = ("sent_at",)
    ordering = ("-sent_at",)
