from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Client


# ---------- 1️⃣ CLIENT FORM ----------
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "client_name","client_profession", "company_name","company_logo", "email", "phone", "address",
            "country", "currency", "gst_number"
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
        }


# ---------- 2️⃣ INVOICE FORM ----------
class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "client","due_date",
            "payment_terms", "currency", "notes", "public_message"
        ]
        widgets = {
            "client": forms.Select(attrs={"class": "form-select"}),
            "invoice_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Auto-generated or custom"}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "payment_terms": forms.TextInput(attrs={"class": "form-control"}),
            "currency": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "public_message": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }


# ---------- 3️⃣ INVOICE ITEM FORM ----------
class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["description", "quantity", "unit_price", "tax_rate", "discount"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Service description"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "unit_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tax_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
            "discount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


# ---------- 4️⃣ INVOICE ITEM FORMSET ----------
InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True
)
