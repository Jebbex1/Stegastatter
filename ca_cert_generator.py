import subprocess
import sys

CA_KEY = "certificate_authority_secrets/ca-key.pem"
CA_CERT = "shared/certificate_authority/ca-cert.pem"


def generate_ca():
    subprocess.run(["openssl", "genrsa", "-aes256", "-out", f"\'{CA_KEY}\'", "4096"],
                   stderr=sys.stdout)
    subprocess.run(["openssl", "req", "-new", "-x509", "-sha256", "-days", "3650", "-key", f"\'{CA_KEY}\'", "-out",
                    f"\'{CA_CERT}\'"],
                   stderr=sys.stdout)
    subprocess.run(["openssl", "x509", "-in", f"\'{CA_CERT}\'", "-purpose", "-noout", "-text"],
                   stderr=sys.stdout)


if __name__ == '__main__':
    generate_ca()
