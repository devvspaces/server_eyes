from django.contrib import admin


# To add (add_form and add_fieldset) functionalities to admin model forms
class ExtraAdminFeature(admin.ModelAdmin):
    add_form = None
    add_fieldsets = None

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during object creation
        """
        defaults = {}
        if obj is None:
            if self.add_form is not None:
                defaults['form'] = self.add_form
        
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
    

    def get_fieldsets(self, request, obj=None):
        if not obj:
            if self.add_fieldsets is not None:
                return self.add_fieldsets
        return super().get_fieldsets(request, obj)
