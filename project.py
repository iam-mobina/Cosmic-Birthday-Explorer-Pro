import json
import os
import random
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


NASA_APOD_URL = "https://science.nasa.gov/wp-json/wp/v2/apod-basic/"
API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
APOD_START_DATE = date(1995, 6, 16)

HISTORY_FILE = Path("history.json")
REPORTS_DIR = Path("reports")
IMAGES_DIR = Path("images")
MAX_HISTORY = 20

console = Console()


def main():
    while True:
        print_header()
        console.print("[bold cyan]1.[/] Explore my birthday")
        console.print("[bold cyan]2.[/] Search a specific date")
        console.print("[bold cyan]3.[/] Random APOD")
        console.print("[bold cyan]4.[/] View history")
        console.print("[bold cyan]5.[/] Clear history")
        console.print("[bold cyan]6.[/] Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            explore_birthday()
        elif choice == "2":
            search_specific_date()
        elif choice == "3":
            random_apod()
        elif choice == "4":
            view_history()
        elif choice == "5":
            clear_history()
        elif choice == "6":
            console.print("\n[green]Thank you for exploring the universe![/]")
            break
        else:
            console.print("[red]Invalid option.[/]")

        input("\nPress Enter to continue...")


def print_header():
    console.print(
        Panel.fit(
            "[bold magenta]Cosmic Birthday Explorer Pro[/]\n"
            "[cyan]NASA APOD birthday and space discovery tool[/]",
            border_style="bright_blue",
        )
    )


def explore_birthday():
    month = input("Birth month (1-12): ")
    day = input("Birth day (1-31): ")

    if not validate_date(month, day):
        console.print("[red]Invalid date.[/]")
        return

    try:
        data = find_latest_apod_for_birthday(month, day)
        handle_result(data)
    except ValueError:
        console.print("[red]No APOD was found for this birthday.[/]")


def search_specific_date():
    user_date = input("Enter date (YYYY-MM-DD): ").strip()

    if not validate_full_date(user_date):
        console.print("[red]Invalid date or date outside APOD archive.[/]")
        return

    try:
        data = fetch_apod(user_date)
        handle_result(data)
    except requests.RequestException:
        console.print("[red]Could not fetch APOD.[/]")


def random_apod():
    random_date = get_random_apod_date()

    try:
        data = fetch_apod(random_date)
        handle_result(data)
    except requests.RequestException:
        console.print("[red]Could not fetch random APOD.[/]")


def handle_result(data):
    print_report(data)
    print_quick_facts(data)
    save_report(data)
    save_history(data)
    offer_image_download(data)


def offer_image_download(data):
    if data["media_type"] != "image":
        console.print("[yellow]This APOD is not an image, so there is no image to download.[/]")
        return

    console.print("\n[bold]Image detected.[/]")
    console.print("1. Download image")
    console.print("2. Skip")

    choice = input("> ").strip()

    if choice != "1":
        console.print("[yellow]Image download skipped.[/]")
        return

    try:
        filename = download_image(data)
        console.print(f"[green]Image saved to {filename}[/]")
        print_image_info(filename)

        console.print("\n[bold]Open image now?[/]")
        console.print("1. Yes")
        console.print("2. No")

        open_choice = input("> ").strip()

        if open_choice == "1":
            open_file(filename)

    except ValueError:
        console.print("[yellow]This APOD is not an image.[/]")
    except requests.RequestException:
        console.print("[red]Could not download image.[/]")


def validate_date(month, day):
    try:
        date(2024, int(month), int(day))
        return True
    except ValueError:
        return False


def validate_full_date(user_date):
    try:
        chosen_date = date.fromisoformat(user_date)
        return APOD_START_DATE <= chosen_date <= date.today()
    except ValueError:
        return False


def format_apod_date(month, day, year=2024):
    return f"{int(year)}-{int(month):02d}-{int(day):02d}"


def find_latest_apod_for_birthday(month, day):
    for year in range(date.today().year, APOD_START_DATE.year - 1, -1):
        apod_date = date(year, int(month), int(day))

        if apod_date < APOD_START_DATE or apod_date > date.today():
            continue

        try:
            return fetch_apod(apod_date.isoformat())
        except requests.RequestException:
            continue

    raise ValueError("No APOD found.")


def get_random_apod_date():
    days_range = (date.today() - APOD_START_DATE).days
    random_days = random.randint(0, days_range)
    return (APOD_START_DATE + timedelta(days=random_days)).isoformat()

def fetch_apod(apod_date):
    date_code = apod_date.replace("-", "")[2:]
    request_url = f"{NASA_APOD_URL}{date_code}"

    response = requests.get(
        request_url,
        params={"api_key": API_KEY},
        timeout=15,
    )
    response.raise_for_status()
    result = response.json()

    if isinstance(result, list):
        data = next(
            (
                item for item in result
                if isinstance(item, dict)
                and item.get("date") == apod_date
            ),
            None,
        )

        if data is None:
            raise ValueError(
                f"No APOD found for {apod_date}"
            )

    elif isinstance(result, dict):
        data = result

    else:
        raise ValueError(
            "Unexpected response from NASA API."
        )

    title = data.get("title", "No title")
    explanation = data.get(
        "explanation",
        "No explanation available."
    )

    return {
        "title": title,
        "date": data.get("date", apod_date),
        "media_type": data.get("media_type", "unknown"),
        "url": get_best_media_url(data),
        "explanation": explanation,
        "summary": simplify_explanation(explanation),
        "category": classify_space_object(
            title, explanation
        ),
        "telescope": detect_telescope(
            title, explanation
        ),
        "quick_object": detect_known_object(
            title, explanation
        ),
    }


def get_best_media_url(data):
    if data.get("media_type") == "image":
        return data.get("hdurl") or "No image URL"

    return data.get("thumbnail_url") or "No image URL"


def classify_space_object(title, explanation):
    text = f"{title} {explanation}".lower()

    if "galaxy" in text or "galaxies" in text:
        return "Galaxy"
    if "nebula" in text:
        return "Nebula"
    if any(planet in text for planet in ["mars", "jupiter", "saturn", "venus", "mercury", "uranus", "neptune"]):
        return "Planet"
    if "moon" in text:
        return "Moon"
    if "earth" in text:
        return "Planet"
    if "star" in text or "supernova" in text:
        return "Star"
    return "Deep Space Object"


def detect_telescope(title, explanation):
    text = f"{title} {explanation}".lower()

    if "james webb" in text or "jwst" in text or "webb" in text:
        return "James Webb Space Telescope"
    if "hubble" in text:
        return "Hubble Space Telescope"
    if "spitzer" in text:
        return "Spitzer Space Telescope"
    if "chandra" in text:
        return "Chandra X-ray Observatory"
    if "international space station" in text or "iss" in text:
        return "International Space Station"
    return "Other / Unknown"


def detect_known_object(title, explanation):
    text = f"{title} {explanation}".lower()

    known_objects = {
        "earth": "Earth",
        "mars": "Mars",
        "jupiter": "Jupiter",
        "saturn": "Saturn",
        "venus": "Venus",
        "mercury": "Mercury",
        "uranus": "Uranus",
        "neptune": "Neptune",
        "moon": "Moon",
        "andromeda": "Andromeda Galaxy",
        "orion nebula": "Orion Nebula",
        "ring nebula": "Ring Nebula",
        "crab nebula": "Crab Nebula",
        "milky way": "Milky Way",
    }

    for keyword, name in known_objects.items():
        if keyword in text:
            return name

    return "Unknown"


def simplify_explanation(explanation, max_sentences=2):
    sentences = explanation.split(". ")

    if len(sentences) <= max_sentences:
        return explanation

    return ". ".join(sentences[:max_sentences]).strip() + "."


def print_report(data):
    console.print("\n[bold cyan]Your Cosmic Report[/]")

    table = Table(show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Date", data["date"])
    table.add_row("Title", data["title"])
    table.add_row("Media Type", data["media_type"])
    table.add_row("Category", data["category"])
    table.add_row("Detected Object", data["quick_object"])
    table.add_row("Telescope / Source", data["telescope"])
    table.add_row("URL", data["url"])

    console.print(table)
    console.print(Panel(data["summary"], title="Short Explanation", border_style="green"))
    console.print(Panel(data["explanation"], title="Full NASA Explanation", border_style="blue"))


def print_quick_facts(data):
    table = Table(title="Quick Facts", title_style="bold magenta")
    table.add_column("Item", style="bold cyan")
    table.add_column("Information")

    table.add_row("Object Type", data["category"])
    table.add_row("Detected Object", data["quick_object"])
    table.add_row("Source / Telescope", data["telescope"])
    table.add_row("NASA Media Type", data["media_type"])
    table.add_row("Published Date", data["date"])

    telescope_facts = get_telescope_facts(data["telescope"])
    object_facts = get_object_facts(data["quick_object"])

    for item, value in telescope_facts.items():
        table.add_row(item, value)

    for item, value in object_facts.items():
        table.add_row(item, value)

    console.print(table)


def get_telescope_facts(telescope):
    facts = {
        "James Webb Space Telescope": {
            "Telescope Launch": "2021",
            "Primary Mirror": "6.5 meters",
            "Orbit": "Sun-Earth L2",
            "Mission Focus": "Infrared astronomy",
        },
        "Hubble Space Telescope": {
            "Telescope Launch": "1990",
            "Primary Mirror": "2.4 meters",
            "Orbit": "Low Earth Orbit",
            "Mission Focus": "Visible, ultraviolet, and infrared astronomy",
        },
        "Spitzer Space Telescope": {
            "Telescope Launch": "2003",
            "Mission Focus": "Infrared astronomy",
            "Status": "Retired in 2020",
        },
        "Chandra X-ray Observatory": {
            "Telescope Launch": "1999",
            "Mission Focus": "X-ray astronomy",
            "Orbit Type": "Highly elliptical Earth orbit",
        },
        "International Space Station": {
            "Launch / Assembly Start": "1998",
            "Orbit": "Low Earth Orbit",
            "Role": "Human spaceflight laboratory",
        },
    }

    return facts.get(telescope, {})


def get_object_facts(object_name):
    facts = {
        "Earth": {
            "Planet Radius": "6,371 km",
            "Estimated Age": "4.54 billion years",
            "Natural Satellite": "Moon",
        },
        "Mars": {
            "Planet Type": "Terrestrial planet",
            "Known For": "Iron-rich red surface",
            "Moons": "Phobos and Deimos",
        },
        "Jupiter": {
            "Planet Type": "Gas giant",
            "Known For": "Great Red Spot",
            "Largest Moon": "Ganymede",
        },
        "Saturn": {
            "Planet Type": "Gas giant",
            "Known For": "Large ring system",
            "Largest Moon": "Titan",
        },
        "Moon": {
            "Object Type": "Natural satellite",
            "Parent Body": "Earth",
            "Average Distance": "384,400 km from Earth",
        },
        "Andromeda Galaxy": {
            "Object Type": "Spiral galaxy",
            "Approx. Distance": "2.5 million light-years",
            "Constellation": "Andromeda",
        },
        "Orion Nebula": {
            "Object Type": "Emission nebula",
            "Approx. Distance": "1,344 light-years",
            "Constellation": "Orion",
        },
        "Ring Nebula": {
            "Object Type": "Planetary nebula",
            "Constellation": "Lyra",
        },
        "Crab Nebula": {
            "Object Type": "Supernova remnant",
            "Constellation": "Taurus",
        },
        "Milky Way": {
            "Object Type": "Barred spiral galaxy",
            "Contains": "Solar System",
        },
    }

    return facts.get(object_name, {})


def download_image(data):
    if data["media_type"] != "image":
        raise ValueError("APOD is not an image.")

    IMAGES_DIR.mkdir(exist_ok=True)

    extension = get_file_extension(data["url"])
    filename = IMAGES_DIR / f"{data['date']}{extension}"

    response = requests.get(data["url"], timeout=30)
    response.raise_for_status()

    with open(filename, "wb") as file:
        file.write(response.content)

    return filename


def get_file_extension(url):
    clean_url = url.split("?")[0].lower()

    if clean_url.endswith(".png"):
        return ".png"
    if clean_url.endswith(".jpeg"):
        return ".jpeg"
    if clean_url.endswith(".jpg"):
        return ".jpg"
    return ".jpg"


def print_image_info(filename):
    path = Path(filename)
    size_mb = path.stat().st_size / (1024 * 1024)

    with Image.open(path) as image:
        table = Table(title="Image Information", title_style="bold magenta")
        table.add_column("Property", style="bold cyan")
        table.add_column("Value")

        table.add_row("Filename", path.name)
        table.add_row("Saved Location", str(path.resolve()))
        table.add_row("Resolution", f"{image.width} × {image.height}")
        table.add_row("Format", image.format or "Unknown")
        table.add_row("Color Mode", image.mode)
        table.add_row("File Size", f"{size_mb:.2f} MB")
        table.add_row("Aspect Ratio", f"{image.width}:{image.height}")

        console.print(table)


def open_file(filename):
    filename = str(filename)

    if sys.platform.startswith("win"):
        os.startfile(filename)
    elif sys.platform == "darwin":
        subprocess.run(["open", filename], check=False)
    else:
        subprocess.run(["xdg-open", filename], check=False)


def save_report(data):
    REPORTS_DIR.mkdir(exist_ok=True)

    filename = REPORTS_DIR / f"cosmic_report_{data['date']}.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write("=" * 55 + "\n")
        file.write("COSMIC BIRTHDAY EXPLORER PRO REPORT\n")
        file.write("=" * 55 + "\n\n")
        file.write("NASA Astronomy Picture of the Day\n")
        file.write("-" * 55 + "\n\n")
        file.write(f"Date: {data['date']}\n")
        file.write(f"Title: {data['title']}\n")
        file.write(f"Media Type: {data['media_type']}\n")
        file.write(f"Category: {data['category']}\n")
        file.write(f"Detected Object: {data['quick_object']}\n")
        file.write(f"Telescope / Source: {data['telescope']}\n")
        file.write(f"URL: {data['url']}\n\n")
        file.write("Short Explanation:\n")
        file.write(data["summary"] + "\n\n")
        file.write("Full NASA Explanation:\n")
        file.write(data["explanation"] + "\n")

    console.print(f"[green]Report saved to {filename}[/]")


def save_history(data):
    history = load_history()

    item = {
        "date": data["date"],
        "title": data["title"],
        "category": data["category"],
        "object": data["quick_object"],
        "telescope": data["telescope"],
        "url": data["url"],
    }

    history.append(item)
    history = history[-MAX_HISTORY:]

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)


def load_history():
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []


def view_history():
    history = load_history()

    if not history:
        console.print("[yellow]No history yet.[/]")
        return

    table = Table(title=f"Search History — Last {MAX_HISTORY} Entries")
    table.add_column("#")
    table.add_column("Date")
    table.add_column("Title")
    table.add_column("Category")
    table.add_column("Object")
    table.add_column("Telescope / Source")

    for index, item in enumerate(history, start=1):
        table.add_row(
            str(index),
            item["date"],
            item["title"],
            item["category"],
            item.get("object", "Unknown"),
            item["telescope"],
        )

    console.print(table)


def clear_history():
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
        console.print("[green]History cleared.[/]")
    else:
        console.print("[yellow]No history file found.[/]")


if __name__ == "__main__":
    main()