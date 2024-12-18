EUR_TO_MDL = 19.6
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
# =================================
# Connection utils
# =================================

import socket
import ssl
from urllib.parse import urlparse

def get_http_response_body(url, max_redirects=5):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    path = parsed_url.path or '/'
    port = 443 if parsed_url.scheme == 'https' else 80

    # Create a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if parsed_url.scheme == 'https':
        context = ssl.create_default_context()
        wrapped_socket = context.wrap_socket(sock, server_hostname=hostname)
    else:
        wrapped_socket = sock

    # Connect to the server
    wrapped_socket.connect((hostname, port))

    # Send HTTP GET request
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {hostname}\r\n"
        "Connection: close\r\n"
        "Accept-Encoding: identity\r\n"
        "User-Agent: MyScraper/1.0\r\n\r\n"
    )
    wrapped_socket.send(request.encode())

    # Receive the response
    response = b''
    while True:
        data = wrapped_socket.recv(4096)
        if not data:
            break
        response += data

    # Close the socket
    wrapped_socket.close()

    # Find the end of headers in bytes
    header_end = response.find(b'\r\n\r\n')
    if header_end == -1:
        raise ValueError("Could not find the end of the headers in the HTTP response")
    headers = response[:header_end].decode('iso-8859-1')
    body = response[header_end + 4:]

    # Parse the status code
    header_lines = headers.split('\r\n')
    status_line = header_lines[0]
    _, status_code, status_message = status_line.split(' ', 2)
    status_code = int(status_code)

    if status_code in (301, 302):
        if max_redirects <= 0:
            raise ValueError("Maximum number of redirects exceeded")
        # Find 'Location' header
        location = None
        for header in header_lines[1:]:
            if header.lower().startswith('location:'):
                location = header.split(':', 1)[1].strip()
                break
        if location is None:
            raise ValueError("Redirect response but no Location header found")
        # Handle relative redirects
        if location.startswith('/'):
            location = f"{parsed_url.scheme}://{hostname}{location}"
        elif not location.startswith('http'):
            location = f"{parsed_url.scheme}://{hostname}/{location}"
        # Recursive call to handle redirect
        return get_http_response_body(location, max_redirects - 1)
    elif status_code != 200:
        raise ValueError(f"HTTP request failed with status code {status_code}: {status_message}")

    # Check for Content-Encoding header
    content_encoding = None
    for header in header_lines[1:]:
        if header.lower().startswith('content-encoding:'):
            content_encoding = header.split(':', 1)[1].strip().lower()
            break

    # Decode the body accordingly
    if content_encoding == 'gzip':
        import gzip
        body = gzip.decompress(body)
    elif content_encoding == 'deflate':
        import zlib
        body = zlib.decompress(body)

    # Now, decode body to text
    body_text = body.decode('utf-8', errors='replace')

    return body_text
# =================================
# JSON and XML Serialization utils
# =================================

def json_escape(s):
    """Escape special characters for JSON."""
    result = ''
    for c in s:
        if c == '"':
            result += '\\"'
        elif c == '\\':
            result += '\\\\'
        elif c == '\b':
            result += '\\b'
        elif c == '\f':
            result += '\\f'
        elif c == '\n':
            result += '\\n'
        elif c == '\r':
            result += '\\r'
        elif c == '\t':
            result += '\\t'
        else:
            result += c
    return result

def xml_escape(s):
    """Escape special characters for XML."""
    return s.replace('&', '&amp;') \
            .replace('<', '&lt;') \
            .replace('>', '&gt;') \
            .replace('"', '&quot;') \
            .replace("'", '&apos;')

def serialize_product_to_json(product):
    """Manually serialize a Product object to a JSON-formatted string."""
    json_str = '{\n'
    json_str += f'    "product_name": "{json_escape(product.product_name)}",\n'
    json_str += f'    "price": {product.price},\n'
    json_str += f'    "currency": "{json_escape(product.currency)}",\n'
    if product.specifications is None:
        json_str += '    "specifications": null,\n'
    else:
        json_str += '    "specifications": [\n'
        for i, spec in enumerate(product.specifications):
            comma = ',' if i < len(product.specifications) - 1 else ''
            json_str += f'        "{json_escape(spec)}"{comma}\n'
        json_str += '    ],\n'
    scrape_time_str = product.scrape_time_utc.isoformat()
    json_str += f'    "scrape_time_utc": "{scrape_time_str}"\n'
    json_str += '}'
    return json_str

