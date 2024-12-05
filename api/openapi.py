from drf_standardized_errors.handler import exception_handler as standardized_errors_handler
from drf_standardized_errors.openapi import AutoSchema as StandarizedErrorsAutoSchema


class AutoSchema(StandarizedErrorsAutoSchema):
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