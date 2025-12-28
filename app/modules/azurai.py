"""
This module provides an Azure AI client for communication with Azure-hosted OpenAI models. 
It facilitates authentication using OAuth 2.0 client credentials and communicates with Azure models.
"""

import base64
import os
import re

import markdown
import requests
from openai import AzureOpenAI
from dotenv import load_dotenv


class AzureAIClient:
    """
    A client to interact with Azure OpenAI using client credentials.

    This class handles authentication via OAuth 2.0 client credentials and
    provides methods to communicate with Azure-hosted OpenAI models.

    Attributes:
        client_id (str): Azure Client ID.
        client_secret (str): Azure Client Secret.
        token_url (str): URL to fetch OAuth token.
        app_key (str): Application key used for user metadata.
        endpoint (str): Azure OpenAI endpoint.
        api_version (str): API version for OpenAI.
        model (str): Azure OpenAI model name.
        access_token (str): Retrieved OAuth access token.
        client (AzureOpenAI): Instance of AzureOpenAI client.
    """

    def __init__(self, env_path: str = os.path.expanduser("~/azureai.env")):
        self.env_path = env_path
        self.ready = None
        self.access_token = None
        self.client = None
        self.load_env_vars()

    def load_env_vars(self):
        """
        Load environment variables from the specified .env file.
        """
        if os.path.exists(self.env_path):
            load_dotenv(self.env_path)

        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.token_url = os.getenv("AZURE_TOKEN_URL")
        self.app_key = os.getenv("AZURE_APP_KEY")
        self.endpoint = os.getenv("AZURE_ENDPOINT")
        self.api_version = os.getenv("AZURE_API_VERSION")
        self.model = os.getenv("AZURE_MODEL")

        self.ready = False if not self.client_id else True

    def is_ready(self):
        """
        Check if the client is properly configured with necessary environment variables.
        """
        self.load_env_vars()
        return self.ready

    def obtain_oauth_token(self) -> str:
        """
        Authenticate with Azure and retrieve an access token.

        Returns:
            str: The OAuth2 access token.

        Raises:
            Exception: If token retrieval fails.
        """
        payload = "grant_type=client_credentials"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }

        response = requests.post(self.token_url, headers=headers, data=payload)

        if response.status_code != 200:
            raise Exception(f"Failed to obtain access token: {response.status_code} - {response.text}")

        self.access_token = response.json().get("access_token")
        return self.access_token

    def initialize_client(self):
        """
        Initialize the AzureOpenAI client using the access token.
        """
        if not self.access_token:
            self.obtain_oauth_token()

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.access_token,
            api_version=self.api_version
        )

    def ask(self, system_prompt: str, user_prompt: str, format: str = "raw") -> str:
        """
        Send a prompt and receive a response from the Azure OpenAI model, optionally formatted.

        Args:
            system_prompt (str): The system message guiding the model.
            user_prompt (str): The user's input message.
            format (str): Output format - "raw", "html", or "plain". Default is "raw".

        Returns:
            str: Formatted model response based on the specified format.
        """
        if not self.client:
            self.initialize_client()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            user=f'{{"appkey": "{self.app_key}"}}'
        )

        content = response.choices[0].message.content.strip()

        if format == "html":
            return self.in_html(content)
        elif format == "plain":
            return self.in_plaintext(content)
        elif format == "code":
            return self.code(content)

        return content

    @staticmethod
    def in_html(content: str) -> str:
        """
        Convert Markdown content into styled HTML with table support.

        Args:
            content (str): Markdown-formatted string.

        Returns:
            str: Styled HTML with support for tables.
        """
        content = re.sub(r'!\[(.*?)\]\((.*?)\)', "", content)
        html_body = markdown.markdown(content, extensions=["tables"])

        styled_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-weight: 300;
                    padding: 10px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                }}
                pre {{
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                code {{
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                blockquote {{
                    border-left: 4px solid #888;
                    padding-left: 10px;
                    margin-left: 0;
                    font-style: italic;
                }}
                a {{
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                ul, ol {{
                    padding-left: 20px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 10px 0;
                }}
                th, td {{
                    border: 1px solid #d0d7de;
                    padding: 6px 13px;
                    text-align: left;
                }}

                /* Light theme */
                @media (prefers-color-scheme: light) {{
                    body {{ background-color: #ffffff; color: #24292e; }}
                    pre {{ background-color: #f6f8fa; color: #000; }}
                    code {{ background-color: #f6f8fa; color: #000; }}
                    th {{ background-color: #f6f8fa; }}
                    td, th {{ border: 1px solid #d0d7de; }}
                }}

                /* Dark theme */
                @media (prefers-color-scheme: dark) {{
                    body {{ background-color: #1e1e1e; color: #d4d4d4; }}
                    pre {{ background-color: #2d2d2d; color: #ddd; }}
                    code {{ background-color: #2d2d2d; color: #ddd; }}
                    th {{ background-color: #333; }}
                    td, th {{ border: 1px solid #444; }}
                }}
            </style>
        </head>
        <body>{html_body}</body>
        </html>
        """
        return styled_html

    @staticmethod
    def in_plaintext(content: str) -> str:
        """
        Convert Markdown or code-formatted string to plain text.

        Args:
            content (str): Markdown-formatted or code-wrapped string.

        Returns:
            str: Cleaned plain text.
        """
        content = re.sub(r"^```[\w]*\n(.*?)\n```$", r"\1", content.strip(), flags=re.DOTALL)
        content = re.sub(r'^.*!\[.*?\]\(.*?\).*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'^(#{1,6})\s+(.*)$', r'\2', content, flags=re.MULTILINE)
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        content = re.sub(r'__([^_]+)__', r'\1', content)
        content = re.sub(r'_([^_]+)_', r'\1', content)
        content = re.sub(r'^\s*[-*]\s+', '- ', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s+', lambda m: m.group(), content, flags=re.MULTILINE)
        content = re.sub(r'`([^`]+)`', r'\1', content)
        content = re.sub(r'\n{2,}', '\n\n', content)

        return content

    @staticmethod
    def code(markdown: str) -> str:
        """
        Extract the first triple-backtick code block as plain text.

        Args:
            markdown (str): Markdown containing code blocks.

        Returns:
            str: Extracted code or original markdown if no code block found.
        """
        match = re.search(r"```(?:python)?\n(.*?)\n```", markdown, flags=re.DOTALL)
        return match.group(1) if match else markdown