def serialize_product_to_xml(product):
    """Manually serialize a Product object to an XML-formatted string."""
    xml_str = '<Product>\n'
    xml_str += f'    <product_name>{xml_escape(product.product_name)}</product_name>\n'
    xml_str += f'    <price>{product.price}</price>\n'
    xml_str += f'    <currency>{xml_escape(product.currency)}</currency>\n'
    if product.specifications is not None:
        xml_str += '    <specifications>\n'
        for spec in product.specifications:
            xml_str += f'        <specification>{xml_escape(spec)}</specification>\n'
        xml_str += '    </specifications>\n'
    scrape_time_str = product.scrape_time_utc.isoformat()
    xml_str += f'    <scrape_time_utc>{scrape_time_str}</scrape_time_utc>\n'
    xml_str += '</Product>'
    return xml_str

# =================================
# Custom serialization utils
# =================================

import struct
from datetime import datetime
from models import Product

def serialize_product_custom(product):
    """Custom serialize a Product object."""
    data = b''

    # Serialize each field
    fields = [
        ('product_name', "hello"),
        ('price', 112),
        ('currency', "rubles"),
        ('specifications', ["ivbnm","fvgbhmkl"]),
        ('scrape_time_utc', product.scrape_time_utc)
    ]

    for field_name, value in fields:
        # Field Name Length and Field Name
        field_name_bytes = field_name.encode('utf-8')
        field_name_len = len(field_name_bytes)
        if field_name_len > 255:
            raise ValueError(f"Field name too long: {field_name}")
        data += struct.pack('B', field_name_len)
        data += field_name_bytes

        # Type code and Value
        if isinstance(value, str):
            type_code = b'S'
            value_bytes = value.encode('utf-8')
            value_len = len(value_bytes)
            data += type_code
            data += struct.pack('I', value_len)
            data += value_bytes
        elif isinstance(value, int):
            type_code = b'I'
            data += type_code
            data += struct.pack('i', value)  # 4-byte signed integer
        elif isinstance(value, float):
            type_code = b'F'
            data += type_code
            data += struct.pack('d', value)  # 8-byte double-precision float
        elif isinstance(value, list):
            type_code = b'L'
            data += type_code
            num_elements = len(value)
            data += struct.pack('I', num_elements)
            for item in value:
                item_bytes = item.encode('utf-8')
                item_len = len(item_bytes)
                data += struct.pack('I', item_len)
                data += item_bytes
        elif isinstance(value, datetime):
            type_code = b'D'
            value_str = value.isoformat()
            value_bytes = value_str.encode('utf-8')
            value_len = len(value_bytes)
            data += type_code
            data += struct.pack('I', value_len)
            data += value_bytes
        else:
            raise TypeError(f"Unsupported field type for field {field_name}: {type(value)}")

    return data

def deserialize_product_custom(data):
    """Custom deserialize a Product object from bytes."""
    offset = 0
    fields = {}

    while offset < len(data):
        # Read Field Name Length
        field_name_len = struct.unpack_from('B', data, offset)[0]
        offset += 1
        # Read Field Name
        field_name = data[offset:offset+field_name_len].decode('utf-8')
        offset += field_name_len
        # Read Type Code
        type_code = data[offset:offset+1]
        offset += 1

        if type_code == b'S':
            # String
            value_len = struct.unpack_from('I', data, offset)[0]
            offset += 4
            value_bytes = data[offset:offset+value_len]
            value = value_bytes.decode('utf-8')
            offset += value_len
        elif type_code == b'I':
            # Integer
            value = struct.unpack_from('i', data, offset)[0]
            offset += 4
        elif type_code == b'F':
            # Float
            value = struct.unpack_from('d', data, offset)[0]
            offset += 8
        elif type_code == b'L':
            # List
            num_elements = struct.unpack_from('I', data, offset)[0]
            offset += 4
            value = []
            for _ in range(num_elements):
                item_len = struct.unpack_from('I', data, offset)[0]
                offset += 4
                item_bytes = data[offset:offset+item_len]
                item = item_bytes.decode('utf-8')
                value.append(item)
                offset += item_len
        elif type_code == b'D':
            # Datetime
            value_len = struct.unpack_from('I', data, offset)[0]
            offset += 4
            value_bytes = data[offset:offset+value_len]
            value_str = value_bytes.decode('utf-8')
            value = datetime.fromisoformat(value_str)
            offset += value_len
        else:
            raise ValueError(f"Unknown type code: {type_code}")

        fields[field_name] = value

    # Create Product object
    product = Product(
        product_name=fields.get('product_name'),
        price=fields.get('price'),
        currency=fields.get('currency'),
        specifications=fields.get('specifications'),
        scrape_time_utc=fields.get('scrape_time_utc')
    )

    return product
