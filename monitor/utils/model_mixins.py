from django.db import models


class ModelChangeFunc(models.Model):

    class Meta:
        abstract = True

    # Setup update func
    """
    Key and Update function to run when something changes
    """
    monitor_change = None

    @property
    def monitor_change_fields(self) -> list:
        if self.monitor_change:
            return [key for key, _ in self.monitor_change.items()]
        return []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.monitor_change_fields:
            default_value = getattr(self, field, None)
            clone_field = f"__{field}"
            setattr(self, clone_field, default_value)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):

        for field in self.monitor_change_fields:
            clone_field = f"__{field}"

            # Get clone and normal values
            clone_value = getattr(self, clone_field, None)
            normal_value = getattr(self, field, None)

            # Check if value are different
            if normal_value != clone_value:
                # Get Function to run
                change_func = self.monitor_change.get(field)
                change_func(self)

        super().save(force_insert, force_update, *args, **kwargs)

        for field in self.monitor_change_fields:
            clone_field = f"__{field}"
            default_value = getattr(self, field, None)
            setattr(self, clone_field, default_value)
