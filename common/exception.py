class VerifyError(Exception):
    """An error while validating VerifyCode."""
    def __init__(self, message, code=None):
        super(VerifyError, self).__init__(message, code)

        self.message = message
        self.code = code


class SmsError(Exception):
    """An error while validating VerifyCode."""
    def __init__(self, message, code=None):
        super(SmsError, self).__init__(message, code)

        self.message = message
        self.code = code
