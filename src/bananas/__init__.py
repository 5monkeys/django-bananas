VERSION = (2, 4, 0, "final", 0)


def get_version() -> str:
    """Derives a PEP386-compliant version number from VERSION."""
    assert len(VERSION) == 5
    assert VERSION[3] in ("alpha", "beta", "rc", "final")

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases

    parts = 2 if VERSION[2] == 0 else 3
    main = ".".join(str(x) for x in VERSION[:parts])

    sub = ""
    if VERSION[3] != "final":
        mapping = {"alpha": "a", "beta": "b", "rc": "c"}
        sub = mapping[VERSION[3]] + str(VERSION[4])

    return main + sub


__version__ = get_version()
