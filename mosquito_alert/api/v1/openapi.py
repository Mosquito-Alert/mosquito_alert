import re

from drf_standardized_errors.handler import exception_handler as standardized_errors_handler
from drf_standardized_errors.openapi import AutoSchema as StandarizedErrorsAutoSchema


class AutoSchema(StandarizedErrorsAutoSchema):
    def get_operation_id(self) -> str:
        """Overriding needed when using the --remove-operation-id-prefix option in the code generator."""
        tokenized_path = self._tokenize_path()
        # ensure only alphanumeric characters exist
        tokenized_path = [re.sub(r'\W+', '', t) for t in tokenized_path]

        if self.method == 'GET' and self._is_list_view():
            action = 'list'
        else:
            action = self.method_mapping[self.method.lower()]

        if not tokenized_path:
            tokenized_path.append('root')

        if re.search(r'<drf_format_suffix\w*:\w+>', self.path_regex):
            tokenized_path.append('formatted')

        return '_'.join(tokenized_path + [action])

    def _should_add_error_response(self, responses: dict, status_code: str) -> bool:
        if (
            status_code == "400"
            and status_code not in responses
            and self.view.get_exception_handler() is standardized_errors_handler
        ):
            # no need to account for parse errors when deciding if we should add
            # the 400 error response
            return self._should_add_validation_error_response()
        else:
            return super()._should_add_error_response(responses, status_code)

    def _get_http400_serializer(self):
        # removed all logic related to having parse errors
        return self._get_serializer_for_validation_error_response()