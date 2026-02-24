from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize the Limiter instance
# We use get_remote_address to rate limit based on the client's IP address
limiter = Limiter(key_func=get_remote_address)
