from typing import Any

from nested_admin.formsets import NestedBaseGenericInlineFormSet


class TaxonClassificationCandidateFormSet(NestedBaseGenericInlineFormSet):
    def save(self, commit: bool = ...) -> Any:
        has_changed = self.has_changed()

        if has_changed:
            self.instance.candidates.filter(is_seed=False).delete()

        result = super().save(commit)

        if not commit:
            return result

        try:
            self.instance.refresh_from_db()
        except self.instance.DoesNotExist:
            pass
        else:
            if has_changed:
                # NOTE: The parent formset MUST be in charge of updating results or whatever needed.
                self.instance.skip_notify_changes_parent = self.is_nested
                self.instance.recompute_candidates_tree()
                self.instance.skip_notify_changes_parent = False

        return result
