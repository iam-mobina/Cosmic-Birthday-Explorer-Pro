from datetime import date
from project import (
    APOD_START_DATE,
    validate_date,
    validate_full_date,
    format_apod_date,
    classify_space_object,
    detect_telescope,
    detect_known_object,
    simplify_explanation,
    get_file_extension,
    get_random_apod_date,
    get_telescope_facts,
    get_object_facts,
)


def test_validate_date():
    assert validate_date("1", "1") is True
    assert validate_date("12", "31") is True
    assert validate_date("2", "30") is False
    assert validate_date("13", "1") is False
    assert validate_date("hello", "1") is False


def test_validate_full_date():
    assert validate_full_date("1995-06-16") is True
    assert validate_full_date("1995-06-15") is False
    assert validate_full_date("hello") is False
    assert validate_full_date("2024-02-30") is False
    assert validate_full_date(date.today().isoformat()) is True


def test_format_apod_date():
    assert format_apod_date("1", "5") == "2024-01-05"
    assert format_apod_date("12", "31") == "2024-12-31"
    assert format_apod_date("4", "28", 2026) == "2026-04-28"


def test_classify_space_object():
    assert classify_space_object("Andromeda Galaxy", "") == "Galaxy"
    assert classify_space_object("Orion Nebula", "") == "Nebula"
    assert classify_space_object("The Moon", "") == "Moon"
    assert classify_space_object("Planet Earth at Twilight", "") == "Planet"
    assert classify_space_object("Jupiter and its moons", "") == "Planet"
    assert classify_space_object("Unknown object", "") == "Deep Space Object"


def test_detect_telescope():
    assert detect_telescope("James Webb captures a galaxy", "") == "James Webb Space Telescope"
    assert detect_telescope("JWST image", "") == "James Webb Space Telescope"
    assert detect_telescope("Hubble views a nebula", "") == "Hubble Space Telescope"
    assert detect_telescope("Spitzer infrared image", "") == "Spitzer Space Telescope"
    assert detect_telescope("Chandra X-ray data", "") == "Chandra X-ray Observatory"
    assert detect_telescope("Photo from the International Space Station", "") == "International Space Station"
    assert detect_telescope("Beautiful Milky Way", "") == "Other / Unknown"


def test_detect_known_object():
    assert detect_known_object("Planet Earth at Twilight", "") == "Earth"
    assert detect_known_object("Mars at Opposition", "") == "Mars"
    assert detect_known_object("The Orion Nebula", "") == "Orion Nebula"
    assert detect_known_object("The Andromeda Galaxy", "") == "Andromeda Galaxy"
    assert detect_known_object("Unknown deep field", "") == "Unknown"


def test_simplify_explanation():
    text = "This is sentence one. This is sentence two. This is sentence three."
    assert simplify_explanation(text) == "This is sentence one. This is sentence two."
    assert simplify_explanation("Only one sentence.") == "Only one sentence."


def test_get_file_extension():
    assert get_file_extension("https://example.com/image.jpg") == ".jpg"
    assert get_file_extension("https://example.com/image.png") == ".png"
    assert get_file_extension("https://example.com/image.jpeg") == ".jpeg"
    assert get_file_extension("https://example.com/image") == ".jpg"


def test_get_random_apod_date():
    random_date = date.fromisoformat(get_random_apod_date())
    assert APOD_START_DATE <= random_date <= date.today()


def test_get_telescope_facts():
    jwst = get_telescope_facts("James Webb Space Telescope")
    assert jwst["Telescope Launch"] == "2021"

    hubble = get_telescope_facts("Hubble Space Telescope")
    assert hubble["Primary Mirror"] == "2.4 meters"

    unknown = get_telescope_facts("Unknown Telescope")
    assert unknown == {}


def test_get_object_facts():
    earth = get_object_facts("Earth")
    assert earth["Natural Satellite"] == "Moon"

    andromeda = get_object_facts("Andromeda Galaxy")
    assert andromeda["Object Type"] == "Spiral galaxy"

    unknown = get_object_facts("Unknown")
    assert unknown == {}
