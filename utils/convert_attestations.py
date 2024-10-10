"""Convert Sigstore attestations to PEP 740.

See https://github.com/trailofbits/pypi-attestations.
"""

import json
import sys
from base64 import b64decode
from pathlib import Path

from pypi_attestations import Attestation, Distribution
from sigstore.models import Bundle
from sigstore.verify import Verifier
from sigstore.verify.policy import Identity

DIST = Path('dist')
bundle_path = Path(sys.argv[1])
signer_identity = sys.argv[2]

for line in bundle_path.read_bytes().splitlines():
    dsse_envelope_payload = json.loads(line)['dsseEnvelope']['payload']
    subjects = json.loads(b64decode(dsse_envelope_payload))['subject']
    for subject in subjects:
        filename = subject['name']
        assert (DIST / filename).is_file()

        # Convert attestation from Sigstore to PEP 740
        print(f'Converting attestation for {filename}')
        sigstore_bundle = Bundle.from_json(line)
        attestation = Attestation.from_bundle(sigstore_bundle)
        attestation_path = DIST / f'{filename}.publish.attestation'
        attestation_path.write_text(attestation.model_dump_json())
        print(f'Attestation for {filename} written to {attestation_path}')
        print()

        # Validate attestation
        dist = Distribution.from_file(DIST / filename)
        attestation = Attestation.model_validate_json(attestation_path.read_bytes())
        verifier = Verifier.production()
        policy = Identity(identity=signer_identity)
        attestation.verify(verifier, policy, dist)
        print(f'Verified {attestation_path}')
