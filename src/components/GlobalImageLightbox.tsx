import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import "../image-lightbox.css";

type LightboxImage = {
  src: string;
  alt: string;
};

const ENLARGEABLE_IMAGE_SELECTOR = ".sidebar > .portrait-image, .visual-reference-card img, .media-preview img";

function matchingImage(target: EventTarget | null): HTMLImageElement | null {
  if (!(target instanceof Element)) return null;
  const image = target.closest(ENLARGEABLE_IMAGE_SELECTOR);
  return image instanceof HTMLImageElement ? image : null;
}

function imagePayload(image: HTMLImageElement): LightboxImage {
  return {
    src: image.currentSrc || image.src,
    alt: image.alt || "Image de référence",
  };
}

export function GlobalImageLightbox() {
  const [image, setImage] = useState<LightboxImage | null>(null);

  useEffect(() => {
    const markImages = () => {
      document.querySelectorAll<HTMLImageElement>(ENLARGEABLE_IMAGE_SELECTOR).forEach((candidate) => {
        candidate.dataset.kitabaEnlargeable = "true";
        candidate.tabIndex = 0;
        candidate.setAttribute("role", "button");
        candidate.setAttribute("aria-label", `${candidate.alt || "Image"} — agrandir`);
      });
    };

    const openFromTarget = (target: EventTarget | null) => {
      const candidate = matchingImage(target);
      if (!candidate) return false;
      setImage(imagePayload(candidate));
      return true;
    };

    const onClick = (event: MouseEvent) => {
      if (openFromTarget(event.target)) event.preventDefault();
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setImage(null);
        return;
      }
      if (event.key !== "Enter" && event.key !== " ") return;
      if (openFromTarget(event.target)) event.preventDefault();
    };

    markImages();
    const observer = new MutationObserver(markImages);
    observer.observe(document.body, { childList: true, subtree: true });
    document.addEventListener("click", onClick);
    document.addEventListener("keydown", onKeyDown);

    return () => {
      observer.disconnect();
      document.removeEventListener("click", onClick);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  useEffect(() => {
    if (!image) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [image]);

  if (!image) return null;

  return createPortal(
    <div
      className="image-lightbox-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label={image.alt}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) setImage(null);
      }}
    >
      <div className="image-lightbox-panel">
        <button className="image-lightbox-close" type="button" onClick={() => setImage(null)} aria-label="Fermer l'image agrandie">Fermer</button>
        <img src={image.src} alt={image.alt} />
        {image.alt && <div className="image-lightbox-caption">{image.alt}</div>}
      </div>
    </div>,
    document.body,
  );
}
