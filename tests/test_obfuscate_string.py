from rectifier.obfuscate_string import obfuscate_string


def test_obfuscate_string():
    assert (
        obfuscate_string('aaf34c5e-asdf-zxcd-14141-80360cdf0df0')
        == 'aaf3****-****-****-*****-************'
    )
