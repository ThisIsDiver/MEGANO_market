class SoftDeleteAdminMixin:
    actions = ["archive_selected", "unarchive_selected"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def get_queryset(self, request):
        return super().get_queryset(request)

    def get_deleted_objects(self, objs, request):
        return [str(obj) for obj in objs], {}, set(), []

    def archive_selected(self, request, queryset):
        updated_count = queryset.update(is_archived=True)
        self.message_user(request, "Archived: %s" % updated_count)

    def unarchive_selected(self, request, queryset):
        updated_count = queryset.update(is_archived=False)
        self.message_user(request, "Archived: %s" % updated_count)

    archive_selected.short_description = "Archive selected"