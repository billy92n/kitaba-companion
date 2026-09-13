from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_character_and_reference_images_open_in_global_lightbox():
    main = read("src/main.tsx")
    component = read("src/components/GlobalImageLightbox.tsx")
    css = read("src/image-lightbox.css")

    assert 'import { GlobalImageLightbox } from "./components/GlobalImageLightbox"' in main
    assert "<GlobalImageLightbox />" in main
    assert ".sidebar > .portrait-image" in component
    assert ".visual-reference-card img" in component
    assert ".media-preview img" in component
    assert "createPortal" in component
    assert 'event.key === "Escape"' in component
    assert 'event.key !== "Enter" && event.key !== " "' in component
    assert "MutationObserver" in component
    assert 'document.body.style.overflow = "hidden"' in component
    assert ".image-lightbox-backdrop" in css
    assert "max-width: 94vw" in css
    assert "max-height: 86vh" in css
    assert "object-fit: contain" in css


def test_map_image_is_not_accidentally_opened_as_profile_lightbox():
    component = read("src/components/GlobalImageLightbox.tsx")
    selector_line = next(line for line in component.splitlines() if "ENLARGEABLE_IMAGE_SELECTOR" in line and "const" in line)
    assert "interactive-map" not in selector_line
