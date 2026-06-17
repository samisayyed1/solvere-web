// §7.10 — Footer. Cream-deep bg. Three columns desktop / stacked mobile.
// Hairline rule above. Bottom row with copyright, hairline rule above.

export function Footer() {
  return (
    <footer
      aria-label="Site footer"
      className="bg-cream-deep border-t border-rule"
    >
      <div className="mx-auto max-w-content px-3 md:px-5 py-6 md:py-7">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6">
          <div>
            <p className="font-display font-medium text-[18px] leading-none text-ink">
              Solvere
            </p>
            <p className="mt-3 font-sans text-muted text-caption-m md:text-caption-d tracking-normal">
              1WEB FZE
              <br />
              Abu Dhabi, United Arab Emirates
            </p>
          </div>

          <div className="md:text-center">
            <a
              href="mailto:hello@solvere.ai"
              className="font-sans text-ink-soft text-body-m md:text-body-d underline-offset-4 hover:underline"
            >
              hello@solvere.ai
            </a>
          </div>

          <div className="md:text-right">
            <p className="font-sans text-muted text-caption-m md:text-caption-d tracking-normal">
              DIFC Data Protection Law compliant.
              <br />
              No protected health information is collected via this website.
              <br />
              Sensitive data exchange occurs only after a signed NDA via
              secure encrypted channels.
            </p>
          </div>
        </div>

        <div className="mt-6 md:mt-7 border-t border-rule pt-4 text-center">
          <p className="font-sans text-muted text-caption-m md:text-caption-d tracking-normal">
            © 2026 1WEB FZE. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
