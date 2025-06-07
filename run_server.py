import sys

from server.steganography_server import Server

if __name__ == '__main__':
    record_secrets = False
    if len(sys.argv) > 1:
        record_secrets = sys.argv[1] == '--rec-secrets'
    if record_secrets:
        print("Recording TLS secrets!")
    s = Server(record_secrets)
    s.start()
