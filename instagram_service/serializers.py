from rest_framework import serializers


class ResponseSerializer(serializers.Serializer):
    """
    Standardized response serializer that wraps all API responses
    """

    success = serializers.BooleanField(default=True)
    data = serializers.JSONField(required=False)
    error = serializers.CharField(required=False)

    @classmethod
    def format_response(cls, success=True, data=None, error=None):
        """
        Format response data according to the standard format

        Args:
            success (bool): Whether the request was successful
            data (dict): Response data
            error (str): Error message if any

        Returns:
            dict: Formatted response
        """
        response = {"success": success}

        if data is not None:
            response["data"] = data

        if error is not None:
            response["error"] = error

        return response
