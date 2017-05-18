import sys

if sys.version_info < (3, ):
    from urlparse import urldefrag
else:
    from urllib.parse import urldefrag
    
    
__all__ = ["urldefrag"]
