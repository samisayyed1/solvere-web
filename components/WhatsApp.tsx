"use client";

const WA_NUMBER = "971566320559";
const WA_MESSAGE =
  "Hi — I'm interested in Solvere and would like to know more about your claim recovery service.";

export function whatsappUrl(message: string = WA_MESSAGE) {
  return `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(message)}`;
}

export function WhatsAppGlyph({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M19.05 4.91A9.82 9.82 0 0 0 12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38a9.9 9.9 0 0 0 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.91-7.01zM12.04 20.15a8.21 8.21 0 0 1-4.19-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.2 8.2 0 0 1-1.26-4.38c0-4.54 3.7-8.24 8.24-8.24 2.2 0 4.27.86 5.82 2.42a8.18 8.18 0 0 1 2.41 5.83c0 4.54-3.7 8.24-8.23 8.24zm4.52-6.16c-.25-.12-1.47-.72-1.69-.81-.23-.08-.39-.12-.56.12s-.64.81-.78.97c-.14.17-.29.19-.54.06-.25-.12-1.05-.39-1.99-1.23-.74-.66-1.23-1.47-1.38-1.72-.14-.25-.02-.38.11-.51.11-.11.25-.29.37-.43.12-.14.16-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.41-.42-.56-.43-.14-.01-.31-.01-.48-.01-.17 0-.43.06-.66.31-.23.25-.86.84-.86 2.05 0 1.21.88 2.38 1 2.55.12.17 1.74 2.65 4.21 3.72.59.25 1.05.41 1.41.52.59.19 1.13.16 1.55.1.47-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.14-1.18-.06-.1-.22-.16-.46-.28z" />
    </svg>
  );
}

// Compact icon-only button (nav, tight spaces)
export function WhatsAppIconButton({
  className = "",
  message,
}: {
  className?: string;
  message?: string;
}) {
  return (
    <a
      href={whatsappUrl(message)}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Chat on WhatsApp"
      className={`inline-flex items-center justify-center w-9 h-9 rounded-full border border-ink/15 text-ink-soft/70 hover:text-teal hover:border-teal/40 transition-colors ${className}`}
    >
      <WhatsAppGlyph className="w-[18px] h-[18px]" />
    </a>
  );
}

// Outline pill — pairs beside primary dark CTA on cream sections
export function WhatsAppPillLight({
  message,
  label = "WhatsApp",
  className = "",
}: {
  message?: string;
  label?: string;
  className?: string;
}) {
  return (
    <a
      href={whatsappUrl(message)}
      target="_blank"
      rel="noopener noreferrer"
      className={`group inline-flex items-center gap-2.5 rounded-full border border-ink/15 text-ink px-5 py-2.5 text-[15px] font-medium hover:border-teal hover:text-teal transition-colors ${className}`}
    >
      <WhatsAppGlyph className="w-[18px] h-[18px] text-teal" />
      {label}
    </a>
  );
}

// Outline pill for INK/dark sections (FinalCta)
export function WhatsAppPillDark({
  message,
  label = "WhatsApp",
  className = "",
}: {
  message?: string;
  label?: string;
  className?: string;
}) {
  return (
    <a
      href={whatsappUrl(message)}
      target="_blank"
      rel="noopener noreferrer"
      className={`group inline-flex items-center gap-2.5 rounded-full border border-cream/20 text-cream px-5 py-2.5 text-[15px] font-medium hover:border-teal hover:bg-teal/10 transition-colors ${className}`}
    >
      <WhatsAppGlyph className="w-[18px] h-[18px] text-teal" />
      {label}
    </a>
  );
}
