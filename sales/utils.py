from django.utils import timezone


def generate_reference(prefix):
    from sales.models import JobOrder, Quotation, DeliveryNote, Receipt

    model_map = {
        'JOB': JobOrder,
        'QUO': Quotation,
        'DN':  DeliveryNote,
        'REC': Receipt,
    }
    Model = model_map.get(prefix)
    if not Model:
        raise ValueError(f"Unknown prefix: {prefix}")

    year = timezone.now().year
    pattern = f"{prefix}-{year}-"
    last = Model.objects.filter(reference__startswith=pattern).order_by('-reference').first()
    if last:
        next_num = int(last.reference.split('-')[-1]) + 1
    else:
        next_num = 1
    return f"{pattern}{next_num:04d}"
