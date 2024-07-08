import pytest


@pytest.fixture
def testing_config():
    from src.config import TestingConfig

    return TestingConfig(
        {
            "STARKBANK_ENVIRONMENT": "sandbox",
            "STARKBANK_PROJECT_ID": "12345678900",
            "STARKBANK_PRIVATE_KEY_CONTENT": """
            -----BEGIN EC PARAMETERS-----
            BgUrgQQACg==
            -----END EC PARAMETERS-----
            -----BEGIN EC PRIVATE KEY-----
            MHQCAQEEIMCwW74H6egQkTiz87WDvLNm7fK/cA+ctA2vg/bbHx3woAcGBSuBBAAK
            oUQDQgAE0iaeEHEgr3oTbCfh8U2L+r7zoaeOX964xaAnND5jATGpD/tHec6Oe9U1
            IF16ZoTVt1FzZ8WkYQ3XomRD4HS13A==
            -----END EC PRIVATE KEY-----
            """,
            "TRANSFERS_TAG": "test",
            
        }
    )
