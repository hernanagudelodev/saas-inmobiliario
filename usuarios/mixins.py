# usuarios/mixins.py
from django.core.exceptions import PermissionDenied

class TenantRequiredMixin:
    enforce_for_superuser = False  # <--- superuser NO obligado a tener inmobiliaria

    def get_user_inmobiliaria(self):
        user = self.request.user
        if user.is_superuser and not self.enforce_for_superuser:
            return None  # superuser: sin filtro
        try:
            return user.profile.inmobiliaria
        except Exception:
            return None

    def get_queryset(self):
        qs = super().get_queryset()
        inmobiliaria = self.get_user_inmobiliaria()
        # Si hay inmobiliaria, filtra; si es None (superuser), no filtra
        if hasattr(self.model, 'inmobiliaria') and inmobiliaria is not None:
            qs = qs.filter(inmobiliaria=inmobiliaria)
        return qs

    def form_valid(self, form):
        inmobiliaria = self.get_user_inmobiliaria()
        obj = form.instance
        if hasattr(obj, 'inmobiliaria') and obj.inmobiliaria_id is None:
            if inmobiliaria is not None:
                obj.inmobiliaria = inmobiliaria
            else:
                # superusuario creando: debe elegir inmobiliaria antes (o manejarlo en el form)
                from django.core.exceptions import ValidationError
                raise ValidationError("Como superusuario, selecciona la inmobiliaria antes de guardar.")
        return super().form_valid(form)
