import socket
import ssl
from urllib.parse import urlparse
import zlib
import gzip

EUR_TO_MDL = 19.
MDL_TO_EUR = 1 / EUR_TO_MDL

def convert_to_eur_or_mdl(product):
    if product.currency == "lei":
        product.price = product.price * MDL_TO_EUR  # Convert MDL to EUR
        product.currency = "eur"
    elif product.currency == "eur":
        product.price = product.price * EUR_TO_MDL  # Convert EUR to MDL
        product.currency = "lei"
    return product

def filter_price_range(product):
    if product.currency == "eur" and 100 <= product.price <= 500:
        return True
    return False

def get_http_response_body(url, max_redirects=5):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    path = parsed_url.path or '/'
    port = 443 if parsed_url.scheme == 'https' else 80

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if parsed_url.scheme == 'https':
        context = ssl.create_default_context()
        wrapped_socket = context.wrap_socket(sock, server_hostname=hostname)
    else:
        wrapped_socket = sock
    wrapped_socket.connect((hostname, port))

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {hostname}\r\n"
        "Connection: close\r\n"
        "Accept-Encoding: identity\r\n"
        "User-Agent: MyScraper/1.0\r\n\r\n"
    )
    wrapped_socket.send(request.encode())

    response = b''
    while True:
        data = wrapped_socket.recv(4096)
        if not data:
            break
        response += data

    wrapped_socket.close()

    header_end = response.find(b'\r\n\r\n')
    if header_end == -1:
        raise ValueError("Could not find the end of the headers in the HTTP response")
    headers = response[:header_end].decode('iso-8859-1')
    body = response[header_end + 4:]

    header_lines = headers.split('\r\n')
    status_line = header_lines[0]
    _, status_code, status_message = status_line.split(' ', 2)
    status_code = int(status_code)

    if status_code in (301, 302):
        if max_redirects <= 0:
            raise ValueError("Maximum number of redirects exceeded")
        location = None
        for header in header_lines[1:]:
            if header.lower().startswith('location:'):
                location = header.split(':', 1)[1].strip()
                break
        if location is None:
            raise ValueError("Redirect response but no Location header found")
        if location.startswith('/'):
            location = f"{parsed_url.scheme}://{hostname}{location}"
        elif not location.startswith('http'):
            location = f"{parsed_url.scheme}://{hostname}/{location}"
        return get_http_response_body(location, max_redirects - 1)
    elif status_code != 200:
        raise ValueError(f"HTTP request failed with status code {status_code}: {status_message}")

    content_encoding = None
    for header in header_lines[1:]:
        if header.lower().startswith('content-encoding:'):
            content_encoding = header.split(':', 1)[1].strip().lower()
            break

    if content_encoding == 'gzip':
        body = gzip.decompress(body)
    elif content_encoding == 'deflate':
        body = zlib.decompress(body)

    body_text = body.decode('utf-8', errors='replace')
    return body_text
