from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Store, Asset

# For Store CSV import/export
class StoreResource(resources.ModelResource):
    class Meta:
        model = Store
        fields = ('id', 'code', 'name', 'address')  # customize as needed

@admin.register(Store)
class StoreAdmin(ImportExportModelAdmin):
    resource_class = StoreResource


# For Asset CSV import/export (store is matched by its unique code)
class AssetResource(resources.ModelResource):
    class Meta:
        model = Asset
        fields = (
            'id', 'item', 'model', 'invoice_number', 'purchase_date',
            'serial_number', 'current_location', 'supplier_name', 'working_status',
            'current_custodian', 'warranty_end_date', 'quantity', 'store'
        )
        import_id_fields = ['serial_number']  # Ensure uniqueness

    def before_import_row(self, row, **kwargs):
        # Match store by code from CSV
        store_code = row.get('store')
        try:
            store = Store.objects.get(code=store_code)
            row['store'] = store.pk  # replace with ID for foreign key
        except Store.DoesNotExist:
            raise Exception(f"Store with code '{store_code}' does not exist. Import the Store CSV first.")


@admin.register(Asset)
class AssetAdmin(ImportExportModelAdmin):
    resource_class = AssetResource
