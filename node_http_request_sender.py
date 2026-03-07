import json
import io

from comfy_api.latest import io as comfy_api_io # pyright: ignore[reportMissingImports]
import httpx
import torch  # pyright: ignore[reportMissingImports]

from .utils import Utils

class HttpRequestSender(comfy_api_io.ComfyNode):
    @classmethod
    def define_schema(cls) -> comfy_api_io.Schema:
        return comfy_api_io.Schema(
            node_id="HttpRequestSender",
            display_name="HTTP Request Sender",
            category="NEKONOTE/HTTP",
            is_output_node=True,
            inputs=[
                comfy_api_io.String.Input(
                    id="request_url",
                    display_name="Request HTTP(S) URL",
                    default="",
                    multiline=False,
                    optional=False
                ),
                comfy_api_io.Combo.Input(
                    id="request_method",
                    display_name="HTTP Request method",
                    options=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                    default="POST",
                    optional=False,
                ),
                comfy_api_io.String.Input(
                    id="header_json",
                    display_name="Request Headers",
                    tooltip="JSON object representing the request headers.",
                    default="",
                    multiline=True,
                    optional=True
                ),
                comfy_api_io.String.Input(
                    id="cookies_json",
                    display_name="Request Cookies",
                    tooltip="JSON object representing the request cookies.",
                    default="",
                    multiline=True,
                    optional=True
                ),
                comfy_api_io.String.Input(
                    id="body_json",
                    display_name="Request Body",
                    tooltip="JSON object representing the request body.",
                    default="",
                    multiline=True,
                    optional=True
                ),
                comfy_api_io.Int.Input(
                    id="timeout",
                    display_name="Request Timeout (seconds)",
                    default=10,
                    min=1,
                    step=1,
                    max=60,
                    optional=False,
                    display_mode=comfy_api_io.NumberDisplay.number
                ),
                comfy_api_io.Image.Input(
                    id="send_image",
                    display_name="Input Image",
                    optional=True
                ),
                comfy_api_io.Combo.Input(
                    id="send_image_format",
                    display_name="Send Image Format",
                    default="PNG",
                    options=["PNG", "WEBP"],
                    optional=True,
                ),
                comfy_api_io.String.Input(
                    id="multipart_field_name_in_image",
                    display_name="Multipart Field Name in the image",
                    tooltip="When sending multipart/form-data, the image will be sent as a separate part with this field name. Default is 'upload_image'.",
                    default="upload_image",
                    multiline=False,
                    optional=True
                ),
                comfy_api_io.String.Input(
                    id="multipart_field_name_in_body",
                    display_name="Multipart Field Name in the body",
                    tooltip="When sending multipart/form-data, the JSON body will be sent as a separate part with this field name. Default is 'metadata'.",
                    default="metadata",
                    multiline=False,
                    optional=True
                ),
                comfy_api_io.Boolean.Input(
                    id="send_image_enabled",
                    display_name="Send Image Enabled",
                    tooltip="When enabled, the node will send the image as multipart/form-data. If disabled, it will send only JSON. Default is True.",
                    default=True,
                ),
                comfy_api_io.String.Input(
                    id="user_agent",
                    display_name="User Agent",
                    tooltip="User agent string to be sent with the request.",
                    default=f"comfy-nekonote-extensions/{Utils.get_version()}",
                    multiline=False,
                    optional=True
                ),
            ],
            outputs=[
                comfy_api_io.Int.Output(
                    id="status_code",
                    display_name="HTTP Status Code",
                ),
                comfy_api_io.String.Output(
                    id="response_text",
                    display_name="Response Text",
                ),
                comfy_api_io.String.Output(
                    id="response_cookies",
                    display_name="Response Cookies",
                ),
            ]
        )

    @classmethod
    def execute(cls,
                request_url: str,
                request_method: str,
                header_json: str,
                body_json: str,
                cookies_json: str,
                timeout: int,
                send_image: torch.Tensor = None,
                send_image_format: str = "PNG",
                multipart_field_name_in_image: str = "upload_image",
                multipart_field_name_in_body: str = "metadata",
                send_image_enabled: bool = False,
                user_agent: str = f"comfy-nekonote-extensions/{Utils.get_version()}",
                **kwargs) -> comfy_api_io.NodeOutput:

        if not request_url:
            print(f"[HttpRequestSender] ERROR: Request URL is required.")
            return comfy_api_io.NodeOutput(400, "Request URL is required", "")

        # URL スキーム検証
        if not request_url.startswith("http://") and not request_url.startswith("https://"):
            print(f"[HttpRequestSender] ERROR: Unsupported URL scheme. Use http:// or https://")
            return comfy_api_io.NodeOutput(400, "Unsupported URL scheme", "")

        headers: dict = {}
        if header_json and header_json.strip():
            try:
                headers = json.loads(header_json)
            except json.JSONDecodeError as e:
                print(f"[HttpRequestSender] ERROR: Invalid JSON in headers: {e}")
                return comfy_api_io.NodeOutput(400, f"Invalid JSON in headers: {e}", "")

        body_data: dict|None = None
        if body_json and body_json.strip():
            try:
                body_data = json.loads(body_json)
            except json.JSONDecodeError as e:
                print(f"[HttpRequestSender] ERROR: Invalid JSON in body: {e}")
                return comfy_api_io.NodeOutput(400, f"Invalid JSON in body: {e}", "")

        cookies: dict = {}
        if cookies_json and cookies_json.strip():
            try:
                cookies = json.loads(cookies_json)
                if isinstance(cookies, dict):
                    headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
                else:
                    print(f"[HttpRequestSender] ERROR: Cookies JSON must be an object/dictionary.")
                    return comfy_api_io.NodeOutput(400, "Cookies JSON must be an object/dictionary.", "")
            except json.JSONDecodeError as e:
                print(f"[HttpRequestSender] ERROR: Invalid JSON in cookies: {e}")
                return comfy_api_io.NodeOutput(400, f"Invalid JSON in cookies: {e}", "")

        try:
            if user_agent != "":
                headers["User-Agent"] = user_agent

            with httpx.Client(headers=headers, cookies=cookies, timeout=timeout, http2=True, follow_redirects=True) as client:
                response = None
                # multipart/form-data で送信（send_image_enabled = True の場合）
                if send_image_enabled and send_image is not None:
                    print(f"[HttpRequestSender] Sending multipart/form-data with image...")

                    # 画像をバイナリに変換
                    img_pil = Utils.tensor_to_image(send_image)
                    img_pil = img_pil.convert("RGBA")

                    img_bytes = io.BytesIO()
                    img_pil.save(img_bytes, format=send_image_format if send_image_format else "PNG")
                    img_bytes.seek(0)

                    # multipart フォーム構築
                    files = {
                        multipart_field_name_in_image: (f"image.{send_image_format.lower()}", img_bytes.getvalue(), f"image/{send_image_format.lower()}"),
                    }

                    # メタデータがあれば追加
                    if body_data is not None:
                        files[multipart_field_name_in_body] = (f"{multipart_field_name_in_body}.json", json.dumps(body_data).encode("utf-8"), "application/json")

                    response = client.request(
                        method=request_method,
                        url=request_url,
                        files=files,
                    )

                # JSON のみ送信（send_image_enabled = False の場合）
                else:
                    print(f"[HttpRequestSender] Sending JSON...")

                    response = client.request(
                        method=request_method,
                        url=request_url,
                        json=body_data,
                    )

                if response is None:
                    print(f"[HttpRequestSender] Response is None")
                    return comfy_api_io.NodeOutput(500, "No response received", "")

                print(f"[HttpRequestSender] Response Status: {response.status_code}")
                print(f"[HttpRequestSender] Response: {response.text}")
                return comfy_api_io.NodeOutput(response.status_code, response.text, response.cookies)

        except httpx.ConnectError as e:
            print(f"[HttpRequestSender] ERROR: Connection failed: {e}")
            return comfy_api_io.NodeOutput(500, f"Connection error: {e}", "")

        except httpx.TimeoutException as e:
            print(f"[HttpRequestSender] ERROR: Request timeout: {e}")
            return comfy_api_io.NodeOutput(408, f"Request timeout: {e}", "")

        except Exception as ex:
            print(f"[HttpRequestSender] ERROR: {ex}")
            import traceback
            traceback.print_exc()
            return comfy_api_io.NodeOutput(500, f"Error: {ex}", "")
