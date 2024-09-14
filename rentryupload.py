import json, requests

# Taken wholly from RimPy
BASE_URL = "https://rentry.co"
BASE_URL_RAW = f"{BASE_URL}/raw"
API_NEW_ENDPOINT = f"{BASE_URL}/api/new"
_HEADERS = {"Referer": BASE_URL}

class HttpClient:
    def __init__(self) -> None:
        # Initialize a session for making HTTP requests
        self.session = requests.Session()

    def make_request(
        self,
        method: str,
        url: str,
        data: dict[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        # Perform a HTTP request and return the response
        headers = headers or {}
        request_method = getattr(self.session, method.lower())
        response = request_method(url, data=data, headers=headers)
        response.data = response.text
        return response

    def get(self, url: str, headers: dict[str, str] | None = None) -> requests.Response:
        return self.make_request("GET", url, headers=headers)

    def post(
        self,
        url: str,
        data: dict[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return self.make_request("POST", url, data=data, headers=headers)

    def get_csrf_token(self) -> str | None:
        # Get CSRF token from the response cookies after making a GET request to the base URL
        response = self.get(BASE_URL)
        return response.cookies.get("csrftoken")


class RentryUpload:
    def __init__(self, text: str):
        self.upload_success = False
        self.url = None

        try:
            response = self.new(text)
            if response.get("status") != "200":
                self.handle_upload_failure(response)
            else:
                self.upload_success = True
                self.url = response["url"]
        finally:
            if self.upload_success:
                print(f"RentryUpload successfully uploaded data! Url: {self.url}, Edit code: {response['edit_code']}")

    def handle_upload_failure(self, response: dict[str]) -> None:
        """
        Log and handle upload failure details.
        """
        error_content = response.get("content", "Unknown")
        errors = response.get("errors", "").split(".")
        for error in errors:
            print(error)

        print("RentryUpload failed!")

    def new(self, text: str):
        """
        Upload new entry to Rentry.co.
        """
        # Initialize an HttpClient for making HTTP requests
        client = HttpClient()

        # Get CSRF token for authentication
        csrf_token = client.get_csrf_token()

        # Prepare payload for the POST request
        payload = {
            "csrfmiddlewaretoken": csrf_token,
            "text": text,
        }

        # Perform the POST request to create a new entry
        return json.loads(
            client.post(API_NEW_ENDPOINT, data=payload, headers=_HEADERS).text
        )